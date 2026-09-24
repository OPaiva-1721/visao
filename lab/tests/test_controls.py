from visao.config import load_params
from visao.controls import persistence
from visao.controls.keyboard import aplicar_tecla
from visao.controls.types import ControlsState
from visao.core.types import Mode

PARAMS = load_params()
INICIAL = ControlsState(mode=Mode.CAMINHADA, volume=0.8)


# --- teclado -------------------------------------------------------------------


def test_troca_para_explorar_confirma_com_o_clipe_certo():
    state, confirmacao = aplicar_tecla("e", INICIAL, PARAMS)
    assert state.mode == Mode.EXPLORAR
    assert confirmacao is not None
    assert confirmacao.clip_key == "modo_explorar"
    assert confirmacao.beep_referencia is False


def test_troca_para_silencioso_confirma_com_o_clipe_certo():
    state, confirmacao = aplicar_tecla("s", INICIAL, PARAMS)
    assert state.mode == Mode.SILENCIOSO
    assert confirmacao is not None
    assert confirmacao.clip_key == "modo_silencioso"


def test_trocar_para_o_mesmo_modo_nao_confirma_nada():
    state, confirmacao = aplicar_tecla("c", INICIAL, PARAMS)  # já está em Caminhada
    assert state == INICIAL
    assert confirmacao is None


def test_volume_sobe_e_confirma_com_bipe_de_referencia():
    state, confirmacao = aplicar_tecla("+", INICIAL, PARAMS)
    assert state.volume > INICIAL.volume
    assert confirmacao is not None
    assert confirmacao.beep_referencia is True
    assert confirmacao.clip_key is None


def test_volume_desce():
    state, _ = aplicar_tecla("-", INICIAL, PARAMS)
    assert state.volume < INICIAL.volume


def test_volume_nao_passa_de_1():
    quase_no_topo = ControlsState(mode=Mode.CAMINHADA, volume=0.95)
    state, _ = aplicar_tecla("+", quase_no_topo, PARAMS)
    assert state.volume == 1.0


def test_volume_nao_fica_negativo():
    quase_no_fundo = ControlsState(mode=Mode.CAMINHADA, volume=0.05)
    state, _ = aplicar_tecla("-", quase_no_fundo, PARAMS)
    assert state.volume == 0.0


def test_tecla_desconhecida_nao_muda_nada():
    state, confirmacao = aplicar_tecla("x", INICIAL, PARAMS)
    assert state == INICIAL
    assert confirmacao is None


# --- persistência (RN-22) ------------------------------------------------------


def test_load_sem_arquivo_devolve_o_padrao(tmp_path):
    caminho = tmp_path / "controles.json"
    assert persistence.load(caminho, default=INICIAL) == INICIAL


def test_save_depois_load_recupera_o_estado(tmp_path):
    caminho = tmp_path / "controles.json"
    modificado = ControlsState(mode=Mode.SILENCIOSO, volume=0.3)
    persistence.save(caminho, modificado)
    assert persistence.load(caminho, default=INICIAL) == modificado


def test_load_com_arquivo_corrompido_devolve_o_padrao(tmp_path):
    caminho = tmp_path / "controles.json"
    caminho.write_text("{ isso não é json válido", encoding="utf-8")
    assert persistence.load(caminho, default=INICIAL) == INICIAL


def test_load_com_campo_faltando_devolve_o_padrao(tmp_path):
    caminho = tmp_path / "controles.json"
    caminho.write_text('{"mode": "caminhada"}', encoding="utf-8")  # sem "volume"
    assert persistence.load(caminho, default=INICIAL) == INICIAL


def test_load_com_modo_invalido_devolve_o_padrao(tmp_path):
    caminho = tmp_path / "controles.json"
    caminho.write_text('{"mode": "voando", "volume": 0.5}', encoding="utf-8")
    assert persistence.load(caminho, default=INICIAL) == INICIAL
