#!/usr/bin/env python3
"""Calibra a câmera: mede f_px (distância focal em pixels) com uma pessoa de altura
conhecida a uma distância conhecida — usa o próprio Detector (YOLO26n) pra achar a
caixa, sem precisar clicar pixel por pixel.

Fórmula (docs/arquitetura.md seção 4.2): d = f · H_real / h_px  →  f = d · h_px / H_real
cx, cy ficam no centro da imagem (sem crop assimétrico conhecido).

Não escreve nos perfis automaticamente — imprime os valores para você conferir e
colar em shared/config/perfis/<perfil>.yaml (config é editada por você, ADR-003).

Requer o extra "visao": `uv sync --extra visao`.

Uso:
    # ela (ou você) fica parada a 2 m da câmera, de corpo inteiro no quadro
    uv run python tools/calibrate_camera.py --distancia-m 2.0
    uv run python tools/calibrate_camera.py --distancia-m 2.0 --altura-m 1.55 --profile pc
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import time

from visao.capture.source import CameraFrameSource
from visao.config import REPO_ROOT, load_classes, load_params
from visao.perception.detector import Detector

MODELO = REPO_ROOT / "data" / "modelos" / "yolo26n.pt"


def medir_altura_pessoa_px(
    device: int | str, detector: Detector, timeout_s: float
) -> tuple[float, int, int]:
    """Espera até achar uma caixa de "person" confirmada pelo tracker, não cortada.
    Devolve (altura_px, largura_imagem, altura_imagem)."""
    fonte = CameraFrameSource(device=device)
    fonte.start()
    try:
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout_s:
            frame = fonte.latest()
            if frame is None:
                time.sleep(0.05)
                continue
            candidatos = [
                d for d in detector.detect(frame) if d.cls == "person" and not d.truncated
            ]
            if candidatos:
                maior = max(candidatos, key=lambda d: d.y2 - d.y1)
                altura_img, largura_img = frame.image.shape[0], frame.image.shape[1]
                return maior.y2 - maior.y1, largura_img, altura_img
            time.sleep(0.05)
    finally:
        fonte.stop()
    raise RuntimeError(
        "não achou uma pessoa confirmada a tempo — fique de corpo inteiro, bem "
        "iluminada, parada e visível por alguns segundos, e tente de novo."
    )


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(AttributeError, ValueError):  # acentos no console do Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--distancia-m", type=float, required=True, help="Distância real câmera→pessoa (fita/trena)"
    )
    parser.add_argument(
        "--altura-m",
        type=float,
        default=None,
        help="Altura real da pessoa (padrão: usuaria.altura_m)",
    )
    parser.add_argument("--profile", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    params = load_params(args.profile)
    device = args.device if args.device is not None else params["camera"]["dispositivo"]
    altura_real_m = args.altura_m if args.altura_m is not None else params["usuaria"]["altura_m"]

    classes = load_classes()
    detector = Detector(
        str(MODELO), classes, tolerancia_borda_px=params["deteccao"]["borda_tolerancia_px"]
    )

    print(f"procurando pessoa no quadro (até {args.timeout:.0f}s)...")
    altura_px, largura_img, altura_img = medir_altura_pessoa_px(device, detector, args.timeout)

    f_px = args.distancia_m * altura_px / altura_real_m
    cx_px = largura_img / 2
    cy_px = altura_img / 2

    print()
    print(f"caixa da pessoa: {altura_px:.1f} px de altura  (imagem {largura_img}x{altura_img})")
    print(f"f_px  = {f_px:.1f}")
    print(f"cx_px = {cx_px:.1f}")
    print(f"cy_px = {cy_px:.1f}")
    print()
    print(f"cole/ajuste em shared/config/perfis/{args.profile or 'pc'}.yaml:")
    print("camera:")
    print(f"  f_px: {f_px:.1f}")
    print(f"  cx_px: {cx_px:.1f}")
    print(f"  cy_px: {cy_px:.1f}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"Erro: {e}", file=sys.stderr)
        raise SystemExit(1) from e
