"""Bipes sintetizados, clipes pré-gerados e prioridade/preempção (ADR-008, RN-06). Fase 0.5.

- `synth.py`  — geração das formas de onda (puro, testável)
- `player.py` — reprodução via sounddevice e leitura de .wav (IO)
- `vocab.py`  — ponte entre os tipos do núcleo e o vocabulário falado

A fila de prioridade/preempção (RN-06, tabela P0–P4 da arquitetura) chega na Fase 1,
junto com o AudioEngine que consome AlertPlan.
"""
