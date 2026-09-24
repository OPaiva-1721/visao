"""Grava um JSON por linha (JSONL) — cada linha é independente; dá para ler em
streaming, sem carregar a sessão inteira, e uma sessão interrompida não corrompe as
linhas já escritas (RN-28)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TelemetryWriter:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8")

    def write(self, record: dict[str, Any]) -> None:
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._file.flush()  # a sessão pode ser interrompida; não perder o que já foi gravado

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> TelemetryWriter:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
