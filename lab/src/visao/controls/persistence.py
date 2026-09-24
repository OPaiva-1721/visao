"""Salva/carrega o ControlsState entre usos (RN-22). Só sabe ler e escrever JSON —
quem chama decide o caminho do arquivo."""

from __future__ import annotations

import json
from pathlib import Path

from visao.controls.types import ControlsState
from visao.core.types import Mode


def save(path: Path, state: ControlsState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"mode": state.mode.value, "volume": state.volume}), encoding="utf-8"
    )


def load(path: Path, default: ControlsState) -> ControlsState:
    """Devolve `default` se o arquivo não existir ou estiver corrompido — na dúvida,
    usa o padrão em vez de travar o início do sistema por causa de um arquivo ruim."""
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ControlsState(mode=Mode(data["mode"]), volume=float(data["volume"]))
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return default
