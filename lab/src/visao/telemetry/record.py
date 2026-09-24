"""Monta o registro de um tick — puro. Só metadados, nunca a imagem (RN-28, ADR-009):
a função nem recebe o `Frame`, só o que já saiu do núcleo e do supervisor.

Limitação conhecida: quando não há fala nova (RN-14 mantém a mesma zona), o registro
não sabe qual classe está sendo sinalizada pelo bipe — só o `AlertPlan` não guarda a
classe do vencedor. `eval.py` (RN-30, ainda não construído) pode precisar de mais
detalhe do que isso; se precisar, o jeito é `decide()` expor esse detalhe também, não
adivinhar aqui.
"""

from __future__ import annotations

from typing import Any

from visao.core.types import AlertPlan, Mode
from visao.supervisor.types import SupervisorReport


def build_record(
    *,
    now: float,
    mode: Mode,
    plan: AlertPlan,
    supervisor: SupervisorReport | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "t": now,
        "modo": mode.value,
        "latencia_ms": (now - plan.t_capture) * 1000,
        "bipe": None,
        "fala": None,
    }
    if plan.beep is not None:
        record["bipe"] = {
            "rate_hz": plan.beep.rate_hz,
            "banda": plan.beep.band.value,
            "lado": plan.beep.side,
        }
    if plan.speech is not None:
        record["fala"] = {
            "clip_keys": list(plan.speech.clip_keys),
            "prioridade": plan.speech.priority,
        }
    if supervisor is not None:
        record["estado"] = supervisor.state.value
        record["falha"] = supervisor.fault.value if supervisor.fault is not None else None
        record["pouca_luz"] = supervisor.pouca_luz
    return record
