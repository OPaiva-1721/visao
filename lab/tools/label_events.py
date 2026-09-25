#!/usr/bin/env python3
"""Rotula eventos de zona num vídeo gravado (ADR-007): quando o obstáculo entra/sai da
zona, marca o intervalo com o teclado — uns 2 minutos por vídeo. A saída alimenta
eval.py (quando a Fase 2 — geometria — existir).

Controles (janela do vídeo em foco):
    espaço      pausa / continua
    1 / 2 / 3   entra em longe / atenção / perto (fecha o evento anterior, abre um novo)
    0           sai de qualquer zona (fecha o evento atual)
    c / t / h   faixa do evento atual: cabeça / tronco / chão
    e / f / d   lado do evento atual: esquerda / frente / direita
    q / ESC     termina e salva

Requer o extra "visao" (cv2 pra tocar o vídeo): `uv sync --extra visao`.

Uso:
    uv run python tools/label_events.py data/videos/corredor_01.mp4
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from visao.config import REPO_ROOT

ZONA_POR_TECLA = {"1": "longe", "2": "atencao", "3": "perto"}
FAIXA_POR_TECLA = {"c": "cabeca", "t": "tronco", "h": "chao"}
LADO_POR_TECLA = {"e": "esq", "f": "frente", "d": "dir"}


@dataclass
class EventoAberto:
    t_start: float
    zona: str
    faixa: str = "cabeca"
    lado: str = "frente"


def rotular(video_path: Path) -> list[dict[str, Any]]:
    try:
        import cv2  # pyright: ignore[reportMissingImports] — extra "visao" opcional
    except ImportError as e:
        raise RuntimeError("opencv-python não instalado. Rode: uv sync --extra visao.") from e

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"não abriu o vídeo: {video_path}")

    eventos: list[dict[str, Any]] = []
    atual: EventoAberto | None = None
    pausado = False
    frame = None
    t_s = 0.0

    print(__doc__)
    while True:
        if not pausado or frame is None:
            ok, frame = cap.read()
            if not ok:
                break
            t_s = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        hud = frame.copy()
        estado = f"{'PAUSADO' if pausado else 'tocando'}  t={t_s:.1f}s"
        if atual is not None:
            estado += f"  [{atual.zona} / {atual.faixa} / {atual.lado}]"
        cv2.putText(hud, estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("label_events (espaco=pausa 1/2/3=zona 0=sai c/t/h=faixa e/f/d=lado q=sai)", hud)

        tecla_codigo = cv2.waitKey(0 if pausado else 30) & 0xFF
        tecla = chr(tecla_codigo) if tecla_codigo < 128 else ""
        if tecla_codigo in (ord("q"), 27):  # ESC
            break
        if tecla == " ":
            pausado = not pausado
        elif tecla in ZONA_POR_TECLA:
            if atual is not None:
                eventos.append({**asdict(atual), "t_end": t_s})
            atual = EventoAberto(t_start=t_s, zona=ZONA_POR_TECLA[tecla])
        elif tecla == "0" and atual is not None:
            eventos.append({**asdict(atual), "t_end": t_s})
            atual = None
        elif tecla in FAIXA_POR_TECLA and atual is not None:
            atual.faixa = FAIXA_POR_TECLA[tecla]
        elif tecla in LADO_POR_TECLA and atual is not None:
            atual.lado = LADO_POR_TECLA[tecla]

    if atual is not None:
        eventos.append({**asdict(atual), "t_end": t_s})

    cap.release()
    cv2.destroyAllWindows()
    return eventos


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(AttributeError, ValueError):  # acentos no console do Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("video", type=Path, help="Caminho do .mp4 gravado por record_session.py")
    parser.add_argument("--saida", type=Path, default=None, help="Padrão: data/eventos/<nome>.json")
    args = parser.parse_args(argv)

    eventos = rotular(args.video)

    saida = args.saida or (REPO_ROOT / "data" / "eventos" / f"{args.video.stem}.json")
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(
        json.dumps({"video": args.video.name, "events": eventos}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(eventos)} eventos salvos em {saida}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"Erro: {e}", file=sys.stderr)
        raise SystemExit(1) from e
