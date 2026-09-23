# data/ (fora do git)

Vídeos de teste, rótulos de eventos, datasets e pesos de modelo ficam aqui, **só na máquina local** (ADR-009, RN-29).

Sugestão de organização:

```text
data/
├── videos/       gravados com tools/record_session.py
├── eventos/      rótulos de tools/label_events.py (um JSON por vídeo)
├── modelos/      pesos exportados (.onnx, OpenVINO, .tflite)
└── datasets/     Fase 4
```

Faça backup fora do repositório (ex.: um drive privado). Publicar qualquer trecho exige OK dela para aquele vídeo.
