import pytest

from visao.audio.vocab import SIDE_TO_VOCAB_KEY, flatten_vocabulary
from visao.config import load_vocabulary


def test_flatten_junta_todas_as_secoes():
    vocab = {"a": {"x": "X"}, "b": {"y": "Y"}}
    assert flatten_vocabulary(vocab) == {"x": "X", "y": "Y"}


def test_flatten_detecta_chave_duplicada_entre_secoes():
    vocab = {"a": {"x": "X"}, "b": {"x": "outra coisa"}}
    with pytest.raises(ValueError, match="duplicada"):
        flatten_vocabulary(vocab)


def test_vocabulario_real_nao_tem_chave_duplicada():
    # Também garante que flatten_vocabulary(load_vocabulary()) nunca quebra em runtime.
    flat = flatten_vocabulary(load_vocabulary())
    assert len(flat) > 0


def test_side_to_vocab_key_cobre_os_tres_lados_e_bate_com_o_vocabulario():
    assert set(SIDE_TO_VOCAB_KEY.keys()) == {"esq", "frente", "dir"}
    direcoes = load_vocabulary()["direcoes"]
    for vocab_key in SIDE_TO_VOCAB_KEY.values():
        assert vocab_key in direcoes
