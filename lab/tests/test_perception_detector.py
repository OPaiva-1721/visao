"""`parse_boxes` é pura — testável sem o Ultralytics instalado (roda sempre no CI).
`Detector` precisa do extra "visao" de verdade — os testes que o usam são pulados
quando ele não está instalado (`pytest.importorskip`)."""

from pathlib import Path

import numpy as np
import pytest

from visao.capture.frame import Frame
from visao.config import load_classes
from visao.perception.detector import Detector, parse_boxes

CLASSES = load_classes()
NAMES = {0: "person", 1: "chair", 2: "unicornio"}  # "unicornio" não está em classes.yaml


def test_parse_boxes_filtra_classe_desconhecida():
    boxes = [(0, 0, 10, 10, 0.9, 2, 1)]  # cls_id=2 -> "unicornio"
    out = parse_boxes(boxes, NAMES, CLASSES, 100, 100, t_capture=0.0, tolerancia_borda_px=2)
    assert out == []


def test_parse_boxes_descarta_sem_track_id():
    """ByteTrack ainda não confirmou um ID — RN-11 do núcleo precisa de um track_id
    estável; sem ele, essa caixa é ignorada até o próprio ByteTrack lhe dar um."""
    boxes = [(10, 10, 20, 20, 0.9, 0, None)]
    out = parse_boxes(boxes, NAMES, CLASSES, 100, 100, t_capture=0.0, tolerancia_borda_px=2)
    assert out == []


def test_parse_boxes_mantem_classe_conhecida_com_track_id():
    boxes = [(10, 10, 20, 30, 0.9, 0, 7)]  # cls_id=0 -> "person"
    out = parse_boxes(boxes, NAMES, CLASSES, 100, 100, t_capture=1.5, tolerancia_borda_px=2)
    assert len(out) == 1
    d = out[0]
    assert d.track_id == 7
    assert d.cls == "person"
    assert d.conf == 0.9
    assert (d.x1, d.y1, d.x2, d.y2) == (10, 10, 20, 30)
    assert d.t_capture == 1.5
    assert d.truncated is False


def test_parse_boxes_marca_rn33_caixa_encostando_na_borda():
    largura, altura = 100, 100
    tolerancia = 2
    casos = [
        (0, 10, 20, 20, "esquerda"),
        (10, 0, 20, 20, "topo"),
        (80, 10, largura, 20, "direita"),
        (10, 80, 20, altura, "base"),
    ]
    for x1, y1, x2, y2, _lado in casos:
        boxes = [(x1, y1, x2, y2, 0.9, 0, 1)]
        out = parse_boxes(boxes, NAMES, CLASSES, largura, altura, 0.0, tolerancia)
        assert out[0].truncated is True, _lado


def test_parse_boxes_nao_marca_caixa_bem_no_meio():
    boxes = [(40, 40, 60, 60, 0.9, 0, 1)]
    out = parse_boxes(boxes, NAMES, CLASSES, 100, 100, 0.0, tolerancia_borda_px=2)
    assert out[0].truncated is False


def test_parse_boxes_varias_caixas_juntas():
    boxes = [
        (10, 10, 20, 20, 0.9, 0, 1),
        (30, 30, 40, 40, 0.8, 1, 2),  # "chair"
        (50, 50, 60, 60, 0.7, 2, 3),  # "unicornio" — descartada
    ]
    out = parse_boxes(boxes, NAMES, CLASSES, 100, 100, 0.0, tolerancia_borda_px=2)
    assert {d.track_id for d in out} == {1, 2}


# --- Detector (real, precisa do extra "visao") --------------------------------

MODELO_LOCAL = Path(__file__).resolve().parents[2] / "data" / "modelos" / "yolo26n.pt"


@pytest.mark.skipif(not MODELO_LOCAL.exists(), reason="peso não baixado (data/modelos/)")
def test_detector_roda_sem_quebrar_numa_imagem_sintetica():
    pytest.importorskip("ultralytics")
    from visao.config import load_params

    borda = load_params()["deteccao"]["borda_tolerancia_px"]
    detector = Detector(str(MODELO_LOCAL), CLASSES, tolerancia_borda_px=borda)

    rng = np.random.default_rng(seed=0)
    image = rng.integers(0, 255, size=(320, 320, 3), dtype=np.uint8)
    frame = Frame(image=image, t_capture=0.0)

    detections = detector.detect(frame, imgsz=320)
    assert isinstance(detections, list)  # ruído não deveria ter nada — a checagem é não quebrar
