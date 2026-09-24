"""Tipos do supervisor (RN-04, RN-27, RN-34; arquitetura seção 7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SystemState(StrEnum):
    """Só os estados que `tick()` decide (arquitetura seção 7). Iniciando/Pronto/
    Encerrando são responsabilidade de quem liga e desliga o sistema, não do supervisor
    — ele só vigia enquanto o sistema já está Rodando."""

    RODANDO = "rodando"
    DEGRADADO = "degradado"
    FALHA = "falha"


class FaultKind(StrEnum):
    """Chave de shared/audio/vocabulario.yaml (seção sistema) — a mensagem já existe."""

    CAMERA = "falha_camera"
    LENTO = "falha_lento"
    ERRO = "falha_erro"


@dataclass(frozen=True)
class SupervisorInputs:
    """O que o supervisor observa a cada chamada — ele não mede nada sozinho, só decide
    a partir do que a captura, o detector e o sensor de luz já mediram."""

    last_frame_t: float | None  # t_capture do último frame visto; None = nenhum ainda
    fps_recente: float | None  # fps medido numa janela recente; None = sem dados ainda
    profundidade_esperada: bool  # params.profundidade.ligada do perfil atual (RN-34)
    profundidade_last_update: float | None  # None = nunca (só importa se esperada=True)
    brilho_medio: float | None  # 0–255; None = sem leitura de luz ainda
    excecao: bool  # alguma thread lançou uma exceção não tratada


@dataclass(frozen=True)
class SupervisorState:
    """Os pequenos temporizadores que precisam persistir entre chamadas — tudo o mais
    é recalculado do zero a cada `tick()` (não precisa acumular histórico)."""

    fps_baixo_desde: float | None = None
    luz_baixa_desde: float | None = None


@dataclass(frozen=True)
class SupervisorReport:
    """O que fazer com o áudio neste tick (fora do fluxo do `decide()` — ADR-002
    princípio 4: um supervisor independente, para o silêncio nunca ser ambíguo)."""

    state: SystemState
    fault: FaultKind | None  # só quando state == FALHA
    pouca_luz: bool  # RN-27 — pode ser True mesmo com state == RODANDO
