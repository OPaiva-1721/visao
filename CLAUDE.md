# visao — instruções para o Claude

Protótipo que avisa, por som, obstáculos na altura da cabeça/peito e pessoas para uma pessoa cega (irmã do Gabryel). É segurança física de uma pessoa real **e** peça de portfólio. Repositório público: https://github.com/OPaiva-1721/visao

## Onde está cada coisa

| Arquivo | Para quê |
| --- | --- |
| `docs/plano.md` | Requisitos, respostas da usuária (seção 1.1), **regras de negócio RN-01…36**, fases, riscos |
| `docs/arquitetura.md` | Componentes, latência, perfis, app Flutter, spikes S1–S6, pendências |
| `docs/adr/` | Uma decisão por arquivo + índice |
| `docs/referencias.md` | Modelos, datasets e projetos aproveitáveis (com licença) |
| `docs/testes-campo/` | Relatório de cada sessão de teste com ela |
| `shared/config/` | `params.yaml` (todos os valores das RNs), `perfis/`, `classes.yaml` |
| `shared/audio/vocabulario.yaml` | Tudo o que o sistema fala |
| `lab/` | Python (Fases 0.5–4) |

Leia a parte relevante do plano e da arquitetura antes de implementar uma fase. Não invente requisito que já está lá.

**Ordem de execução:** 0.5 → 1 → 2 → 3a → 5 → 3b → 4 (ADR-012). Status atual no topo de `docs/plano.md`.

## Regras do projeto

- **Parâmetros nunca no código.** Todo limiar, tempo ou distância das RNs vem de `shared/config/params.yaml` (ADR-003). Perfil de máquina sobrepõe a base (ADR-013).
- **`core/` é puro** (ADR-002): sem IO, sem câmera, sem áudio, sem `time.time()`. O tempo entra como parâmetro `now`.
- **Último frame vence** (ADR-004): nunca enfileirar frames.
- **Sem imagens gravadas** fora do modo explícito de gravação; vídeos e pesos só em `data/`, fora do git (ADR-009).
- **Classe nova** → entrada em `classes.yaml` + clipe em `vocabulario.yaml` (o teste falha se faltar).
- **Na dúvida, alerta.** O sistema nunca diz "caminho livre" (RN-02). Silêncio nunca pode ser ambíguo: falha tem som próprio (RN-04).
- Mudança em `core/`, nas RNs de segurança (3.1 e 3.6 do plano) ou em limiar de alerta: explique o impacto na segurança dela e peça confirmação antes.
- Decisão de arquitetura nova → ADR novo em `docs/adr/`, índice atualizado e linha na seção 12 da arquitetura.

## Fatos da usuária que afetam o código

Cegueira total · 1,55 m, ombro 1,25 m · só bengala · **fone com fio em um ouvido só** (áudio mono; direção por voz ou timbre, nunca estéreo) · **não entende posição de relógio** (falar "esquerda / frente / direita") · usa TalkBack · Redmi 13C 4G (Helio G85, fraco) · sessões de no máximo 30 min.

## Máquinas (perfis)

| Perfil | Máquina | Runtime |
| --- | --- | --- |
| `pc` | PC de mesa Ryzen 5 5600GT, sem GPU dedicada | ONNX Runtime (+ DirectML) |
| `notebook` | i3 7ª geração (teste de campo 3a) | OpenVINO, sem profundidade |
| `celular` | Redmi 13C | LiteRT (Flutter) |

Windows: use o Bash (Git Bash) ou o PowerShell conforme o comando.

## Comandos

```bash
cd lab
uv sync                        # base + dev; extras: --extra audio | visao | openvino
uv run pytest
uv run ruff check .
uv run ruff format .
uv run pyright
```

## Como trabalhar com o Gabryel

- Docs, comentários e mensagens em **português**. Identificadores dos tipos em inglês (como em `core/types.py`); chaves de config em português (como em `params.yaml`).
- Precisa perguntar algo? **Uma pergunta por mensagem.**
- **Sempre atualize os docs** no mesmo turno em que algo muda (resposta dele, resultado de spike, decisão).
- Antes de commitar: `pytest`, `ruff check` e `ruff format --check` passando. Mensagens no estilo Conventional Commits, em português.
- **Nunca** adicionar `Co-Authored-By` nem "Generated with Claude Code" em commits ou PRs.
- Commit e push só quando ele pedir.
