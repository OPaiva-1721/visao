"""Tipos dos controles (RN-20, RN-21, RN-22)."""

from __future__ import annotations

from dataclasses import dataclass

from visao.core.types import Mode


@dataclass(frozen=True)
class ControlsState:
    """Ficam salvos entre usos (RN-22). `voz_velocidade` não está aqui de propósito:
    a voz é pré-gravada (ADR-008) e mudar a velocidade em tempo real exigiria
    re-sintetizar ou esticar o áudio — decisão de projeto ainda em aberto, não uma
    omissão."""

    mode: Mode
    volume: float  # 0.0–1.0


@dataclass(frozen=True)
class Confirmacao:
    """RN-21: toda ação tem confirmação. Ou fala uma palavra, ou toca um bipe de
    referência no volume novo (assim ela ouve o volume mudar, sem precisar de uma
    palavra nova no vocabulário)."""

    clip_key: str | None = None
    beep_referencia: bool = False
