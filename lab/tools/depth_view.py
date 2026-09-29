#!/usr/bin/env python3
"""Spike S2 (docs/arquitetura.md seção 13): mede a PRECISÃO do YOLO26n-depth em metros,
comparando com a trena. Mostra a câmera e o mapa de profundidade lado a lado; um ponto
de prova (clique com o mouse; começa no centro) mostra a profundidade estimada nele.

Como medir: aponte o ponto de prova para uma superfície plana (parede, caixa, porta),
meça com a trena a distância da câmera até ela, aperte 's' e digite o valor real.
Cada amostra vai para data/medidas_s2.csv (fora do git). Repita de 0,5 m a 3 m, dentro
e fora de casa, e nas resoluções que quiser comparar (--imgsz 320 / 512 / 768).

Teclas: clique = move o ponto de prova · s = salva amostra · q/ESC = sai.

Requer o extra "visao": `uv sync --extra visao`.

Uso:
    uv run python tools/depth_view.py
    uv run python tools/depth_view.py --imgsz 320
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import sys
import time
from pathlib import Path
from typing import Any

from visao.capture.source import CameraFrameSource
from visao.config import REPO_ROOT, load_params

MODELO = REPO_ROOT / "data" / "modelos" / "yolo26n-depth.pt"
CSV_SAIDA = REPO_ROOT / "data" / "medidas_s2.csv"
COLUNAS = ["timestamp", "imgsz", "x", "y", "estimada_m", "real_m"]
ALCANCE_COR_M = 5.0  # profundidade que vira a cor "mais longe" no mapa


def _mediana_no_ponto(depth: Any, x: int, y: int, raio: int = 4) -> float:
    import numpy as np

    h, w = depth.shape
    y0, y1 = max(y - raio, 0), min(y + raio + 1, h)
    x0, x1 = max(x - raio, 0), min(x + raio + 1, w)
    return float(np.median(depth[y0:y1, x0:x1]))


def _salvar_amostra(imgsz: int, x: int, y: int, estimada_m: float) -> None:
    texto = input(f"\nprofundidade estimada: {estimada_m:.2f} m — distância real (m)? ").strip()
    if not texto:
        print("cancelado.")
        return
    real_m = float(texto.replace(",", "."))
    CSV_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    novo = not CSV_SAIDA.exists()
    with CSV_SAIDA.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo:
            writer.writerow(COLUNAS)
        writer.writerow(
            [time.strftime("%Y-%m-%d %H:%M:%S"), imgsz, x, y, f"{estimada_m:.3f}", real_m]
        )
    erro = (estimada_m - real_m) / real_m * 100
    print(
        f"salvo em {CSV_SAIDA.name}: estimada {estimada_m:.2f} × real {real_m:.2f} ({erro:+.0f}%)"
    )


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(AttributeError, ValueError):  # acentos no console do Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        import cv2  # pyright: ignore[reportMissingImports] — extra "visao" opcional
        import numpy as np
        from ultralytics import YOLO  # pyright: ignore[reportMissingImports]
    except ImportError as e:
        raise RuntimeError("extra 'visao' não instalado. Rode: uv sync --extra visao.") from e

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--imgsz", type=int, default=512, help="Resolução de entrada do modelo")
    parser.add_argument("--profile", default="pc")
    parser.add_argument("--modelo", type=Path, default=MODELO)
    args = parser.parse_args(argv)

    params = load_params(args.profile)
    modelo = YOLO(str(args.modelo))
    fonte = CameraFrameSource(device=params["camera"]["dispositivo"])
    fonte.start()

    ponto = {"x": 320, "y": 240}

    def ao_clicar(evento: int, x: int, y: int, _flags: int, _param: Any) -> None:
        if evento == cv2.EVENT_LBUTTONDOWN:
            ponto["x"], ponto["y"] = x % 640, y  # vale clicar em qualquer metade

    janela = "depth_view (clique=ponto, s=salva, q/ESC sai)"
    cv2.namedWindow(janela)
    cv2.setMouseCallback(janela, ao_clicar)

    ultimo_t_capture: float | None = None
    estimada_m = 0.0
    print("janela aberta — aponte o ponto de prova para uma superfície e aperte 's'.")
    try:
        while True:
            frame = fonte.take_if_new(ultimo_t_capture)
            if frame is None:
                if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                    break
                time.sleep(0.005)
                continue
            ultimo_t_capture = frame.t_capture

            inicio = time.perf_counter()
            depth = modelo.predict(frame.image, imgsz=args.imgsz, verbose=False)[0].depth.data
            depth = depth.cpu().numpy()
            ms = (time.perf_counter() - inicio) * 1000

            x, y = ponto["x"], ponto["y"]
            estimada_m = _mediana_no_ponto(depth, x, y)

            normalizado = np.clip(depth / ALCANCE_COR_M, 0.0, 1.0)
            cor = cv2.applyColorMap((normalizado * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
            esquerda = frame.image.copy()
            for painel in (esquerda, cor):
                cv2.drawMarker(painel, (x, y), (255, 255, 255), cv2.MARKER_CROSS, 24, 2)
            cv2.putText(
                esquerda,
                f"{estimada_m:.2f} m  ({args.imgsz}px, {ms:.0f} ms)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.imshow(janela, np.hstack([esquerda, cor]))

            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):
                break
            if tecla == ord("s"):
                _salvar_amostra(args.imgsz, x, y, estimada_m)
    finally:
        fonte.stop()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"Erro: {e}", file=sys.stderr)
        raise SystemExit(1) from e
