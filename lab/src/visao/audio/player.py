"""Reprodução de áudio (IO). Sem lógica de negócio — isso fica em `synth.py`.

`sounddevice` é importado sob demanda, só dentro de `Player.play`, para que o resto do
módulo (em especial `load_wav`) funcione e seja testável sem o extra "audio" instalado
nem hardware de som (CI, por exemplo).
"""

from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np


def load_wav(path: Path) -> tuple[np.ndarray, int]:
    """Lê um .wav PCM 16-bit e devolve (amostras em float32 em [-1, 1], sample_rate).

    Áudio com mais de um canal é mixado para mono (ela usa fone em um ouvido só, U7).
    """
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        n_channels = wav_file.getnchannels()
        raw = wav_file.readframes(wav_file.getnframes())
    if sample_width != 2:
        raise ValueError(f"{path}: só suporta PCM 16-bit (sampwidth={sample_width})")
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)
    return samples, sample_rate


def _import_sounddevice():
    try:
        import sounddevice as sd  # pyright: ignore[reportMissingImports] — extra "audio" opcional
    except ImportError as e:
        raise RuntimeError(
            "sounddevice não instalado. Rode: uv sync --extra audio (ADR-008)."
        ) from e
    return sd


@runtime_checkable
class AudioPlayer(Protocol):
    """O que `AudioEngine` precisa — permite injetar um falso nos testes (sem
    hardware), do mesmo jeito que `FrameSource`/`FakeFrameSource` em capture/."""

    def play(self, samples: np.ndarray, sample_rate: int, *, wait: bool = True) -> None: ...
    def play_wav(self, path: Path, *, wait: bool = True) -> None: ...
    def play_sequence(self, clips: list[tuple[np.ndarray, int]], *, gap_s: float = 0.2) -> None: ...
    def stop(self) -> None: ...


@dataclass
class Player:
    """Toca waveforms numpy e clipes .wav. Saída mono por padrão (params.audio.saida)."""

    device: int | str | None = None

    def play(self, samples: np.ndarray, sample_rate: int, *, wait: bool = True) -> None:
        sd = _import_sounddevice()
        sd.play(samples, sample_rate, device=self.device)
        if wait:
            sd.wait()

    def play_wav(self, path: Path, *, wait: bool = True) -> None:
        samples, sample_rate = load_wav(path)
        self.play(samples, sample_rate, wait=wait)

    def stop(self) -> None:
        """Interrompe o que estiver tocando agora — usado para trocar de fala no meio
        (RN-17, arquitetura seção 6: prioridade mais alta corta a que está tocando)."""
        sd = _import_sounddevice()
        sd.stop()

    def play_sequence(self, clips: list[tuple[np.ndarray, int]], *, gap_s: float = 0.2) -> None:
        """Toca vários trechos em sequência, com uma pausa entre eles.

        Todos os trechos precisam ter o mesmo sample_rate.
        """
        if not clips:
            return
        sample_rate = clips[0][1]
        if any(sr != sample_rate for _, sr in clips):
            raise ValueError("play_sequence exige o mesmo sample_rate em todos os trechos")
        gap = np.zeros(int(sample_rate * gap_s), dtype=np.float32)
        parts: list[np.ndarray] = []
        for samples, _ in clips:
            parts.append(samples)
            parts.append(gap)
        self.play(np.concatenate(parts[:-1]), sample_rate)
