#!/usr/bin/env python3
"""Mostra o pipeline inteiro rodando ao vivo: câmera -> detector -> geometria ->
decide() -> (opcional) áudio de verdade. Cada caixa detectada aparece com classe,
distância e zona; o topo da janela mostra a decisão real (o que soaria/falaria).

Só visualização/demonstração — não é uma das ferramentas formais da arquitetura
(seção 10); serve pra ver e ouvir o sistema funcionando antes de existir app.py.

Requer o extra "visao" (e "audio" se quiser ouvir de verdade):
    uv sync --extra visao --extra audio

Uso:
    uv run python tools/live_view.py
    uv run python tools/live_view.py --sem-audio
    uv run python tools/live_view.py --profile pc --modo explorar
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import time
from typing import Any

from visao.capture.source import CameraFrameSource
from visao.config import REPO_ROOT, load_classes, load_params
from visao.core.decide import decide
from visao.core.state import CoreState
from visao.core.types import AlertPlan, Mode
from visao.perception.detector import Detector
from visao.perception.geometry import Calibracao, detection_to_perception
from visao.perception.types import Detection

MODELO = REPO_ROOT / "data" / "modelos" / "yolo26n.pt"


def _cor_zona(distance_m: float, truncated: bool, zonas_m: dict) -> tuple[int, int, int]:
    """BGR (cv2). Réplica leve de `core.decide._zone` só para colorir a caixa na tela."""
    if truncated or distance_m < zonas_m["perto"]:
        return (0, 0, 255)  # vermelho: Perto
    if distance_m < zonas_m["atencao"]:
        return (0, 200, 255)  # amarelo: Atenção
    return (0, 200, 0)  # verde: Longe


def _desenhar(hud: Any, cv2: Any, pares: list, zonas_m: dict, plan: AlertPlan) -> None:
    for deteccao, perception in pares:
        x1, y1, x2, y2 = (int(v) for v in (deteccao.x1, deteccao.y1, deteccao.x2, deteccao.y2))
        cinza = (150, 150, 150)
        if perception is None:
            cv2.rectangle(hud, (x1, y1), (x2, y2), cinza, 1)
            pos = (x1, max(y1 - 6, 0))
            cv2.putText(hud, deteccao.cls, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, cinza, 1)
            continue
        cor = _cor_zona(perception.distance_m, perception.truncated, zonas_m)
        cv2.rectangle(hud, (x1, y1), (x2, y2), cor, 2)
        rotulo = f"{deteccao.cls} {perception.distance_m:.1f}m"
        cv2.putText(hud, rotulo, (x1, max(y1 - 6, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)

    if plan.beep is not None:
        texto = f"BIPE: {plan.beep.band.value} / {plan.beep.side} / {plan.beep.rate_hz:.1f}Hz"
        cor_hud = (0, 0, 255)
    else:
        texto = "sem alerta"
        cor_hud = (150, 150, 150)
    cv2.putText(hud, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_hud, 2)
    if plan.speech is not None:
        cv2.putText(
            hud,
            f"FALA: {' '.join(plan.speech.clip_keys)}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),
            2,
        )


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(AttributeError, ValueError):  # acentos no console do Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        import cv2  # pyright: ignore[reportMissingImports] — extra "visao" opcional
    except ImportError as e:
        raise RuntimeError("opencv-python não instalado. Rode: uv sync --extra visao.") from e

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--profile", default="pc")
    parser.add_argument(
        "--modo", default="caminhada", choices=["caminhada", "explorar", "silencioso"]
    )
    parser.add_argument("--sem-audio", action="store_true", help="Só mostra, não toca som")
    args = parser.parse_args(argv)

    params = load_params(args.profile)
    classes = load_classes()
    cam = params["camera"]
    if "f_px" not in cam:
        raise RuntimeError(
            f"perfil {args.profile!r} sem calibração — rode tools/calibrate_camera.py primeiro."
        )
    calib = Calibracao(
        f_px=cam["f_px"],
        cx_px=cam["cx_px"],
        cy_px=cam["cy_px"],
        altura_camera_m=cam["altura_m"],
        inclinacao_graus=cam["inclinacao_graus"],
    )

    detector = Detector(
        str(MODELO), classes, tolerancia_borda_px=params["deteccao"]["borda_tolerancia_px"]
    )
    fonte = CameraFrameSource(device=cam["dispositivo"])
    fonte.start()

    engine = None
    if not args.sem_audio:
        from visao.audio.engine import AudioEngine

        engine = AudioEngine(clip_dir=REPO_ROOT / "shared" / "audio", params=params)
        engine.start()

    modo = Mode(args.modo)
    state = CoreState()
    ultimo_t_capture: float | None = None
    print("janela aberta — q/ESC para sair.")
    try:
        while True:
            frame = fonte.take_if_new(ultimo_t_capture)
            if frame is None:
                # sem frame novo da câmera: só espera, não reprocessa o mesmo de novo
                # (rodar o detector à toa rouba CPU da thread de áudio — causa estalo)
                if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                    break
                time.sleep(0.005)
                continue
            ultimo_t_capture = frame.t_capture

            deteccoes: list[Detection] = detector.detect(frame)
            pares = []
            for d in deteccoes:
                info = classes.get(d.cls)
                altura_real_m = info.altura_m if info is not None else None
                pares.append((d, detection_to_perception(d, altura_real_m, calib)))
            perceptions = [p for _, p in pares if p is not None]

            now = time.monotonic()
            plan, state = decide(perceptions, state, modo, now, params, classes)
            if engine is not None:
                engine.update(plan, now)

            hud = frame.image.copy()
            _desenhar(hud, cv2, pares, params["zonas_m"], plan)
            cv2.imshow("live_view (q/ESC sai)", hud)
            if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                break
    finally:
        fonte.stop()
        if engine is not None:
            engine.stop()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"Erro: {e}", file=sys.stderr)
        raise SystemExit(1) from e
