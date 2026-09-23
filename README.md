# visao — detecção de obstáculos para acessibilidade

Protótipo que ajuda uma pessoa cega a **não esbarrar em obstáculos na altura da cabeça e do peito, e em pessoas** — o ponto cego da bengala. Uma câmera (celular preso ao peito) detecta o que está no caminho e avisa por **bipes** que indicam distância e altura, com uma fala curta dizendo o que é e de que lado.

> **Aviso:** é um protótipo de estudo, **não** um dispositivo certificado, e **não substitui a bengala**. Ausência de alerta não significa caminho livre.

## Status

Planejamento concluído (22–23/09/2026). **Fase 0.5 concluída** (23/09): design de áudio aprovado com a usuária — bipe + voz, direção pelo timbre do bipe (opção B). Próxima etapa: **Fase 1** — protótipo de bancada.

Ordem de execução: 0.5 → 1 → 2 → 3a → 5 → 3b → 4 ([ADR-012](docs/adr/012-teste-campo-duas-etapas.md)).

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [docs/plano.md](docs/plano.md) | Requisitos, regras de negócio (RN-01…36), fases, riscos, marcos |
| [docs/arquitetura.md](docs/arquitetura.md) | Componentes, latência, perfis de máquina, app Flutter, spikes |
| [docs/adr/](docs/adr/README.md) | Decisões de arquitetura, uma por arquivo |
| [docs/referencias.md](docs/referencias.md) | Modelos, datasets e projetos relacionados (Hugging Face, GitHub) |
| [docs/testes-campo/](docs/testes-campo/README.md) | Relatórios das sessões de teste com a usuária |

## Estrutura

```text
docs/       planejamento, arquitetura, ADRs, relatórios de campo
shared/     config, vocabulário de áudio e traces — fonte única para Python e Dart
lab/        laboratório Python (Fases 0.5–4)
training/   fine-tuning do YOLO (Fase 4)
mobile/     app Flutter (Fase 5)
data/       vídeos e datasets locais — fora do git
```

## Rodando o laboratório

Requer [uv](https://docs.astral.sh/uv/).

```bash
cd lab
uv sync                  # núcleo + testes
uv run pytest
uv run ruff check .
```

Extras por fase: `uv sync --extra audio` (Fase 0.5), `--extra visao` (Fase 1), `--extra openvino` (notebook Intel).

## Privacidade

Nenhuma imagem é gravada durante o uso normal. Vídeos de teste só são gravados em modo explícito, com consentimento, sem terceiros identificáveis, e nunca entram no repositório ([ADR-009](docs/adr/009-sem-imagens-persistidas.md)).

## Licença

[AGPL-3.0](LICENSE), por usar o [Ultralytics YOLO](https://github.com/ultralytics/ultralytics).
