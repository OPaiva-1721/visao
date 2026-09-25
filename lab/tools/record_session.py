#!/usr/bin/env python3
"""Grava uma sessão de vídeo com a câmera real, para rotular depois (label_events.py) e
avaliar (eval.py, quando a Fase 2 — geometria — existir).

RN-29: só em modo explícito, ambiente privado, sem terceiros identificáveis, com
consentimento dela. Vídeos nunca vão para o git — ficam em data/videos/ (ADR-009).

Requer o extra "visao": `uv sync --extra visao`.

Uso:
    uv run python tools/record_session.py
    uv run python tools/record_session.py --duracao 60 --saida data/videos/corredor_01.mp4
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import time
from pathlib import Path
from typing import Any

from visao.config import REPO_ROOT, load_params


def _abrir_camera(device: int | str) -> tuple[Any, Any]:
    try:
        import cv2  # pyright: ignore[reportMissingImports] — extra "visao" opcional
    except ImportError as e:
        raise RuntimeError("opencv-python não instalado. Rode: uv sync --extra visao.") from e
    return cv2, cv2.VideoCapture(device)


def confirmar_consentimento() -> bool:
    print("RN-29: grava só em modo explícito — ambiente privado, sem terceiros")
    print("identificáveis, com consentimento dela. O vídeo fica em data/ (fora do git).")
    resposta = input("Essa sessão respeita isso? [sim/não] ").strip().lower()
    return resposta in ("sim", "s", "yes", "y")


def gravar(device: int | str, saida: Path, duracao_s: float | None) -> tuple[int, float]:
    cv2, cap = _abrir_camera(device)
    if not cap.isOpened():
        raise RuntimeError(f"não abriu a câmera (dispositivo={device!r})")

    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    saida.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(saida), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    n_frames = 0
    inicio = time.monotonic()
    try:
        print("gravando... Ctrl+C para parar.")
        while duracao_s is None or (time.monotonic() - inicio) < duracao_s:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
            n_frames += 1
    except KeyboardInterrupt:
        print("\ninterrompido.")
    finally:
        cap.release()
        writer.release()
    return n_frames, time.monotonic() - inicio


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(AttributeError, ValueError):  # acentos no console do Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--device", default=None, help="Índice/caminho da câmera (padrão: config)")
    parser.add_argument("--profile", default=None, help="Perfil de máquina (perfis/*.yaml)")
    parser.add_argument(
        "--saida",
        type=Path,
        default=None,
        help="Caminho do .mp4 (padrão: data/videos/<timestamp>.mp4)",
    )
    parser.add_argument(
        "--duracao", type=float, default=None, help="Segundos; sem isso, grava até Ctrl+C"
    )
    parser.add_argument(
        "--sem-confirmar",
        action="store_true",
        help="Pula o aviso da RN-29 (só para teste técnico local)",
    )
    args = parser.parse_args(argv)

    params = load_params(args.profile)
    device = args.device if args.device is not None else params["camera"]["dispositivo"]

    if not args.sem_confirmar and not confirmar_consentimento():
        print("cancelado.")
        return 1

    saida = args.saida or (REPO_ROOT / "data" / "videos" / f"{time.strftime('%Y%m%d_%H%M%S')}.mp4")
    n_frames, duracao = gravar(device, saida, args.duracao)
    fps_real = n_frames / duracao if duracao > 0 else 0.0
    print(f"gravado: {n_frames} frames em {duracao:.1f}s ({fps_real:.1f} fps) → {saida}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"Erro: {e}", file=sys.stderr)
        raise SystemExit(1) from e
