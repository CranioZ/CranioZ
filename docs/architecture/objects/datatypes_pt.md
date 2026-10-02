# Datatypes

## 1. Visão geral

Um **Datatype** define a estrutura fundamental dos dados manipulados pelo CranioZ.

Ele responde à pergunta:

> **Como este dado é representado?**

O Datatype não define, por si só, o significado clínico do dado.

Por exemplo, uma superfície triangular carregada a partir de um arquivo STL é uma **Mesh**. Ela possui vértices, faces, normais e outras informações geométricas, mas o Datatype `Mesh` não sabe se essa superfície representa uma mandíbula, uma maxila, um dente, uma placa de osteossíntese ou um guia cirúrgico.

Essa interpretação é atribuída por meio de um **Semantic Type**.

A arquitetura utiliza, portanto, uma separação entre:

```text
Object
├── Datatype
├── Semantic Type
├── Components
├── Capabilities
└── Relationships
```

Cada conceito possui uma responsabilidade específica:

```text
Datatype      → como o dado é estruturado
Semantic      → o que o dado representa
Components    → o que o objeto possui
Capabilities  → o que o objeto pode fazer
Relationships → como se relaciona com outros objetos
```

Essa separação permite que os Datatypes permaneçam genéricos e reutilizáveis, enquanto a semântica clínica determina como cada Object será utilizado pelo CranioZ.

---

# 2. Datatype × Semantic Type

Um **Datatype** representa a estrutura dos dados.

Um **Semantic Type** representa o significado atribuído a esses dados.

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

Assim, diferentes Objects podem compartilhar o mesmo Datatype:

```text
Mesh
├── Anatomy.Bone.Mandible
├── Anatomy.Bone.Maxilla
├── Anatomy.Tooth
├── Anatomy.Face
├── Implant.Dental
├── Implant.OsteosynthesisPlate
└── Surgical.SurgicalGuide
```

O Datatype continua sendo `Mesh` em todos esses casos.

O que muda é a semântica atribuída ao Object e, consequentemente, as Components e Capabilities que podem ser associadas ou disponibilizadas.

---

# 3. Objects e Datatypes

O Datatype não é o Object.

Um Object é a entidade manipulável pelo CranioZ e pode utilizar um Datatype como sua representação estrutural.

Conceitualmente:

```text
Object
├── id
├── name
├── datatype
├── semantic_type
├── components
├── state
└── relationships
```

Por exemplo:

```text
Object
├── Datatype: Mesh
├── Semantic Type: Anatomy.Bone.Mandible
└── Components:
    └── Transform
```

Nesse caso, `Mesh` define a estrutura geométrica, enquanto `Mandible` define o significado clínico.

Essa distinção evita que o sistema precise criar classes específicas para cada combinação possível.

Em vez de:

```text
MandibleMesh
OrthognathicMandibleMesh
SegmentedMandibleMesh
MandibleWithLandmarks
MandibleWithImplantPlanning
```

o CranioZ pode representar essas combinações por composição:

```text
Object
├── Datatype: Mesh
├── Semantic: Mandible
├── Components:
│   ├── Transform
│   ├── Landmark
│   └── Planning
└── Capabilities:
    ├── Osteotomy
    ├── Landmark
    └── OrthognathicMovement
```

---

# 4. Datatypes fundamentais

Os Datatypes fundamentais representam estruturas de dados genéricas utilizadas pelo sistema.

Eles devem permanecer independentes da semântica clínica sempre que possível.

Os principais Datatypes previstos são:

```text
Mesh
Volume
Image2D
Curve
Point
PointCloud
ROI
```

Novos Datatypes podem ser adicionados conforme as necessidades do sistema.

---

# 5. Mesh

`Mesh` representa uma geometria poligonal tridimensional.

Uma Mesh pode conter:

* vértices;
* arestas;
* faces;
* normais;
* atributos por vértice;
* atributos por face;
* informações topológicas;
* atributos geométricos adicionais.

Formatos de entrada e saída podem incluir:

* STL;
* OBJ;
* PLY;
* VTK;
* outros formatos suportados pelos adaptadores de infraestrutura.

A `Mesh` é um Datatype genérico.

Ela não deve possuir conhecimento específico sobre:

* mandíbula;
* maxila;
* dentes;
* placas;
* parafusos;
* implantes;
* guias cirúrgicas.

Essas classificações pertencem ao sistema de **Semantics**.

Exemplo:

```text
Object
├── Datatype: Mesh
└── Semantic Type: Anatomy.Bone.Mandible
```

ou:

```text
Object
├── Datatype: Mesh
└── Semantic Type: Implant.OsteosynthesisPlate
```

As operações geométricas fundamentais sobre Mesh são disponibilizadas pela camada de geometria.

Exemplos:

* transformação espacial;
* medição;
* interseção;
* booleano;
* corte;
* limpeza;
* suavização;
* decimação;
* cálculo de área;
* cálculo de volume;
* análise de superfície.

A possibilidade de utilizar uma determinada operação deve ser determinada pelas **Capabilities** do Object, e não simplesmente pelo Datatype.

---

# 6. Volume

`Volume` representa dados volumétricos organizados em uma matriz de voxels.

Pode ser utilizado para representar dados médicos tridimensionais, como tomografias computadorizadas.

Formatos e representações possíveis incluem:

* DICOM;
* VTI;
* NRRD;
* NIfTI;
* outros formatos suportados pelo sistema.

Um Volume pode conter:

* matriz de voxels;
* intensidade por voxel;
* dimensões;
* espaçamento;
* origem;
* orientação;
* sistema de coordenadas;
* metadados de aquisição.

O Datatype `Volume` não determina que o dado seja necessariamente uma tomografia.

Por exemplo:

```text
Object
├── Datatype: Volume
└── Semantic Type: Imaging.CT
```

A semântica poderá posteriormente determinar características específicas do dado.

As operações típicas sobre Volume incluem:

* visualização volumétrica;
* MPR;
* thresholding;
* filtragem;
* processamento de imagem;
* segmentação;
* reamostragem;
* registro;
* exportação.

Operações próprias de geometria poligonal não devem ser aplicadas diretamente a um Volume.

Quando necessário, um Volume pode participar de um fluxo que produza uma representação superficial:

```text
Volume
    ↓
Segmentation
    ↓
Surface Extraction
    ↓
Mesh
```

A conversão pode utilizar, por exemplo, Marching Cubes ou outro método apropriado.

---

# 7. Image2D

`Image2D` representa uma imagem bidimensional.

Pode utilizar formatos como:

* JPEG;
* PNG;
* TIFF;
* DICOM 2D;
* outros formatos de imagem suportados.

O Datatype `Image2D` não define se a imagem é uma fotografia, uma radiografia ou uma imagem de referência.

Essa classificação pertence ao Semantic Type.

Exemplos:

```text
Object
├── Datatype: Image2D
└── Semantic Type: Imaging.PanoramicRadiograph
```

ou:

```text
Object
├── Datatype: Image2D
└── Semantic Type: ClinicalPhotography
```

Operações genéricas de Image2D podem incluir:

* zoom;
* pan;
* rotação 2D;
* espelhamento;
* brilho;
* contraste;
* recorte;
* anotação;
* copiar;
* colar;
* exportação.

Capacidades específicas podem ser adicionadas conforme a semântica do Object.

Uma radiografia panorâmica, por exemplo, pode receber ferramentas específicas para radiografias, mas não deve receber automaticamente operações próprias de geometria tridimensional.

Assim:

```text
Image2D
+
PanoramicRadiograph
```

pode disponibilizar:

```text
Transform2D
BrightnessContrast
Crop
Annotation
CopyPaste
ExternalEditor
```

mas não:

```text
Boolean3D
MeshCut
Osteotomy
```

Essa restrição é determinada pelo sistema de Capabilities.

---

# 8. Curve

`Curve` representa uma entidade vetorial composta por pontos de controle.

Pode representar diferentes formas geométricas, como:

* linha;
* polyline;
* spline;
* curva de Bézier;
* curva paramétrica.

O Datatype `Curve` é genérico e não determina sua finalidade clínica.

Por exemplo:

```text
Object
├── Datatype: Curve
└── Semantic Type: Anatomy.Nerve.InferiorAlveolarCanal
```

ou:

```text
Object
├── Datatype: Curve
└── Semantic Type: Surgical.OsteotomyLine
```

Curves podem ser utilizadas para:

* trajetos anatômicos;
* linhas de osteotomia;
* eixos;
* contornos;
* trajetórias;
* referências geométricas;
* construção de planos.

---

# 9. Point

`Point` representa uma posição geométrica.

Sua estrutura fundamental pode ser descrita por:

```text
Point
├── x
├── y
└── z
```

O Point representa apenas uma posição no espaço.

Ele não possui necessariamente significado clínico.

Quando uma posição recebe significado anatômico ou clínico, pode ser representada por um Object com semântica de Landmark:

```text
Landmark
└── Point
```

Assim:

```text
Point
    ↓
posição geométrica
```

enquanto:

```text
Landmark
    ↓
posição geométrica
+
significado clínico
```

Essa separação é importante para que a geometria permaneça independente da aplicação clínica.

---

# 10. PointCloud

`PointCloud` representa um conjunto de pontos.

Pode ser utilizada para:

* escaneamentos;
* aquisição de superfícies;
* fotogrametria;
* reconstrução;
* registro;
* análise espacial;
* processamento geométrico.

Uma PointCloud pode possuir informações adicionais por ponto, como:

* normal;
* cor;
* intensidade;
* confiança;
* identificadores.

Assim como os demais Datatypes, seu significado clínico será determinado pelo Semantic Type.

Por exemplo:

```text
Object
├── Datatype: PointCloud
└── Semantic Type: Acquisition.FacialScan
```

---

# 11. ROI

`ROI` representa uma região geométrica ou espacial utilizada para delimitar uma área de interesse.

Pode ser representada por primitivas como:

* Box;
* Sphere;
* Cylinder;
* Region;
* outras formas geométricas.

Uma ROI pode ser utilizada para:

* limitar cálculos;
* delimitar regiões de interesse;
* criar máscaras;
* restringir operações;
* definir regiões de edição;
* controlar processos de deformação.

Uma ROI é um Datatype auxiliar. Seu significado e sua finalidade específica podem ser determinados pelo contexto e pela semântica associada.

---

# 12. Datatypes derivados

Nem todo conceito utilizado pelo CranioZ precisa necessariamente ser um Datatype primitivo.

Alguns Objects podem ser construídos a partir da composição de Datatypes fundamentais, Components e Semantics.

Por exemplo:

```text
Landmark
└── Point
```

ou:

```text
Scan
└── Mesh
```

ou:

```text
Measurement
├── ObjectRef
├── ObjectRef
└── Result
```

ou:

```text
AnatomicalRegion
└── Region of Mesh
```

Esses conceitos não devem ser automaticamente adicionados à lista de Datatypes fundamentais.

A pergunta deve ser:

> **Esse conceito define uma nova representação estrutural de dados ou representa um Object especializado construído a partir de estruturas existentes?**

Essa distinção evita que a pasta `datatypes/` se transforme em um catálogo de todos os conceitos clínicos do CranioZ.

---

# 13. Datatype e Geometry

Os Datatypes geométricos devem permanecer separados da implementação das operações geométricas.

Por exemplo:

```text
Object
    ↓
Datatype: Mesh
    ↓
Geometry
    ↓
Boolean / Cut / Remesh / Decimation
```

O Datatype `Mesh` define a estrutura dos dados.

A camada `geometry` fornece os algoritmos necessários para trabalhar com essa estrutura.

A geometria não precisa conhecer a semântica clínica do objeto.

Por exemplo, um algoritmo de booleano deve trabalhar com:

```text
Mesh + Mesh
```

e não com:

```text
Mandible + SurgicalGuide
```

A decisão de que um determinado Object pode ou não participar de uma operação deve ocorrer em uma camada superior.

Assim:

```text
Geometry
→ Como executar a operação?

Capability
→ Este Object pode executar a operação?

Tool
→ Qual ação o usuário solicita?

Command
→ Qual alteração será realizada?

Service
→ Como a operação de domínio será executada?
```

---

# 14. Datatype e Semantic Type

A atribuição de uma semântica não altera o Datatype fundamental do Object.

Por exemplo, ao classificar uma Mesh como mandíbula:

```text
Antes:

Object
├── Datatype: Mesh
└── Semantic: None
```

Depois:

```text
Object
├── Datatype: Mesh
└── Semantic: Anatomy.Bone.Mandible
```

O Object continua sendo uma Mesh.

O que mudou foi sua interpretação no domínio.

Essa alteração permite que o sistema disponibilize capacidades específicas.

Por exemplo:

```text
Mesh
+
Mandible
        ↓
Osteotomy
OrthognathicMovement
Landmark
Symmetry
```

Enquanto:

```text
Mesh
+
OsteosynthesisPlate
        ↓
PlateConfiguration
HoleEditing
ThicknessConfiguration
Placement
```

O mesmo princípio permite reutilizar o Datatype `Image2D`:

```text
Image2D
+
PanoramicRadiograph
```

ou:

```text
Image2D
+
ClinicalPhotograph
```

sem criar diferentes classes fundamentais de imagem.

---

# 15. Datatype e Components

Components adicionam características a um Object sem alterar seu Datatype.

Por exemplo:

```text
Object
├── Datatype: Mesh
├── Semantic: Mandible
└── Components:
    ├── Transform
    ├── Anatomical
    └── LandmarkSet
```

Outro Object pode utilizar o mesmo Datatype:

```text
Object
├── Datatype: Mesh
├── Semantic: SurgicalGuide
└── Components:
    ├── Transform
    └── Manufacturing
```

Dessa maneira, combinações de características não exigem novas subclasses.

---

# 16. Datatype e Capabilities

O Datatype fornece informações importantes para determinar quais operações são tecnicamente possíveis, mas não é suficiente para determinar todas as capacidades do Object.

Por exemplo:

```text
Mesh
```

pode suportar operações geométricas básicas.

Entretanto:

```text
Mesh + Mandible
```

pode receber capacidades clínicas adicionais.

A resolução pode ser representada por:

```text
Datatype
+
Semantic Type
+
Components
+
State
+
Context
    ↓
CapabilityResolver
    ↓
Capabilities
```

Portanto, uma Mesh genérica pode possuir:

```text
Transform
Measure
Boolean
Cut
```

enquanto uma Mesh semanticamente identificada como mandíbula pode adicionalmente possuir:

```text
Osteotomy
Landmark
Symmetry
OrthognathicMovement
```

---

# 17. Persistência e formatos de arquivo

O Datatype não deve ser confundido com o formato do arquivo.

Por exemplo:

```text
STL
OBJ
PLY
VTK
```

são formatos de representação ou intercâmbio.

Todos eles podem resultar em um:

```text
Mesh
```

Da mesma maneira:

```text
DICOM
NRRD
NIfTI
VTI
```

podem resultar em:

```text
Volume
```

Portanto:

```text
File Format
    ↓
Importer / Adapter
    ↓
Datatype
    ↓
Object
```

Por exemplo:

```text
mandible.stl
    ↓
STL Importer
    ↓
Mesh
    ↓
Object
    ↓
Semantic: Mandible
```

Essa separação permite que a infraestrutura de importação e exportação seja modificada sem alterar a definição dos Datatypes do domínio.

---

# 18. Validação

Cada Datatype deve possuir regras mínimas de validade estrutural.

Exemplos:

### Mesh

Uma Mesh inválida pode apresentar:

* ausência de vértices;
* faces inexistentes;
* índices inválidos;
* topologia inconsistente, quando determinada pela operação;
* dados geométricos inválidos.

### Volume

Pode ser inválido quando:

* dimensões estão ausentes;
* matriz de voxels não corresponde às dimensões declaradas;
* espaçamento é inválido;
* orientação é inconsistente.

### Image2D

Pode ser inválida quando:

* dimensões não são válidas;
* os dados de imagem estão ausentes;
* o número de canais não corresponde à representação.

### Point

Pode ser inválido quando suas coordenadas não são válidas.

A validação estrutural pertence ao Datatype.

A validação clínica pertence à Semantic Type ou aos componentes e regras de domínio correspondentes.

---

# 19. Extensibilidade

O sistema deve permitir a inclusão de novos Datatypes sem modificar o núcleo dos Objects.

Por exemplo, futuramente poderão ser adicionados:

```text
Surface
VolumeMask
TensorField
Transform
Plane
CoordinateSystem
Polyline
AnnotationData
```

Entretanto, um novo conceito só deve ser criado como Datatype quando representar uma nova estrutura fundamental de dados.

Conceitos clínicos ou funcionais devem, quando apropriado, ser representados por:

* Semantic Types;
* Components;
* Relationships;
* Objects especializados;
* Capabilities.

---

# 20. Princípio fundamental

O sistema de Datatypes do CranioZ deve seguir o princípio:

> **Datatype define a estrutura do dado, mas não seu significado clínico.**

Assim:

```text
STL
    ↓
Mesh
    ↓
Object
    ↓
Semantic: Mandible
    ↓
Components
    ↓
Capabilities
```

ou:

```text
DICOM
    ↓
Image2D
    ↓
Object
    ↓
Semantic: PanoramicRadiograph
    ↓
Components
    ↓
Capabilities
```

O Datatype permanece genérico e reutilizável.

A semântica clínica é adicionada posteriormente e determina, juntamente com Components, estado e contexto, quais comportamentos podem ser disponibilizados ao usuário.

Dessa forma, o CranioZ consegue utilizar uma mesma infraestrutura de dados para diferentes áreas da cirurgia cranio-maxilofacial sem transformar cada entidade clínica em uma classe rígida e específica.
