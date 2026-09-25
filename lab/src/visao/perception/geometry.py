"""Geometria pinhole por classe (ADR-005, arquitetura seção 4.2): converte `Detection`
(pixels) em `Perception` (metros), para classes com altura real conhecida (`classes.yaml`
`altura_m` não nulo). Pura: sem IO, sem câmera.

**Correção de inclinação:** em vez das fórmulas lineares simplificadas do arquitetura.md
(`d = f·H/h`, `y = y_cam+(cy−v)·d/f`), aqui vai a versão exata em ângulo, porque a
câmera tem inclinação (`camera.inclinacao_graus`, ~10°) e a diferença chega a ~20–30 cm
nas distâncias que importam (1–2 m) — grande o bastante pra confundir RN-09
(tronco/cabeça têm ~0,45–0,75 m de faixa).

Um pixel na linha `v` corresponde a um raio que faz este ângulo com a horizontal:

    ang(v) = θ + atan((cy − v) / f)        θ = inclinação da câmera para cima

Para um objeto vertical de altura real H, com topo em `y1` e base em `y2`, supondo a
mesma distância `d` ao longo do raio para as duas bordas:

    H = d · (tan(ang(y1)) − tan(ang(y2)))   →   d = H / (tan(ang(y1)) − tan(ang(y2)))
    lateral = (u_centro − cx) · d / f
    top     = y_cam + d · tan(ang(y1))
    bottom  = y_cam + d · tan(ang(y2))

Com θ = 0, `tan(atan(x)) = x` e a conta vira exatamente a fórmula simplificada do
arquitetura.md (não é uma aproximação — coincide também para ângulos grandes).

Classe sem altura conhecida (`altura_m: null`) não passa por aqui — só o caminho de
profundidade (ADR-006, ainda não construído) vai perceber esses casos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from visao.core.types import ClassInfo, Perception
from visao.perception.types import Detection


@dataclass(frozen=True)
class Calibracao:
    """f_px/cx_px/cy_px vêm de `tools/calibrate_camera.py` (uma vez por câmera).
    altura_camera_m/inclinacao_graus vêm de `params.camera` (montagem no corpo)."""

    f_px: float
    cx_px: float
    cy_px: float
    altura_camera_m: float
    inclinacao_graus: float


def _angulo_da_linha(v: float, calib: Calibracao) -> float:
    """Ângulo (rad) acima da horizontal do raio que passa pela linha `v` da imagem."""
    theta = math.radians(calib.inclinacao_graus)
    return theta + math.atan2(calib.cy_px - v, calib.f_px)


def detection_to_perception(
    detection: Detection, altura_real_m: float | None, calib: Calibracao
) -> Perception | None:
    """None quando a classe não tem altura conhecida, ou quando a geometria degenera
    (caixa invertida/achatada) — mais seguro descartar essa percepção do que inventar
    um número; o objeto continua sendo visto no frame seguinte."""
    if altura_real_m is None:
        return None

    ang_topo = _angulo_da_linha(detection.y1, calib)
    ang_base = _angulo_da_linha(detection.y2, calib)
    delta = math.tan(ang_topo) - math.tan(ang_base)
    if delta <= 0:
        return None

    distancia_m = altura_real_m / delta
    if not math.isfinite(distancia_m) or distancia_m <= 0:
        return None

    u_centro = (detection.x1 + detection.x2) / 2
    lateral_m = (u_centro - calib.cx_px) * distancia_m / calib.f_px
    top_m = calib.altura_camera_m + distancia_m * math.tan(ang_topo)
    bottom_m = calib.altura_camera_m + distancia_m * math.tan(ang_base)

    return Perception(
        track_id=detection.track_id,
        cls=detection.cls,
        conf=detection.conf,
        distance_m=distancia_m,
        lateral_m=lateral_m,
        top_m=top_m,
        bottom_m=bottom_m,
        truncated=detection.truncated,
        source="semantic",
        t_capture=detection.t_capture,
    )


def detections_to_perceptions(
    detections: list[Detection], classes: dict[str, ClassInfo], calib: Calibracao
) -> list[Perception]:
    """Converte um lote de `Detection` (Fase 1) em `Perception` (Fase 2), pulando
    silenciosamente as que não têm altura conhecida ou deram geometria degenerada."""
    perceptions: list[Perception] = []
    for d in detections:
        info = classes.get(d.cls)
        altura_real_m = info.altura_m if info is not None else None
        p = detection_to_perception(d, altura_real_m, calib)
        if p is not None:
            perceptions.append(p)
    return perceptions
