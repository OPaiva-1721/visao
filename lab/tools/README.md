# Ferramentas do laboratório

Scripts de linha de comando. Cada um nasce na fase indicada (docs/arquitetura.md, seção 14).

| Script | Faz | Fase |
| --- | --- | --- |
| `audio_test.py` | Toca bipes e falas num fone só, com as opções A e B de direção, para testar com ela | 0.5 |
| `gen_audio.py` | Gera os clipes `.wav` de `shared/audio/vocabulario.yaml` com o Piper | 0.5 |
| `calibrate_camera.py` | Mede foco, centro óptico e campo de visão da câmera | 1 |
| `record_session.py` | Grava vídeo em modo explícito (RN-29) para `data/` | 1 |
| `label_events.py` | Marca intervalos de obstáculo nos vídeos com o teclado (ADR-007) | 1 |
| `record_trace.py` | Roda o pipeline num vídeo e grava o trace de percepções | 1 |
| `eval.py` | Métricas da RN-30: recall Perto, falsos alarmes/min, latência, fps | 1 |
| `bench.py` | Spikes S1/S1b/S2: fps de YOLO e profundidade por perfil | 1 |
