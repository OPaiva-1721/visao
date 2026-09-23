# Traces (contrato entre Python e Dart)

Sequências de percepções gravadas de vídeos reais, **sem imagem** (ADR-009). Servem de teste golden para o núcleo de decisão (ADR-001, ADR-002).

Para cada cena:

- `<cena>.jsonl` — uma linha por frame: `{"now": <s>, "mode": "...", "perceptions": [Perception, ...]}`
- `<cena>.expected.jsonl` — uma linha por frame com o `AlertPlan` que o núcleo Python produziu

Gerados por `lab/tools/record_trace.py` (Fase 1). O núcleo Dart (Fase 5) precisa reproduzir exatamente o `.expected.jsonl`.
