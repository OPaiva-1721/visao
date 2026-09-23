"""Testes do núcleo de decisão (docs/plano.md RN-08..16, RN-33). Usa a config real de
shared/config/ — se alguém mudar a forma do params.yaml sem atualizar decide.py, é aqui
que quebra."""

from dataclasses import replace

from visao.config import load_classes, load_params
from visao.core.decide import _band, _side, _zone, decide
from visao.core.state import CoreState
from visao.core.types import AlertPlan, Band, Mode, Perception, Zone

PARAMS = load_params()
CLASSES = load_classes()

_PERCEPTION_PADRAO = Perception(
    track_id=1,
    cls="person",
    conf=0.9,
    distance_m=1.5,  # zona Atenção (zonas_m: perto=1.0, atencao=2.0)
    lateral_m=0.0,
    top_m=1.65,  # pessoa de pé: alcança a faixa da cabeça
    bottom_m=0.0,
    truncated=False,
    source="semantic",
    t_capture=0.0,
)


def make_perception(**overrides) -> Perception:
    return replace(_PERCEPTION_PADRAO, **overrides)


def run(
    frames: list[list[Perception]], *, mode: Mode = Mode.CAMINHADA, step: float = 0.2
) -> tuple[list[AlertPlan], CoreState]:
    """Roda decide() um frame por vez, `now` avançando `step` segundos a cada chamada.

    `step` precisa ficar bem abaixo de tracking.ttl_s (1,0 s) — senão o objeto é
    esquecido entre uma chamada e outra e a persistência (RN-11) nunca se acumula.
    """
    state = CoreState()
    plans = []
    now = 0.0
    for perceptions in frames:
        plan, state = decide(perceptions, state, mode, now, PARAMS, CLASSES)
        plans.append(plan)
        now += step
    return plans, state


# --- Funções puras internas (band/zone/side) ---------------------------------


def test_zone_perto_atencao_longe():
    zonas = PARAMS["zonas_m"]
    assert _zone(0.5, False, zonas) == Zone.PERTO
    assert _zone(1.5, False, zonas) == Zone.ATENCAO
    assert _zone(5.0, False, zonas) == Zone.LONGE


def test_zone_rn33_objeto_cortado_forca_perto():
    """Mesmo longe, um objeto cortado pela borda conta como Perto — RN-33."""
    assert _zone(5.0, True, PARAMS["zonas_m"]) == Zone.PERTO


def test_band_classificacao_por_altura():
    faixas = PARAMS["faixas_altura_m"]
    assert _band(top_m=0.4, bottom_m=0.0, faixas=faixas) == Band.CHAO
    assert _band(top_m=0.9, bottom_m=0.0, faixas=faixas) == Band.TRONCO
    assert _band(top_m=1.65, bottom_m=0.0, faixas=faixas) == Band.CABECA


def test_band_rn09_ignora_objeto_com_base_acima_do_teto():
    """Ela passa por baixo — RN-09."""
    faixas = PARAMS["faixas_altura_m"]
    assert _band(top_m=2.0, bottom_m=1.8, faixas=faixas) is None


def test_side_frente_esquerda_direita():
    centro = PARAMS["audio"]["lado_centro_m"]
    assert _side(0.0, centro) == "frente"
    assert _side(-1.0, centro) == "esq"
    assert _side(1.0, centro) == "dir"


# --- RN-08 corredor, RN-10 confiança, RN-16 classes --------------------------


def test_rn08_fora_do_corredor_e_ignorado():
    largura = PARAMS["corredor"]["largura_corpo_m"] / 2 + PARAMS["corredor"]["margem_m"]
    p = make_perception(lateral_m=largura + 0.5)
    plans, _ = run([[p]] * 5)
    assert all(plan.beep is None for plan in plans)


def test_rn16_classe_fora_da_lista_e_ignorada():
    p = make_perception(cls="unicornio")
    plans, _ = run([[p]] * 5)
    assert all(plan.beep is None for plan in plans)


def test_rn10_confianca_abaixo_do_limiar_da_classe_e_ignorada():
    """'person' tem conf_min=0.45 em classes.yaml — abaixo disso, é ignorada mesmo confirmada."""
    p = make_perception(conf=0.30)
    plans, _ = run([[p]] * 5)
    assert all(plan.beep is None for plan in plans)


def test_rn10_limiar_por_classe_sobrepoe_o_padrao():
    """'person' aceita conf=0.46 (> 0.45), mesmo estando abaixo do padrão geral (0.50)."""
    p = make_perception(conf=0.46)
    plans, _ = run([[p]] * 5)
    assert any(plan.beep is not None for plan in plans)


# --- RN-11 persistência -------------------------------------------------------


def test_rn11_atencao_confirma_em_3_de_5():
    p = make_perception(distance_m=1.5)  # zona Atenção → persistencia.padrao (n=3, m=5)
    plans, _ = run([[p]] * 5)
    assert plans[0].beep is None
    assert plans[1].beep is None
    assert plans[2].beep is not None  # 3ª aparição seguida: confirmado


def test_rn11_perto_confirma_mais_rapido_2_de_3():
    p = make_perception(distance_m=0.5)  # zona Perto → persistencia.perto (n=2, m=3)
    plans, _ = run([[p]] * 3)
    assert plans[0].beep is None
    assert plans[1].beep is not None  # 2ª aparição seguida: confirmado


def test_rn11_um_frame_isolado_nao_confirma():
    """'Corta os fantasmas de um único frame' (RN-11)."""
    p = make_perception(distance_m=0.5)
    plans, _ = run([[p], [], [], [], []])
    assert all(plan.beep is None for plan in plans)


def test_ttl_esquece_objeto_apos_ausencia_longa():
    p = make_perception(track_id=42, distance_m=0.5)
    ttl = PARAMS["tracking"]["ttl_s"]
    # confirma (2 de 3, zona Perto), depois some por mais que o ttl, depois reaparece
    frames = [[p], [p], [], [p]]
    steps = [0.1, 0.1, ttl + 0.5, 0.1]
    state = CoreState()
    plans = []
    now = 0.0
    for perceptions, step in zip(frames, steps, strict=True):
        plan, state = decide(perceptions, state, Mode.CAMINHADA, now, PARAMS, CLASSES)
        plans.append(plan)
        now += step
    assert plans[1].beep is not None  # confirmado antes de desaparecer
    assert plans[3].beep is None  # precisa reconquistar a persistência


# --- RN-13 prioridade entre vários candidatos --------------------------------


def test_rn13_zona_mais_proxima_vence():
    perto = make_perception(track_id=1, distance_m=0.5, lateral_m=0.0)
    atencao = make_perception(track_id=2, distance_m=1.5, lateral_m=0.0)
    plans, _ = run([[perto, atencao]] * 3)
    assert plans[-1].beep is not None
    assert plans[-1].beep.rate_hz == PARAMS["audio"]["bipe"]["ritmo_hz"]["perto"]


def test_rn13_cabeca_vence_do_chao_na_mesma_zona():
    chao = make_perception(track_id=1, cls="obstaculo", conf=0.9, top_m=0.4, bottom_m=0.0)
    cabeca = make_perception(track_id=2, cls="obstaculo", conf=0.9, top_m=1.65, bottom_m=0.0)
    plans, _ = run([[chao, cabeca]] * 5)
    assert plans[-1].beep is not None
    assert plans[-1].beep.band == Band.CABECA


def test_rn13_mais_central_desempata():
    lateral = make_perception(track_id=1, lateral_m=0.3)
    central = make_perception(track_id=2, lateral_m=0.0)
    plans, _ = run([[lateral, central]] * 5)
    assert plans[-1].beep is not None
    assert plans[-1].beep.side == "frente"


def test_rn13_classe_mais_perigosa_desempata():
    """'person' (perigo=3) e 'chair' (perigo=2) no mesmo lugar — pessoa vence."""
    cadeira = make_perception(track_id=1, cls="chair", conf=0.9)
    pessoa = make_perception(track_id=2, cls="person", conf=0.9)
    plans, _ = run([[cadeira, pessoa]] * 5)
    assert plans[2].speech is not None
    assert plans[2].speech.clip_keys == ("pessoa",)  # 1º anúncio, já com o desempate certo
    assert plans[-1].beep is not None  # continua sinalizando a pessoa (RN-14 só cala a voz)


# --- RN-14 anti-repetição e RN-15 cooldown -----------------------------------


def test_rn14_nao_reanuncia_na_mesma_zona():
    p = make_perception(distance_m=1.5)
    plans, _ = run([[p]] * 6)  # confirma na 3ª (índice 2) e continua na mesma zona
    assert plans[2].speech is not None
    assert plans[3].speech is None
    assert plans[4].speech is None
    assert plans[3].beep is not None  # o bipe continua mesmo sem nova fala


def test_rn14_reanuncia_ao_se_aproximar():
    # fica um tempo em Atenção (confirma e anuncia no 3º frame, e o cooldown some
    # nesse meio-tempo) antes de se aproximar — senão o RN-15 mascararia este teste
    longe = [[make_perception(distance_m=1.5)]] * 10
    perto = [[make_perception(distance_m=0.5)]] * 2
    plans, _ = run(longe + perto)
    assert plans[2].speech is not None  # 1º anúncio, em Atenção
    assert plans[10].speech is not None  # se aproximou: novo anúncio, em Perto
    assert plans[10].speech.priority == 1  # P1 (arquitetura seção 6)


def test_rn14_nao_reanuncia_ao_se_afastar():
    perto = [[make_perception(distance_m=0.5)]] * 2  # confirma e anuncia em Perto
    atencao = [[make_perception(distance_m=1.5)]] * 2  # se afasta
    plans, _ = run(perto + atencao)
    assert plans[1].speech is not None  # 1º anúncio, em Perto
    assert plans[2].speech is None  # afastou — RN-14 não reanuncia (mesmo sem cooldown)
    assert plans[2].beep is not None  # o bipe ainda reflete a zona atual (Atenção)


def test_rn15_cooldown_bloqueia_voz_mas_nunca_o_bipe():
    # 3 frames confirmam e anunciam em Atenção; a aproximação seguinte cai no cooldown
    # (cooldown_voz_s = 1,5 s); frames continuam chegando (câmera não parou) até ele passar
    atencao = [[make_perception(distance_m=1.5)]] * 3
    perto = [[make_perception(distance_m=0.5)]] * 20
    plans, _ = run(atencao + perto, step=0.1)

    assert plans[2].speech is not None  # 1º anúncio (Atenção)
    assert plans[3].speech is None  # aproximou, mas o cooldown ainda não passou
    assert plans[3].beep is not None
    assert plans[3].beep.rate_hz == PARAMS["audio"]["bipe"]["ritmo_hz"]["perto"]  # bipe não espera

    # passado o cooldown, a mesma aproximação (ainda não anunciada) finalmente fala
    assert any(plan.speech is not None for plan in plans[4:])


# --- RN-20 modos ---------------------------------------------------------------


def test_modo_silencioso_so_alerta_na_zona_perto():
    atencao = make_perception(distance_m=1.5)
    plans, _ = run([[atencao]] * 5, mode=Mode.SILENCIOSO)
    assert all(plan.beep is None for plan in plans)

    perto = make_perception(distance_m=0.5)
    plans, _ = run([[perto]] * 3, mode=Mode.SILENCIOSO)
    assert plans[-1].beep is not None


def test_modo_caminhada_nao_anuncia_zona_longe():
    longe = make_perception(distance_m=5.0)
    plans, _ = run([[longe]] * 5, mode=Mode.CAMINHADA)
    assert all(plan.beep is None for plan in plans)


def test_modo_explorar_nunca_gera_alerta_automatico():
    p = make_perception(distance_m=0.3, truncated=True)  # o caso mais urgente possível
    plans, _ = run([[p]] * 5, mode=Mode.EXPLORAR)
    assert all(plan.beep is None and plan.speech is None for plan in plans)


# --- Robustez e pureza ---------------------------------------------------------


def test_percepcoes_vazias_nao_quebra():
    plan, state = decide([], CoreState(), Mode.CAMINHADA, 0.0, PARAMS, CLASSES)
    assert plan.beep is None
    assert plan.speech is None
    assert state.tracks == {}


def test_decide_e_puro_mesma_entrada_mesma_saida():
    p = make_perception()
    state = CoreState()
    plan_a, state_a = decide([p], state, Mode.CAMINHADA, 10.0, PARAMS, CLASSES)
    plan_b, state_b = decide([p], state, Mode.CAMINHADA, 10.0, PARAMS, CLASSES)
    assert plan_a == plan_b
    assert state_a == state_b


def test_decide_nao_muta_o_estado_recebido():
    """A casca pode reusar o `state` antigo em outro lugar — decide() nunca pode alterá-lo."""
    p = make_perception()
    original = CoreState()
    snapshot = replace(original)
    decide([p], original, Mode.CAMINHADA, 0.0, PARAMS, CLASSES)
    assert original == snapshot
