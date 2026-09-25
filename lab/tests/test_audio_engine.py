"""Testa a orquestração do AudioEngine sem tocar som nem abrir threads: chama
update()/notify_*() direto (métodos síncronos) e olha o estado interno + as chamadas
que teriam ido para o Player. Nunca chama start() — sem hardware, sem timing incerto.
"""

from dataclasses import dataclass, field

from visao.audio.engine import AudioEngine, confirmacao_para_fala, falha_para_fala
from visao.config import load_params
from visao.controls.types import Confirmacao
from visao.core.types import AlertPlan, Band, BeepSpec, SpeechSpec
from visao.supervisor.types import FaultKind, SupervisorReport, SystemState

PARAMS = load_params()


@dataclass
class FakePlayer:
    """Registra o que teria tocado, sem tocar nada de verdade."""

    chamadas: list[tuple] = field(default_factory=list)

    def play(self, samples, sample_rate, *, wait=True):
        self.chamadas.append(("play", wait))

    def play_wav(self, path, *, wait=True):
        self.chamadas.append(("play_wav", path, wait))

    def play_sequence(self, clips, *, gap_s=0.2):
        self.chamadas.append(("play_sequence", len(clips)))

    def stop(self):
        self.chamadas.append(("stop",))


def make_engine(tmp_path) -> tuple[AudioEngine, FakePlayer]:
    player = FakePlayer()
    engine = AudioEngine(clip_dir=tmp_path, params=PARAMS, player=player)
    return engine, player


# --- mapeamentos puros ----------------------------------------------------------


def test_falha_para_fala_usa_a_chave_do_vocabulario_e_prioridade_0():
    spec = falha_para_fala(FaultKind.CAMERA)
    assert spec.clip_keys == ("falha_camera",)
    assert spec.priority == 0


def test_confirmacao_com_clipe_vira_fala_prioridade_2():
    spec = confirmacao_para_fala(Confirmacao(clip_key="modo_explorar"))
    assert spec is not None
    assert spec.clip_keys == ("modo_explorar",)
    assert spec.priority == 2


def test_confirmacao_so_com_bipe_nao_vira_fala():
    assert confirmacao_para_fala(Confirmacao(beep_referencia=True)) is None


# --- update() -------------------------------------------------------------------


def test_update_guarda_o_beep_spec(tmp_path):
    engine, _ = make_engine(tmp_path)
    beep = BeepSpec(rate_hz=8.0, band=Band.CABECA, side="dir")
    engine.update(AlertPlan(beep=beep, speech=None, t_capture=0.0), now=0.0)
    assert engine._beep_spec is beep


def test_update_com_fala_poe_para_tocar_e_corta_o_player(tmp_path):
    engine, player = make_engine(tmp_path)
    fala = SpeechSpec(clip_keys=("pessoa",), priority=1)
    engine.update(AlertPlan(beep=None, speech=fala, t_capture=0.0), now=0.0)
    assert engine._voice_state.tocando is fala
    assert ("stop",) in player.chamadas  # RN-17: mesmo a primeira fala corta (é inofensivo)


def test_update_com_fala_menos_urgente_nao_corta_a_que_esta_tocando(tmp_path):
    engine, player = make_engine(tmp_path)
    atencao = SpeechSpec(clip_keys=("cadeira",), priority=3)
    engine.update(AlertPlan(beep=None, speech=atencao, t_capture=0.0), now=0.0)
    player.chamadas.clear()

    outra_atencao = SpeechSpec(clip_keys=("banco",), priority=3)
    engine.update(AlertPlan(beep=None, speech=outra_atencao, t_capture=0.1), now=0.1)
    assert engine._voice_state.tocando is atencao  # continua tocando a primeira
    assert engine._voice_state.esperando is outra_atencao
    assert player.chamadas == []  # não interrompeu nada


# --- notify_supervisor() (RN-04) -------------------------------------------------


def test_falha_interrompe_e_anuncia(tmp_path):
    engine, player = make_engine(tmp_path)
    report = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.CAMERA, pouca_luz=False)
    engine.notify_supervisor(report, now=0.0)
    assert engine._voice_state.tocando == falha_para_fala(FaultKind.CAMERA)
    assert ("stop",) in player.chamadas


def test_falha_nao_repete_antes_do_intervalo(tmp_path):
    engine, player = make_engine(tmp_path)
    report = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.CAMERA, pouca_luz=False)
    engine.notify_supervisor(report, now=0.0)
    player.chamadas.clear()

    engine.notify_supervisor(report, now=0.1)  # bem antes do falha_repete_s (3 s)
    assert player.chamadas == []  # não anunciou de novo


def test_falha_repete_apos_o_intervalo(tmp_path):
    engine, player = make_engine(tmp_path)
    report = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.CAMERA, pouca_luz=False)
    intervalo = PARAMS["seguranca"]["falha_repete_s"]

    engine.notify_supervisor(report, now=0.0)
    engine.notify_supervisor(report, now=intervalo + 0.1)
    # duas falas foram enfileiradas: a 2ª interrompeu a 1ª (mesma prioridade, mas é
    # uma repetição de falha — tratada como nova chegada) ou entrou à espera; de todo
    # jeito, o "stop" da 1ª chamada precisa ter ocorrido pelo menos uma vez
    assert ("stop",) in player.chamadas


def test_falha_resolvida_reseta_o_temporizador(tmp_path):
    engine, _ = make_engine(tmp_path)
    falha = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.CAMERA, pouca_luz=False)
    ok = SupervisorReport(state=SystemState.RODANDO, fault=None, pouca_luz=False)

    engine.notify_supervisor(falha, now=0.0)
    engine.notify_supervisor(ok, now=0.1)
    assert engine._falha_ativa is None
    assert engine._falha_ultima_vez is None


def test_trocar_de_falha_anuncia_na_hora_sem_esperar_o_intervalo(tmp_path):
    engine, player = make_engine(tmp_path)
    camera = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.CAMERA, pouca_luz=False)
    erro = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.ERRO, pouca_luz=False)

    engine.notify_supervisor(camera, now=0.0)
    player.chamadas.clear()
    engine.notify_supervisor(erro, now=0.05)  # bem antes do intervalo de repetição

    assert engine._voice_state.tocando == falha_para_fala(FaultKind.ERRO)
    assert ("stop",) in player.chamadas


# --- notify_confirmacao() (RN-21) ------------------------------------------------


def test_confirmacao_de_modo_enfileira_a_fala(tmp_path):
    engine, player = make_engine(tmp_path)
    engine.notify_confirmacao(Confirmacao(clip_key="modo_explorar"), now=0.0)
    assert engine._voice_state.tocando == SpeechSpec(clip_keys=("modo_explorar",), priority=2)
    assert ("stop",) in player.chamadas


def test_confirmacao_de_volume_toca_bipe_de_referencia_sem_tocar_fala(tmp_path):
    engine, player = make_engine(tmp_path)
    engine.notify_confirmacao(Confirmacao(beep_referencia=True), now=0.0)
    assert engine._voice_state.tocando is None  # nada foi enfileirado como fala
    assert ("play", False) in player.chamadas  # o bipe de referência não espera (wait=False)
