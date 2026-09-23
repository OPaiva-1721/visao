#!/usr/bin/env python3
"""Teste de áudio "de mentira" — Fase 0.5 (docs/plano.md).

Toca só os sons, em um fone só (como ela vai usar de verdade), para decidir com ela:
  - bipe, voz, ou os dois? (U6)
  - direção falada ("esquerda/frente/direita") ou no timbre do bipe? (RN-18, params.audio.direcao)
  - o ritmo/tom do bipe incomoda? é rápido demais, devagar demais?

Não depende de câmera, YOLO nem profundidade — é só áudio (arquitetura seção 5.3 e 6).
Requer o extra "audio": `uv sync --extra audio`.

Uso:
    uv run --extra audio python tools/audio_test.py [--perfil pc] [--device N]

Depois da sessão: anote o que ela disse em docs/testes-campo/ e ajuste
shared/config/params.yaml (audio.direcao, audio.bipe.*, RN-17..19) com o resultado.
"""

from __future__ import annotations

import argparse
import contextlib
import sys

from visao.audio.player import Player, load_wav
from visao.audio.synth import SAMPLE_RATE, beep_with_side_timbre, repeat_at_rate, sine_tone
from visao.audio.vocab import SIDE_TO_VOCAB_KEY
from visao.config import SHARED_DIR, ClassInfo, load_classes, load_params, load_vocabulary
from visao.core.types import Band, Side

ZONAS = [("perto", "perto (bipe rápido)"), ("atencao", "atenção (bipe mais lento)")]
BANDAS = [(Band.CHAO, "chão"), (Band.TRONCO, "tronco"), (Band.CABECA, "cabeça")]
LADOS: list[tuple[Side, str]] = [("esq", "esquerda"), ("frente", "frente"), ("dir", "direita")]

AUDIO_DIR = SHARED_DIR / "audio"


def _ask(prompt: str, options: list[tuple[str, str]]) -> str | None:
    """Mostra `options` numeradas; devolve a chave escolhida, ou None se ela cancelar (Enter)."""
    print(prompt)
    for i, (_key, label) in enumerate(options, start=1):
        print(f"  {i}) {label}")
    raw = input("> ").strip()
    if not raw:
        return None
    try:
        idx = int(raw) - 1
    except ValueError:
        print("  não entendi, tentando de novo.")
        return _ask(prompt, options)
    if not 0 <= idx < len(options):
        print("  número fora da lista, tentando de novo.")
        return _ask(prompt, options)
    return options[idx][0]


def _clip(key: str):
    path = AUDIO_DIR / f"{key}.wav"
    if not path.exists():
        raise FileNotFoundError(path)
    return load_wav(path)


def _play_clip_or_warn(player: Player, key: str) -> None:
    try:
        samples, sample_rate = _clip(key)
    except FileNotFoundError:
        print(f"  (sem áudio para '{key}' — rode tools/gen_audio.py --voice pt_BR-... primeiro)")
        return
    player.play(samples, sample_rate)


def beep_only(player: Player, params: dict) -> None:
    """Só o bipe, nas duas dimensões que ele carrega: distância (ritmo) e altura (tom)."""
    zona = _ask("\nZona (distância):", ZONAS)
    if zona is None:
        return
    banda_key = _ask("Banda (altura do obstáculo):", BANDAS)
    if banda_key is None:
        return

    bipe = params["audio"]["bipe"]
    volume = params["audio"]["volume"]
    freq_hz = bipe["tom_hz"][banda_key]
    rate_hz = bipe["ritmo_hz"][zona]
    pulse = sine_tone(freq_hz=freq_hz, duration_ms=bipe["duracao_ms"], volume=volume)
    print(f"  tocando: zona={zona} ({rate_hz} Hz), banda={banda_key} ({freq_hz} Hz)...")
    player.play(repeat_at_rate(pulse, rate_hz=rate_hz, total_duration_s=2.5), SAMPLE_RATE)


def _ask_objeto(classes: dict[str, ClassInfo]) -> str | None:
    vistos: set[str] = set()
    opcoes: list[tuple[str, str]] = []
    for info in sorted(classes.values(), key=lambda c: c.fala):
        if info.fala in vistos:
            continue
        vistos.add(info.fala)
        opcoes.append((info.fala, info.fala))
    return _ask("\nObjeto:", opcoes)


def option_a(player: Player, params: dict, classes: dict[str, ClassInfo]) -> None:
    """Opção A (arquitetura 5.3): bipe só com distância/altura; a voz diz o lado."""
    zona = _ask("\nZona (distância):", ZONAS)
    if zona is None:
        return
    banda_key = _ask("Banda (altura):", BANDAS)
    if banda_key is None:
        return
    objeto = _ask_objeto(classes)
    if objeto is None:
        return
    lado = _ask("Lado:", LADOS)
    if lado is None:
        return

    bipe = params["audio"]["bipe"]
    volume = params["audio"]["volume"]
    pulse = sine_tone(
        freq_hz=bipe["tom_hz"][banda_key], duration_ms=bipe["duracao_ms"], volume=volume
    )
    print(f"  bipe (zona={zona}, banda={banda_key}) + voz: '{objeto}, {SIDE_TO_VOCAB_KEY[lado]}'")
    player.play(
        repeat_at_rate(pulse, rate_hz=bipe["ritmo_hz"][zona], total_duration_s=1.5), SAMPLE_RATE
    )
    _play_clip_or_warn(player, objeto)
    _play_clip_or_warn(player, SIDE_TO_VOCAB_KEY[lado])


def option_b(player: Player, params: dict, classes: dict[str, ClassInfo]) -> None:
    """Opção B (arquitetura 5.3): o timbre do bipe diz o lado; a voz só nomeia o objeto."""
    zona = _ask("\nZona (distância):", ZONAS)
    if zona is None:
        return
    banda_key = _ask("Banda (altura):", BANDAS)
    if banda_key is None:
        return
    objeto = _ask_objeto(classes)
    if objeto is None:
        return
    lado = _ask("Lado:", LADOS)
    if lado is None:
        return

    bipe = params["audio"]["bipe"]
    volume = params["audio"]["volume"]
    pulse = beep_with_side_timbre(
        lado, freq_hz=bipe["tom_hz"][banda_key], duration_ms=bipe["duracao_ms"], volume=volume
    )
    print(f"  bipe com timbre '{lado}' (zona={zona}, banda={banda_key}) + voz: '{objeto}'")
    player.play(
        repeat_at_rate(pulse, rate_hz=bipe["ritmo_hz"][zona], total_duration_s=1.5), SAMPLE_RATE
    )
    _play_clip_or_warn(player, objeto)


def system_phrases(player: Player) -> None:
    sistema = load_vocabulary()["sistema"]
    opcoes = [(key, f"{key} — {texto}") for key, texto in sorted(sistema.items())]
    key = _ask("\nFrase do sistema:", opcoes)
    if key is None:
        return
    _play_clip_or_warn(player, key)


def main(argv: list[str] | None = None) -> int:
    # console do Windows pode não estar em UTF-8 e encavalar os acentos
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--perfil", default="pc", help="Perfil de máquina (padrão: pc)")
    parser.add_argument("--device", default=None, help="Dispositivo de saída do sounddevice")
    args = parser.parse_args(argv)

    params = load_params(args.perfil)
    classes = load_classes()
    player = Player(device=args.device)

    print("=== Teste de áudio — Fase 0.5 (docs/plano.md) ===")
    print("Fone em um ouvido só, num lugar tranquilo. Ela avalia cada som.\n")
    if not any(AUDIO_DIR.glob("*.wav")):
        print(
            f"(nenhum clipe de voz em {AUDIO_DIR} ainda — rode tools/gen_audio.py;"
            " os bipes funcionam sem isso)\n"
        )

    menu = [
        ("1", "Bipe sozinho — ritmo (distância) × tom (altura)", beep_only, (player, params)),
        ("2", "Opção A — bipe + voz diz o lado", option_a, (player, params, classes)),
        (
            "3",
            "Opção B — bipe com timbre por lado + voz só o objeto",
            option_b,
            (player, params, classes),
        ),
        ("4", "Frases curtas do sistema", system_phrases, (player,)),
    ]

    while True:
        print("\n--- Menu ---")
        for key, label, _fn, _args in menu:
            print(f"  {key}) {label}")
        print("  0) Sair")
        try:
            escolha = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            escolha = "0"
            print()

        if escolha == "0":
            break
        acao = next((item for item in menu if item[0] == escolha), None)
        if acao is None:
            print("  opção inválida.")
            continue
        _key, _label, fn, fn_args = acao
        try:
            fn(*fn_args)
        except RuntimeError as e:
            print(f"  {e}")
        except (EOFError, KeyboardInterrupt):
            print()
            continue

    print(
        "\nSessão terminada. Anote em docs/testes-campo/: o que ela entendeu, o que incomodou,\n"
        "se prefere bipe/voz/os dois, e A ou B para a direção. Depois ajuste\n"
        "shared/config/params.yaml (audio.direcao, audio.bipe.*)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
