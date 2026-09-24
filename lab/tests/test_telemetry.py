import json

import pytest

from visao.core.types import AlertPlan, Band, BeepSpec, Mode, SpeechSpec
from visao.supervisor.types import FaultKind, SupervisorReport, SystemState
from visao.telemetry.record import build_record
from visao.telemetry.writer import TelemetryWriter

VAZIO = AlertPlan(beep=None, speech=None, t_capture=1.0)


def test_registro_de_plano_vazio():
    r = build_record(now=1.2, mode=Mode.CAMINHADA, plan=VAZIO)
    assert r["modo"] == "caminhada"
    assert r["bipe"] is None
    assert r["fala"] is None
    assert r["latencia_ms"] == pytest.approx(200.0)


def test_registro_com_bipe_e_fala():
    plan = AlertPlan(
        beep=BeepSpec(rate_hz=8.0, band=Band.CABECA, side="dir"),
        speech=SpeechSpec(clip_keys=("pessoa",), priority=1),
        t_capture=0.0,
    )
    r = build_record(now=0.0, mode=Mode.CAMINHADA, plan=plan)
    assert r["bipe"] == {"rate_hz": 8.0, "banda": "cabeca", "lado": "dir"}
    assert r["fala"] == {"clip_keys": ["pessoa"], "prioridade": 1}


def test_registro_inclui_o_supervisor_quando_fornecido():
    supervisor = SupervisorReport(state=SystemState.FALHA, fault=FaultKind.CAMERA, pouca_luz=False)
    r = build_record(now=0.0, mode=Mode.CAMINHADA, plan=VAZIO, supervisor=supervisor)
    assert r["estado"] == "falha"
    assert r["falha"] == "falha_camera"
    assert r["pouca_luz"] is False


def test_registro_sem_supervisor_nao_tem_essas_chaves():
    r = build_record(now=0.0, mode=Mode.CAMINHADA, plan=VAZIO)
    assert "estado" not in r
    assert "falha" not in r


def test_registro_nunca_carrega_imagem():
    """RN-28: o registro só pode conter tipos simples (serializáveis em JSON) — nunca
    um array de imagem, mesmo que alguém tente passar algo estranho como plan/supervisor."""
    r = build_record(now=0.0, mode=Mode.CAMINHADA, plan=VAZIO)
    json.dumps(r)  # não lança — só tipos simples


# --- TelemetryWriter (IO) ------------------------------------------------------


def test_writer_grava_um_json_por_linha(tmp_path):
    caminho = tmp_path / "sessao.jsonl"
    with TelemetryWriter(caminho) as w:
        w.write({"t": 1})
        w.write({"t": 2})

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 2
    assert json.loads(linhas[0]) == {"t": 1}
    assert json.loads(linhas[1]) == {"t": 2}


def test_writer_cria_o_diretorio_se_precisar(tmp_path):
    caminho = tmp_path / "sessoes" / "hoje" / "sessao.jsonl"
    with TelemetryWriter(caminho) as w:
        w.write({"t": 1})
    assert caminho.exists()


def test_writer_acrescenta_em_vez_de_sobrescrever(tmp_path):
    caminho = tmp_path / "sessao.jsonl"
    with TelemetryWriter(caminho) as w:
        w.write({"t": 1})
    with TelemetryWriter(caminho) as w:
        w.write({"t": 2})
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 2
