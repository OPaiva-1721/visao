"""Síntese de bipes (ADR-008). Funções puras — sem IO; a reprodução fica em `player.py`.

Frequências, ritmos e volumes são parâmetros: quem chama lê os valores de
`shared/config/params.yaml` (ADR-003). Nada aqui é hardcoded.
"""

from __future__ import annotations

import numpy as np

from visao.core.types import Side

SAMPLE_RATE = 44_100


def _fade(n: int, sample_rate: int, fade_ms: float = 5.0) -> np.ndarray:
    """Janela de fade in/out curta, só para o som não estalar nas bordas."""
    fade_n = min(int(sample_rate * fade_ms / 1000), n // 2)
    window = np.ones(n, dtype=np.float32)
    if fade_n > 0:
        ramp = np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
        window[:fade_n] *= ramp
        window[-fade_n:] *= ramp[::-1]
    return window


def sine_tone(
    *, freq_hz: float, duration_ms: float, sample_rate: int = SAMPLE_RATE, volume: float = 0.8
) -> np.ndarray:
    """Um tom puro (seno) com fade nas bordas.

    `freq_hz` vem de `params.audio.bipe.tom_hz` por banda (chão/tronco/cabeça, RN-09).
    """
    if freq_hz <= 0:
        raise ValueError(f"freq_hz precisa ser positivo: {freq_hz}")
    if not 0.0 <= volume <= 1.0:
        raise ValueError(f"volume fora de [0, 1]: {volume}")
    n = max(1, int(sample_rate * duration_ms / 1000))
    t = np.arange(n, dtype=np.float32) / sample_rate
    tone = np.sin(2 * np.pi * freq_hz * t).astype(np.float32)
    return tone * _fade(n, sample_rate) * volume


def click(
    *, agudo: bool, duration_ms: float = 15.0, sample_rate: int = SAMPLE_RATE, volume: float = 0.8
) -> np.ndarray:
    """Ruído curto e filtrado: um 'tic' agudo ou um 'toc' grave.

    Determinístico (mesma seed sempre) — o mesmo som toda vez, para ela reconhecer o padrão.
    """
    n = max(1, int(sample_rate * duration_ms / 1000))
    rng = np.random.default_rng(seed=0)
    noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)
    carrier_hz = 2200.0 if agudo else 220.0
    carrier = np.sin(2 * np.pi * carrier_hz * np.arange(n, dtype=np.float32) / sample_rate)
    wave = noise * 0.3 + carrier.astype(np.float32) * 0.7
    return wave * _fade(n, sample_rate, fade_ms=2.0) * volume


def beep_with_side_timbre(
    side: Side,
    *,
    freq_hz: float,
    duration_ms: float,
    sample_rate: int = SAMPLE_RATE,
    volume: float = 0.8,
) -> np.ndarray:
    """Opção B de direção (arquitetura seção 5.3): um timbre por lado, no fone mono.

    frente = tom limpo · esq = 'tic' agudo antes do tom · dir = 'toc' grave antes do tom.
    """
    tone = sine_tone(
        freq_hz=freq_hz, duration_ms=duration_ms, sample_rate=sample_rate, volume=volume
    )
    if side == "frente":
        return tone
    prefix = click(agudo=(side == "esq"), sample_rate=sample_rate, volume=volume)
    gap = np.zeros(int(sample_rate * 0.02), dtype=np.float32)
    return np.concatenate([prefix, gap, tone])


def repeat_at_rate(
    pulse: np.ndarray, *, rate_hz: float, total_duration_s: float, sample_rate: int = SAMPLE_RATE
) -> np.ndarray:
    """Repete `pulse` no ritmo `rate_hz` (RN-17): mais rápido = mais perto."""
    if rate_hz <= 0:
        raise ValueError(f"rate_hz precisa ser positivo: {rate_hz}")
    period_n = int(sample_rate / rate_hz)
    if period_n < len(pulse):
        raise ValueError(
            f"rate_hz={rate_hz} alto demais para a duração do pulso: os bipes se sobreporiam"
        )
    cycle = np.zeros(period_n, dtype=np.float32)
    cycle[: len(pulse)] = pulse
    n_cycles = max(1, round(total_duration_s * rate_hz))
    return np.tile(cycle, n_cycles)
