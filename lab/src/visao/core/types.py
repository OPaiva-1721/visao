"""Tipos trocados entre percepção, núcleo e áudio (docs/arquitetura.md, seções 4.4 e 5.3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class Mode(StrEnum):
    """RN-20."""

    CAMINHADA = "caminhada"
    EXPLORAR = "explorar"
    SILENCIOSO = "silencioso"


class Zone(StrEnum):
    """RN-12."""

    PERTO = "perto"
    ATENCAO = "atencao"
    LONGE = "longe"


class Band(StrEnum):
    """RN-09."""

    CHAO = "chao"
    TRONCO = "tronco"
    CABECA = "cabeca"


Side = Literal["esq", "frente", "dir"]
Source = Literal["semantic", "geometric", "fused"]


@dataclass(frozen=True)
class Perception:
    track_id: int | None  # None para obstáculo genérico
    cls: str  # chave de classes.yaml, ou "obstaculo"
    conf: float
    distance_m: float
    lateral_m: float  # + direita, − esquerda
    top_m: float  # altura do topo do objeto
    bottom_m: float  # altura da base
    truncated: bool  # encosta na borda da imagem (RN-33)
    source: Source
    t_capture: float  # timestamp monotônico da captura do frame


@dataclass(frozen=True)
class BeepSpec:
    rate_hz: float
    band: Band  # vira tom: grave / médio / agudo
    side: Side  # vira timbre (fone mono) ou pan (fone estéreo), conforme params.audio.saida


@dataclass(frozen=True)
class SpeechSpec:
    clip_keys: tuple[str, ...]  # chaves de shared/audio/vocabulario.yaml, ex.: ("pessoa", "frente")
    priority: int  # 0 = falha … 4 = informação (arquitetura seção 6)


@dataclass(frozen=True)
class AlertPlan:
    beep: BeepSpec | None  # contínuo enquanto o alvo existir
    speech: SpeechSpec | None  # evento pontual
    t_capture: float  # herdado da percepção → mede latência e descarta mensagem velha
