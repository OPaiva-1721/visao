"""Núcleo de decisão puro (ADR-002): percepções → AlertPlan. Sem IO, sem relógio do sistema.

- `types.py`  — os tipos trocados com o resto do sistema (Perception, AlertPlan, ClassInfo...)
- `state.py`  — o estado guardado entre chamadas (CoreState, TrackState)
- `decide.py` — a função `decide()`, RN-08 a RN-16 e RN-33
"""
