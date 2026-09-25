import math

from visao.core.types import ClassInfo
from visao.perception.geometry import (
    Calibracao,
    detection_to_perception,
    detections_to_perceptions,
)
from visao.perception.types import Detection

CLASSES = {
    "person": ClassInfo(name="person", fala="pessoa", perigo=3, altura_m=1.65, conf_min=0.45),
    "stop sign": ClassInfo(name="stop sign", fala="placa", perigo=3, altura_m=None, conf_min=None),
}


def make_detection(y1: float, y2: float, x1: float = 300.0, x2: float = 340.0) -> Detection:
    return Detection(
        track_id=1,
        cls="person",
        conf=0.9,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        truncated=False,
        t_capture=0.0,
    )


def test_sem_inclinacao_bate_com_a_formula_simplificada():
    """θ=0: d = f·H/h, top/bottom = y_cam ± (metade da caixa)·d/f (arquitetura seção 4.2)."""
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    d = make_detection(y1=140, y2=340, x1=300, x2=340)  # h_px=200, u_centro=320=cx
    p = detection_to_perception(d, altura_real_m=1.65, calib=calib)

    assert p is not None
    assert math.isclose(p.distance_m, 500 * 1.65 / 200, rel_tol=1e-9)
    assert math.isclose(p.top_m, 1.0 + 0.825, rel_tol=1e-9)
    assert math.isclose(p.bottom_m, 1.0 - 0.825, rel_tol=1e-9)
    assert math.isclose(p.lateral_m, 0.0, abs_tol=1e-9)


def test_lateral_positivo_a_direita_negativo_a_esquerda():
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    direita = detection_to_perception(
        make_detection(y1=140, y2=340, x1=400, x2=440), altura_real_m=1.65, calib=calib
    )
    esquerda = detection_to_perception(
        make_detection(y1=140, y2=340, x1=200, x2=240), altura_real_m=1.65, calib=calib
    )
    assert direita is not None and esquerda is not None
    assert direita.lateral_m > 0
    assert esquerda.lateral_m < 0


def test_inclinacao_muda_a_altura_estimada():
    """Mesma caixa, mesma câmera, só a inclinação muda — top/bottom têm que mudar."""
    d = make_detection(y1=140, y2=340)
    calib_reta = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    calib_inclinada = Calibracao(
        f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=10
    )

    p_reta = detection_to_perception(d, altura_real_m=1.65, calib=calib_reta)
    p_inclinada = detection_to_perception(d, altura_real_m=1.65, calib=calib_inclinada)

    assert p_reta is not None and p_inclinada is not None
    assert not math.isclose(p_reta.top_m, p_inclinada.top_m, abs_tol=1e-6)
    assert not math.isclose(p_reta.bottom_m, p_inclinada.bottom_m, abs_tol=1e-6)


def test_classe_sem_altura_conhecida_devolve_none():
    """RN: altura_m null = sem pinhole, só profundidade (ainda não construída)."""
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    p = detection_to_perception(make_detection(y1=140, y2=340), altura_real_m=None, calib=calib)
    assert p is None


def test_caixa_degenerada_devolve_none_em_vez_de_quebrar():
    """y1 >= y2 (caixa invertida/achatada) não deve gerar distância inválida."""
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    p = detection_to_perception(make_detection(y1=200, y2=200), altura_real_m=1.65, calib=calib)
    assert p is None


def test_preserva_track_id_classe_confianca_truncado_e_t_capture():
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    d = Detection(
        track_id=7,
        cls="person",
        conf=0.77,
        x1=300,
        y1=140,
        x2=340,
        y2=340,
        truncated=True,
        t_capture=12.5,
    )
    p = detection_to_perception(d, altura_real_m=1.65, calib=calib)
    assert p is not None
    assert p.track_id == 7
    assert p.cls == "person"
    assert p.conf == 0.77
    assert p.truncated is True
    assert p.t_capture == 12.5
    assert p.source == "semantic"


def test_detections_to_perceptions_pula_classe_sem_altura_e_preserva_a_outra():
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    pessoa = make_detection(y1=140, y2=340)
    placa = Detection(
        track_id=2,
        cls="stop sign",
        conf=0.8,
        x1=300,
        y1=140,
        x2=340,
        y2=340,
        truncated=False,
        t_capture=0.0,
    )
    resultado = detections_to_perceptions([pessoa, placa], CLASSES, calib)
    assert len(resultado) == 1
    assert resultado[0].cls == "person"


def test_detections_to_perceptions_classe_desconhecida_e_ignorada():
    calib = Calibracao(f_px=500, cx_px=320, cy_px=240, altura_camera_m=1.0, inclinacao_graus=0)
    desconhecida = Detection(
        track_id=3,
        cls="skateboard",
        conf=0.9,
        x1=300,
        y1=140,
        x2=340,
        y2=340,
        truncated=False,
        t_capture=0.0,
    )
    assert detections_to_perceptions([desconhecida], CLASSES, calib) == []
