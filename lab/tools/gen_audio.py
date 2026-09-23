#!/usr/bin/env python3
"""Gera os clipes de voz do vocabulário com o Piper (ADR-008).

Requer o extra "voz": `uv sync --extra voz` (piper-tts, GPL-3.0 — ferramenta de build,
nunca embarcada no app; ver comentário em pyproject.toml).

Uso:
    # baixa a voz pt-BR e gera todos os clipes que ainda não existem
    uv run --extra voz python tools/gen_audio.py --voice pt_BR-faber-medium

    # usando um modelo .onnx já baixado
    uv run --extra voz python tools/gen_audio.py --model /caminho/pt_BR-faber-medium.onnx

    # só listar o vocabulário, sem gerar nada
    uv run python tools/gen_audio.py --list

Os .wav saem em shared/audio/<chave>.wav (fora do git — .gitignore).
"""

from __future__ import annotations

import argparse
import contextlib
import subprocess
import sys
import wave
from pathlib import Path

from visao.audio.vocab import flatten_vocabulary
from visao.config import SHARED_DIR, load_vocabulary


def download_voice(voice: str, data_dir: Path) -> Path:
    """Baixa a voz via `python -m piper.download_voices` (CLI documentado do Piper)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [sys.executable, "-m", "piper.download_voices", voice, "--data-dir", str(data_dir)],
            check=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError("Piper não instalado. Rode: uv sync --extra voz") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Falha ao baixar a voz {voice!r} (veja a saída acima)") from e
    model_path = data_dir / f"{voice}.onnx"
    if not model_path.exists():
        raise RuntimeError(f"Download terminou mas {model_path} não apareceu")
    return model_path


def generate_clips(
    words: dict[str, str], *, model_path: Path, output_dir: Path, force: bool
) -> None:
    try:
        from piper import PiperVoice
    except ImportError as e:
        raise RuntimeError("Piper não instalado. Rode: uv sync --extra voz") from e

    voice = PiperVoice.load(str(model_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, text in sorted(words.items()):
        destination = output_dir / f"{key}.wav"
        if destination.exists() and not force:
            print(f"  já existe, pulando: {destination.name}")
            continue
        with wave.open(str(destination), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        print(f"  gerado: {destination.name}  ({text!r})")


def main(argv: list[str] | None = None) -> int:
    # console do Windows pode não estar em UTF-8 e encavalar os acentos
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--model", type=Path, help="Caminho de um modelo de voz (.onnx) já baixado")
    parser.add_argument(
        "--voice",
        help="Nome da voz para baixar antes de gerar (ex.: pt_BR-faber-medium)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".local" / "share" / "piper-voices",
        help="Onde baixar/procurar a voz (padrão: ~/.local/share/piper-voices)",
    )
    parser.add_argument("--force", action="store_true", help="Regera mesmo o que já existe")
    parser.add_argument("--list", action="store_true", help="Só lista as palavras, sem gerar nada")
    args = parser.parse_args(argv)

    words = flatten_vocabulary(load_vocabulary())
    print(f"{len(words)} palavras em shared/audio/vocabulario.yaml.")

    if args.list:
        for key, text in sorted(words.items()):
            print(f"  {key}: {text}")
        return 0

    if args.voice:
        model_path = download_voice(args.voice, args.data_dir)
    elif args.model:
        model_path = args.model
    else:
        parser.error("passe --model <arquivo.onnx> ou --voice <nome> (ex.: pt_BR-faber-medium)")
        return 2  # pragma: no cover — parser.error já encerra o processo

    output_dir = SHARED_DIR / "audio"
    generate_clips(words, model_path=model_path, output_dir=output_dir, force=args.force)
    print(f"Pronto. Rode tools/audio_test.py para ouvir (arquivos em {output_dir}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"Erro: {e}", file=sys.stderr)
        raise SystemExit(1) from e
