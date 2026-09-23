# ADR-005 — Distância por pinhole + Depth Anything, sem sensor

- **Status:** Aceito · 22/09/2026 · candidatos de modelo atualizados pelo [ADR-015](015-familia-yolo26.md) (YOLO26n-depth × Depth Anything V2 Small, decidido no spike S2)

## Contexto

Orçamento de hardware R$ 0. Sem sensor de distância, sem câmera estéreo.

## Decisão

- **Pinhole por classe** (altura real conhecida → distância), a cada frame.
- **Depth Anything V2 Small** assíncrono (~5 Hz) para profundidade densa, reescalado pelas detecções de altura conhecida.
- Objeto cortado pela borda = Perto (RN-33); profundidade velha = modo degradado (RN-34).

## Alternativas descartadas

- **Sensor ToF/ultrassom:** mais confiável, mas custa dinheiro. Volta com patrocínio, como fonte extra.
- **Câmera estéreo (OAK-D):** cara e volumosa.

## Consequências

- O erro de escala do modelo monocular é o risco principal (medido no spike S2, com trena).
- No notebook i3 e no Redmi 13C (Helio G85) a profundidade pode não caber (ADR-013).
