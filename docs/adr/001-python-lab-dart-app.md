# ADR-001 — Python como laboratório, app em Dart, traces como contrato

- **Status:** Aceito · 22/09/2026

## Contexto

O ML (YOLO, profundidade, avaliação) é muito mais rápido de experimentar em Python. O produto final roda no celular dela (Android), e o desenvolvedor tem afinidade com Flutter. Reescrever a lógica em outra linguagem costuma introduzir diferenças sutis de comportamento.

## Decisão

- `lab/` em Python é o laboratório e a implementação de referência (Fases 0.5–4).
- O app (Fase 5) é Flutter/Dart, com o núcleo de decisão portado.
- **Traces** (sequências de `Perception` em JSONL, sem imagem) + os `AlertPlan` esperados são o contrato: o núcleo Dart precisa produzir exatamente as mesmas saídas.

## Alternativas descartadas

- **Só Python num Raspberry Pi:** exige hardware (R$ 0 hoje) e fica volumoso. Continua como plano B.
- **Dart desde o início:** ecossistema de ML fraco para experimentar; atrasaria as Fases 1–2.

## Consequências

- O núcleo precisa ser pequeno e puro (ADR-002) para o port ser barato.
- `shared/traces/` passa a ser artefato versionado e testado no CI dos dois lados.
