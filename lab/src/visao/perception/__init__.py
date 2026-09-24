"""Detector (YOLO26n + ByteTrack), profundidade, geometria e obstáculo genérico.

ADR-005, ADR-006, ADR-015. Fases 1–2.

- `types.py`     — `Detection` (caixa + track_id + classe; sem distância ainda)
- `detector.py`  — `parse_boxes` (pura) e `Detector` (Ultralytics, extra "visao")

Distância e altura reais (pinhole + profundidade) e o obstáculo genérico chegam na
Fase 2 — o que sai daqui ainda não é `Perception`, só `Detection`.
"""
