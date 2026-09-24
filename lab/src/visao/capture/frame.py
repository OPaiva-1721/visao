"""O tipo `Frame` — uma imagem capturada, com o instante da captura."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, eq=False)
class Frame:
    """Uma imagem capturada e o instante em que foi capturada (não o de leitura).

    `eq=False`: comparar dois `Frame` por `==` compararia `image` (um array numpy) e
    isso levanta `ValueError` em vez de devolver bool. Comparação aqui é por identidade
    (`is`) — dois `Frame` só são "o mesmo" se forem literalmente o mesmo objeto.
    """

    image: np.ndarray
    t_capture: float
