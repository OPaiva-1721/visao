"""Testes da fila de prioridade de voz (RN-06, RN-15). Config real, como no resto."""

from visao.audio.priority import Acao, VoiceState, canal_livre, chegou, deve_repetir_falha
from visao.config import load_params
from visao.core.types import SpeechSpec

PARAMS = load_params()

FALHA = SpeechSpec(clip_keys=("falha_camera",), priority=0)
PERTO = SpeechSpec(clip_keys=("pessoa",), priority=1)
CONFIRMACAO = SpeechSpec(clip_keys=("modo_explorar",), priority=2)
ATENCAO = SpeechSpec(clip_keys=("cadeira",), priority=3)
INFORMACAO = SpeechSpec(clip_keys=("mesa",), priority=4)


def test_canal_livre_toca_na_hora():
    acao, estado = chegou(PERTO, t_capture=0.0, state=VoiceState(), now=0.01, params=PARAMS)
    assert acao == Acao.TOCAR_AGORA
    assert estado.tocando is PERTO


def test_mais_urgente_interrompe_o_que_esta_tocando():
    """RN-17/tabela P0–P4: Falha (P0) interrompe qualquer coisa, mesmo Perto (P1)."""
    tocando_atencao = VoiceState(tocando=ATENCAO)
    acao, estado = chegou(FALHA, t_capture=0.0, state=tocando_atencao, now=0.0, params=PARAMS)
    assert acao == Acao.TOCAR_AGORA
    assert estado.tocando is FALHA
    assert estado.esperando is None  # o que estava tocando foi cortado, não virou espera


def test_menos_urgente_nao_interrompe_e_vai_para_espera():
    tocando_perto = VoiceState(tocando=PERTO)
    acao, estado = chegou(ATENCAO, t_capture=0.0, state=tocando_perto, now=0.0, params=PARAMS)
    assert acao == Acao.ESPERAR
    assert estado.tocando is PERTO  # continua tocando o que já estava
    assert estado.esperando is ATENCAO


def test_prioridade_igual_tambem_nao_interrompe():
    """RN-14 evita repetir o mesmo objeto; aqui é sobre prioridades diferentes chegando
    juntas — duas P3 (ex.: dois obstáculos em Atenção) não deveriam se cortar uma à outra."""
    tocando_atencao = VoiceState(tocando=ATENCAO)
    outra_atencao = SpeechSpec(clip_keys=("banco",), priority=3)
    acao, estado = chegou(
        outra_atencao, t_capture=0.0, state=tocando_atencao, now=0.0, params=PARAMS
    )
    assert acao == Acao.ESPERAR


def test_nova_espera_substitui_a_espera_antiga_se_mais_urgente():
    esperando_informacao = VoiceState(tocando=PERTO, esperando=INFORMACAO, esperando_t_capture=0.0)
    acao, estado = chegou(
        CONFIRMACAO, t_capture=1.0, state=esperando_informacao, now=1.0, params=PARAMS
    )
    assert acao == Acao.ESPERAR
    assert estado.esperando is CONFIRMACAO  # P2 é mais urgente que a P4 que esperava


def test_nova_espera_nao_substitui_se_menos_urgente_que_a_que_esperava():
    esperando_confirmacao = VoiceState(
        tocando=PERTO, esperando=CONFIRMACAO, esperando_t_capture=0.0
    )
    acao, estado = chegou(
        INFORMACAO, t_capture=1.0, state=esperando_confirmacao, now=1.0, params=PARAMS
    )
    assert acao == Acao.DESCARTAR
    assert estado.esperando is CONFIRMACAO  # não perde o que já esperava por algo pior


def test_mensagem_que_ja_nasce_velha_e_descartada_mesmo_com_canal_livre():
    limite_s = PARAMS["seguranca"]["mensagem_max_idade_ms"] / 1000
    acao, estado = chegou(
        ATENCAO, t_capture=0.0, state=VoiceState(), now=limite_s + 0.1, params=PARAMS
    )
    assert acao == Acao.DESCARTAR
    assert estado == VoiceState()


def test_mensagem_dentro_do_limite_de_idade_toca():
    limite_s = PARAMS["seguranca"]["mensagem_max_idade_ms"] / 1000
    acao, _ = chegou(ATENCAO, t_capture=0.0, state=VoiceState(), now=limite_s - 0.05, params=PARAMS)
    assert acao == Acao.TOCAR_AGORA


def test_canal_livre_sem_nada_esperando():
    proximo, estado = canal_livre(VoiceState(tocando=PERTO), now=0.0, params=PARAMS)
    assert proximo is None
    assert estado == VoiceState()


def test_canal_livre_toca_o_que_esperava():
    estado_antes = VoiceState(tocando=PERTO, esperando=ATENCAO, esperando_t_capture=0.0)
    proximo, estado = canal_livre(estado_antes, now=0.05, params=PARAMS)
    assert proximo is ATENCAO
    assert estado.tocando is ATENCAO
    assert estado.esperando is None


def test_canal_livre_descarta_quem_esperou_demais():
    limite_s = PARAMS["seguranca"]["mensagem_max_idade_ms"] / 1000
    estado_antes = VoiceState(tocando=PERTO, esperando=ATENCAO, esperando_t_capture=0.0)
    proximo, estado = canal_livre(estado_antes, now=limite_s + 0.1, params=PARAMS)
    assert proximo is None
    assert estado == VoiceState()


def test_deve_repetir_falha_na_primeira_vez():
    assert deve_repetir_falha(None, now=0.0, params=PARAMS) is True


def test_deve_repetir_falha_antes_do_intervalo():
    assert deve_repetir_falha(0.0, now=0.5, params=PARAMS) is False


def test_deve_repetir_falha_apos_o_intervalo():
    intervalo = PARAMS["seguranca"]["falha_repete_s"]
    assert deve_repetir_falha(0.0, now=intervalo + 0.1, params=PARAMS) is True
