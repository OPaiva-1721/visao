"""Tipos internos da percepção — não cruzam para o núcleo (isso é `Perception`, em
core/types.py). `Detection` é o que o detector devolve; a Fase 2 (geometria/profundidade)
converte `Detection` em `Perception`, com distância e altura reais."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    """Uma caixa detectada e rastreada, em pixels — sem distância nem altura ainda."""

    track_id: int
    cls: str  # chave de shared/config/classes.yaml
    conf: float
    x1: float
    y1: float
    x2: float
    y2: float
    truncated: bool  # RN-33: a caixa encosta na borda da imagem
    t_capture: float
