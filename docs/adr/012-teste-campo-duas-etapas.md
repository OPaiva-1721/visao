# ADR-012 — Teste de campo em duas etapas

- **Status:** Aceito · 22/09/2026

## Contexto

A máquina forte (Ryzen 5 5600GT) é PC de mesa. O único portátil é um notebook i3 de 7ª geração, que roda o YOLO mas não a profundidade.

## Decisão

- **3a:** notebook na mochila, celular por USB, fone com fio em um ouvido. Perfil `notebook` (sem profundidade). Testa pessoas e objetos do COCO.
- Depois, o **app de celular** (Fase 5).
- **3b:** sistema completo no celular, incluindo obstáculo na altura da cabeça.

Ordem de execução: 0.5 → 1 → 2 → 3a → 5 → 3b → 4.

## Alternativas descartadas

- **PC de mesa via Wi-Fi + fone Bluetooth:** estoura a RN-03 (300 ms) e limita o alcance.
- **Adiantar o app antes de qualquer teste:** atrasaria o feedback dela em 1–2 meses.

## Consequências

- O primeiro teste não cobre o obstáculo genérico de cabeça; isso é dito a ela antes.
