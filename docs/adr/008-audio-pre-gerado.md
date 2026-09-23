# ADR-008 — Voz pré-gerada com Piper; bipes sintetizados

- **Status:** Aceito · 22/09/2026

## Contexto

Tudo precisa funcionar offline (RN-25), com latência mínima, igual no Python e no celular. O vocabulário é pequeno e fixo.

## Decisão

- `tools/gen_audio.py` gera um `.wav` por palavra com **Piper** (voz pt-BR) em `shared/audio/`.
- Em runtime só se tocam arquivos. Os bipes são sintetizados em tempo real.
- Saída **mono** por padrão: ela usa fone em um ouvido só.

## Alternativas descartadas

- **TTS em runtime (pyttsx3, gTTS):** o gTTS precisa de internet; o pyttsx3 depende da voz instalada no Windows; ambos adicionam latência.

## Consequências

- Palavra nova = rodar o gerador de novo.
- Os mesmos arquivos servem para o app Flutter.
