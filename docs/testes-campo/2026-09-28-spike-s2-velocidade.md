# Spike S2 — velocidade da profundidade (parcial: falta a precisão)

28/09/2026 · PC de mesa (Ryzen 5 5600GT, sem GPU dedicada) · ONNX Runtime, `CPUExecutionProvider` · imagem sintética, só mede tempo

Pergunta do S2 ([arquitetura, seção 13](../arquitetura.md)): qual modelo roda a ≥ 5 Hz junto com o YOLO e erra menos em metros? **Esta página cobre só a metade da velocidade.** A precisão precisa de trena (`tools/depth_view.py`).

## Resultado

| Modelo | Resolução de entrada | Média | fps | p95 |
| --- | --- | --- | --- | --- |
| **YOLO26n-depth** | 320 px | **30,0 ms** | **33,4** | 37,6 ms |
| YOLO26n-depth | 512 px | 83,7 ms | 12,0 | 167,2 ms |
| YOLO26n-depth | 768 px | 185,1 ms | 5,4 | 215,5 ms |
| Depth Anything V2 Small | 224×294 | 109,5 ms | 9,1 | 119,2 ms |
| Depth Anything V2 Small | 322×434 | 288,7 ms | 3,5 | 348,5 ms |
| Depth Anything V2 Small | 518×686 | 1132,6 ms | 0,9 | 1270,7 ms |

Como medir de novo: `uv run python tools/bench.py --model ../data/modelos/yolo26n-depth.pt --imgsz 512` (o `bench.py` do S1 serve para qualquer modelo do Ultralytics). O Depth Anything foi medido direto no ONNX Runtime (`onnx-community/depth-anything-v2-small`, entrada dinâmica em múltiplos de 14).

## Leitura

- **YOLO26n-depth é ~3,6× mais rápido** que o Depth Anything em tamanho parecido (512 px: 84 ms × 322×434: 289 ms) **e** já devolve metros — o Depth Anything é relativo e precisaria do reescalonamento pelo pinhole (arquitetura 4.2).
- Até 768 px o YOLO26n-depth passa dos 5 Hz sozinho; a 320–512 px sobra folga para rodar junto do detector (8,6 ms) na mesma CPU.
- Sanidade numa frame real (DroidCam, 512 px): saída em metros plausíveis (mediana 0,85 m para a cena de mesa).
- Ainda **não** medido: DirectML (Vega 7), CPU do notebook i3 (S1b/S2 no perfil `notebook`) e o Redmi 13C (S4).

## Falta para fechar o S2

- **Precisão contra a trena:** 20 medidas de 0,5 a 3 m, dentro e fora de casa, em 320 / 512 / 768 px, com `tools/depth_view.py` (salva em `data/medidas_s2.csv`). O erro decide a resolução — e se o YOLO26n-depth vale ou se o Depth Anything precisa entrar.
- Preferência já registrada no [ADR-015](../adr/015-familia-yolo26.md): YOLO26n-depth, se a precisão for parecida.
