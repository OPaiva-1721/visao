import threading
import time

import numpy as np

from visao.capture.frame import Frame
from visao.capture.slot import LatestFrameSlot
from visao.capture.source import FakeFrameSource, FrameSource


def make_frame(t_capture: float) -> Frame:
    return Frame(image=np.zeros((2, 2), dtype=np.uint8), t_capture=t_capture)


def test_slot_vazio_devolve_none():
    assert LatestFrameSlot().get() is None


def test_get_devolve_o_frame_colocado():
    slot = LatestFrameSlot()
    frame = make_frame(1.0)
    slot.put(frame)
    assert slot.get() is frame


def test_put_novo_sobrescreve_o_antigo():
    """ADR-004: nunca enfileira, o mais recente sempre vence."""
    slot = LatestFrameSlot()
    frame1 = make_frame(1.0)
    frame2 = make_frame(2.0)
    slot.put(frame1)
    slot.put(frame2)
    assert slot.get() is frame2


def test_get_repetido_sem_put_novo_devolve_o_mesmo_frame():
    slot = LatestFrameSlot()
    frame = make_frame(1.0)
    slot.put(frame)
    assert slot.get() is frame
    assert slot.get() is frame  # a percepção pode reprocessar; não trava esperando


def test_take_if_new_primeira_leitura_devolve_o_frame():
    slot = LatestFrameSlot()
    frame = make_frame(1.0)
    slot.put(frame)
    assert slot.take_if_new(None) is frame


def test_take_if_new_mesmo_frame_devolve_none_na_segunda_vez():
    slot = LatestFrameSlot()
    frame = make_frame(1.0)
    slot.put(frame)
    assert slot.take_if_new(1.0) is None


def test_take_if_new_detecta_frame_novo():
    slot = LatestFrameSlot()
    slot.put(make_frame(1.0))
    frame2 = make_frame(2.0)
    slot.put(frame2)
    assert slot.take_if_new(1.0) is frame2


def test_take_if_new_sem_nenhum_frame_devolve_none():
    assert LatestFrameSlot().take_if_new(None) is None


def test_concorrencia_nao_quebra_e_nao_perde_integridade():
    """Várias threads escrevendo e uma lendo — não deve lançar exceção nem devolver
    um Frame corrompido (t_capture sempre um valor de fato colocado)."""
    slot = LatestFrameSlot()
    postos = {round(i * 0.001, 3) for i in range(500)}
    erros: list[Exception] = []

    def escrever(inicio: int) -> None:
        try:
            for i in range(inicio, inicio + 100):
                slot.put(make_frame(round(i * 0.001, 3)))
        except Exception as e:  # noqa: BLE001 — só para o teste reportar, não engolir
            erros.append(e)

    def ler() -> None:
        try:
            for _ in range(200):
                frame = slot.get()
                if frame is not None:
                    assert frame.t_capture in postos
        except Exception as e:  # noqa: BLE001
            erros.append(e)

    threads = [threading.Thread(target=escrever, args=(i,)) for i in range(0, 500, 100)]
    threads.append(threading.Thread(target=ler))
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert not erros
    assert slot.get() is not None


# --- FakeFrameSource ----------------------------------------------------------


def test_fake_frame_source_implementa_o_protocol():
    assert isinstance(FakeFrameSource(), FrameSource)


def test_fake_frame_source_comeca_vazia():
    assert FakeFrameSource().latest() is None


def test_fake_frame_source_push_depois_latest():
    source = FakeFrameSource()
    frame = make_frame(1.0)
    source.push(frame)
    assert source.latest() is frame


def test_fake_frame_source_start_stop_nao_quebram():
    source = FakeFrameSource()
    source.start()  # não faz nada, mas precisa existir e não lançar
    source.push(make_frame(time.monotonic()))
    source.stop()
    assert source.latest() is not None
