# ADR-004 — Captura "último frame vence"

- **Status:** Aceito · 22/09/2026

## Contexto

A RN-03 limita a latência captura → som a 300 ms. Se a inferência for mais lenta que a câmera, uma fila acumula atraso sem limite.

## Decisão

A captura mantém um único slot com o frame mais recente. A inferência sempre pega o mais novo; frames intermediários são descartados.

## Alternativas descartadas

- **Fila de frames:** processa tudo, mas com atraso crescente. Aqui atraso = batida.

## Consequências

- O fps efetivo cai em máquina lenta, mas a informação nunca fica velha.
- O tracking precisa tolerar saltos entre frames (o ByteTrack tolera).
