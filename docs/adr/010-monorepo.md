# ADR-010 — Monorepo com `shared/`

- **Status:** Aceito · 22/09/2026

## Contexto

Python e Flutter precisam da mesma config, dos mesmos áudios e dos mesmos traces.

## Decisão

Um repositório só: `docs/`, `shared/`, `lab/` (Python), `training/`, `mobile/` (Flutter), `data/` (fora do git).

## Alternativas descartadas

- **Repos separados:** config e traces duplicados e fora de sincronia.

## Consequências

- O CI roda os testes das duas linguagens sobre os mesmos arquivos de `shared/`.
