"""Testa só `load_wav` (IO pura em arquivo). `Player.play*` precisa de sounddevice + hardware
de som e não é exercitado aqui — ver docs/arquitetura.md seção 13 (não há spike de CI para áudio;
a validação é ouvindo, na Fase 0.5)."""

import struct
import wave
from pathlib import Path

import numpy as np
import pytest

from visao.audio.player import load_wav


def _write_wav(
    path: Path, samples: list[int], *, channels: int = 1, sample_rate: int = 8000
) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def test_load_wav_mono_roundtrip(tmp_path):
    path = tmp_path / "mono.wav"
    _write_wav(path, [0, 16384, -16384, 32767, -32768], sample_rate=8000)

    samples, sample_rate = load_wav(path)

    assert sample_rate == 8000
    np.testing.assert_allclose(samples, [0, 0.5, -0.5, 32767 / 32768, -1.0], atol=1e-4)


def test_load_wav_mixa_estereo_para_mono(tmp_path):
    path = tmp_path / "stereo.wav"
    # canal esquerdo em -1.0, direito em +1.0 → mixado deveria virar ~0.0
    _write_wav(path, [-32768, 32767, -32768, 32767], channels=2, sample_rate=8000)

    samples, _ = load_wav(path)

    assert len(samples) == 2  # 4 amostras intercaladas / 2 canais
    np.testing.assert_allclose(samples, [0.0, 0.0], atol=1e-3)


def test_load_wav_rejeita_sampwidth_diferente_de_16bit(tmp_path):
    path = tmp_path / "8bit.wav"
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(1)
        wav_file.setframerate(8000)
        wav_file.writeframes(bytes([0, 128, 255]))

    with pytest.raises(ValueError, match="16-bit"):
        load_wav(path)
