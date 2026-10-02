# Objects

## 1. Visão geral

Um **Object** representa um elemento de dados que pode ser criado, carregado, manipulado, visualizado ou utilizado pelo CranioZ durante um fluxo de trabalho.

Objects constituem os principais **elementos de domínio manipulados pelo sistema**. Eles representam informações clínicas, geométricas, anatômicas, espaciais ou derivadas produzidas durante o planejamento cirúrgico.

Exemplos de Objects incluem:

* Malhas tridimensionais;
* Imagens médicas;
* Volumes;
* Escaneamentos;
* Pontos anatômicos e cefalométricos;
* Mensurações;
* Curvas e contornos;
* Transformações espaciais;
* Regiões de interesse;
* Modelos anatômicos;
* Estruturas dentárias;
* Objetos de planejamento cirúrgico.

Um Object **não representa uma operação**. Ele representa o **dado ou entidade sobre a qual as operações podem atuar**.

Por exemplo:

* uma **Mesh** representa uma malha tridimensional;
* uma **Landmark** representa um ponto anatômico;
* uma **Measurement** representa uma mensuração;
* uma **Volume** representa um volume de imagem;
* uma **Transform** representa uma transformação espacial.

Uma Tool pode utilizar esses Objects para executar uma operação, enquanto Commands podem modificar seu estado de maneira controlada e reversível.

---

## 2. Objetivo

O sistema de Objects tem como objetivos:

* fornecer uma representação consistente dos dados manipulados pelo CranioZ;
* separar os dados de domínio da interface gráfica;
* permitir que diferentes módulos trabalhem sobre os mesmos tipos de objetos;
* estabelecer uma linguagem comum entre os módulos;
* preservar informações clínicas e geométricas relevantes;
* permitir composição entre diferentes tipos de objetos;
* facilitar persistência, serialização e recuperação dos dados;
* possibilitar a extensão do sistema por novos tipos de objetos.

Objects devem representar **conceitos do domínio**, e não detalhes específicos da interface ou de bibliotecas externas.

---

## 3. Princípios

### 3.1. Objects representam dados

Um Object representa um elemento existente no contexto do projeto.

Por exemplo:

```
Mesh
Volume
Image
Landmark
Measurement
```

Não deve ser confundido com uma operação como:

```
Segment
Register
Measure
Cut
Align
```

As operações pertencem a outras abstrações do sistema.

---

### 3.2. Objects não pertencem à interface

Objects não devem depender de elementos da interface gráfica.

Uma Mesh deve existir independentemente de:

* viewport;
* scene tree;
* toolbar;
* painel;
* widget;
* janela;
* dock.

A interface apenas apresenta e permite a interação com os Objects.

---

### 3.3. Objects devem possuir semântica de domínio

Sempre que possível, o CranioZ deve utilizar objetos que representem diretamente conceitos relevantes para cirurgia e traumatologia buco-maxilo-facial.

Por exemplo, uma estrutura óssea não deve ser tratada apenas como uma `Mesh` quando o sistema precisa reconhecer que ela representa uma mandíbula.

Assim, pode existir uma relação como:

```
Mesh
  └── AnatomicalObject
        ├── Bone
        │   ├── Maxilla
        │   └── Mandible
        └── Tooth
```

A geometria continua sendo uma malha, mas o objeto passa a possuir **semântica clínica**.

---

### 3.4. Objects podem ser derivados

Nem todo Object precisa representar diretamente um dado importado.

Alguns Objects são produzidos a partir de outros Objects.

Por exemplo:

```
Volume
    ↓
Segmentation
    ↓
Mesh
```

ou:

```
Landmark A
Landmark B
    ↓
Measurement
```

ou:

```
Mesh
Transform
    ↓
Transformed Mesh
```

Objects derivados devem manter, quando relevante, informações sobre sua origem e suas relações com outros objetos.

---

## 4. Classificação

Os Objects podem ser organizados em diferentes categorias de acordo com a natureza dos dados que representam.

Uma classificação inicial pode ser:

```
Object
├── Geometric Objects
│   ├── Mesh
│   ├── Point
│   ├── Curve
│   ├── Surface
│   └── Region
│
├── Imaging Objects
│   ├── Image
│   ├── Volume
│   └── ImageSeries
│
├── Clinical Objects
│   ├── AnatomicalObject
│   ├── Bone
│   ├── Tooth
│   └── Landmark
│
├── Measurement Objects
│   ├── Distance
│   ├── Angle
│   ├── Area
│   └── VolumeMeasurement
│
├── Planning Objects
│   ├── Osteotomy
│   ├── SurgicalGuide
│   ├── Splint
│   └── Implant
│
└── Spatial Objects
    ├── Transform
    ├── CoordinateSystem
    └── Registration
```

Essa classificação não precisa representar necessariamente uma hierarquia rígida de herança. Ela serve principalmente para organizar os conceitos do domínio.

---

## 5. Object base

Todos os Objects do CranioZ devem possuir uma abstração comum.

O Object base deve fornecer apenas características realmente comuns a todos os objetos.

Entre elas podem estar:

* identificador;
* nome;
* tipo;
* metadados;
* estado;
* visibilidade, quando aplicável;
* origem;
* relações com outros Objects;
* informações de persistência.

Um Object não deve receber características apenas porque são úteis para um determinado tipo de objeto.

Por exemplo, uma propriedade de transformação espacial não deve obrigatoriamente existir em um objeto puramente textual ou em um dado clínico que não possua representação espacial.

---

## 6. Identidade

Cada Object deve possuir um identificador único dentro do contexto em que é utilizado.

O identificador deve ser independente do nome apresentado ao usuário.

Por exemplo:

```
id: 7f2e4d...
name: "Mandible"
```

O usuário pode alterar o nome de um Object sem modificar sua identidade.

Isso permite que Objects sejam referenciados de maneira estável por:

* Commands;
* Services;
* Modules;
* Flows;
* Scene;
* Workspace;
* arquivos de projeto;
* histórico de operações.

---

## 7. Nome e metadados

Objects podem possuir informações descritivas adicionais.

Exemplo:

```
name
description
type
tags
metadata
```

Os metadados devem ser utilizados para informações auxiliares que não constituem necessariamente propriedades estruturais do domínio.

Informações clínicas ou geométricas relevantes devem, sempre que possível, possuir propriedades próprias no modelo do Object, em vez de serem armazenadas arbitrariamente em `metadata`.

---

# 8. Geometric Objects

Geometric Objects representam informações relacionadas à geometria espacial.

## 8.1. Mesh

Uma **Mesh** representa uma superfície ou geometria tridimensional discretizada.

Pode ser utilizada para representar:

* estruturas anatômicas;
* modelos dentários;
* escaneamentos;
* segmentos ósseos;
* modelos faciais;
* implantes;
* guias cirúrgicos;
* placas;
* splints;
* modelos produzidos durante o planejamento.

Uma Mesh pode conter:

* vértices;
* arestas;
* faces;
* normais;
* coordenadas de textura;
* atributos por vértice;
* atributos por face;
* sistemas de coordenadas;
* propriedades geométricas.

A implementação interna pode utilizar bibliotecas especializadas, mas o domínio não deve depender diretamente de uma implementação específica.

---

## 8.2. Point

Um **Point** representa uma posição no espaço.

Pode ser utilizado como base para:

* pontos anatômicos;
* pontos cefalométricos;
* pontos de referência;
* centros geométricos;
* pontos de controle.

Um Point representa apenas uma posição geométrica.

Quando essa posição possui significado clínico, deve ser representada por uma abstração semanticamente apropriada, como `Landmark`.

---

## 8.3. Curve

Uma **Curve** representa uma entidade geométrica linear ou paramétrica.

Pode representar:

* curvas anatômicas;
* arcos dentários;
* linhas de referência;
* trajetórias;
* contornos;
* linhas de osteotomia.

---

## 8.4. Region

Uma **Region** representa uma região espacial ou geométrica.

Pode ser utilizada para:

* regiões de interesse;
* áreas selecionadas;
* regiões anatômicas;
* regiões de recorte;
* áreas de análise.

---

# 9. Imaging Objects

Imaging Objects representam dados de imagem utilizados pelo CranioZ.

## 9.1. Image

Uma **Image** representa uma imagem digital.

Pode representar:

* radiografias;
* fotografias;
* imagens cefalométricas;
* imagens intraorais;
* imagens faciais;
* cortes individuais de exames.

Uma Image pode possuir:

* dimensões;
* resolução;
* profundidade;
* espaçamento;
* orientação;
* sistema de coordenadas;
* informações de aquisição;
* metadados.

---

## 9.2. Volume

Um **Volume** representa um conjunto tridimensional de dados de imagem organizado em uma estrutura volumétrica.

Exemplos:

* tomografia computadorizada;
* CBCT;
* ressonância magnética;
* volumes reconstruídos;
* volumes derivados.

Um Volume pode conter:

* matriz de voxels;
* dimensões;
* espaçamento;
* origem;
* orientação;
* unidade;
* informações de aquisição;
* metadados.

Um Volume pode possuir diferentes representações derivadas, como:

```
Volume
  ├── axial view
  ├── sagittal view
  └── coronal view
```

A visualização dessas representações pertence à camada de apresentação. O Volume continua sendo um objeto de domínio.

---

## 9.3. ImageSeries

Uma **ImageSeries** representa uma coleção ordenada de imagens relacionadas.

Pode ser utilizada para representar:

* séries DICOM;
* sequências de cortes;
* estudos de imagem;
* conjuntos de imagens relacionados.

Uma ImageSeries pode dar origem a um Volume quando os dados possuem informações espaciais suficientes para reconstrução volumétrica.

---

# 10. Scanning Objects

Scans representam dados obtidos por sistemas de aquisição tridimensional.

## 10.1. Scan

Um **Scan** representa um conjunto de dados produzido por um processo de escaneamento.

Exemplos:

* escaneamento intraoral;
* escaneamento facial;
* escaneamento de modelos;
* escaneamento de superfície;
* escaneamento de objetos físicos.

Um Scan pode possuir:

* geometria;
* informações de aquisição;
* resolução;
* sistema de coordenadas;
* dispositivo de aquisição;
* data de aquisição;
* metadados.

Quando o resultado do escaneamento é uma malha, o Scan pode possuir uma Mesh associada.

Isso permite distinguir:

```
Scan
  └── Mesh
```

A Mesh representa a geometria resultante, enquanto o Scan representa o **contexto de aquisição**.

---

# 11. Clinical Objects

Clinical Objects adicionam significado clínico aos dados geométricos ou de imagem.

## 11.1. AnatomicalObject

Um **AnatomicalObject** representa uma estrutura anatômica identificável.

Exemplos:

* mandíbula;
* maxila;
* zigoma;
* dentes;
* tecidos faciais.

Um AnatomicalObject pode possuir uma ou mais representações geométricas.

Por exemplo:

```
Mandible
  └── Mesh
```

Isso permite separar:

* **o que a estrutura representa**;
* **como sua geometria é representada**.

---

## 11.2. Bone

Um **Bone** representa uma estrutura óssea.

Exemplos:

* Maxilla;
* Mandible;
* Zygoma;
* Nasal bone.

Um Bone pode possuir uma ou mais Meshes associadas e informações anatômicas adicionais.

---

## 11.3. Tooth

Um **Tooth** representa uma unidade dentária.

Pode possuir:

* identificação;
* sistema de numeração;
* posição;
* orientação;
* Mesh;
* relações com outros dentes;
* informações clínicas relevantes.

---

# 12. Landmark Objects

Um **Landmark** representa um ponto de referência com significado anatômico, clínico ou cefalométrico.

Um Landmark pode possuir:

* posição tridimensional;
* nome;
* definição;
* categoria;
* estrutura anatômica associada;
* sistema de coordenadas;
* método de obtenção;
* confiança ou qualidade, quando aplicável.

Exemplos:

```
Nasion
Point A
Point B
ANS
PNS
Pogonion
Menton
```

Um Landmark é semanticamente diferente de um Point genérico.

O Point representa uma posição.

O Landmark representa uma posição **com significado clínico**.

---

# 13. Measurement Objects

Uma **Measurement** representa um resultado quantitativo obtido a partir de um ou mais Objects.

Exemplos:

* distância;
* ângulo;
* área;
* volume;
* overjet;
* overbite;
* comprimento mandibular;
* altura facial;
* medidas cefalométricas.

Uma Measurement deve manter, quando aplicável, referência aos objetos utilizados para sua obtenção.

Por exemplo:

```
Landmark A
Landmark B
    ↓
Distance Measurement
```

ou:

```
Landmark A
Landmark B
Landmark C
    ↓
Angle Measurement
```

Isso permite que a mensuração seja atualizada quando seus elementos de origem forem modificados.

---

# 14. Spatial Objects

Spatial Objects representam informações relacionadas à posição, orientação e transformação dos dados no espaço.

## 14.1. Transform

Uma **Transform** representa uma transformação espacial.

Pode representar:

* translação;
* rotação;
* escala;
* transformação rígida;
* transformação afim;
* transformação não rígida.

Transformações podem ser utilizadas para:

* registro;
* alinhamento;
* movimentação cirúrgica;
* posicionamento de modelos;
* comparação pré/pós-operatória.

---

## 14.2. CoordinateSystem

Um **CoordinateSystem** representa um sistema de coordenadas utilizado para interpretar posições e orientações.

Objects espaciais podem estar associados a diferentes sistemas de coordenadas.

O CranioZ deve evitar assumir que todos os objetos compartilham automaticamente o mesmo sistema de coordenadas.

---

# 15. Planning Objects

Planning Objects representam elementos criados durante o planejamento cirúrgico.

Exemplos:

* Osteotomy;
* SurgicalGuide;
* Splint;
* Implant;
* Plate;
* PlateElement;
* Segment;
* SurgicalPosition.

Esses Objects possuem maior semântica clínica e podem utilizar outros Objects como representação ou referência.

Por exemplo:

```
Mandible
    ├── Mesh
    └── Osteotomy
          └── SurgicalPosition
```

ou:

```
SurgicalGuide
    ├── Mesh
    ├── Target Anatomy
    └── Registration
```

Planning Objects devem permanecer separados dos mecanismos que executam as operações sobre eles.

---

# 16. Relações entre Objects

Objects podem possuir relações explícitas entre si.

Exemplos:

```
Volume → Segmentation

Segmentation → Mesh

Mesh → AnatomicalObject

Landmark → AnatomicalObject

Measurement → Landmark

Transform → Mesh

SurgicalGuide → AnatomicalObject
```

Essas relações são importantes para preservar a semântica do projeto e permitir rastreabilidade.

O sistema deve evitar duplicar dados quando uma relação entre Objects for suficiente.

---

# 17. Objects e representação

Um conceito de domínio pode possuir múltiplas representações.

Por exemplo:

```
Mandible
   ├── Mesh
   ├── Landmark Set
   └── Volume Region
```

Isso permite que uma mesma entidade clínica seja utilizada em diferentes contextos sem confundir o conceito clínico com uma determinada representação computacional.

Da mesma forma, uma Mesh pode ser utilizada para representar diferentes conceitos dependendo do contexto:

```
Mesh
  ├── AnatomicalObject
  ├── Scan
  ├── SurgicalGuide
  └── Implant
```

A Mesh, portanto, é uma representação geométrica; não necessariamente o conceito clínico em si.

---

# 18. Estado dos Objects

Objects podem possuir estado.

Exemplos:

* ativo;
* oculto;
* bloqueado;
* selecionado;
* válido;
* inválido;
* atualizado;
* desatualizado;
* derivado;
* temporário.

Entretanto, estados relacionados exclusivamente à interface devem permanecer na camada de apresentação quando não fizerem parte do domínio.

Por exemplo, a posição de um painel que exibe uma Mesh não pertence à Mesh.

---

# 19. Persistência

Objects devem ser projetados de maneira que possam ser persistidos dentro de um projeto do CranioZ.

A persistência pode envolver:

* dados estruturados;
* arquivos binários;
* arquivos DICOM;
* arquivos STL/OBJ/PLY;
* imagens;
* volumes;
* metadados;
* relações entre Objects.

O formato de persistência não deve determinar a estrutura conceitual do Object.

Por exemplo, uma Mesh pode ser armazenada como STL, mas o Object `Mesh` não deve ser definido como um "arquivo STL".

---

# 20. Objects e bibliotecas externas

Objects pertencem ao domínio do CranioZ e não devem ser definidos diretamente por bibliotecas externas.

Bibliotecas como:

* VTK;
* ITK;
* NumPy;
* Open CASCADE;
* OpenMesh;
* CGAL;
* PyDICOM;

podem fornecer mecanismos de armazenamento e processamento.

Entretanto, esses tipos devem permanecer na camada de infraestrutura ou em adaptadores apropriados.

A arquitetura deve permitir, por exemplo:

```
CranioZ Mesh
      ↓
VTK representation
```

sem transformar `vtkPolyData` na definição da Mesh do domínio.

Isso reduz o acoplamento e facilita a substituição ou combinação de tecnologias.

---

# 21. Objects e Modules

Modules podem definir e utilizar Objects relacionados às suas responsabilidades.

Por exemplo:

```
Tomography Module
    → Volume
    → Image
    → ImageSeries

Segmentation Module
    → Segmentation
    → Mesh

Cephalometry Module
    → Landmark
    → Measurement

Osteotomy Module
    → Osteotomy
    → Segment
    → SurgicalPosition
```

Entretanto, Objects fundamentais devem permanecer disponíveis para outros módulos sempre que forem conceitos compartilhados pelo sistema.

Um módulo pode **produzir, consumir ou modificar** Objects sem necessariamente ser seu proprietário exclusivo.

---

# 22. Objects e Tools

Tools representam ações disponibilizadas ao usuário.

Uma Tool pode atuar sobre um ou mais Objects.

Por exemplo:

```
Tool: Add Landmark
    → cria Landmark

Tool: Measure Distance
    → cria Measurement

Tool: Register
    → cria ou modifica Transform

Tool: Segment
    → cria Segmentation

Tool: Generate Mesh
    → cria Mesh
```

A Tool não deve incorporar a definição do Object.

A Tool utiliza os Objects como entrada, saída ou contexto da operação.

---

# 23. Objects e Commands

Quando uma operação altera um Object, essa alteração deve, quando aplicável, ser realizada por meio de um Command.

Por exemplo:

```
Command: Move Object
    → modifica Transform

Command: Rename Object
    → modifica name

Command: Add Landmark
    → cria Landmark

Command: Delete Object
    → remove Object
```

Isso permite:

* undo/redo;
* histórico;
* rastreabilidade;
* validação;
* integração com automações;
* execução por Tools;
* execução por outros sistemas, incluindo mecanismos de IA.

---

# 24. Objects e Services

Services fornecem operações complexas ou especializadas que trabalham sobre Objects.

Por exemplo:

```
RegistrationService
    Mesh + Mesh
    → Transform

MeasurementService
    Landmark + Landmark
    → Measurement

SegmentationService
    Volume
    → Segmentation

MeshBooleanService
    Mesh + Mesh
    → Mesh
```

Services não devem substituir os Objects. Eles operam sobre eles.

---

# 25. Ciclo de vida

Um Object pode passar por diferentes etapas durante sua existência:

```
Creation
    ↓
Validation
    ↓
Use
    ↓
Modification
    ↓
Derivation
    ↓
Persistence
    ↓
Removal
```

Objects derivados devem, quando necessário, manter informações sobre sua origem.

Isso é especialmente importante para dados clínicos derivados, nos quais a rastreabilidade pode ser relevante.

---

# 26. Organização conceitual

Uma possível organização geral dos Objects do CranioZ é:

```
Objects
│
├── Core
│   ├── Object
│   ├── Identifier
│   └── Metadata
│
├── Geometry
│   ├── Mesh
│   ├── Point
│   ├── Curve
│   ├── Surface
│   └── Region
│
├── Imaging
│   ├── Image
│   ├── Volume
│   └── ImageSeries
│
├── Clinical
│   ├── AnatomicalObject
│   ├── Bone
│   ├── Tooth
│   └── Landmark
│
├── Measurement
│   ├── Distance
│   ├── Angle
│   ├── Area
│   └── VolumeMeasurement
│
├── Spatial
│   ├── Transform
│   └── CoordinateSystem
│
└── Planning
    ├── Osteotomy
    ├── Segment
    ├── SurgicalGuide
    ├── Splint
    ├── Implant
    ├── Plate
    └── SurgicalPosition
```

Essa organização deve ser entendida como uma organização conceitual. A estrutura física dos arquivos pode ser ajustada conforme a evolução da arquitetura.

---

# 27. Princípio fundamental

O principal princípio para o sistema de Objects é:

> **Objects representam aquilo sobre o que o CranioZ trabalha; Tools representam aquilo que o usuário pode fazer; Commands representam alterações executáveis e reversíveis; Services representam operações especializadas sobre os dados.**

Essa separação permite que o CranioZ mantenha uma arquitetura orientada ao domínio, na qual os conceitos clínicos e geométricos permanecem independentes da interface gráfica e das bibliotecas utilizadas para processamento.
