"""Fila de prioridade da voz — P0 a P4 (arquitetura seção 6), RN-06 e RN-15.

Só a voz passa por aqui. O bipe é contínuo e nunca entra nesta fila (RN-15, RN-17) —
quem toca o bipe só lê o `BeepSpec` mais recente, sem fila nenhuma.

Puro: decide o que fazer, não toca nada — isso é `engine.py`. Não sabe quanto tempo um
clipe demora a tocar; por isso `canal_livre()` é chamado pelo `engine.py` quando o
clipe que estava tocando *de fato* terminou, não por um cálculo de duração aqui.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from visao.core.types import SpeechSpec


class Acao(StrEnum):
    TOCAR_AGORA = "tocar_agora"
    ESPERAR = "esperar"
    DESCARTAR = "descartar"


@dataclass(frozen=True)
class VoiceState:
    """`esperando` é um slot só, não uma fila longa: uma fala nova mais urgente ou mais
    recente substitui a que estava esperando — não faz sentido acumular avisos velhos."""

    tocando: SpeechSpec | None = None
    esperando: SpeechSpec | None = None
    esperando_t_capture: float | None = None


def _velha(t_capture: float, now: float, params: dict) -> bool:
    """RN-06: mais velha que isso não é falada."""
    return (now - t_capture) * 1000 > params["seguranca"]["mensagem_max_idade_ms"]


def chegou(
    novo: SpeechSpec, t_capture: float, state: VoiceState, now: float, params: dict
) -> tuple[Acao, VoiceState]:
    """Uma fala nova chegou (do `decide()`, do supervisor ou dos controles). Decide:
    toca já (nada tocando, ou isso é mais urgente que o que está tocando), espera
    (não interrompe, mas é o próximo), ou é descartada (menos urgente que tudo, ou já
    nasceu velha)."""
    if _velha(t_capture, now, params):
        return Acao.DESCARTAR, state

    if state.tocando is None or novo.priority < state.tocando.priority:
        return Acao.TOCAR_AGORA, VoiceState(tocando=novo)

    if state.esperando is None or novo.priority <= state.esperando.priority:
        return Acao.ESPERAR, replace(state, esperando=novo, esperando_t_capture=t_capture)

    return Acao.DESCARTAR, state


def canal_livre(
    state: VoiceState, now: float, params: dict
) -> tuple[SpeechSpec | None, VoiceState]:
    """O `engine.py` chama isto quando o que estava tocando *de fato* terminou. Se havia
    algo esperando, aplica o RN-06 antes de tocá-lo — pode ter ficado velho na espera."""
    if state.esperando is None:
        return None, VoiceState()
    if state.esperando_t_capture is not None and _velha(state.esperando_t_capture, now, params):
        return None, VoiceState()
    return state.esperando, VoiceState(tocando=state.esperando)


def deve_repetir_falha(ultima_vez: float | None, now: float, params: dict) -> bool:
    """RN-04: uma falha em curso repete a cada [3 s] até se resolver."""
    if ultima_vez is None:
        return True
    return now - ultima_vez >= params["seguranca"]["falha_repete_s"]
