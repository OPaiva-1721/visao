# ADR-002 — Núcleo de decisão puro e determinístico

- **Status:** Aceito · 22/09/2026

## Contexto

As regras RN-08 a RN-16 (corredor, faixas, zonas, persistência, prioridade, anti-repetição, modos) são o coração do comportamento e precisam ser calibradas, testadas e portadas.

## Decisão

`core.decide(perceptions, state, mode, now, params) -> (AlertPlan, state)` é uma função pura: sem câmera, áudio, relógio do sistema, aleatoriedade ou IO. O tempo entra como parâmetro.

## Alternativas descartadas

- **Lógica dentro do loop principal:** difícil de testar, impossível de reproduzir uma cena exatamente.

## Consequências

- Qualquer cena gravada vira teste determinístico.
- A casca (captura, inferência, áudio) fica fina e específica de cada plataforma.
