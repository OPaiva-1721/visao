"""Estado do núcleo entre chamadas de `decide()` (ADR-002).

A casca guarda o `CoreState` e o devolve inalterado a cada chamada; só `decide()` sabe
como produzir o próximo. Tudo aqui é imutável — nenhum método muda um `TrackState` ou
`CoreState` existente, sempre devolve um novo (arquitetura seção 5.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from visao.core.types import Zone

# Maior janela entre persistencia.perto.m e persistencia.padrao.m (RN-11) — quantos
# frames de histórico guardar por objeto. Se os parâmetros mudarem para uma janela maior,
# aumentar aqui também (é só o tamanho do buffer, não o limiar).
MAX_HISTORY = 5


@dataclass(frozen=True)
class TrackState:
    """Histórico de um objeto rastreado — ou do "obstáculo" genérico sem track_id (ADR-006:
    nesse caso, todas as percepções sem ID compartilham este mesmo estado; ver decide.py)."""

    presence_history: tuple[bool, ...] = ()  # um frame por posição; True = visto e válido (RN-11)
    last_seen: float = float("-inf")  # `now` do último frame em que foi visto
    last_announced_zone: Zone | None = None  # RN-14: última zona em que a voz o anunciou


@dataclass(frozen=True)
class CoreState:
    """Estado completo entre frames — vazio no início (arquitetura: estado "Iniciando")."""

    tracks: dict[int | None, TrackState] = field(default_factory=dict)
    last_voice_time: float = float("-inf")  # RN-15: cooldown global entre falas
