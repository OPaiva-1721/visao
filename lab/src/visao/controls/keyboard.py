"""Mapeia teclas para ações — puro (RN-20, RN-21, RN-22). No app (Fase 5), o botão do
fone assume este papel (RN-36); a lógica de "qual ação, qual confirmação" é a mesma.
"""

from __future__ import annotations

from dataclasses import replace

from visao.controls.types import Confirmacao, ControlsState
from visao.core.types import Mode

TECLA_PARA_MODO: dict[str, Mode] = {
    "c": Mode.CAMINHADA,
    "e": Mode.EXPLORAR,
    "s": Mode.SILENCIOSO,
}

_CLIP_DO_MODO: dict[Mode, str] = {
    Mode.CAMINHADA: "modo_caminhada",
    Mode.EXPLORAR: "modo_explorar",
    Mode.SILENCIOSO: "modo_silencioso",
}


def aplicar_tecla(
    tecla: str, state: ControlsState, params: dict
) -> tuple[ControlsState, Confirmacao | None]:
    """Tecla desconhecida não muda nada e não confirma nada — não é toda tecla que
    precisa de som (RN-21 fala de toda *ação*, uma tecla sem efeito não é uma ação)."""
    modo_novo = TECLA_PARA_MODO.get(tecla)
    if modo_novo is not None:
        if modo_novo == state.mode:
            return state, None  # já está nesse modo — nada para confirmar
        return replace(state, mode=modo_novo), Confirmacao(clip_key=_CLIP_DO_MODO[modo_novo])

    passo = params["controles"]["passo_volume"]
    if tecla == "+":
        novo = min(1.0, state.volume + passo)
        return replace(state, volume=novo), Confirmacao(beep_referencia=True)
    if tecla == "-":
        novo = max(0.0, state.volume - passo)
        return replace(state, volume=novo), Confirmacao(beep_referencia=True)

    return state, None
