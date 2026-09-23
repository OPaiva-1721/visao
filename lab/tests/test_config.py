from pathlib import Path

import pytest
import yaml

from visao.config import (
    SHARED_DIR,
    available_profiles,
    deep_merge,
    load_classes,
    load_params,
    load_vocabulary,
)


def test_params_base_carrega_valores_das_rns():
    params = load_params()
    assert params["zonas_m"]["perto"] < params["zonas_m"]["atencao"]
    assert params["seguranca"]["latencia_max_ms"] == 300
    assert params["audio"]["saida"] == "mono"


def test_faixas_de_altura_em_ordem_e_teto_acima_da_usuaria():
    params = load_params()
    faixas = params["faixas_altura_m"]
    assert faixas["chao_ate"] < faixas["tronco_ate"] < faixas["teto"]
    assert faixas["teto"] > params["usuaria"]["altura_m"]


def test_existem_os_tres_perfis():
    assert available_profiles() == ["celular", "notebook", "pc"]


@pytest.mark.parametrize("perfil", ["pc", "notebook", "celular"])
def test_perfil_sobrepoe_so_o_que_define(perfil):
    base = load_params()
    params = load_params(perfil)
    assert "inferencia" in params
    assert params["zonas_m"] == base["zonas_m"]


def test_notebook_desliga_profundidade_sem_perder_os_outros_campos():
    params = load_params("notebook")
    assert params["profundidade"]["ligada"] is False
    assert params["profundidade"]["max_idade_falha_ms"] == 500


def test_perfil_desconhecido_falha_com_mensagem_clara():
    with pytest.raises(ValueError, match="perfil desconhecido"):
        load_params("raspberry")


def test_deep_merge_nao_altera_a_base():
    base = {"a": {"b": 1, "c": 2}}
    merged = deep_merge(base, {"a": {"b": 9}})
    assert merged == {"a": {"b": 9, "c": 2}}
    assert base == {"a": {"b": 1, "c": 2}}


def test_toda_classe_tem_clipe_de_fala_no_vocabulario():
    objetos = load_vocabulary()["objetos"]
    sem_audio = [c.name for c in load_classes().values() if c.fala not in objetos]
    assert sem_audio == []


def test_classes_tem_perigo_valido_e_altura_positiva():
    for info in load_classes().values():
        assert info.perigo in (1, 2, 3), info.name
        assert info.altura_m is None or info.altura_m > 0, info.name


def test_obstaculo_generico_existe():
    assert "obstaculo" in load_classes()


def test_yaml_compartilhado_e_utf8_valido():
    for path in Path(SHARED_DIR).rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
