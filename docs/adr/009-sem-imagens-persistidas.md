# ADR-009 — Nenhuma imagem persistida em runtime

- **Status:** Aceito · 22/09/2026

## Contexto

A câmera filma terceiros na rua (LGPD) e o repositório é público.

## Decisão

- Em uso normal, nenhuma imagem é gravada. A telemetria guarda só metadados (classe, zona, horário, latência).
- Gravação de vídeo só em modo explícito, sem terceiros identificáveis, com consentimento dela (RN-29). Os vídeos ficam em `data/`, fora do git.
- Os testes automatizados usam traces de metadados.

## Alternativas descartadas

- **Gravar sempre:** facilitaria a depuração, mas viola privacidade.

## Consequências

- Publicar qualquer trecho de vídeo exige OK dela para aquele vídeo.
