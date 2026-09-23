# ADR-015 — Família Ultralytics YOLO26 para detecção e profundidade

- **Status:** Proposto · 23/09/2026 — vira Aceito se os spikes S1, S2 e S6 confirmarem
- **Atualiza:** a escolha de detector (antes YOLO11n) e os candidatos de profundidade do ADR-005

## Contexto

A pesquisa de 23/09 ([referencias.md](../referencias.md)) mostrou que:

- O **YOLO26n** (jan/2026) é ~31% mais rápido em CPU que o YOLO11n (38,9 × 56,1 ms, ONNX) e dá saída **sem NMS**.
- O YOLO26 tem uma tarefa nativa de **profundidade em metros** (`yolo26n-depth`), com o mesmo pacote e o mesmo export.
- O **YOLOE-26** detecta classes definidas **por texto** e exporta como um YOLO comum.
- O plugin Flutter oficial (`ultralytics_yolo`) roda tudo isso via LiteRT no Android, incluindo depth.

## Decisão

1. Detector: **YOLO26n** no lugar do YOLO11n.
2. Profundidade: o spike S2 compara **YOLO26n-depth** (metros) × **Depth Anything V2 Small** (relativa + reescala). Preferência pelo YOLO26n-depth se a precisão for parecida, porque evita o reescalonamento e usa um toolchain só.
3. Classes fora do COCO: spike **S6** testa o **YOLOE-26** com prompts de texto nos vídeos dela antes de qualquer treino. A Fase 4 só treina o que o YOLOE não resolver.
4. App (Fase 5): o spike S4 compara o plugin `ultralytics_yolo` × `tflite_flutter` feito à mão.

## Alternativas descartadas

- **Manter o YOLO11n:** mais lento em CPU e com NMS no pós-processamento.
- **Treinar classes novas logo (Fase 4 como estava):** mais trabalho de dados, que o desenvolvedor prefere evitar (D7).

## Consequências

- Tudo continua AGPL-3.0 (já aceito, RN-31).
- O `yolo26n-depth` a 768 px custa 272 ms em CPU. Precisa rodar em resolução menor; o S2 mede o quanto a precisão cai.
- Vocabulário aberto costuma errar mais que classe treinada: o S6 mede recall por classe com os eventos rotulados (ADR-007).
