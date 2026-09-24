"""Testes do supervisor (RN-04, RN-27, RN-34; arquitetura seção 7). Como em
test_core_decide.py, usa a config real de shared/config/."""

from dataclasses import replace

from visao.config import load_params
from visao.supervisor.monitor import tick
from visao.supervisor.types import FaultKind, SupervisorInputs, SupervisorState, SystemState

PARAMS = load_params()
CFG = PARAMS["supervisor"]

OK = SupervisorInputs(
    last_frame_t=0.0,
    fps_recente=30.0,
    profundidade_esperada=False,
    profundidade_last_update=None,
    brilho_medio=200.0,
    excecao=False,
)


def test_tudo_ok_fica_rodando():
    report, _ = tick(OK, SupervisorState(), now=0.05, params=PARAMS)
    assert report.state == SystemState.RODANDO
    assert report.fault is None
    assert report.pouca_luz is False


def test_excecao_e_falha_imediata():
    inputs = replace(OK, excecao=True)
    report, _ = tick(inputs, SupervisorState(), now=0.05, params=PARAMS)
    assert report.state == SystemState.FALHA
    assert report.fault == FaultKind.ERRO


def test_sem_nenhum_frame_ainda_e_falha_de_camera():
    """Primeiro tick, câmera nunca deu sinal — na dúvida, alerta (não assume que está tudo bem)."""
    inputs = replace(OK, last_frame_t=None)
    report, _ = tick(inputs, SupervisorState(), now=0.0, params=PARAMS)
    assert report.state == SystemState.FALHA
    assert report.fault == FaultKind.CAMERA


def test_camera_atrasada_alem_do_timeout_e_falha():
    timeout_s = CFG["captura_timeout_ms"] / 1000
    inputs = replace(OK, last_frame_t=0.0)
    report, _ = tick(inputs, SupervisorState(), now=timeout_s + 0.1, params=PARAMS)
    assert report.state == SystemState.FALHA
    assert report.fault == FaultKind.CAMERA


def test_camera_dentro_do_timeout_nao_e_falha():
    timeout_s = CFG["captura_timeout_ms"] / 1000
    inputs = replace(OK, last_frame_t=0.0)
    report, _ = tick(inputs, SupervisorState(), now=timeout_s / 2, params=PARAMS)
    assert report.state == SystemState.RODANDO


def _em(now: float, **overrides):
    """OK, mas com a câmera "viva" nesse instante — para isolar só o que o teste
    quer verificar (fps/luz/profundidade), sem disparar Falha de câmera por tabela."""
    return replace(OK, last_frame_t=now, **overrides)


def test_fps_baixo_precisa_persistir_a_janela_antes_de_falhar():
    state = SupervisorState()
    janela = CFG["janela_fps_s"]

    report, state = tick(_em(0.0, fps_recente=1.0), state, now=0.0, params=PARAMS)
    assert report.state == SystemState.RODANDO  # acabou de começar a cair

    report, state = tick(_em(janela - 0.1, fps_recente=1.0), state, now=janela - 0.1, params=PARAMS)
    assert report.state == SystemState.RODANDO  # ainda dentro da janela

    report, state = tick(_em(janela + 0.1, fps_recente=1.0), state, now=janela + 0.1, params=PARAMS)
    assert report.state == SystemState.FALHA
    assert report.fault == FaultKind.LENTO


def test_fps_que_se_recupera_reseta_o_temporizador():
    state = SupervisorState()
    _, state = tick(_em(0.0, fps_recente=1.0), state, now=0.0, params=PARAMS)
    assert state.fps_baixo_desde == 0.0

    _, state = tick(_em(0.5), state, now=0.5, params=PARAMS)  # recupera
    assert state.fps_baixo_desde is None

    # cai de novo — precisa recomeçar a contar, não retomar o temporizador antigo
    report, state = tick(_em(0.6, fps_recente=1.0), state, now=0.6, params=PARAMS)
    assert state.fps_baixo_desde == 0.6
    assert report.state == SystemState.RODANDO


def test_profundidade_nao_esperada_nunca_degrada():
    """Perfil sem profundidade (ex.: notebook) não é falha — é o perfil, não um defeito."""
    inputs = _em(1000.0, profundidade_esperada=False, profundidade_last_update=None)
    report, _ = tick(inputs, SupervisorState(), now=1000.0, params=PARAMS)
    assert report.state == SystemState.RODANDO


def test_profundidade_esperada_mas_nunca_chegou_e_degradado():
    inputs = replace(OK, profundidade_esperada=True, profundidade_last_update=None)
    report, _ = tick(inputs, SupervisorState(), now=0.0, params=PARAMS)
    assert report.state == SystemState.DEGRADADO


def test_profundidade_esperada_e_velha_e_degradado():
    max_idade_s = PARAMS["profundidade"]["max_idade_falha_ms"] / 1000
    now = max_idade_s + 0.1
    inputs = _em(now, profundidade_esperada=True, profundidade_last_update=0.0)
    report, _ = tick(inputs, SupervisorState(), now=now, params=PARAMS)
    assert report.state == SystemState.DEGRADADO


def test_profundidade_esperada_e_fresca_nao_degrada():
    inputs = replace(OK, profundidade_esperada=True, profundidade_last_update=0.0)
    report, _ = tick(inputs, SupervisorState(), now=0.05, params=PARAMS)
    assert report.state == SystemState.RODANDO


def test_luz_baixa_precisa_persistir_a_janela_antes_do_aviso():
    state = SupervisorState()
    janela = CFG["luz_janela_s"]

    report, state = tick(_em(0.0, brilho_medio=5.0), state, now=0.0, params=PARAMS)
    assert report.pouca_luz is False

    now = janela + 0.1
    report, state = tick(_em(now, brilho_medio=5.0), state, now=now, params=PARAMS)
    assert report.pouca_luz is True
    assert report.state == SystemState.RODANDO  # pouca luz é aviso, não Falha


def test_luz_ok_nunca_ativa_o_aviso():
    report, _ = tick(OK, SupervisorState(), now=1000.0, params=PARAMS)
    assert report.pouca_luz is False


def test_falha_tem_prioridade_sobre_degradado_e_pouca_luz():
    """Quando há Falha, ela domina o canal de áudio (P0) — o aviso de pouca luz some."""
    inputs = replace(
        OK,
        last_frame_t=None,  # dispara Falha de câmera
        profundidade_esperada=True,
        profundidade_last_update=None,  # também degradaria, se não houvesse Falha
        brilho_medio=5.0,  # também acionaria pouca_luz, se não houvesse Falha
    )
    report, _ = tick(inputs, SupervisorState(), now=0.0, params=PARAMS)
    assert report.state == SystemState.FALHA
    assert report.fault == FaultKind.CAMERA
    assert report.pouca_luz is False


def test_tick_e_puro_mesma_entrada_mesma_saida():
    state = SupervisorState()
    r1, s1 = tick(OK, state, now=10.0, params=PARAMS)
    r2, s2 = tick(OK, state, now=10.0, params=PARAMS)
    assert r1 == r2
    assert s1 == s2


def test_tick_nao_muta_o_estado_recebido():
    original = SupervisorState(fps_baixo_desde=1.0, luz_baixa_desde=2.0)
    snapshot = replace(original)
    tick(OK, original, now=10.0, params=PARAMS)
    assert original == snapshot
