# Plano — Detecção de Objetos para Acessibilidade

Sep 22, 2026 · @Someone

Projeto de visão computacional para portfólio: um sistema de detecção de objetos com saída em áudio para apoiar a irmã de Paiva (deficiente visual), começando simples (webcam + modelo pronto) e incrementando até um dispositivo portátil.

## Fase 0 — Validação rápida (antes de codar)

- Perguntar à irmã qual dor pesa mais hoje: esbarrar em obstáculos, ou não saber o que tem na mão/na prateleira.
- Definir o ambiente de teste inicial: webcam de notebook, ou celular com app tipo DroidCam.
- Critério de saída: prioridade definida para orientar a Fase 3.

**Decisão (22/09):** a irmã confirmou — a prioridade é evitar esbarrar em obstáculos, não identificar produto. A Fase 3 segue pelo caminho de estimativa de distância.

## Fase 1 — MVP: detecção genérica + áudio

- Modelo: YOLOv8n (Ultralytics), pré-treinado em COCO — sem treinar nada do zero.
- Pipeline: webcam → YOLO detecta objetos comuns (pessoa, cadeira, garrafa, banana etc.) → fala o nome do objeto mais próximo/central.
- Voz: pyttsx3 (offline, sem depender de internet) ou gTTS.
- Regra de relevância simples: falar só o objeto com maior bounding box (mais próximo), com cooldown de \~2s para não repetir.
- Critério de sucesso: roda em tempo real (>10 fps) no notebook, fala em português.

## Fase 2 — Teste real e ajuste de usabilidade

- Testar com a irmã em ambiente controlado (não precisa ser o mercado ainda).
- Coletar feedback: frequência de fala incômoda, quais objetos importam de verdade, falsos positivos.
- Ajustar cooldown, velocidade e volume da voz.
- Usar o resultado para confirmar a prioridade da Fase 3.

## Fase 3 — Incremento conforme prioridade

| Prioridade | O que adicionar |
| --- | --- |
| Evitar obstáculo | Estimativa de distância com modelo de profundidade (MiDaS / Depth Anything, Hugging Face) — falar "cadeira a 2 metros" |
| Identificar produto | OCR (EasyOCR/Tesseract) para ler rótulo, ou modelo zero-shot (OWL-ViT/Grounding DINO) para categorias mais específicas |

Caminho confirmado: **evitar obstáculo** (linha 1 da tabela).

## Fase 4 — Portabilidade

- Sair do notebook: rodar em celular (modelo exportado para ONNX/TFLite) ou Raspberry Pi + câmera.
- Validar o uso andando pelo ambiente, sem precisar segurar o notebook.

## Fase 5 — Forma final (óculos)

- Só depois de validado nas fases anteriores.
- Hardware: ESP32-CAM ou Raspberry Pi Zero + câmera acoplados à armação, com fone de condução óssea ou speaker pequeno para o áudio.

## Stack técnica

| Camada | Ferramenta |
| --- | --- |
| Detecção | YOLOv8n (Ultralytics) |
| Áudio | pyttsx3 / gTTS |
| Linguagem | Python |
| Visão auxiliar | OpenCV |
| Profundidade (fase 3) | MiDaS / Depth Anything (Hugging Face) |
| OCR (fase 3) | EasyOCR / Tesseract |
