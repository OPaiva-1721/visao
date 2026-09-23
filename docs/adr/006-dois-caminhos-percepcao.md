# ADR-006 — Percepção semântica + geométrica

- **Status:** Aceito · 22/09/2026

## Contexto

Os obstáculos que mais machucam na altura da cabeça (galho, placa, orelhão) não existem no COCO. Treinar essas classes exige rotulagem, que o desenvolvedor prefere evitar.

## Decisão

Dois caminhos em paralelo:

1. **Semântico:** o YOLO diz *o que* é (pessoa, cadeira…).
2. **Geométrico:** o mapa de profundidade encontra qualquer aglomerado perto, no corredor, na faixa peito–cabeça, e emite "obstáculo" sem classe.

Se os dois coincidem, vale o nome do YOLO.

## Alternativas descartadas

- **Só YOLO:** a segurança dependeria de treinar todas as classes antes (Fase 4).

## Consequências

- A Fase 4 vira melhoria (dar nome), não pré-requisito de segurança.
- O caminho geométrico depende de a profundidade rodar (ADR-005, ADR-013).
