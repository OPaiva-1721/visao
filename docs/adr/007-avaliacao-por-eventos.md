# ADR-007 — Avaliação por eventos, não por caixas

- **Status:** Aceito · 22/09/2026

## Contexto

É preciso medir recall e falsos alarmes (RN-30) a cada versão, sem gastar horas desenhando caixas.

## Decisão

Cada vídeo de avaliação tem um JSON de **intervalos** (`t_start`, `t_end`, zona, faixa, lado), marcados com teclas em `tools/label_events.py`. As métricas são por evento: houve bipe Perto até 300 ms depois do início?

## Alternativas descartadas

- **Caixas por frame:** preciso para treino, caro demais para avaliação contínua.

## Consequências

- ~2 min de rotulagem por vídeo.
- Mede o que importa para ela (alertou a tempo?), não a precisão do detector.
