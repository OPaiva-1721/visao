# ADR-003 — Parâmetros em YAML compartilhado

- **Status:** Aceito · 22/09/2026

## Contexto

As RNs têm dezenas de valores iniciais (entre colchetes no plano) que só serão acertados nos testes com ela.

## Decisão

Todos esses valores ficam em `shared/config/params.yaml`; nomes de classe, perigo e alturas típicas em `shared/config/classes.yaml`. Python e Dart leem os mesmos arquivos.

## Alternativas descartadas

- **Constantes no código:** calibrar exigiria mexer em código e manter duas cópias (Python e Dart).

## Consequências

- Calibrar = editar YAML e rodar `eval.py`.
- Mudança de parâmetro aparece no histórico do git com o motivo.
