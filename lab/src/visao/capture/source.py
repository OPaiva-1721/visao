"""Interface comum a qualquer fonte de frames, e uma fonte falsa para testar sem câmera."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from visao.capture.frame import Frame
from visao.capture.slot import LatestFrameSlot


@runtime_checkable
class FrameSource(Protocol):
    """O que webcam, DroidCam e arquivo de vídeo (Fase 1, ainda não construídas — dependem
    da extra "visao" e de uma câmera real para validar) vão implementar."""

    def start(self) -> None:
        """Liga a captura: abre a câmera, começa a thread que escreve no LatestFrameSlot."""

    def stop(self) -> None:
        """Desliga a captura e libera a câmera."""

    def latest(self) -> Frame | None:
        """O frame mais recente (ADR-004), ou None se nada foi capturado ainda."""


class FakeFrameSource:
    """Fonte de frames de mentira, para testar o resto do pipeline sem câmera nenhuma.

    Implementa o mesmo `FrameSource` que as fontes reais vão implementar — o teste chama
    `push()` para simular a câmera "vendo" um frame novo.
    """

    def __init__(self) -> None:
        self._slot = LatestFrameSlot()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def latest(self) -> Frame | None:
        return self._slot.get()

    def push(self, frame: Frame) -> None:
        self._slot.put(frame)
