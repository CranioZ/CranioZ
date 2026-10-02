# Datatypes

## 1. Visão geral

Um **Datatype** define a representação estrutural dos dados manipulados pelo CranioZ.

O Datatype descreve **como um dado é representado**, mas não necessariamente **o que ele representa no domínio clínico**.

Por exemplo, uma superfície triangular armazenada em um arquivo STL é, estruturalmente, uma **Mesh**. A Mesh contém vértices, faces e informações geométricas, mas, isoladamente, não possui significado clínico.

Se o usuário importar essa Mesh e informar ao sistema que ela representa uma **Mandíbula**, o Object Manager poderá associar a ela uma semântica clínica. A partir dessa associação, o objeto poderá adquirir capacidades específicas de uma mandíbula, como osteotomias, movimentação ortognática, análise cefalométrica, definição de landmarks ou planejamento de osteossíntese.

Portanto:

```text
Datatype
    ↓
Semantic Type
    ↓
Components
    ↓
Capabilities
```

Essas quatro dimensões devem permanecer conceitualmente separadas.

---

## 2. Datatype × Semantic Type

Um **Datatype** responde:

> "Como este dado é representado?"

Um **Semantic Type** responde:

> "O que este dado representa?"

Por exemplo:

```text
Mesh
└── Semantic Type: Anatomy.Bone.Mandible
```

ou:

```text
Image2D
└── Semantic Type: Imaging.PanoramicRadiograph
```

ou:

```text
Mesh
└── Semantic Type: Implant.OsteosynthesisPlate
```

Diferentes objetos podem possuir o mesmo Datatype, mas semânticas completamente diferentes.

Por exemplo:

```text
Mesh
├── Mandible
├── Maxilla
├── Tooth
├── FacialScan
├── SurgicalGuide
├── OsteosynthesisPlate
└── DentalImplant
```

Da mesma forma, diferentes semânticas podem utilizar diferentes Datatypes.

Uma mandíbula pode inicialmente ser representada como uma `Mesh`, mas uma segmentação da mandíbula também pode existir como um `Volume` ou uma `Region`, dependendo da etapa do processamento.

Essa separação permite que o sistema mantenha a infraestrutura geométrica independente da semântica clínica.

---

## 3. Aquisição e atribuição de semântica

A importação de um arquivo não deve determinar necessariamente toda a semântica do objeto.

Por exemplo:

```text
mandible.stl
```

pode ser inicialmente carregado como:

```text
Mesh
```

O usuário ou um processo automatizado poderá posteriormente atribuir:

```text
Anatomy.Bone.Mandible
```

O objeto passa então a ser interpretado pelo sistema como uma mandíbula.

O mesmo princípio se aplica a uma imagem:

```text
panoramica.jpg
```

pode inicialmente ser carregada como:

```text
Image2D
```

e posteriormente receber:

```text
Imaging.PanoramicRadiograph
```

A semântica pode ser atribuída:

* pelo usuário;
* pelo módulo responsável pela importação;
* por metadados do arquivo;
* por um processo de reconhecimento/classificação;
* por um módulo clínico específico.

A atribuição de semântica não deve alterar a natureza fundamental do Datatype.

---

# 4. Datatypes fundamentais

Os Datatypes representam as principais estruturas de dados utilizadas pelo CranioZ.

Eles devem ser genéricos e independentes da aplicação clínica sempre que possível.

## 4.1 Volume

Representa dados volumétricos organizados em uma matriz de voxels.

Formatos e representações possíveis:

* DICOM;
* VTI;
* NRRD;
* NIfTI;
* outros formatos suportados por adaptadores de infraestrutura.

Características:

* matriz tridimensional de voxels;
* intensidade por voxel;
* espaçamento;
* origem;
* orientação;
* sistema de coordenadas;
* metadados de aquisição.

Exemplo:

```text
Volume
└── Semantic Type: Imaging.CT
```

Possíveis capacidades:

* visualização volumétrica;
* MPR;
* thresholding;
* processamento de imagem;
* segmentação;
* filtragem;
* reamostragem;
* registro;
* exportação.

Uma operação diretamente relacionada a uma Mesh, como uma edição topológica ou um booleano poligonal, não deve ser aplicada diretamente ao Volume.

Quando necessário, o Volume pode produzir uma representação superficial:

```text
Volume
    ↓
Segmentation
    ↓
Surface Extraction
    ↓
Mesh
```

---

## 4.2 Mesh

Representa uma geometria poligonal tridimensional.

Uma Mesh pode conter:

* vértices;
* arestas;
* faces;
* normais;
* atributos por vértice;
* atributos por face;
* atributos de superfície;
* informações topológicas.

Formatos comuns:

* STL;
* PLY;
* OBJ;
* VTK;
* outros formatos suportados pelo sistema.

A Mesh é gerenciada pelas ferramentas de geometria e pode receber diferentes semânticas.

Exemplos:

```text
Mesh
├── Anatomy.Bone.Cranium
├── Anatomy.Bone.Maxilla
├── Anatomy.Bone.Mandible
├── Anatomy.Tooth
├── Anatomy.Face
├── Anatomy.Eye
├── Acquisition.IntraoralScan
├── Acquisition.FacialScan
├── Implant.Dental
├── Implant.Facial
├── Implant.OsteosynthesisPlate
├── Implant.OsteosynthesisScrew
└── Surgical.SurgicalGuide
```

As operações geométricas básicas permanecem associadas à Mesh.

Exemplos:

* transformação espacial;
* medição;
* booleanos;
* interseções;
* corte;
* limpeza;
* suavização;
* decimação;
* cálculo de área;
* cálculo de volume;
* análise de superfície.

A semântica do objeto determina quais dessas operações, além de operações clínicas especializadas, são efetivamente disponibilizadas ao usuário.

---

## 4.3 Image2D

Representa uma imagem bidimensional.

Exemplos:

* JPEG;
* PNG;
* TIFF;
* DICOM 2D;
* outros formatos de imagem.

Uma Image2D pode receber diferentes semânticas.

### Imagens de referência

Utilizadas como referência visual para planejamento.

### Fotografias clínicas

Exemplos:

* fotografia frontal;
* fotografia de perfil;
* fotografia em sorriso;
* fotografia intraoral.

### Radiografias

Exemplos:

* panorâmica;
* periapical;
* telerradiografia lateral;
* telerradiografia frontal;
* PA de crânio.

### Conjuntos de fotografias

Um conjunto de fotografias pode ser utilizado como entrada para pipelines de:

* fotogrametria;
* reconstrução tridimensional;
* análise facial;
* registro.

Uma Image2D pode possuir capacidades como:

* zoom;
* pan;
* rotação 2D;
* espelhamento;
* brilho;
* contraste;
* recorte;
* anotação;
* medição 2D;
* copiar;
* colar;
* exportação;
* envio para editor externo.

Entretanto, uma Image2D não deve receber automaticamente capacidades próprias de objetos espaciais tridimensionais.

Por exemplo, uma radiografia panorâmica não deve apresentar ferramentas de:

* booleano 3D;
* corte de Mesh;
* deformação volumétrica;
* osteotomia tridimensional.

Essas restrições devem ser determinadas pelo sistema de capacidades.

---

## 4.4 Curve

Representa uma entidade vetorial composta por pontos de controle.

Subtipos possíveis:

* linha;
* polyline;
* spline;
* Bézier;
* curva paramétrica.

Curves podem ser utilizadas para:

* trajetos anatômicos;
* linhas de osteotomia;
* eixos;
* planos de referência;
* contornos;
* trajetórias de instrumentos;
* construção de geometrias.

Exemplo:

```text
Curve
└── Semantic Type: Anatomy.Nerve.InferiorAlveolarCanal
```

ou:

```text
Curve
└── Semantic Type: Surgical.OsteotomyLine
```

---

## 4.5 Point

Representa uma posição geométrica no espaço.

```text
Point
├── x
├── y
└── z
```

O Point é uma entidade geométrica e não possui necessariamente significado clínico.

Quando uma posição recebe significado clínico, pode ser representada por um objeto semântico que referencia ou contém um Point.

Por exemplo:

```text
Landmark
└── Point
```

Assim:

```text
Point
    ↓
Landmark
```

Um Point representa uma posição.

Um Landmark representa uma posição **com significado anatômico, clínico ou de planejamento**.

---

# 5. Objetos semânticos

A partir dos Datatypes básicos, o CranioZ pode construir objetos semanticamente especializados.

Exemplo:

```text
Mesh
    +
Anatomy.Bone.Mandible
    +
TransformComponent
    +
AnatomicalComponent
    ↓
Mandible Object
```

O objeto continua sendo estruturalmente uma Mesh, mas passa a ser tratado pelo sistema como uma mandíbula.

Esse mecanismo evita a criação de uma hierarquia rígida como:

```text
Mesh
└── BoneMesh
    └── MandibleMesh
        └── OrthognathicMandibleMesh
            └── SegmentedOrthognathicMandibleMesh
```

Em vez disso:

```text
Object
├── Datatype: Mesh
├── Semantic Type: Mandible
├── Components
└── Capabilities
```

Essa abordagem permite que o mesmo Datatype seja reutilizado em diferentes contextos clínicos.

---

# 6. Landmarks

Um **Landmark** representa uma marcação semântica associada a uma posição.

Exemplos:

* Nasion;
* Point A;
* Point B;
* Pogonion;
* Menton;
* Gonion;
* Porion;
* Orbitale.

Estruturalmente:

```text
Landmark
└── Point
```

O Point fornece a posição geométrica.

O Landmark fornece o significado clínico.

Isso permite utilizar landmarks em:

* análise cefalométrica;
* registro;
* alinhamento;
* orientação do paciente;
* planejamento cirúrgico;
* medições;
* construção de planos e eixos.

---

# 7. ROI e Deformer

Representam regiões ou volumes auxiliares utilizados para limitar ou controlar operações.

Exemplos geométricos:

* Box;
* Sphere;
* Cylinder;
* Region;
* Lattice;
* volume de influência.

Podem ser utilizados para:

* delimitar uma região de interesse;
* criar máscaras;
* selecionar áreas;
* controlar deformações;
* restringir cálculos;
* definir regiões de edição.

Um Deformer não representa necessariamente uma anatomia. Ele representa uma estrutura utilizada para controlar uma transformação ou deformação.

---

# 8. Measurement

Uma **Measurement** representa um resultado quantitativo derivado de outros objetos.

Exemplos:

* distância;
* ângulo;
* overjet;
* overbite;
* área;
* volume;
* espessura;
* discrepância espacial.

Uma Measurement deve manter referência aos objetos utilizados no cálculo.

```text
Measurement
├── type
├── inputs
├── result
└── definition
```

Por exemplo:

```text
Measurement
├── type: Distance
├── inputs:
│   ├── Landmark.ObjectRef
│   └── Landmark.ObjectRef
├── result:
│   ├── value
│   └── unit
└── definition:
    └── Euclidean Distance
```

Isso permite que a Measurement seja recalculada quando os objetos de origem forem modificados.

Por exemplo:

```text
Menton
    ↓
Pogonion
    ↓
Distance Measurement
```

Se o Menton for movimentado, a Measurement poderá ser marcada como `stale` e recalculada.

---

# 9. Orientations e Reference Objects

O CranioZ poderá possuir objetos destinados à orientação espacial e análise antropométrica.

Exemplos:

* Plano de Frankfurt;
* Plano de Camper;
* plano sagital;
* plano coronal;
* plano axial;
* eixos anatômicos;
* terços faciais;
* quintos faciais;
* grades de proporção;
* referências estéticas.

Esses objetos podem ser construídos a partir de:

* landmarks;
* pontos;
* curvas;
* planos;
* sistemas de coordenadas.

Por exemplo:

```text
Landmark
    ↓
Reference Plane
    ↓
Facial Analysis
```

---

# 10. Annotation

Uma **Annotation** representa uma informação descritiva associada à cena ou a um objeto.

Pode conter:

* texto livre;
* título;
* autor;
* data;
* referência a um Object;
* posição espacial;
* prioridade;
* categoria.

Exemplos:

* observação clínica;
* lembrete;
* anotação de planejamento;
* ponto de atenção;
* comentário sobre uma região anatômica.

A Annotation não deve ser confundida com o conteúdo clínico estruturado do objeto. Ela representa informação descritiva ou auxiliar.

---

# 11. Surgical Planning Objects

Alguns objetos representam estados ou resultados persistentes do planejamento cirúrgico.

Exemplos:

* segmentos ósseos;
* fragmentos osteotomizados;
* posição planejada;
* splints;
* guias cirúrgicas;
* placas;
* parafusos;
* implantes;
* reconstruções.

Por exemplo:

```text
Mandible
├── Ramus Right
├── Ramus Left
├── Mandibular Body
├── Mental Segment
└── Inferior Teeth
```

Um segmento pode possuir sua própria transformação espacial.

Isso permite representar:

```text
Mandible
    ↓
Osteotomy
    ↓
Segments
    ↓
Planned Transformations
```

A transformação aplicada ao segmento pode ser descrita por:

* translação X/Y/Z;
* rotação Pitch/Roll/Yaw;
* transformação matricial;
* sistema de coordenadas de referência.

É importante distinguir o **objeto que representa o estado planejado** da **operação que produz esse estado**.

Por exemplo:

```text
Move Mandible
```

é uma operação.

```text
Mandible Planned Transform
```

é um dado persistente do planejamento.

---

# 12. Anatomical Regions

Uma malha ou outro objeto anatômico pode possuir regiões semanticamente identificadas.

Exemplo:

```text
Facial Mesh
├── Forehead
├── Nose
├── Right Zygoma
├── Left Zygoma
├── Chin
├── Right Ear
├── Left Ear
├── Upper Lip
├── Lower Lip
└── Other Regions
```

Essas regiões podem ser representadas por:

* submalhas;
* conjuntos de faces;
* máscaras;
* labels;
* regiões derivadas.

Uma região anatômica não precisa ser necessariamente uma nova Mesh independente.

Ela pode ser uma **região semântica de uma Mesh existente**.

Isso é particularmente importante para:

* deformação de tecidos moles;
* análise facial;
* análise de vias aéreas;
* segmentação anatômica;
* cálculo volumétrico;
* simulação de tecidos.

Exemplo:

```text
Facial Mesh
    ├── Region: Nose
    ├── Region: Upper Lip
    ├── Region: Lower Lip
    └── Region: Chin
```

---

# 13. Hierarquia de Objects

Os Objects do CranioZ devem poder ser organizados em uma hierarquia espacial e semântica semelhante à encontrada em softwares de modelagem e planejamento tridimensional.

A hierarquia permite estabelecer relações de transformação entre objetos.

Exemplo:

```text
Mandible
├── Right Ramus
├── Left Ramus
├── Mandibular Body
│   └── Mental Segment
└── Lower Teeth
```

Se a Mandible for movimentada, seus descendentes poderão acompanhar essa transformação.

Se o Mandibular Body for movimentado, o Mental Segment poderá acompanhá-lo.

Isso permite representar estruturas compostas sem duplicar os dados geométricos.

---

# 14. Transformação hierárquica

Cada Object pode possuir uma transformação local em relação ao seu parent.

Conceitualmente:

```text
World
└── Mandible
    ├── Right Ramus
    ├── Left Ramus
    ├── Mandibular Body
    │   └── Mental Segment
    └── Lower Teeth
```

A transformação global de um objeto pode ser determinada pela composição das transformações de seus ancestrais.

Assim:

```text
GlobalTransform(MentalSegment)
=
GlobalTransform(Mandible)
×
LocalTransform(MandibularBody)
×
LocalTransform(MentalSegment)
```

Essa estrutura é fundamental para o planejamento ortognático, no qual diferentes segmentos podem possuir movimentos independentes ou permanecer vinculados hierarquicamente.

---

# 15. Herança, composição e referência

A arquitetura deve distinguir três relações fundamentais.

## 15.1 Herança semântica

Representa uma relação **"é um"**.

```text
Mandible
    →
Bone
    →
AnatomicalObject
    →
Object
```

Essa relação deve ser utilizada principalmente para classificação semântica e não para criar uma árvore extensa de classes concretas.

---

## 15.2 Composição

Representa uma relação **"possui"**.

```text
Mandible
◇── Mesh
```

ou:

```text
Landmark
◇── Point
```

ou:

```text
Scan
◇── Mesh
```

A composição permite separar o significado de um objeto de sua representação estrutural.

---

## 15.3 Referência

Representa uma relação entre objetos independentes.

```text
Measurement ── Landmark
```

ou:

```text
SurgicalGuide ── Mandible
```

ou:

```text
Transform ── CoordinateSystem
```

As referências devem utilizar identificadores estáveis (`ObjectRef`) quando necessário.

---

# 16. Capabilities

As capacidades determinam **quais operações são aplicáveis a um Object**.

Uma Capability não é uma Tool.

Uma Capability responde:

> "Este objeto pode participar desta classe de operação?"

Uma Tool responde:

> "Qual ação concreta o usuário pode executar?"

Por exemplo:

```text
Mandible
    ↓
Capability: Osteotomy
    ↓
Tool: Create BSSO
    ↓
Command
    ↓
Domain/Application Service
```

Uma Mesh genérica pode possuir:

```text
Transform
Measure
Boolean
Cut
```

Uma mandíbula pode possuir adicionalmente:

```text
Osteotomy
Landmark
Symmetry
OrthognathicMovement
```

Uma radiografia panorâmica pode possuir:

```text
Transform2D
WindowLevel
Annotation
Crop
ExternalEditor
```

mas não:

```text
Boolean3D
Osteotomy
MeshCut
```

---

# 17. Capability Resolution

As capacidades não devem ser determinadas exclusivamente pelo Datatype.

A capacidade disponível deve considerar, quando necessário:

```text
Datatype
+
Semantic Type
+
Components
+
Context
+
State
```

Por exemplo:

```text
Mesh
+
Mandible
+
Valid Geometry
+
Planning Context
```

pode resultar em:

```text
Transform
Measure
Boolean
Cut
Osteotomy
Landmark
Symmetry
```

Enquanto:

```text
Mesh
+
Generic Object
```

pode resultar somente em:

```text
Transform
Measure
Boolean
Cut
```

A resolução dessas capacidades deve ser realizada por um mecanismo como:

```text
CapabilityRegistry
CapabilityResolver
```

O `CapabilityRegistry` registra as capacidades disponíveis no sistema.

O `CapabilityResolver` determina quais capacidades são aplicáveis a um determinado Object em determinado contexto.

---

# 18. Object Hierarchy × Scene Graph

A hierarquia de Objects também deve ser diferenciada das relações semânticas e de dependência.

A **Scene Hierarchy** representa principalmente:

* parent;
* child;
* transformação;
* visibilidade hierárquica;
* organização espacial.

Já as relações semânticas representam:

* derivação;
* dependência;
* referência;
* associação clínica.

Por exemplo:

```text
Mandible
└── Mental Segment
```

pode representar uma relação hierárquica espacial.

Enquanto:

```text
Measurement
──→ Menton
──→ Pogonion
```

representa uma relação de referência.

E:

```text
Segmentation
──→ Volume
```

representa uma relação de derivação.

Essas relações não devem ser obrigatoriamente armazenadas em uma única estrutura.

---

# 19. Object Manager

O **Object Manager** é responsável por administrar os Objects existentes no projeto.

Entre suas responsabilidades podem estar:

* registro de Objects;
* criação;
* remoção;
* busca;
* identificação;
* atribuição de semântica;
* resolução de referências;
* gerenciamento da hierarquia;
* gerenciamento de estado;
* acesso às capacidades;
* integração com persistência.

Uma arquitetura possível é:

```text
ObjectManager
├── ObjectRegistry
├── ObjectFactory
├── ObjectTypeRegistry
├── SemanticRegistry
├── CapabilityRegistry
├── CapabilityResolver
└── ObjectRepository
```

Esses componentes não precisam necessariamente constituir classes independentes em todas as implementações. A divisão representa responsabilidades arquiteturais.

---

# 20. ObjectFactory

O `ObjectFactory` é responsável pela criação de Objects.

Pode receber informações como:

```text
Datatype
Semantic Type
Components
```

e produzir um Object válido.

Exemplo:

```text
Datatype: Mesh
Semantic: Anatomy.Bone.Mandible
```

resultando em:

```text
Object
├── id
├── datatype: Mesh
├── semantic_type: Mandible
├── components
└── state
```

A Factory permite centralizar regras de criação e evitar que módulos criem Objects diretamente de maneira inconsistente.

---

# 21. ObjectTypeRegistry

O `ObjectTypeRegistry` mantém o conhecimento sobre os Datatypes disponíveis.

Exemplo:

```text
ObjectTypeRegistry
├── Volume
├── Mesh
├── Image2D
├── Curve
├── Point
├── Landmark
├── Measurement
├── Annotation
├── ROI
└── ...
```

Ele permite que o sistema descubra quais tipos de dados são suportados e quais características estruturais cada tipo possui.

---

# 22. SemanticRegistry

O `SemanticRegistry` mantém as definições semânticas disponíveis no sistema.

Exemplo:

```text
SemanticRegistry
├── Anatomy
│   ├── Bone
│   │   ├── Cranium
│   │   ├── Maxilla
│   │   └── Mandible
│   ├── Tooth
│   ├── Face
│   └── Airway
│
├── Imaging
│   ├── CT
│   ├── PanoramicRadiograph
│   └── CephalometricRadiograph
│
├── Implant
│   ├── DentalImplant
│   ├── FacialImplant
│   └── OsteosynthesisPlate
│
└── Surgical
    ├── Osteotomy
    └── SurgicalGuide
```

A semântica pode fornecer:

* nome;
* categoria;
* relações;
* propriedades;
* componentes esperados;
* capabilities potenciais;
* regras de validação;
* metadados de apresentação.

---

# 23. Componentes

Components representam características ou dados adicionais associados a um Object.

Exemplos:

```text
Mesh
├── TransformComponent
├── RenderComponent
└── AnatomicalComponent
```

ou:

```text
Mandible
├── Mesh
├── TransformComponent
├── LandmarkSet
└── AnatomicalProperties
```

Components devem ser utilizados para composição de características, evitando a criação de classes especializadas para cada combinação possível.

Por exemplo, não é necessário criar:

```text
SegmentedMandibleWithLandmarksAndImplantPlanningMesh
```

A combinação pode ser expressa por:

```text
Mesh
+
Mandible
+
SegmentComponent
+
LandmarkComponent
+
PlanningComponent
```

---

# 24. Restrições de uso

O fato de dois Objects compartilharem o mesmo Datatype não significa que ambos devem possuir as mesmas ferramentas.

Por exemplo:

```text
Mesh + Mandible
```

e:

```text
Mesh + SurgicalGuide
```

compartilham operações geométricas básicas, mas possuem capacidades clínicas diferentes.

Da mesma maneira:

```text
Image2D + Photograph
```

e:

```text
Image2D + PanoramicRadiograph
```

compartilham operações de imagem 2D, mas podem possuir ferramentas específicas diferentes.

Portanto, as ferramentas apresentadas ao usuário devem ser resultado da resolução de capacidades e do contexto atual, e não simplesmente do Datatype.

---

# 25. Princípio geral

O sistema de Objects do CranioZ deve seguir o seguinte princípio:

> **O Datatype define a estrutura do dado. A semântica define o que o dado representa. Os Components definem características adicionais do objeto. As Capabilities definem quais operações podem ser aplicadas ao objeto.**

Dessa forma:

```text
                 ┌──────────────────┐
                 │     Datatype     │
                 │  "Como é o dado?"│
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  Semantic Type   │
                 │ "O que representa?"│
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Components    │
                 │ "O que possui?"  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   Capabilities   │
                 │  "O que pode?"   │
                 └──────────────────┘
```

O resultado é um sistema no qual a mesma estrutura de dados pode ser reutilizada em diferentes contextos clínicos sem criar uma hierarquia excessivamente rígida de classes.

A arquitetura permite, por exemplo:

```text
STL
 ↓
Mesh
 ↓
Semantic: Mandible
 ↓
Capabilities:
    Transform
    Measure
    Boolean
    Cut
    Osteotomy
    Landmark
    OrthognathicMovement
```

enquanto:

```text
Panoramic Image
 ↓
Image2D
 ↓
Semantic: PanoramicRadiograph
 ↓
Capabilities:
    Transform2D
    BrightnessContrast
    Crop
    Annotation
    CopyPaste
    ExternalEditor
```

Assim, **a geometria permanece genérica, enquanto a semântica clínica determina como aquela geometria pode ser utilizada pelo CranioZ**.
