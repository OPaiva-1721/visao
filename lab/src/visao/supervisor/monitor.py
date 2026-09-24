"""`tick()`: as checagens da arquitetura seção 7, RN-04, RN-27 e RN-34. Puro — sem IO,
sem relógio do sistema (ADR-002); quem chama já mediu tudo e passa `now`.

Prioridade quando há mais de um problema ao mesmo tempo: exceção e câmera parada
importam mais que fps baixo; qualquer um dos três é Falha (P0, RN-04). Profundidade
velha é só Degradado — mais leve, o sistema continua com o caminho semântico.
"""

from __future__ import annotations

from visao.supervisor.types import (
    FaultKind,
    SupervisorInputs,
    SupervisorReport,
    SupervisorState,
    SystemState,
)


def tick(
    inputs: SupervisorInputs, state: SupervisorState, now: float, params: dict
) -> tuple[SupervisorReport, SupervisorState]:
    cfg = params["supervisor"]

    fault = _check_fault(inputs, cfg, now)

    fps_baixo_desde = _timer(
        ativo=inputs.fps_recente is not None and inputs.fps_recente < cfg["fps_minimo"],
        desde=state.fps_baixo_desde,
        now=now,
    )
    luz_baixa_desde = _timer(
        ativo=inputs.brilho_medio is not None and inputs.brilho_medio < cfg["luz_brilho_minimo"],
        desde=state.luz_baixa_desde,
        now=now,
    )
    novo_state = SupervisorState(fps_baixo_desde=fps_baixo_desde, luz_baixa_desde=luz_baixa_desde)

    if (
        fault is None
        and fps_baixo_desde is not None
        and now - fps_baixo_desde >= cfg["janela_fps_s"]
    ):
        fault = FaultKind.LENTO

    if fault is not None:
        return SupervisorReport(state=SystemState.FALHA, fault=fault, pouca_luz=False), novo_state

    degradado = _profundidade_degradada(inputs, params, now)
    pouca_luz = luz_baixa_desde is not None and now - luz_baixa_desde >= cfg["luz_janela_s"]
    report = SupervisorReport(
        state=SystemState.DEGRADADO if degradado else SystemState.RODANDO,
        fault=None,
        pouca_luz=pouca_luz,
    )
    return report, novo_state


def _check_fault(inputs: SupervisorInputs, cfg: dict, now: float) -> FaultKind | None:
    if inputs.excecao:  # RN-04: mais severo, checa primeiro
        return FaultKind.ERRO
    if inputs.last_frame_t is None or now - inputs.last_frame_t > cfg["captura_timeout_ms"] / 1000:
        return FaultKind.CAMERA
    return None


def _profundidade_degradada(inputs: SupervisorInputs, params: dict, now: float) -> bool:
    """RN-34. Perfil sem profundidade (`profundidade_esperada=False`) não é falha —
    é o perfil (ex.: notebook), não um defeito (arquitetura seção 4.1)."""
    if not inputs.profundidade_esperada:
        return False
    if inputs.profundidade_last_update is None:  # esperada, mas nunca chegou nenhuma
        return True
    max_idade_s = params["profundidade"]["max_idade_falha_ms"] / 1000
    return now - inputs.profundidade_last_update > max_idade_s


def _timer(*, ativo: bool, desde: float | None, now: float) -> float | None:
    """Marca (ou mantém) o instante em que uma condição passou a ser verdadeira; None
    enquanto ela não estiver ativa."""
    if not ativo:
        return None
    return desde if desde is not None else now
