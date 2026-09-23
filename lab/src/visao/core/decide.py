"""Núcleo de decisão (ADR-002): `Perception[]` + estado → `AlertPlan`.

Cobre RN-08 a RN-16 e a exceção de segurança RN-33. Puro: nada de IO, câmera, áudio ou
relógio do sistema — o tempo entra como `now` (docs/arquitetura.md seção 5).

Ordem das etapas (arquitetura seção 5.1):
  1) descarta classe fora da lista (RN-16) e confiança baixa (RN-10)
  2) corredor em metros (RN-08)
  3) faixa de altura — chão/tronco/cabeça, ou descarta se a base está acima do teto (RN-09)
  4) zona pela distância; objeto cortado pela borda força Perto (RN-12, RN-33)
  5) persistência por track (RN-11) — todo candidato válido atualiza seu histórico,
     mesmo os que não vencerem nem forem anunciados
  6) elegibilidade por modo (RN-20) — Explorar não gera alerta automático aqui
  7) prioridade entre os confirmados elegíveis (RN-13) — só um "vence" por frame
  8) bipe do vencedor, contínuo (RN-17); voz só se ele ficou mais próximo do que da
     última vez que foi anunciado (RN-14) e o cooldown global permitir (RN-15) — o
     bipe **nunca** espera o cooldown, só a voz

Limitação conhecida (Fase 2): percepções de obstáculo genérico (`track_id=None`,
ADR-006) compartilham um único `TrackState`. Sem ID, não há como saber se duas
percepções sem track vistas no mesmo frame são o mesmo obstáculo ou dois diferentes.
Fase 1 não produz esse caso (só a Fase 2 introduz o caminho geométrico); resolver isso
com precisão fica para quando o detector genérico existir de verdade.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from visao.core.state import MAX_HISTORY, CoreState, TrackState
from visao.core.types import (
    AlertPlan,
    Band,
    BeepSpec,
    ClassInfo,
    Mode,
    Perception,
    Side,
    SpeechSpec,
    Zone,
)

_ZONE_RANK = {Zone.PERTO: 0, Zone.ATENCAO: 1, Zone.LONGE: 2}
_BAND_URGENCIA = {Band.CABECA: 1, Band.TRONCO: 1, Band.CHAO: 0}  # RN-13: cabeça/peito > chão


@dataclass(frozen=True)
class _Candidato:
    """Uma percepção já classificada (etapas 1–4) — ainda sem passar pela persistência."""

    perception: Perception
    zone: Zone
    band: Band


def _zone(distance_m: float, truncated: bool, zonas_m: dict) -> Zone:
    if truncated:  # RN-33: objeto cortado pela borda sempre conta como Perto
        return Zone.PERTO
    if distance_m < zonas_m["perto"]:
        return Zone.PERTO
    if distance_m < zonas_m["atencao"]:
        return Zone.ATENCAO
    return Zone.LONGE


def _band(top_m: float, bottom_m: float, faixas: dict) -> Band | None:
    """None = base acima do teto (RN-09): ela passa por baixo, a percepção é ignorada."""
    if bottom_m > faixas["teto"]:
        return None
    if top_m > faixas["tronco_ate"]:
        return Band.CABECA
    if top_m > faixas["chao_ate"]:
        return Band.TRONCO
    return Band.CHAO


def _side(lateral_m: float, lado_centro_m: float) -> Side:
    if abs(lateral_m) <= lado_centro_m:
        return "frente"
    return "esq" if lateral_m < 0 else "dir"  # types.py: lateral_m negativo é esquerda


def _classify(
    perceptions: list[Perception], params: dict, classes: dict[str, ClassInfo]
) -> list[_Candidato]:
    """Etapas 1 a 4: RN-08, RN-09, RN-10, RN-12, RN-16, RN-33. Sem estado nem modo ainda."""
    largura = params["corredor"]["largura_corpo_m"] / 2 + params["corredor"]["margem_m"]
    candidatos: list[_Candidato] = []
    for p in perceptions:
        info = classes.get(p.cls)
        if info is None:  # RN-16: classe fora da lista de mobilidade
            continue
        limiar = info.conf_min if info.conf_min is not None else params["confianca_padrao"]
        if p.conf < limiar:  # RN-10
            continue
        if abs(p.lateral_m) > largura:  # RN-08
            continue
        band = _band(p.top_m, p.bottom_m, params["faixas_altura_m"])
        if band is None:  # RN-09
            continue
        zone = _zone(p.distance_m, p.truncated, params["zonas_m"])
        candidatos.append(_Candidato(perception=p, zone=zone, band=band))
    return candidatos


def _update_tracks(
    candidatos: list[_Candidato],
    tracks: dict[int | None, TrackState],
    now: float,
    ttl_s: float,
) -> dict[int | None, TrackState]:
    """Etapa 5 (RN-11): atualiza o histórico de todo candidato válido e esquece quem não
    aparece há mais de `ttl_s` (arquitetura 5.2: Confirmado/Candidato → Perdido)."""
    seen_ids = {c.perception.track_id for c in candidatos}
    kept = {tid: ts for tid, ts in tracks.items() if now - ts.last_seen <= ttl_s}
    updated: dict[int | None, TrackState] = {}
    for tid in set(kept) | seen_ids:
        old = kept.get(tid, TrackState())
        seen = tid in seen_ids
        history = (old.presence_history + (seen,))[-MAX_HISTORY:]
        updated[tid] = replace(
            old, presence_history=history, last_seen=now if seen else old.last_seen
        )
    return updated


def _is_confirmed(
    candidato: _Candidato, tracks: dict[int | None, TrackState], params: dict
) -> bool:
    """RN-11: N de M frames — a zona Perto exige menos confirmações (reage mais rápido)."""
    limiar = params["persistencia"]["perto" if candidato.zone == Zone.PERTO else "padrao"]
    historico = tracks[candidato.perception.track_id].presence_history
    return sum(historico[-limiar["m"] :]) >= limiar["n"]


def _elegivel_no_modo(zone: Zone, mode: Mode) -> bool:
    """Etapa 6 (RN-20). Em Explorar, `decide()` já retorna antes de chegar aqui."""
    if mode == Mode.SILENCIOSO:
        return zone == Zone.PERTO
    return zone != Zone.LONGE  # Mode.CAMINHADA — RN-12: Longe não é anunciado


def _prioridade(
    candidato: _Candidato, classes: dict[str, ClassInfo]
) -> tuple[int, int, float, int]:
    """RN-13, em ordem: zona mais próxima · cabeça/peito antes de chão · mais central ·
    mais perigoso."""
    return (
        _ZONE_RANK[candidato.zone],
        -_BAND_URGENCIA[candidato.band],
        abs(candidato.perception.lateral_m),
        -classes[candidato.perception.cls].perigo,
    )


def decide(
    perceptions: list[Perception],
    state: CoreState,
    mode: Mode,
    now: float,
    params: dict,
    classes: dict[str, ClassInfo],
) -> tuple[AlertPlan, CoreState]:
    """Uma chamada por frame processado. `now` é o tempo da decisão, nunca lido daqui."""
    candidatos = _classify(perceptions, params, classes)
    tracks = _update_tracks(candidatos, state.tracks, now, params["tracking"]["ttl_s"])

    if mode == Mode.EXPLORAR:
        # RN-20: descreve sob pedido, não reflexivamente. A persistência continua sendo
        # calculada (a câmera não para de ver); só não gera bipe/voz automático aqui.
        return AlertPlan(beep=None, speech=None, t_capture=now), replace(state, tracks=tracks)

    confirmados = [c for c in candidatos if _is_confirmed(c, tracks, params)]
    elegiveis = [c for c in confirmados if _elegivel_no_modo(c.zone, mode)]
    if not elegiveis:
        return AlertPlan(beep=None, speech=None, t_capture=now), replace(state, tracks=tracks)

    vencedor = min(elegiveis, key=lambda c: _prioridade(c, classes))
    track_id = vencedor.perception.track_id
    beep = BeepSpec(
        rate_hz=params["audio"]["bipe"]["ritmo_hz"][vencedor.zone.value],
        band=vencedor.band,
        side=_side(vencedor.perception.lateral_m, params["audio"]["lado_centro_m"]),
    )

    ultima_anunciada = tracks[track_id].last_announced_zone
    aproximou = ultima_anunciada is None or _ZONE_RANK[vencedor.zone] < _ZONE_RANK[ultima_anunciada]
    em_cooldown = now - state.last_voice_time < params["cooldown_voz_s"]

    speech = None
    last_voice_time = state.last_voice_time
    if aproximou and not em_cooldown:  # RN-14 e RN-15 — o bipe acima não espera nenhum dos dois
        prioridade_fala = 1 if vencedor.zone == Zone.PERTO else 3  # arquitetura seção 6, P1/P3
        speech = SpeechSpec(
            clip_keys=(classes[vencedor.perception.cls].fala,), priority=prioridade_fala
        )
        tracks = {**tracks, track_id: replace(tracks[track_id], last_announced_zone=vencedor.zone)}
        last_voice_time = now

    plan = AlertPlan(beep=beep, speech=speech, t_capture=vencedor.perception.t_capture)
    return plan, CoreState(tracks=tracks, last_voice_time=last_voice_time)
