# Referências e recursos aproveitáveis

Pesquisa de 23/09/2026 no Hugging Face, GitHub e docs oficiais. Para cada item: o que é, onde entra no projeto e o cuidado com licença.

## 1. Modelos

| Recurso | O que é | Onde entra | Licença |
| --- | --- | --- | --- |
| [YOLO26n](https://docs.ultralytics.com/models/yolo26) (Ultralytics, jan/2026) | Sucessor do YOLO11. YOLO26n: 40,9 mAP e 38,9 ms em CPU ONNX, contra 56,1 ms do YOLO11n. Saída **sem NMS** (end-to-end) | Substitui o YOLO11n como detector (ADR-015). Sem NMS = menos código no port para Dart | AGPL-3.0 |
| [YOLO26n-depth](https://docs.ultralytics.com/tasks/depth) | Profundidade monocular **em metros**, nativa do Ultralytics. Nano: 6,3 M parâmetros, δ1 = 0,882 no NYU; 272 ms em CPU ONNX a 768 px | Candidato principal de profundidade no spike S2 — mesmo pacote, mesmo export, já em metros | AGPL-3.0 |
| [YOLOE-26](https://docs.ultralytics.com/models/yoloe) (n/s/m/l/x) | Detector de **vocabulário aberto**: define as classes por texto (`set_classes([...])`) e exporta com as classes congeladas, rodando como um YOLO comum | Detectar "tree branch", "street sign", "pole", "awning", "open door"… **sem treinar** (spike S6). Pode encolher ou eliminar a Fase 4 | AGPL-3.0 |
| [Depth Anything V2 Small (LiteRT)](https://huggingface.co/litert-community/depth-anything-v2-small) | Export oficial para LiteRT: FP32 (99,5 MB) e **INT8 (27,7 MB)**. Entrada fixa 518×686. Profundidade **relativa** | Alternativa de profundidade no S2 (precisa do reescalonamento pelo pinhole, arquitetura 4.2) | Apache-2.0 |
| [Depth Anything V2 Small (ONNX)](https://huggingface.co/onnx-community/depth-anything-v2-small) | Mesmo modelo em ONNX | Benchmark no PC (S2) | Apache-2.0 |
| [Depth Anything V2 Metric Hypersim Small (ONNX)](https://huggingface.co/77ukhtar/depth-anything-v2-metric-onnx) | Variante **métrica** para ambiente interno (até 20 m), export da comunidade | Comparação métrica em ambiente interno no S2 | Apache-2.0 (checkpoint base) |
| [Qualcomm AI Hub — Depth Anything V2](https://huggingface.co/qualcomm/Depth-Anything-V2) | TFLite + medições por aparelho | Só como ordem de grandeza: os números são de chips Qualcomm, e o Redmi 13C é MediaTek | Ver página |

## 2. Dados

| Recurso | O que é | Onde entra | Licença |
| --- | --- | --- | --- |
| [ROD — Obstacle-Detection-Dataset-YOLO](https://huggingface.co/datasets/ShafinSI/Obstacle-Detection-Dataset-YOLO) | 24.326 imagens de calçada, 25 classes, formato YOLO. Inclui **Tree, Electrical Pole, Traffic Sign, Stairs, Dustbin, Traffic Cone, Bench, Person** | Fase 4 sem rotular: treino/validação das classes fora do COCO | MIT |
| [Roboflow Universe — visually impaired obstacle detection](https://universe.roboflow.com/visually-impaired-obstacle-detection-uxdze/obstacle-detection-yeuzf) | Dataset/modelo da comunidade para obstáculos | Complemento da Fase 4 | Conferir na página |
| [Obstacle Dataset (Wu et al.)](https://link.springer.com/article/10.1007/s10209-021-00837-9) | ~7,9 mil imagens, 15 tipos de obstáculo de calçada cega (inclui poste e hidrante) | Complemento da Fase 4 | Conferir no artigo |

**Lacuna conhecida:** nenhum dataset achado cobre bem obstáculo **na altura da cabeça** (galho baixo, toldo, orelhão, porta de armário aberta). Esse caso continua dependendo do caminho geométrico (ADR-006) e do YOLOE por texto (S6).

## 3. Código e ferramentas

| Recurso | O que é | Onde entra | Licença |
| --- | --- | --- | --- |
| [ultralytics_yolo (Flutter)](https://pub.dev/packages/ultralytics_yolo) · [repo](https://github.com/ultralytics/yolo-flutter-app) | Plugin **oficial**: câmera + inferência LiteRT com GPU no Android, suporta as tarefas do YOLO26 **incluindo depth** | Fase 5: provavelmente substitui câmera + `tflite_flutter` + conversão YUV feitas à mão (spike S4). Os modelos baixados automaticamente usam 640×640; para o Helio G85, exportar os nossos em resolução menor | AGPL-3.0 |
| [Export LiteRT do Ultralytics](https://docs.ultralytics.com/integrations/litert) | `model.export(format="tflite")` | Gerar os modelos do app | AGPL-3.0 |
| [Piper voices — pt_BR](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR) | Vozes pt-BR (ex.: `pt_BR-faber-medium`) em ONNX | `gen_audio.py` (ADR-008) | Repositório MIT; **conferir o MODEL_CARD de cada voz**, porque o dataset de treino pode ter licença própria |

## 4. Projetos e artigos parecidos (ideias, não código)

| Projeto | O que aproveitar |
| --- | --- |
| [ROD (Amirkabir University)](https://huggingface.co/datasets/ShafinSI/Obstacle-Detection-Dataset-YOLO) | YOLOv8n em Android de gama média + ARCore para distância + TTS. Valida o caminho "celular no peito" |
| [An Embedded Real-time Object Alert System for Visually Impaired (arXiv 2507.08165)](https://arxiv.org/pdf/2507.08165) | Mesma ideia (detecção + profundidade monocular + alerta). Bom para a seção "trabalhos relacionados" do portfólio |
| [Investigating YOLO Models Towards Outdoor Obstacle Detection for Visually Impaired People (arXiv 2312.07571)](https://arxiv.org/pdf/2312.07571) | Comparação de versões de YOLO para obstáculos de calçada |
| [team8/outdoor-blind-navigation](https://github.com/team8/outdoor-blind-navigation) | Feedback sonoro + vibração com detector multithread |
| [GitHub topic: blind-navigation](https://github.com/topics/blind-navigation) | Vários projetos de estudante. Servem de contraste: quase nenhum mede latência, recall ou testa com usuária real — é aí que este projeto se diferencia |

## 5. Descartados

| Recurso | Por quê |
| --- | --- |
| **ARCore Depth API** (distância métrica "de graça" no Android) | O **Redmi 13C não está** na lista de aparelhos com ARCore ([lista oficial](https://developers.google.com/ar/devices)) |
| Qualcomm/NexaAI NPU builds | Específicos para chips Qualcomm; o Redmi 13C é MediaTek |
