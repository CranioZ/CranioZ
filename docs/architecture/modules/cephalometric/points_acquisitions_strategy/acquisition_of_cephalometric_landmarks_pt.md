## 1. Definir pontos prioritários
Isto diminui o custo e tempo computacional além de reduzir a quantidade de pontos para o usuário refinar.

## 2. Definir a origem dos dados
Fonte 1: Segmentação da pele da face da TC (via threshoold ou automática) ou escaneamento da face.
Fonte 2: Segmentação óssea da face da TC (via threshoold ou automática).
Fonte 3: Arcadas dentárias. Segmentação óssea da face da TC (via threshoold ou automática) ou escaneamentos intrabucais.


## 3. Registro da pele e arcadas dentárias

* Registrar o escaneamento intraoral sobre a TC por pontos de referência estáveis (superfícies dentárias não afetadas por artefato) seguido de refinamento por ICP.
* Registrar o escaneamento facial sobre a pele da TC usando regiões estáveis (testa, nariz, região zigomática), evitando boca e mandíbula.
* Registrar a posição natural da cabeça, se disponível, porque ela afeta a interpretação dos planos de referência.

## 4. Geração e preparo da malha

1. Segmentação em estruturas separadas
2. Limpeza: remover componentes soltos, fechar buracos, corrigir normais.
3. Suavização e decimação controladas, pois suavizar demais apaga os extremos geométricos dos quais dependem vários pontos.
4. Sistema de coordenadas canônico:
* Estimar o plano sagital mediano por simetria da malha, refinado por pontos mediais.
* Estabelecer um plano horizontal (Frankfurt, Plano de Camper ou Posição orientada da cabeça, conforme o protocolo).
* Isso reduz muito a variabilidade de pose, simplifica o aprendizado e é a base das medidas clínicas.

## 5. Detecção em camadas

### Camada A: localização grosseira (robusta, global)
Regressão de mapas de calor 3D (heatmap) sobre a TC reduzida ou sobre renderizações multivista da malha, ou redes em nuvem de pontos/malha.
Objetivo: obter uma região provável para cada ponto, com tolerância de poucos milímetros, mesmo em anatomias atípicas.


### Camada B: refinamento local (precisa)
Aqui as famílias de estratégias se complementam:

#### Tipo de ponto	Estratégia preferida
1. Extremos geométricos (Pog, Me, ANS, Pn)	Análise de curvatura e extremos direcionais na vizinhança da estimativa grosseira
2. Pontos de máxima concavidade (A, B)	Análise de perfil sagital e curvatura local no plano mediano
3. Pontos internos (S, Co, Ar, Ba)	Patches de TC em alta resolução com rede de refinamento volumétrico
4. Pontos dentários	Modelo do dente segmentado: eixo longo, borda incisal, cúspides e ápice calculados geometricamente
5. Tecido mole	Malha facial: curvatura e perfil, mais fusão com o escaneamento facial
6. Pontos construídos (Go, Po)	Calculados a partir de outros pontos e planos, não detectados diretamente
7. Camada C: prior de forma e consistência
8. Modelo estatístico de forma (ou atlas com registro não rígido e votação multi-atlas) para verificar a plausibilidade do conjunto.
9. Restrições geométricas: simetria bilateral aproximada, razões e distâncias plausíveis, ordem anatômica dos pontos.
Pontos fora do esperado são reestimados com o prior ou sinalizados.

