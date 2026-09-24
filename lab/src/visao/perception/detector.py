"""Detector (YOLO26n + ByteTrack, ADR-015). Requer o extra "visao".

Produz `Detection` (caixa + track_id + classe), não `Perception` — ainda não há
distância nem altura reais: isso é geometria/profundidade, Fase 2 (docs/arquitetura.md
seção 14). `parse_boxes` é pura e testável sem o Ultralytics instalado; só `Detector`
precisa do extra de verdade.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from visao.core.types import ClassInfo
from visao.perception.types import Detection

if TYPE_CHECKING:
    from visao.capture.frame import Frame

# (x1, y1, x2, y2, conf, cls_id, track_id) em pixels — cls_id é o índice do Ultralytics
# (chave de `model.names`); track_id é None quando o ByteTrack ainda não confirmou um ID.
RawBox = tuple[float, float, float, float, float, int, int | None]


def _is_truncated(
    x1: float, y1: float, x2: float, y2: float, width: int, height: int, tolerancia_px: float
) -> bool:
    """RN-33: a caixa encosta (ou quase) na borda da imagem."""
    return (
        x1 <= tolerancia_px
        or y1 <= tolerancia_px
        or x2 >= width - tolerancia_px
        or y2 >= height - tolerancia_px
    )


def parse_boxes(
    boxes: Sequence[RawBox],
    names: dict[int, str],
    classes: dict[str, ClassInfo],
    img_width: int,
    img_height: int,
    t_capture: float,
    tolerancia_borda_px: float,
) -> list[Detection]:
    """RN-16 (só classes da lista) e RN-33 (marca objeto cortado). Descarta caixas sem
    track_id — o ByteTrack ainda não confirmou um ID; ele aparece nos próximos frames.
    """
    detections: list[Detection] = []
    for x1, y1, x2, y2, conf, cls_id, track_id in boxes:
        if track_id is None:
            continue
        name = names.get(cls_id)
        if name is None or name not in classes:  # RN-16
            continue
        detections.append(
            Detection(
                track_id=track_id,
                cls=name,
                conf=conf,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                truncated=_is_truncated(x1, y1, x2, y2, img_width, img_height, tolerancia_borda_px),
                t_capture=t_capture,
            )
        )
    return detections


def _raw_boxes_from_results(result) -> list[RawBox]:
    """Converte o `Results` do Ultralytics (tensores) em tuplas de Python simples."""
    boxes = result.boxes
    if boxes is None or boxes.id is None:
        return []
    xyxy = boxes.xyxy.tolist()
    conf = boxes.conf.tolist()
    cls = boxes.cls.tolist()
    ids = boxes.id.tolist()
    return [
        (x1, y1, x2, y2, c, int(cl), int(tid))
        for (x1, y1, x2, y2), c, cl, tid in zip(xyxy, conf, cls, ids, strict=True)
    ]


class Detector:
    """Envolve `ultralytics.YOLO` (modelo + ByteTrack). Requer `uv sync --extra visao`."""

    def __init__(
        self,
        model_path: str,
        classes: dict[str, ClassInfo],
        tolerancia_borda_px: float,  # params["deteccao"]["borda_tolerancia_px"] (RN-33)
    ) -> None:
        try:
            # extra "visao" opcional
            from ultralytics import YOLO  # pyright: ignore[reportMissingImports]
        except ImportError as e:
            raise RuntimeError(
                "ultralytics não instalado. Rode: uv sync --extra visao (ADR-015)."
            ) from e
        self._model = YOLO(model_path)
        self._classes = classes
        self._tolerancia_borda_px = tolerancia_borda_px
        # Restringe o YOLO só às classes que o núcleo entende (RN-16) — menos ruído,
        # menos trabalho de pós-processamento.
        self._allowed_ids = [i for i, name in self._model.names.items() if name in classes]

    def detect(self, frame: Frame, imgsz: int = 320) -> list[Detection]:
        results = self._model.track(
            frame.image,
            persist=True,
            tracker="bytetrack.yaml",
            classes=self._allowed_ids,
            imgsz=imgsz,
            verbose=False,
        )
        height, width = frame.image.shape[:2]
        return parse_boxes(
            _raw_boxes_from_results(results[0]),
            self._model.names,
            self._classes,
            width,
            height,
            frame.t_capture,
            self._tolerancia_borda_px,
        )
