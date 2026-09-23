# ADR-014 — App 100% Flutter/Dart

- **Status:** Aceito · 22/09/2026

## Contexto

O desenvolvedor tem afinidade com Flutter e não com Kotlin. O celular alvo é um Redmi 13C (Helio G85), fraco.

## Decisão

App todo em Flutter/Dart: `camera` (image stream), `tflite_flutter` ou `ultralytics_yolo` (decidido no spike S4) num isolate, `flutter_soloud`, `sensors_plus`, `flutter_foreground_task` e `audio_service` (botão do fone). Kotlin só como plano B pontual, se um spike falhar.

## Alternativas descartadas

- **Câmera + inferência em Kotlin nativo:** um pouco mais rápido, mas fora da afinidade do desenvolvedor.

## Consequências

- A conversão YUV → tensor em Dart é o gargalo conhecido (medido no S4; fallback `opencv_dart`).
- A Xiaomi pode matar o app em segundo plano (spike S3).
