"""O slot de um frame só (ADR-004): a captura escreve, a percepção lê. Nunca enfileira."""

from __future__ import annotations

import threading

from visao.capture.frame import Frame


class LatestFrameSlot:
    """Thread-safe: a captura chama `put()` de uma thread, a percepção chama `get()` de
    outra (arquitetura seção 8 — threads "Captura" e "Principal").

    `put()` sempre sobrescreve o que houver. Se a percepção estiver mais lenta que a
    câmera, frames intermediários somem — de propósito (ADR-004: latência importa mais
    que processar todo frame; aqui, atraso pode significar uma batida).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._frame: Frame | None = None

    def put(self, frame: Frame) -> None:
        with self._lock:
            self._frame = frame

    def get(self) -> Frame | None:
        """O frame mais recente, ou None se nenhum chegou ainda.

        Chamadas repetidas sem um `put()` novo pelo meio devolvem o mesmo frame — a
        percepção pode processá-lo de novo em vez de travar esperando um frame novo.
        """
        with self._lock:
            return self._frame

    def take_if_new(self, last_t_capture: float | None) -> Frame | None:
        """Como `get()`, mas devolve None se o frame mais recente já tem o mesmo
        `t_capture` que `last_t_capture` — para quem quer processar cada frame só uma vez.
        """
        with self._lock:
            frame = self._frame
        if frame is None or (last_t_capture is not None and frame.t_capture == last_t_capture):
            return None
        return frame
