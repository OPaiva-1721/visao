"""Leitura da configuração compartilhada em shared/ (ADR-003, ADR-013)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# lab/src/visao/config.py → raiz do repositório
REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_DIR = REPO_ROOT / "shared"


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} não contém um mapeamento YAML")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Devolve uma cópia de `base` com `override` aplicado recursivamente."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def available_profiles(shared_dir: Path = SHARED_DIR) -> list[str]:
    return sorted(p.stem for p in (shared_dir / "config" / "perfis").glob("*.yaml"))


def load_params(profile: str | None = None, shared_dir: Path = SHARED_DIR) -> dict[str, Any]:
    """params.yaml, opcionalmente sobreposto pelo perfil de máquina."""
    params = _read_yaml(shared_dir / "config" / "params.yaml")
    if profile is None:
        return params
    profile_path = shared_dir / "config" / "perfis" / f"{profile}.yaml"
    if not profile_path.exists():
        raise ValueError(
            f"perfil desconhecido: {profile!r} (disponíveis: {available_profiles(shared_dir)})"
        )
    return deep_merge(params, _read_yaml(profile_path))


@dataclass(frozen=True)
class ClassInfo:
    name: str
    fala: str
    perigo: int
    altura_m: float | None
    conf_min: float | None


def load_classes(shared_dir: Path = SHARED_DIR) -> dict[str, ClassInfo]:
    raw = _read_yaml(shared_dir / "config" / "classes.yaml")
    return {
        name: ClassInfo(
            name=name,
            fala=entry["fala"],
            perigo=entry["perigo"],
            altura_m=entry.get("altura_m"),
            conf_min=entry.get("conf_min"),
        )
        for name, entry in raw.items()
    }


def load_vocabulary(shared_dir: Path = SHARED_DIR) -> dict[str, dict[str, str]]:
    return _read_yaml(shared_dir / "audio" / "vocabulario.yaml")
