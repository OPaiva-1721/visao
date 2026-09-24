"""FrameSource: webcam, arquivo de vídeo, DroidCam. Último frame vence (ADR-004). Fase 1.

- `frame.py`  — o tipo `Frame` (imagem + instante da captura)
- `slot.py`   — `LatestFrameSlot`: o slot de um frame só, testado e pronto
- `source.py` — o `FrameSource` (Protocol) e `FakeFrameSource`, para testar sem câmera

Fontes reais (webcam/DroidCam via OpenCV) ficam para quando houver câmera para validar —
dependem da extra "visao" (`ultralytics`, `onnxruntime`, `opencv-python`).
"""
