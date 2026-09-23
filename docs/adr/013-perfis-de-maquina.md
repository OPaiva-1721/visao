# ADR-013 — Perfis de máquina sobre a config base

- **Status:** Aceito · 22/09/2026

## Contexto

O mesmo sistema roda em três máquinas com capacidades muito diferentes: PC Ryzen, notebook i3 e Redmi 13C (Helio G85).

## Decisão

`shared/config/perfis/{pc,notebook,celular}.yaml` sobrepõem `params.yaml`: runtime de inferência, resolução de entrada, profundidade ligada/desligada e taxa. Com a profundidade desligada pelo perfil, o supervisor não trata isso como falha.

## Alternativas descartadas

- **Branches ou flags soltas no código:** código divergente por máquina.

## Consequências

- Trocar de máquina = trocar de perfil.
- As métricas de cada versão são registradas por perfil.
