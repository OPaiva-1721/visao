"""Ponte entre os tipos do núcleo (Side) e as chaves de shared/audio/vocabulario.yaml."""

from __future__ import annotations

from visao.core.types import Side

# vocabulario.yaml usa a palavra por extenso; o núcleo usa o código curto (core/types.py).
SIDE_TO_VOCAB_KEY: dict[Side, str] = {
    "esq": "esquerda",
    "frente": "frente",
    "dir": "direita",
}


def flatten_vocabulary(vocabulary: dict[str, dict[str, str]]) -> dict[str, str]:
    """Achata direcoes/objetos/sistema num só mapa chave → texto falado.

    Levanta ValueError se a mesma chave aparecer em duas seções — evitaria gerar
    ou tocar o clipe errado (os .wav ficam todos juntos em shared/audio/).
    """
    flat: dict[str, str] = {}
    for section, entries in vocabulary.items():
        for key, text in entries.items():
            if key in flat:
                raise ValueError(
                    f"chave '{key}' duplicada entre seções do vocabulário (também em '{section}')"
                )
            flat[key] = text
    return flat
