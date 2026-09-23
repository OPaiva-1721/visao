# Plano Detalhado v2 — Detecção de Obstáculos para Acessibilidade

22/09/2026 · revisão do plano original com regras de negócio, perguntas em aberto e cronograma realista

**Status (23/09/2026):** planejamento concluído; repositório criado com a estrutura da arquitetura (seção 10), configs de `shared/` preenchidas com os parâmetros das RNs, 15 ADRs em `docs/adr/` e CI (lint + testes).

**Fase 0.5 (ferramenta pronta, sessão com ela ainda não feita):** `lab/tools/audio_test.py` toca os bipes (síntese em tempo real, testado sem hardware) e, se os clipes existirem, as frases das opções A e B. `lab/tools/gen_audio.py` gera os clipes de voz com o Piper (`uv sync --extra voz`, extra separado — ver comentário de licença no `pyproject.toml`). Falta: rodar `gen_audio.py` com uma voz pt-BR e sentar com ela para decidir `audio.direcao` (voz × timbre) e calibrar `audio.bipe.*`.

O plano original está em [historico/plano-v1.md](historico/plano-v1.md).

## 1. Objetivo e premissas

**Objetivo:** protótipo que ajuda uma pessoa com deficiência visual (irmã do Paiva) a **evitar esbarrar em obstáculos**, com saída sonora, evoluindo de notebook → dispositivo vestível. Também é peça de portfólio.

**Decisão já tomada (22/09):** prioridade = evitar obstáculo (não identificar produto).

**Premissas deste plano** (confirmadas na seção 1.1):

- Dedicação de ~2 sessões/semana com a irmã (~6h no total combinadas); desenvolvimento solo.
- A bengala continua sendo o equipamento principal. O sistema **complementa**, não substitui.
- Orçamento de hardware: **R$ 0 agora**. Patrocínio possível depois, com uma demo pronta pra mostrar.

## 1.1 Decisões confirmadas (22–23/09)

Respostas coletadas em conversa direta. Todas as perguntas 🔴 de bloqueio (seção 4) estão fechadas — o projeto pode começar.

**Sobre a irmã (usuária):**

| # | Resposta |
| --- | --- |
| U1 | **Cegueira total** (não percebe luz/vulto). Simplifica: foco 100% em áudio, sem preocupação com contraste visual. |
| U2 | Usa **só bengala**, sem cão-guia. **Não entende posição de relógio** → direção falada sempre como "esquerda / frente / direita" (RN-18). |
| U3 | **Esbarra mais na altura da cabeça/peito e em pessoas.** Confirma a aposta do plano: o ponto cego da bengala é exatamente o alvo. "Pessoa" já é classe nativa do COCO — ajuda desde a Fase 1. |
| U4 | **Todo lugar, todo horário**, sempre **acompanhada**. Não dá pra restringir a um ambiente único como sugerido na Fase 0 original — o sistema precisa generalizar. Meta de longo prazo do projeto: dar autonomia pra ela andar sozinha. |
| U5 | Preferência inicial: **bipe** (não voz). É palpite dele, não validado com ela — confirmar na Fase 0.5 antes de construir o resto. |
| U6 (=U11) | Disponibilidade: **2x/semana, ~6h no total.** Define o ritmo de teste das próximas fases. |
| U7 | **Tem fone com fio com botão** e topa usar em **um ouvido só** (RN-05). Serve para o áudio e para o controle (RN-36). Fone de condução óssea entra na lista do patrocínio. |
| U9 | **Usa TalkBack** (nenhum app de acessibilidade citado). O app precisa ser 100% navegável com TalkBack, e o áudio dele não pode ser abafado pela fala do TalkBack (RN-35). Celular dela: **Redmi 13C 4G, Helio G85.** Fraco para YOLO + profundidade juntos: o perfil `celular` começa sem profundidade (igual ao notebook). É também o aparelho do teste 3b (ver D8). Celular melhor entra na lista do patrocínio. |
| U8 (parcial) | **Nos testes, celular preso no peito sem problema** (suporte improvisado, R$ 0). No **uso diário** a discrição pesa: a forma final (bolso da camisa, alça da bolsa, óculos) fica em aberto para a Fase 5/6. Qualquer posição nova é só calibração (`camera.altura_m`, inclinação) + acelerômetro — a arquitetura já cobre. |
| U10 | Uso de **no máximo 30 min seguidos**. RN-26 ajustada: sessão de 30 min com ≤ 20% de bateria e sem superaquecer. Modo de economia vira opcional. |
| U12 | **Autoriza gravar** os trajetos com o celular no peito (RN-29: só em modo explícito, sem terceiros identificáveis). Publicar trecho exige OK por vídeo. |
| U13 | **Altura 1,55 m, ombro 1,25 m.** Faixas de altura: chão < 0,50 · tronco 0,50–1,25 · cabeça 1,25–1,70 (1,55 + 0,15 de margem). Acima de 1,70 ela passa por baixo → ignorado. Câmera no peito fica a ~1,12 m. |

**Sobre você (escopo e recursos):**

| # | Resposta |
| --- | --- |
| D1 | **Portfólio é a prioridade**, mas quer que funcione de verdade também. Estratégia: Marco A (Fase 1) cobre portfólio rápido; Marco B (Fase 3, estudo de caso real) serve os dois objetivos ao mesmo tempo sem sacrificar nenhum. |
| D2 | **Sem prazo fixo.** Dá folga pra fazer as Fases 3/4 com calma em vez de correr só pro Marco A. |
| D3 | **R$ 0 de orçamento agora.** Fases 1-2 rodam 100% em software (webcam/celular, sem sensor). Sensor ToF/Pi só entram na Fase 5, com patrocínio. |
| D4 | **Sem GPU NVIDIA.** YOLO26n roda tranquilo em CPU pra inferência. Treino de modelo próprio (Fase 4) vai pro Colab/Kaggle. |
| D5 | **Python muito bom** (Fases 1-2 sem gargalo) · **ML nunca fez** (curva de aprendizado na Fase 4, mas API do Ultralytics é de alto nível) · **Flutter bom** (encaixa direto na Fase 5, celular Android). |
| D6 | **Repositório público no GitHub, confirmado.** Atende a licença AGPL (RN-31) e serve pro portfólio. |
| D7 | **Prefere não rotular do zero se der.** Estratégia da Fase 4: priorizar datasets públicos prontos (Roboflow Universe tem "sidewalk/street obstacles"), rotular só o que faltar — provavelmente itens nicho como orelhão, porta de armário. |
| D8 | Câmera da DroidCam = **Redmi 13C, mesmo modelo do app**. Há **2 aparelhos iguais em casa**: um fica para desenvolvimento, o dela segue no uso diário (sem precisar emprestar). Hardware continua R$ 0. Não há celular mais forte: o obstáculo genérico na cabeça, no celular, depende do spike S4; se falhar, só roda no PC até vir patrocínio. |
| D9 | Processador **Ryzen 5 5600GT** (6 núcleos, vídeo integrado Vega 7). Inferência via ONNX Runtime; DirectML no Vega 7 como opção para o modelo de profundidade. |
| D10 | Máquina principal (Ryzen) é **PC de mesa**. Portátil disponível: **notebook fraco, Intel i3 de 7ª geração** (2 núcleos). **Decidido (opção A):** teste 3a com notebook na mochila (só pessoas/objetos COCO), depois app de celular, depois teste 3b completo. Ver ordem de execução na seção 5. |

**Ainda em aberto (não bloqueia nada até a Fase 5):** U8 — forma discreta para o uso diário. Todas as outras perguntas de usuária e de escopo estão respondidas. As perguntas técnicas (T1–T5) e os spikes (S1–S5) são respondidos por experimento, nas fases indicadas.

## 2. O que muda em relação ao plano original (e por quê)

| # | Plano original | Problema | Ajuste |
| --- | --- | --- | --- |
| 1 | Falar "cadeira a 2 metros" | Falar essa frase leva ~1,5 s. Andando a ~1 m/s, ela já avançou 1,5 m quando a frase termina. Voz é lenta demais para alerta. | **Alerta = som curto (bipe) que muda com a distância, tipo sensor de ré. Voz só para dizer o que é, e sem pressa.** |
| 2 | Objeto mais próximo = maior bounding box | Uma pessoa a 4 m pode ter caixa maior que uma garrafa a 50 cm. Um objeto grande ao lado não bloqueia o caminho. | Usar distância real + **corredor de caminhada** (só importa o que está no caminho dela). |
| 3 | Classes do COCO | O COCO não tem poste, degrau, meio-fio, buraco, porta aberta, galho, orelhão nem parede. Esses são os obstáculos que mais machucam. | Fase dedicada a treinar essas classes (fine-tuning). O COCO serve só para o MVP. |
| 4 | MiDaS para medir distância | O MiDaS dá profundidade **relativa** (o que está mais perto), não metros. | Comparar opções: **YOLO26n-depth** (já sai em metros), Depth Anything V2, sensor ToF/ultrassom ou câmera estéreo. A escolha sai de teste com trena (spike S2). |
| 5 | gTTS como opção de voz | O gTTS precisa de internet. Na rua a conexão cai. | Tudo offline: áudios **pré-gravados** para o vocabulário fixo + Piper TTS (tem voz pt-BR) para o resto. |
| 6 | Testar com ela antes de ter distância | Para obstáculos, um teste sem distância mede quase nada. | Testar **só o design de áudio** com ela bem cedo (sem sistema, só tocando os sons), e fazer o teste real depois da distância. |
| 7 | ESP32-CAM / Pi Zero nos óculos | O ESP32-CAM não roda YOLO. O Pi Zero 2W roda a ~1 fps ou menos, inútil para andar. | Óculos viram meta opcional. Caminho mais realista: **celular preso no peito** ou Pi 5 + acelerador. |
| 8 | Sem aviso de falha | Silêncio pode significar "nada à frente" ou "o sistema travou". Confundir os dois é perigoso. | Regra de fail-safe com som próprio para falha (RN-04). |

**Onde o projeto agrega de verdade:** a bengala detecta bem o que está no chão, mas **não pega obstáculo na altura do peito e da cabeça** (galho, orelhão, placa, toldo, porta de armário aberta, retrovisor de caminhão). Uma câmera na altura do peito ou da cabeça cobre exatamente esse ponto cego. Vale focar nisso.

## 3. Regras de Negócio (RN)

Os valores entre colchetes são **iniciais**: calibrar nos testes e confirmar com ela.

### 3.1 Segurança (inegociáveis)

| ID | Regra |
| --- | --- |
| RN-01 | O sistema é **complementar** à bengala ou ao cão-guia. Toda documentação e todo teste partem disso. |
| RN-02 | O sistema **nunca** diz "caminho livre" nem nada parecido. Não detectar um obstáculo não significa que ele não existe. |
| RN-03 | Latência de ponta a ponta (captura da imagem → começo do som) ≤ [300 ms] para alertas na zona "perto". Medida e registrada a cada versão. |
| RN-04 | **Fail-safe:** câmera travada, fps abaixo de [5], erro no modelo, sensor desconectado ou bateria crítica disparam um **som exclusivo de falha**, diferente de todos os outros, e o aviso se repete até ser resolvido. |
| RN-05 | O áudio não pode tapar os sons do ambiente: fone de condução óssea ou só um ouvido, com volume máximo limitado. Ela usa o ouvido para atravessar a rua. |
| RN-06 | Alerta de risco **interrompe** qualquer fala em andamento (preempção). A fila de mensagens descarta tudo o que tiver mais de [500 ms]: informação velha não é falada. |
| RN-07 | Nenhuma versão vai para teste com ela sem antes passar nos testes de bancada (RN-30). Teste com ela sempre com bengala e acompanhante vidente, primeiro em ambiente controlado. |

### 3.2 Detecção e relevância

| ID | Regra |
| --- | --- |
| RN-08 | **Corredor de caminhada:** só são avaliados objetos dentro de uma faixa central da imagem que corresponde à largura do corpo mais uma margem de [30 cm] de cada lado. Fora dela, nada é anunciado no modo Caminhada. |
| RN-09 | **Faixa de altura:** chão < [0,50 m] · tronco [0,50–1,25 m] · cabeça [1,25–1,70 m] (altura dela 1,55 m + 0,15 de margem). Obstáculo cuja **base** está acima de [1,70 m] é ignorado (ela passa por baixo). Tronco e cabeça têm **prioridade maior**, porque a bengala não os pega. |
| RN-10 | **Confiança mínima** por classe, com padrão de [0,5]. Classes críticas (poste, degrau, porta) podem ter limiar menor: preferimos um falso alarme a um obstáculo perdido. |
| RN-11 | **Persistência:** um objeto só é anunciado se aparecer em [3 de 5] frames seguidos. Isso corta os "fantasmas" de um único frame. |
| RN-12 | **Zonas de distância** em vez de metros exatos: Perto < [1,0 m], Atenção [1,0–2,0 m], Longe > [2,0 m]. No modo Caminhada, o Longe não é anunciado. |
| RN-13 | **Prioridade** quando há vários objetos: 1) zona mais próxima; 2) altura cabeça/peito antes de chão; 3) mais central no corredor; 4) classe mais perigosa. Só **um** alerta por vez. |
| RN-14 | **Anti-repetição por objeto:** com tracking (ID por objeto), o mesmo objeto não é anunciado de novo enquanto continuar na mesma zona. Ele volta a ser anunciado ao **se aproximar** e mudar de zona. |
| RN-15 | **Cooldown global** de [1,5 s] entre falas de voz. Os bipes de distância não entram no cooldown, porque são contínuos. |
| RN-16 | **Lista de classes relevantes:** só as classes da lista de mobilidade geram alerta. Cada uma tem um nome curto em pt-BR (ex.: "dining table" → "mesa"). As demais são ignoradas. |

### 3.3 Áudio e interação

| ID | Regra |
| --- | --- |
| RN-17 | **Dois canais:** (a) bipe cujo ritmo acelera conforme a distância diminui, para alerta imediato; (b) voz curta para dizer o que é e onde está. |
| RN-18 | **Direção:** como ela usa **fone em um ouvido só** (U7), o estéreo não serve para indicar lado. A direção vai (a) na **voz**, sempre como **"esquerda / frente / direita"** (ela **não** entende posição de relógio — confirmado em 23/09) e (b) opcionalmente no **timbre** do bipe (ex.: um som diferente para esquerda e para direita). Qual das duas funciona melhor é decidido na Fase 0.5. Estéreo volta a ser opção se um dia ela usar fone de condução óssea nos dois lados. |
| RN-19 | **Vocabulário mínimo:** a frase segue o padrão `<objeto>, <direção>` (ex.: "poste, frente"). No máximo 3 palavras por frase. |
| RN-20 | **Modos:** *Caminhada* (só obstáculos no corredor), *Explorar* (descreve o que está à frente quando ela pede) e *Silencioso* (só alertas da zona Perto). |
| RN-21 | **Controle 100% não visual:** botão físico ou gesto. Cada ação tem som de confirmação. Nenhuma função depende de olhar para uma tela. |
| RN-22 | Volume, velocidade da voz e modo ficam **salvos** entre usos. |
| RN-23 | Ao iniciar, o sistema diz "pronto" em até [10 s]. Ao desligar, toca um som de encerramento. |
| RN-24 | Bateria baixa é avisada por voz em [20%] e [10%]. |
| RN-35 | **Convivência com TalkBack:** o app é 100% navegável com TalkBack (todo controle com rótulo falado). No modo Caminhada, os alertas de obstáculo não podem ser abafados pela fala do TalkBack nem por notificações; o app sugere ligar o "Não perturbe" ao entrar no modo. |
| RN-36 | **Controle com tela apagada:** a troca de modo funciona sem tela, pelo **botão do fone com fio** (clique = alterna modo, duplo clique = repete o último alerta). Os botões de volume não servem para isso, porque com a tela apagada e o TalkBack ligado o sistema fica com eles. |

### 3.4 Operação

| ID | Regra |
| --- | --- |
| RN-25 | Funciona **100% offline**: detecção, distância e voz. |
| RN-26 | **Sessão típica de até 30 min seguidos** (U10). Nessa sessão o app deve gastar no máximo [20%] da bateria e **não pode** entrar em estrangulamento térmico (queda de fps por calor). Modo de economia (pausar quando ela está parada) é opcional, não requisito. |
| RN-27 | Iluminação: o sistema detecta quando está escuro demais para confiar na câmera e **avisa** ("pouca luz"), em vez de ficar em silêncio. |

### 3.5 Privacidade, legal e portfólio

| ID | Regra |
| --- | --- |
| RN-28 | **Nenhuma imagem é gravada** no uso normal (a LGPD protege a imagem de terceiros na rua). O log guarda só metadados: classe, zona, horário e latência. |
| RN-29 | Gravar vídeo para montar o dataset só em modo explícito, em ambiente privado ou sem terceiros identificáveis, e com consentimento dela (**dado em 22/09**). Vídeos nunca vão para o git (`data/` fica fora). **Publicar** qualquer trecho (README, portfólio, demo) exige OK dela para aquele vídeo específico. |
| RN-30 | **Critério de liberação** de cada versão, medido em vídeos gravados: recall ≥ [90%] para obstáculos no corredor na zona Perto e ≤ [1] falso alarme por minuto em cena sem obstáculo. Os números são calibrados na Fase 1. |
| RN-31 | O código usa Ultralytics, que tem licença **AGPL-3.0**: o repositório precisa ser público/open source (serve para portfólio). Uso comercial exigiria licença paga. |
| RN-32 | O README deixa claro que é um **protótipo**, não um dispositivo certificado, e que não substitui a bengala. |

### 3.6 Segurança da estimativa de distância (adicionadas com a arquitetura)

| ID | Regra |
| --- | --- |
| RN-33 | Objeto cuja caixa encosta na borda superior ou inferior da imagem é tratado como **Perto**, seja qual for a distância calculada. Objeto cortado sempre parece mais longe do que está. |
| RN-34 | Se o mapa de profundidade estiver velho (> [500 ms]), o sistema entra em modo **degradado** (só detector semântico) e toca um aviso leve de falha. |

## 4. Perguntas a responder ANTES de começar

🔴 = bloqueia o início · 🟡 = precisa estar respondida até a fase indicada · ✅ = respondida (ver seção 1.1)

### 4.1 Para a irmã (usuária)

Melhor numa conversa presencial e, se ela topar, acompanhando um trajeto real.

| # | Pergunta | Por que importa / o que muda | Quando |
| --- | --- | --- | --- |
| U1 | Cegueira total ou baixa visão? Percebe luz, vultos, contraste? | Com baixa visão, alto contraste e alertas mais leves podem bastar. Isso muda todo o design. | ✅ Cegueira total |
| U2 | Usa bengala? Cão-guia? Fez treino de orientação e mobilidade? | Define o que o sistema complementa e se ela já conhece a posição de relógio (RN-18). | ✅ Só bengala; não entende posição de relógio |
| U3 | **Em que ela mais esbarra?** Altura da cabeça/peito (galho, placa, orelhão, porta de armário) ou chão (degrau, buraco, meio-fio)? Pessoas? | Define a lista de classes (RN-16) e onde montar a câmera. É a pergunta mais importante. | ✅ Cabeça/peito + pessoas |
| U4 | Em que ambiente isso acontece? Casa, rua, trabalho/faculdade, ônibus/metrô, mercado? | Interno e externo são problemas técnicos diferentes (luz, distância, classes). Começar por um só. | ✅ Todo lugar |
| U5 | Anda sozinha nesses lugares ou acompanhada? Em que horário (luz do dia, noite)? | Uso noturno exige outra solução (RN-27, sensor ativo). | ✅ Sempre acompanhada, todo horário |
| U6 | Prefere bipe, voz, vibração ou uma mistura? Quanto de "falação" ela aguenta antes de desligar? | A fadiga de alertas é o principal motivo de abandono desse tipo de dispositivo. | ✅ Bipe (palpite — validar na Fase 0.5) |
| U7 | Topa usar fone? Qual tipo (condução óssea, um ouvido)? | RN-05. O fone de condução óssea custa ~R$ 150–400. Na 3a é fone com fio, em um ouvido. | ✅ Tem fone com fio com botão, topa um ouvido só. Condução óssea fica para o patrocínio |
| U8 | Onde levaria o dispositivo: celular no peito, cordão no pescoço, óculos, cinto? Se preocupa com aparência ou com chamar atenção? | Define a forma final. Estigma social derruba a adoção. | 🟡 Parcial: **nos testes, celular no peito sem problema**. No uso diário a discrição importa — forma final em aberto (Fase 5/6) |
| U9 | Qual celular ela usa (Android ou iPhone)? Usa TalkBack/VoiceOver? Já usa Seeing AI, Lookout, Be My Eyes ou Envision? | Define a plataforma da Fase 5 e mostra o que ela já tem, para não reinventar. | ✅ **Redmi 13C 4G, Helio G85 (fraco)** · **usa TalkBack** · nenhum app de acessibilidade citado |
| U10 | Por quanto tempo seguido usaria por dia? | Autonomia de bateria (RN-26). | ✅ No máximo 30 min seguidos |
| U11 | Quanto tempo ela tem para testar? Com que frequência? | Define o ritmo das fases de teste. | ✅ 2x/semana, ~6h no total |
| U12 | Autoriza gravar vídeos dos trajetos (sem terceiros) para treinar o modelo? | RN-29. Sem vídeos reais, o fine-tuning fica fraco. Agora também alimenta a avaliação da Fase 1 e a demo de patrocínio. | ✅ Autorizado (nas condições da RN-29) |
| U13 | Qual a altura dela? (e, se possível, a altura do ombro) | Define as faixas chão/tronco/cabeça (RN-09) e onde/como inclinar a câmera. | ✅ 1,55 m, ombro 1,25 m |

### 4.2 Para você (escopo e recursos)

| # | Pergunta | Por que importa | Quando |
| --- | --- | --- | --- |
| D1 | **Portfólio ou uso real no dia a dia?** Se for os dois, qual vence quando houver conflito? | Portfólio pede demo bonita e métricas. Uso real pede robustez, bateria e ergonomia. Isso muda prazos e o que cortar. | ✅ Portfólio > uso real, mas quer que funcione |
| D2 | Tem prazo (processo seletivo, fim de semestre)? | Pode antecipar a entrega do portfólio (ver marcos na seção 6). | ✅ Sem prazo |
| D3 | Orçamento para hardware? | Sensor ToF: ~R$ 50. OAK-D Lite: ~R$ 1.200+. Pi 5 + AI Kit: ~R$ 1.300+. | ✅ R$ 0 agora, patrocínio possível depois |
| D4 | O notebook tem GPU NVIDIA? | Sem GPU, o Depth Anything roda devagar e o fine-tuning vai para o Colab/Kaggle (GPU grátis com limite). | ✅ Sem GPU |
| D5 | Qual a sua experiência com Python, OpenCV, treino de modelo e Android/Flutter? | Muda a estimativa das Fases 4 e 5. | ✅ Python forte, ML zero, Flutter forte |
| D6 | Repositório público no GitHub? | A AGPL exige código aberto (RN-31). Para portfólio isso é bom. | ✅ Sim |
| D7 | Topa rotular ~500–1.500 imagens? (~10–20 h de trabalho manual) | É o custo real da Fase 4. | ✅ Prefere dataset pronto, rotula só o que faltar |

### 4.3 Técnicas (decididas por experimento, não por opinião)

| # | Pergunta | Como decidir | Fase |
| --- | --- | --- | --- |
| T1 | Como medir distância: bbox + altura conhecida, YOLO26n-depth, Depth Anything V2, sensor ToF/ultrassom ou câmera estéreo? | Benchmark: 20 posições medidas com trena, comparando erro e fps de cada opção. | 2 |
| T2 | Com que resolução de entrada o YOLO mantém ≥ 10 fps no hardware final (320 ou 640)? | Medir o fps × recall nos vídeos de teste. | 1 e 5 |
| T3 | Onde montar a câmera: peito ou cabeça? | A cabeça segue o olhar, mas balança. O peito é estável e segue o corpo. Testar os dois. | 3 |
| T4 | Superfície de vidro (porta, vitrine) é detectável? | Câmera e ToF falham com vidro. O ultrassom costuma pegar. Testar. | 2 |
| T5 | Degrau descendo e buraco (desnível negativo): detectar com profundidade ou deixar para a bengala? | Provavelmente fora do escopo v1, e isso deve estar documentado. | 2 |

## 5. Fases revisadas

Estimativas com ~10 h/semana. O total até a Fase 5 fica em **~5–7 meses**.

**Ordem de execução (decidida em 22/09, opção A):** os números das fases são identificadores, não a ordem.

```text
0 → 0.5 → 1 → 2 → 3a (notebook i3) → 5 (app celular) → 3b (celular) → 4 (fine-tuning) → 6 (óculos, opcional)
```

Motivo: a máquina forte (Ryzen) é PC de mesa e o único portátil é um i3 de 7ª geração, que roda o YOLO mas não o modelo de profundidade. O teste 3a com o notebook traz o feedback dela cedo (pessoas e objetos conhecidos, bipes, incômodo). O app de celular vem antes do fine-tuning porque é ele que habilita o teste completo (3b), com obstáculo genérico na altura da cabeça.

### Fase 0 — Descoberta (1–2 semanas)

- Conversa estruturada com ela usando as perguntas U1–U12.
- Se ela topar: acompanhar 1–2 trajetos reais e anotar **cada** esbarrão ou quase-esbarrão (o que foi, a altura, o ambiente).
- Pesquisar os apps que ela já usa ou pode usar, para não duplicar funções.
- **Saída:** top 10 obstáculos prioritários, ambiente inicial (interno ou externo), respostas 🔴 fechadas.

### Fase 0.5 — Teste de áudio "de mentira" (1 semana, sem código de visão)

- Montar um script que só toca os sons, **em um fone só** (como ela vai usar): bipes com ritmos e tons diferentes, as opções A (direção na voz) e B (direção no timbre) da Arquitetura seção 5.3, e frases curtas.
- Ela avalia se entende, se incomoda e o que prefere (U6, RN-17 a RN-19).
- É barato e evita construir um sistema inteiro com uma interface que ela vai rejeitar.
- **Saída:** design de áudio aprovado.

### Fase 1 — Protótipo de bancada (3–4 semanas)

- **Câmera: celular em retrato preso no peito, via DroidCam** (grátis), em vez da webcam do notebook. Motivo na Arquitetura, seção 4.2 (campo de visão). De quebra, os dados e a calibração já ficam parecidos com a Fase 5.
- **YOLO26n** (Ultralytics, jan/2026), pré-treinado no COCO: ~31% mais rápido em CPU que o YOLO11n e sem NMS (ADR-015).
- Tracking com ByteTrack (já vem no Ultralytics), corredor (RN-08), persistência (RN-11), lista de classes (RN-16).
- Áudio conforme a Fase 0.5, com clipes pré-gravados e preempção (RN-06).
- **Infra de teste:** gravar 10–15 vídeos curtos do ambiente-alvo e rotular à mão onde há obstáculo. Script de avaliação que roda o pipeline nos vídeos e mede recall, falsos alarmes/min, fps e latência.
- **Saída:** pipeline a ≥ 10 fps no notebook, com métricas de base medidas.

### Fase 2 — Distância (3–4 semanas)

- Benchmark T1 com as opções lado a lado.
- **Atualizado (orçamento R$ 0, ver Arquitetura ADR-005/006):** distância só pela câmera — geometria pinhole por classe (altura conhecida) + modelo de profundidade assíncrono (~5 Hz): **YOLO26n-depth** (metros) ou **Depth Anything V2 Small**, decidido no spike S2 (ADR-015). O mapa de profundidade também alimenta o **detector de obstáculo genérico** (galho, placa, orelhão sem precisar de classe). Sensor ToF volta como fonte extra quando houver patrocínio.
- Implementar as zonas (RN-12), a prioridade (RN-13) e as exceções RN-33/RN-34.
- Fail-safe (RN-04) e aviso de pouca luz (RN-27).
- **Saída:** a versão passa nos critérios da RN-30.

### Fase 3 — Teste com ela em ambiente controlado

Dividida em duas rodadas por causa do hardware (ver ordem de execução acima). Protocolo comum às duas:

- Um corredor em casa com 5–8 obstáculos posicionados, ela sempre com a bengala e acompanhante vidente (RN-07).
- Rodadas comparativas: só bengala × bengala + sistema.
- Medir: toques ou colisões, tempo do percurso, alertas falsos e opinião dela (questionário curto, ex.: SUS adaptado).
- Relatório de cada sessão em `docs/testes-campo/`.

#### Fase 3a — Notebook na mochila (2 semanas, logo após a Fase 2)

- **Montagem:** notebook i3 na mochila · celular no peito ligado por **cabo USB** (DroidCam USB, menos atraso que Wi-Fi) · **fone com fio** em um ouvido só. Nada de Bluetooth (atraso extra).
- **Perfil `notebook`:** YOLO via **OpenVINO** (i3 é Intel) a 320 px, distância só por pinhole, **profundidade desligada** → sem obstáculo genérico. Supervisor não trata isso como falha (é o perfil, não um defeito).
- **Obstáculos do teste:** só **pessoas e objetos do COCO** (cadeira, mesa, bicicleta etc.). Obstáculo genérico na altura da cabeça **não** é testado aqui, e isso é dito a ela antes.
- **Foco:** validar os bipes em uso real, a fadiga de alertas, a persistência e o cooldown; calibrar parâmetros.
- Antes: spike S1b (fps no i3) e checar se a bateria do notebook aguenta a sessão.
- **Saída:** parâmetros de áudio e relevância calibrados; lista do que incomodou.

#### Fase 3b — Celular (2 semanas, depois da Fase 5)

- Sistema completo no celular: YOLO + profundidade + obstáculo genérico.
- Inclui obstáculos na **altura da cabeça** (galho simulado, placa, porta de armário aberta).
- Rodada extra: câmera no peito × na cabeça (decisão T3).
- **Saída:** parâmetros finais calibrados e decisão T3.

### Fase 4 — Obstáculos fora do COCO (1–6 semanas · executada depois da 3b)

- **Atualizado:** com o detector de obstáculo genérico da Fase 2, a segurança já não depende desta fase. Aqui o objetivo é **dar nome** ao que hoje é anunciado como "obstáculo".
- Classes-alvo vindas da Fase 0 (provável: poste, degrau, porta aberta, galho, placa, lixeira, orelhão, meio-fio).
- **Passo 1 — sem treinar (atualizado 23/09):** o spike S6 (Fase 2) já terá medido o **YOLOE-26** com essas classes escritas como texto. Classe que o YOLOE acha bem nos vídeos dela entra direto, exportada com as classes congeladas. Se todas passarem, a Fase 4 termina aqui (~1 semana).
- **Passo 2 — só o que sobrar:** fine-tuning com o dataset **ROD** (24 mil imagens de calçada, 25 classes incluindo árvore, poste, placa de trânsito, escada e lixeira; licença MIT) + fotos próprias (RN-29). Rotular à mão só o que nenhum dataset cobre (D7). Detalhes em [referencias.md](referencias.md).
- Treino no Colab/Kaggle e comparação com o modelo base nos mesmos vídeos de teste.
- **Saída:** recall melhor nas classes críticas, com o mínimo de rotulagem.

### Fase 5 — Portabilidade (4–8 semanas · executada logo após a 3a, antes da 3b e da 4)

| Opção | Prós | Contras | Custo aprox. |
| --- | --- | --- | --- |
| **Celular Android no peito** (TFLite/NCNN) | Já tem câmera, bateria, TTS e acessibilidade, e ela já carrega um | Aquece; drena a bateria do celular dela; exige app nativo/Flutter | R$ 0–100 (suporte de peito) |
| Raspberry Pi 5 + AI Kit (Hailo) + câmera + power bank | 30+ fps; dá para ligar sensor ToF direto | Peso, fios, montagem | ~R$ 1.300+ |
| OAK-D Lite (estéreo + IA embarcada) + Pi ou notebook | Distância real e detecção na própria câmera | Caro, volumoso | ~R$ 1.200+ |

- Recomendação inicial: **celular**, se o Android dela aguentar. Se não, **Pi 5 + sensor ToF**.
- **Atualizado:** app **100% Flutter/Dart** (câmera, inferência LiteRT via `tflite_flutter` em isolate, áudio, núcleo portado e validado pelos mesmos traces do Python). Kotlin só como plano B pontual se um spike falhar. Celular dela: **Redmi 13C 4G (Helio G85)** — fraco para rodar YOLO + profundidade juntos (Arquitetura, seção 11.1). Detalhes e spikes S3–S5 na Arquitetura, seção 11.
- **Saída:** uso andando, sem notebook, por ≥ 30 min seguidos.
- **Forma de carregar (U8):** nos testes, celular no peito. Para o uso diário ela quer algo **discreto**: testar com ela 2–3 posições (bolso da camisa com a câmera para fora, alça da bolsa, cordão curto) medindo o que cada uma perde de campo de visão e estabilidade. Óculos continuam na Fase 6.

### Fase 6 — Óculos (opcional)

- Só se a Fase 3b mostrar que a cabeça é melhor que o peito.
- Caminho viável: câmera pequena na armação, **processamento fora dela** (celular ou Pi no bolso/cinto). O ESP32-CAM só serve para transmitir, com latência maior (conferir a RN-03).

## 6. Marcos de portfólio (se o prazo apertar, D2)

- **Marco A (fim da Fase 1):** demo em vídeo + README com métricas. Já é um projeto apresentável.
- **Demo para patrocínio (fim da Fase 2):** PC rodando o pipeline completo, com obstáculo genérico na cabeça, sobre vídeos gravados com o Redmi no peito dela. Mostra o sistema inteiro e o que falta de hardware.
- **Marco B (fim da Fase 3a):** primeiro estudo de caso com usuária real, métricas antes/depois e decisões de design justificadas. É o que diferencia de "mais um projeto de YOLO".
- **Marco C (fim da Fase 3b):** app de celular funcionando com ela, estudo de caso completo (inclui obstáculo de cabeça).
- **Marco D (Fase 4):** modelo próprio treinado.

## 7. Riscos

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Falso negativo causa uma batida | Alto (físico) | RN-01, RN-02, RN-07; bengala sempre |
| Fadiga de alertas faz ela desligar o sistema | Alto (abandono) | Fase 0.5, RN-11, RN-14, RN-15, modos |
| Latência alta deixa o alerta inútil | Alto | Bipe em vez de voz, RN-03 medida a cada versão |
| Profundidade monocular imprecisa | Médio | Sensor ToF/ultrassom como fonte principal de distância |
| Pouca luz ou vidro | Médio | RN-27, teste T4, sensor ativo |
| Hardware pesado ou quente | Médio | Celular primeiro; óculos opcionais |
| Redmi 13C 4G (Helio G85, confirmado) fraco para YOLO + profundidade; sem aparelho mais forte | Alto | Perfil sem profundidade; S4 testa profundidade em baixa resolução; demo no PC para buscar patrocínio (celular melhor ou ToF) |
| Xiaomi (MIUI/HyperOS) mata o app em segundo plano → sistema some em silêncio | Alto | Ajustes de bateria na instalação; spike S3; app avisa por voz ao voltar depois de ter sido morto |
| Pouca disponibilidade dela para teste | Médio | Vídeos gravados para teste de regressão; sessões curtas e agendadas |
| Escopo crescendo (OCR, produtos etc.) | Médio | Fora do escopo até a Fase 5 terminar |

## 8. Fora do escopo (v1)

- Identificar produtos e ler rótulos (OCR).
- Navegação por GPS e rotas.
- Detectar desnível negativo (degrau descendo, buraco), salvo se T5 mostrar que dá.
- Semáforo e travessia de rua. Risco alto demais para um protótipo.

## 9. Stack revisada

Arquitetura completa (componentes, threads, latência, repositório, ADRs, spikes): [Arquitetura — Detecção de Obstáculos](arquitetura.md). Modelos, datasets e projetos aproveitáveis do Hugging Face/GitHub: [referencias.md](referencias.md).

| Camada | Ferramenta | Observação |
| --- | --- | --- |
| Detecção | YOLO26n (Ultralytics); YOLOE-26 com prompts de texto para classes fora do COCO (S6) | AGPL-3.0; exporta para ONNX Runtime (PC, Ryzen) e LiteRT (celular) |
| Tracking | ByteTrack (embutido no Ultralytics) | Para a RN-14 |
| Distância | Pinhole por classe + YOLO26n-depth ou Depth Anything V2 Small (S2) | Sem hardware (R$ 0). Sensor ToF entra com patrocínio. ARCore não roda no Redmi 13C |
| Voz | Clipes pré-gerados com Piper (pt-BR, offline) | Nada de TTS em runtime |
| Ambiente Python | Python 3.12, uv, ruff, pytest, GitHub Actions | CI roda unitários + traces |
| App (Fase 5) | Flutter puro: `camera`, `tflite_flutter` (ou `ultralytics_yolo`), `flutter_soloud`, `sensors_plus`, `flutter_foreground_task`, `audio_service` (botão do fone) | Kotlin só como plano B |
| Bipes | `sounddevice` | Síntese em tempo real; direção por timbre (fone mono) ou pan (estéreo) |
| Visão auxiliar | OpenCV | |
| Avaliação | Script próprio sobre vídeos rotulados | Base da RN-30 |
| Treino | Google Colab / Kaggle | Se não houver GPU local (D4) |
| Rotulagem | Roboflow ou CVAT | Fase 4 |
