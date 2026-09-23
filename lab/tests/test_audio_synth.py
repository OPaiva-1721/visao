import numpy as np
import pytest

from visao.audio.synth import beep_with_side_timbre, click, repeat_at_rate, sine_tone


def test_sine_tone_tem_duracao_e_tipo_corretos():
    tone = sine_tone(freq_hz=440.0, duration_ms=100.0, sample_rate=1000)
    assert tone.dtype == np.float32
    assert len(tone) == 100


def test_sine_tone_respeita_o_volume():
    tone = sine_tone(freq_hz=440.0, duration_ms=50.0, volume=0.5)
    assert np.max(np.abs(tone)) <= 0.5 + 1e-6


def test_sine_tone_sem_nan_nem_infinito():
    tone = sine_tone(freq_hz=1400.0, duration_ms=60.0)
    assert np.isfinite(tone).all()


@pytest.mark.parametrize("freq_hz", [0.0, -10.0])
def test_sine_tone_rejeita_frequencia_invalida(freq_hz):
    with pytest.raises(ValueError, match="freq_hz"):
        sine_tone(freq_hz=freq_hz, duration_ms=50.0)


@pytest.mark.parametrize("volume", [-0.1, 1.1])
def test_sine_tone_rejeita_volume_fora_da_faixa(volume):
    with pytest.raises(ValueError, match="volume"):
        sine_tone(freq_hz=440.0, duration_ms=50.0, volume=volume)


def test_sine_tone_tem_fade_nas_bordas():
    """Sem fade, um seno começa e termina perto de zero só por acaso; a borda precisa ser
    sempre próxima de zero, senão o áudio estala (arquitetura seção 6)."""
    tone = sine_tone(freq_hz=1234.0, duration_ms=100.0)
    assert abs(tone[0]) < 1e-3
    assert abs(tone[-1]) < 1e-3


def test_click_e_deterministico():
    """Mesma seed sempre: ela precisa reconhecer o mesmo som em sessões diferentes."""
    a = click(agudo=True)
    b = click(agudo=True)
    np.testing.assert_array_equal(a, b)


def test_click_agudo_e_grave_sao_diferentes():
    agudo = click(agudo=True)
    grave = click(agudo=False)
    assert not np.array_equal(agudo, grave)


def test_beep_frente_e_so_o_tom_puro():
    tone = sine_tone(freq_hz=800.0, duration_ms=60.0)
    beep = beep_with_side_timbre("frente", freq_hz=800.0, duration_ms=60.0)
    np.testing.assert_array_equal(tone, beep)


@pytest.mark.parametrize("side", ["esq", "dir"])
def test_beep_esq_dir_tem_prefixo_e_e_mais_longo_que_o_tom_sozinho(side):
    tone = sine_tone(freq_hz=800.0, duration_ms=60.0)
    beep = beep_with_side_timbre(side, freq_hz=800.0, duration_ms=60.0)
    assert len(beep) > len(tone)


def test_beep_esq_e_dir_sao_diferentes_entre_si():
    esq = beep_with_side_timbre("esq", freq_hz=800.0, duration_ms=60.0)
    dir_ = beep_with_side_timbre("dir", freq_hz=800.0, duration_ms=60.0)
    assert len(esq) == len(dir_)
    assert not np.array_equal(esq, dir_)


def test_repeat_at_rate_gera_o_numero_certo_de_ciclos():
    pulse = np.ones(10, dtype=np.float32)
    out = repeat_at_rate(pulse, rate_hz=2.0, total_duration_s=3.0, sample_rate=100)
    # período = sample_rate / rate_hz = 50 amostras; 2 Hz por 3 s = 6 ciclos
    assert len(out) == 50 * 6


def test_repeat_at_rate_preserva_o_pulso_no_inicio_de_cada_ciclo():
    pulse = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    out = repeat_at_rate(pulse, rate_hz=10.0, total_duration_s=0.3, sample_rate=100)
    period_n = 10  # 100 / 10
    np.testing.assert_array_equal(out[:3], pulse)
    np.testing.assert_array_equal(out[period_n : period_n + 3], pulse)
    np.testing.assert_array_equal(out[3:period_n], np.zeros(period_n - 3, dtype=np.float32))


def test_repeat_at_rate_rejeita_rate_nao_positivo():
    with pytest.raises(ValueError, match="rate_hz"):
        repeat_at_rate(np.ones(5, dtype=np.float32), rate_hz=0.0, total_duration_s=1.0)


def test_repeat_at_rate_rejeita_pulso_maior_que_o_periodo():
    """Bipe de 8 Hz (zona Perto) com pulso longo demais se sobreporia — tem que travar cedo."""
    pulse = np.ones(1000, dtype=np.float32)
    with pytest.raises(ValueError, match="sobreporiam"):
        repeat_at_rate(pulse, rate_hz=8.0, total_duration_s=1.0, sample_rate=1000)
