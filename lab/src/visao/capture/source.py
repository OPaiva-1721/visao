"""Interface comum a qualquer fonte de frames, a câmera real e uma fonte falsa para
testar sem câmera."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from visao.capture.frame import Frame
from visao.capture.slot import LatestFrameSlot


@runtime_checkable
class FrameSource(Protocol):
    """O que `CameraFrameSource` (webcam/DroidCam) e arquivo de vídeo (ainda não
    construído — ferramentas de avaliação) implementam."""

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


def _abrir_camera_cv2(device: int | str) -> Any:
    try:
        import cv2  # pyright: ignore[reportMissingImports] — extra "visao" opcional

        return cv2.VideoCapture(device)
    except ImportError as e:
        raise RuntimeError("opencv-python não instalado. Rode: uv sync --extra visao.") from e


class CameraFrameSource:
    """Câmera real — webcam ou DroidCam (ADR-011) — via OpenCV `VideoCapture`.

    Uma thread própria lê da câmera continuamente e só escreve no `LatestFrameSlot`
    (ADR-004): nunca enfileira, e se a percepção estiver mais lenta, frames somem de
    propósito. `t_capture` é `time.monotonic()` no instante da leitura (mais fiel ao
    "agora" do que qualquer timestamp do driver).

    `abrir_camera` injeta a abertura da câmera — nos testes, uma câmera falsa sem cv2
    nem hardware (mesmo padrão de `AudioPlayer`/`FakePlayer` em audio/player.py).
    """

    def __init__(
        self,
        device: int | str = 0,
        *,
        abrir_camera: Callable[[int | str], Any] = _abrir_camera_cv2,
    ) -> None:
        self._device = device
        self._abrir_camera = abrir_camera
        self._slot = LatestFrameSlot()
        self._cap: Any = None
        self._encerrar = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._cap = self._abrir_camera(self._device)
        if not self._cap.isOpened():
            raise RuntimeError(f"não abriu a câmera (dispositivo={self._device!r})")
        self._encerrar.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._encerrar.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def latest(self) -> Frame | None:
        return self._slot.get()

    def _loop(self) -> None:
        assert self._cap is not None
        while not self._encerrar.is_set():
            ok, image = self._cap.read()
            t_capture = time.monotonic()
            if not ok:
                time.sleep(0.01)
                continue
            self._slot.put(Frame(image=image, t_capture=t_capture))
