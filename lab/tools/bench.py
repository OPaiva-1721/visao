#!/usr/bin/env python3
"""Spikes S1/S1b (docs/arquitetura.md seção 13): mede o fps do detector no perfil atual.

Baixa o peso pré-treinado (Ultralytics), exporta para ONNX no tamanho de entrada pedido,
e mede o tempo de inferência sobre uma imagem sintética — sem precisar de câmera.

Requer o extra "visao": `uv sync --extra visao`.

Uso:
    uv run --extra visao python tools/bench.py
    uv run --extra visao python tools/bench.py --imgsz 256 --runs 100
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Resultado:
    modelo: str
    imgsz: int
    runs: int
    media_ms: float
    p50_ms: float
    p95_ms: float

    @property
    def fps_media(self) -> float:
        return 1000 / self.media_ms


def benchmark(model_name: str, imgsz: int, runs: int, warmup: int) -> Resultado:
    import numpy as np
    from ultralytics import YOLO

    print(f"Carregando/baixando {model_name}...")
    model = YOLO(model_name)

    print(f"Exportando para ONNX (imgsz={imgsz})...")
    onnx_path = model.export(format="onnx", imgsz=imgsz, simplify=True)
    onnx_model = YOLO(onnx_path)

    # Imagem sintética (ruído): só para medir velocidade, a precisão não importa aqui.
    rng = np.random.default_rng(seed=0)
    image = rng.integers(0, 255, size=(imgsz, imgsz, 3), dtype=np.uint8)

    print(f"Aquecendo ({warmup} rodadas)...")
    for _ in range(warmup):
        onnx_model.predict(image, imgsz=imgsz, verbose=False)

    print(f"Medindo ({runs} rodadas)...")
    tempos_ms = []
    for _ in range(runs):
        inicio = time.perf_counter()
        onnx_model.predict(image, imgsz=imgsz, verbose=False)
        tempos_ms.append((time.perf_counter() - inicio) * 1000)

    tempos_ms.sort()
    media = sum(tempos_ms) / len(tempos_ms)
    return Resultado(
        modelo=model_name,
        imgsz=imgsz,
        runs=runs,
        media_ms=media,
        p50_ms=tempos_ms[len(tempos_ms) // 2],
        p95_ms=tempos_ms[int(len(tempos_ms) * 0.95)],
    )


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(AttributeError, ValueError):  # acentos no console do Windows
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--model", default="yolo26n.pt", help="Peso do Ultralytics")
    parser.add_argument("--imgsz", type=int, default=320, help="Resolução de entrada")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--meta-fps", type=float, default=15.0, help="Meta do spike S1")
    args = parser.parse_args(argv)

    r = benchmark(args.model, args.imgsz, args.runs, args.warmup)

    print()
    print(f"modelo={r.modelo}  imgsz={r.imgsz}  runs={r.runs}")
    print(f"média: {r.media_ms:.1f} ms  ({r.fps_media:.1f} fps)")
    print(f"p50:   {r.p50_ms:.1f} ms")
    print(f"p95:   {r.p95_ms:.1f} ms")
    print()
    if r.fps_media >= args.meta_fps:
        print(f"OK — spike S1 passou (meta >= {args.meta_fps} fps)")
    else:
        print(f"NÃO passou (meta >= {args.meta_fps} fps) — considerar imgsz menor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
