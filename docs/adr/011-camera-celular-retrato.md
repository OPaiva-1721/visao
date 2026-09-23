# ADR-011 — Câmera = celular em retrato no peito

- **Status:** Aceito · 22/09/2026

## Contexto

Câmera no peito a ~1,12 m (ela tem 1,55 m). Para ver a faixa da cabeça (até 1,70 m) e uma mesa (0,75 m) a 1 m de distância, são necessários ~50° de campo vertical.

## Decisão

Desde a Fase 1, a câmera é um **Redmi 13C em retrato** preso no peito, inclinado ~10° para cima, ligado ao PC pela DroidCam. Há dois aparelhos iguais: um de desenvolvimento, outro dela.

## Alternativas descartadas

- **Webcam do notebook:** ~40–45° de campo vertical; nivelada, perde o obstáculo de cabeça a 1 m.

## Consequências

- A calibração e os vídeos de avaliação já saem do modelo de câmera final.
- Outras posições (uso diário discreto) são só configuração (`camera.altura_m`, `camera.inclinacao_graus`).
