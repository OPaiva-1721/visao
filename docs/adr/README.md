# Decisões de arquitetura (ADRs)

Uma decisão por arquivo. Formato: contexto → decisão → alternativas → consequências.
Para mudar uma decisão, crie um ADR novo que **substitui** o antigo e marque o antigo como `Substituído por ADR-xxx`.

| ADR | Decisão | Status |
| --- | --- | --- |
| [001](001-python-lab-dart-app.md) | Python como laboratório, app em Dart, traces como contrato | Aceito |
| [002](002-nucleo-puro.md) | Núcleo de decisão puro e determinístico | Aceito |
| [003](003-parametros-yaml.md) | Parâmetros em YAML compartilhado | Aceito |
| [004](004-ultimo-frame-vence.md) | Captura "último frame vence" | Aceito |
| [005](005-distancia-sem-sensor.md) | Distância por pinhole + modelo de profundidade, sem sensor | Aceito (candidatos atualizados pelo 015) |
| [006](006-dois-caminhos-percepcao.md) | Percepção semântica + geométrica | Aceito |
| [007](007-avaliacao-por-eventos.md) | Avaliação por eventos, não por caixas | Aceito |
| [008](008-audio-pre-gerado.md) | Voz pré-gerada com Piper; bipes sintetizados | Aceito |
| [009](009-sem-imagens-persistidas.md) | Nenhuma imagem persistida em runtime | Aceito |
| [010](010-monorepo.md) | Monorepo com `shared/` | Aceito |
| [011](011-camera-celular-retrato.md) | Câmera = celular em retrato no peito | Aceito |
| [012](012-teste-campo-duas-etapas.md) | Teste de campo em duas etapas (3a notebook, 3b celular) | Aceito |
| [013](013-perfis-de-maquina.md) | Perfis de máquina sobre a config base | Aceito |
| [014](014-app-flutter-puro.md) | App 100% Flutter/Dart | Aceito |
| [015](015-familia-yolo26.md) | Família YOLO26: detecção, profundidade e classes por texto (YOLOE) | Proposto (spikes S1, S2, S6) |
