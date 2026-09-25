"""AudioEngine: liga a fila de prioridade (`priority.py`) e o bipe contínuo
(`synth.py`) na saída de verdade (`player.py`) — duas threads, bipe e voz, que o
sistema operacional mixa no mesmo dispositivo (arquitetura seção 8). Nenhuma mistura
de amostras feita à mão aqui: menos código de baixo nível, menos risco de travar ou
estourar o áudio.

`update()`/`notify_*` só escrevem em estado compartilhado (com lock) — são chamados
pela thread principal, sem bloquear. Quem de fato toca som são as duas threads de
`start()`.

Testado automaticamente só a fiação (com um Player falso, sem hardware — o que vira
`BeepSpec`/`SpeechSpec`, quem interrompe quem). A qualidade do som de verdade (sem
clique, sem atraso perceptível) só se valida ouvindo (Fase 0.5/3a).
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from visao.audio import synth
from visao.audio.player import AudioPlayer, Player, load_wav
from visao.audio.priority import Acao, VoiceState, canal_livre, chegou, deve_repetir_falha
from visao.controls.types import Confirmacao
from visao.core.types import AlertPlan, SpeechSpec
from visao.supervisor.types import FaultKind, SupervisorReport, SystemState


def falha_para_fala(fault: FaultKind) -> SpeechSpec:
    """P0 (arquitetura seção 6) — a chave do fault já é a chave certa do vocabulário."""
    return SpeechSpec(clip_keys=(fault.value,), priority=0)


def confirmacao_para_fala(confirmacao: Confirmacao) -> SpeechSpec | None:
    """P2. `beep_referencia` não é uma fala — o engine toca o bipe de referência direto."""
    if confirmacao.clip_key is None:
        return None
    return SpeechSpec(clip_keys=(confirmacao.clip_key,), priority=2)


class AudioEngine:
    def __init__(self, clip_dir: Path, params: dict, player: AudioPlayer | None = None) -> None:
        self._clip_dir = clip_dir
        self._params = params
        self._player = player if player is not None else Player()

        self._encerrar = threading.Event()
        self._voice_wake = threading.Event()

        self._beep_lock = threading.Lock()
        self._beep_spec = None  # BeepSpec | None

        self._voice_lock = threading.Lock()
        self._voice_state = VoiceState()
        self._falha_ativa: FaultKind | None = None
        self._falha_ultima_vez: float | None = None

        self._beep_thread: threading.Thread | None = None
        self._voice_thread: threading.Thread | None = None

    # --- ciclo de vida ------------------------------------------------------------

    def start(self) -> None:
        self._encerrar.clear()
        self._beep_thread = threading.Thread(target=self._loop_bipe, daemon=True)
        self._voice_thread = threading.Thread(target=self._loop_voz, daemon=True)
        self._beep_thread.start()
        self._voice_thread.start()

    def stop(self) -> None:
        self._encerrar.set()
        self._voice_wake.set()
        self._player.stop()
        for t in (self._beep_thread, self._voice_thread):
            if t is not None:
                t.join(timeout=2)

    # --- entradas: decide(), supervisor, controles ---------------------------------

    def update(self, plan: AlertPlan, now: float) -> None:
        """Chamado a cada frame processado pelo `decide()`."""
        with self._beep_lock:
            self._beep_spec = plan.beep
        if plan.speech is not None:
            self._enfileirar(plan.speech, plan.t_capture, now)

    def notify_supervisor(self, report: SupervisorReport, now: float) -> None:
        """RN-04: falha repete a cada [3 s] até se resolver; trocar de falha anuncia
        na hora, sem esperar o intervalo da falha anterior.

        Corta direto (sem passar por `chegou()`): duas falhas diferentes têm a mesma
        prioridade (P0) entre si, então a fila genérica só colocaria a segunda para
        esperar — mas P0 é sempre a verdade atual, tem que substituir a anterior, não
        esperar a vez.
        """
        if report.state != SystemState.FALHA:
            self._falha_ativa = None
            self._falha_ultima_vez = None
            return
        if report.fault is None:  # não deveria acontecer — na dúvida, não quebra
            return
        if self._falha_ativa != report.fault or deve_repetir_falha(
            self._falha_ultima_vez, now, self._params
        ):
            with self._voice_lock:
                self._voice_state = VoiceState(tocando=falha_para_fala(report.fault))
            self._player.stop()
            self._voice_wake.set()
            self._falha_ultima_vez = now
        self._falha_ativa = report.fault

    def notify_confirmacao(self, confirmacao: Confirmacao, now: float) -> None:
        fala = confirmacao_para_fala(confirmacao)
        if fala is not None:
            self._enfileirar(fala, now, now)
        if confirmacao.beep_referencia:
            self._tocar_beep_referencia()

    # --- internos: voz --------------------------------------------------------------

    def _enfileirar(self, spec: SpeechSpec, t_capture: float, now: float) -> None:
        with self._voice_lock:
            acao, self._voice_state = chegou(spec, t_capture, self._voice_state, now, self._params)
        if acao == Acao.TOCAR_AGORA:
            self._player.stop()  # corta o que estivesse tocando (sem custo se nada tocava)
            self._voice_wake.set()

    def _loop_voz(self) -> None:
        while not self._encerrar.is_set():
            with self._voice_lock:
                tocar = self._voice_state.tocando
            if tocar is None:
                self._voice_wake.wait(timeout=0.05)
                self._voice_wake.clear()
                continue

            self._tocar_speech(tocar)
            if self._encerrar.is_set():
                break

            with self._voice_lock:
                # só avança a fila se terminou por conta própria — se foi cortado por
                # algo mais urgente enquanto tocava, `tocando` já é outro objeto, e o
                # loop volta ao topo e toca esse, sem passar pelo canal_livre()
                if self._voice_state.tocando is tocar:
                    _, self._voice_state = canal_livre(
                        self._voice_state, time.monotonic(), self._params
                    )

    def _tocar_speech(self, spec: SpeechSpec) -> None:
        clipes = []
        for key in spec.clip_keys:
            caminho = self._clip_dir / f"{key}.wav"
            if not caminho.exists():
                print(f"AudioEngine: sem áudio para {key!r} ({caminho})", file=sys.stderr)
                continue
            clipes.append(load_wav(caminho))
        if clipes:
            self._player.play_sequence(clipes)

    # --- internos: bipe ---------------------------------------------------------------

    def _loop_bipe(self) -> None:
        cfg = self._params["audio"]["bipe"]
        volume = self._params["audio"]["volume"]
        while not self._encerrar.is_set():
            with self._beep_lock:
                spec = self._beep_spec
            if spec is None:
                time.sleep(0.05)
                continue
            freq = cfg["tom_hz"][spec.band.value]
            pulso = synth.beep_with_side_timbre(
                spec.side, freq_hz=freq, duration_ms=cfg["duracao_ms"], volume=volume
            )
            onda = synth.repeat_at_rate(
                pulso, rate_hz=spec.rate_hz, total_duration_s=1.0 / spec.rate_hz
            )
            self._player.play(onda, synth.SAMPLE_RATE, wait=True)

    def _tocar_beep_referencia(self) -> None:
        volume = self._params["audio"]["volume"]
        pulso = synth.sine_tone(freq_hz=800.0, duration_ms=120.0, volume=volume)
        self._player.play(pulso, synth.SAMPLE_RATE, wait=False)
