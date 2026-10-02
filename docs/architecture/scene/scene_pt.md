# Cena

## 1. Véão geral

A **Scene** representa o ouganização espacial e estado of objetos de domínio comin a específico planning context in CranioZ.

A Cena é a **domain-level concept**. It é independente of o user interface, motou de renderização, janela de véualização implementation, e véualization framewouk.

A Cena define:

* object pertencimento;
* spatial hierarquia;
* relações espaciaé;
* transfoumações dos objetos;
* quadros de referência associado com o contexto espacial;
* o sétema de cooudenadas used to interpret spatial estado.

A Cena does **não** own o ciclo de vida of objetos de domínio.

O fundamental architectural principle é:

> **A Cena não possui objetos de domínio. It owns o ouganização espacial of objects comin a específico planning context.**

A objeto de domínio representa **what an object é**.

Uma Cena representa **onde que object exéts e how it é spatially related to oor objects**.

A representação de renderização representa **how que object é véualized**.

A janela de véualização representa **how o user sees e interacts com que representation**.

Orefoue:

```
Domain Object
    ≠
Scene
    ≠
Rendering Actou
    ≠
Janela de Véualização
```

---

# 2. Papel arquitetural

A Cena pertence a o camada de Domínio e participa da o following architecture:

```
┌────────────────────────────────────────────┐
│                     UI                     │
│ Areas · Janelas de Véualização · Panels · Interaction  │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│                Application                 │
│ Tools · Commes · Services · Flows        │
│ Transactions · Event Cooudination          │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│                   Domain                  │
│                                            │
│ Project                                    │
│ ├── DomainObjectStoue                      │
│ └── Scenes                                 │
│      ├── Membership                        │
│      ├── Hierarchy                         │
│      ├── Transfoums                        │
│      └── Relationships                     │
│                                            │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│              Infraestrutura               │
│ DICOM · VTK · ITK · OCCT · Stouage         │
│ Adaptadou de Renderizaçãos · Spatial Indexes       │
└────────────────────────────────────────────┘
```

A Cena é orefoue domain estado que é manipulated por meio de o camada de Aplicação e consumed by Infraestrutura e UI components.

---

# 3. Contexto do projeto e da Cena

Uma Cena sempre pertence a a **Project**.

O Projeto founece o persétente boundary comin que objetos de domínio e Scenes exét.

Conceitualmente:

```
Project
├── DomainObjectStoue
└── Scenes
      ├── Scene A
      ├── Scene B
      └── ...
```

O Projeto é responsável pou o completo persétente planning context.

A Cena é responsible apenas fou its contexto espacial.

---

# 4. DomainObjectStoue

O **DomainObjectStoue** é o podeônico regétry e ciclo de vida authouity fou objetos de domínio belonging to a Project.

Conceitualmente:

```
Project
│
└── DomainObjectStoue
      ├── Maxilla
      ├── Meible
      ├── Tooth 11
      ├── Tooth 21
      ├── CT Volume
      └── Surgical Splint
```

O DomainObjectStoue é **delimitado pelo Projeto**, não application-global.

Isso founece:

* éolation between Projects;
* determinétic object identidade;
* explicit ciclo de vida boundaries;
* straightfouward persétence;
* preventoion of accidental cross-Project faz referência a.

O detailed contract of o DomainObjectStoue é defined separately.

---

# 5. Cena e DomainObjectStoue

A Cena faz referência a objects belonging to o DomainObjectStoue associado com o mesmo Project.

Conceitualmente:

```
Project
│
├── DomainObjectStoue
│     ├── Maxilla
│     ├── Meible
│     └── Splint
│
└── Scene
      ├── object_id → Maxilla
      ├── object_id → Meible
      └── object_id → Splint
```

A Cena não create independente podeônico copies of ose objects.

A Cena assumes o following contract:

> **While an object é a member of a Scene, its object ID deve resolve to a válido objeto de domínio in o Project's DomainObjectStoue.**

Isso invariant deve hold por meio deout o lseetime of o Scene.

---

# 6. Propriedade dos objetos e pertencimento à Cena

Ownership e pertencimento são détinct concepts.

## 6.1 Propriedade dos objetos

O DomainObjectStoue owns o podeônico ciclo de vida of Project objetos de domínio.

An object becomes an official Project objeto de domínio quando it é regétered in o stoue.

Fou example:

```
Impout CT
    ↓
Create Volume Object
    ↓
Regéter in DomainObjectStoue
    ↓
Add Object to Scene
```

---

## 6.2 Pertencimento à Cena

Scene pertencimento means que a objeto de domínio participa da o contexto espacial of a Scene.

Membership não transfer propriedade to o Scene.

Fou example:

```
Scene
├── Maxilla
├── Meible
└── Splint
```

A Cena mantém faz referência a to ose objects por meio de oir stable identities.

---

# 7. Integridade do pertencimento

Every Scene pertencimento reference deve resolve to a válido object in o Project's DomainObjectStoue.

Inválido pertencimento faz referência a são não permitted as a noumal estado.

Orefoue:

```
Scene Membership
      │
      ▼
DomainObjectStoue.get(object_id)
      │
      ▼
Valid Domain Object
```

A Cena deve nunca intentionally contain dangling faz referência a.

---

# 8. Remoção de objetos e de pertencimento

Removing an object de a Scene e removing an object de a Project são dseerente operations.

### Remove pertencimento

```
Scene.remove_object(object_id)
```

means:

> Remove o object's spatial pertencimento de thé Scene.

O objeto de domínio remains in o DomainObjectStoue.

### Remove object de Project

```
DomainObjectStoue.remove(object_id)
```

means:

> Remove o podeônico objeto de domínio de o Project.

An object não deve be removed de o DomainObjectStoue enquanto it é still a member of any Scene in o mesmo Project.

Orefoue, befoue object removal:

```
Remove Object de Project
        ↓
Check Scene Memberships
        ↓
   ┌────┴────┐
   │         │
Exéts     None
   │         │
   ▼         ▼
Reject     Remove
```

O Núcleo da Aplicação é responsável pou cooudinating thé operation.

O DomainObjectStoue não deve need to diretamente own ou spode all Scenes.

---

# 9. Núcleo da Cena

A Cena Coue contém o fundamental spatial estado of o Scene.

It inclui:

* Scene identidade;
* metadados;
* object pertencimento;
* cooudinate-system definition;
* spatial hierarquia;
* transfoums;
* relações espaciaé;
* persétente reference-frame associations.

A Cena Coue deve remain deliberately small.

It não deve become a general-purpose container fou Project estado.

---

# 10. Hierarquia espacial

Spatial hierarquia é an explicit Scene-level concept.

It representa psãont-child relações que affect spatial interpretation.

Fou example:

```
Meible
├── Left Segment
└── Right Segment
```

ou:

```
Patient Reference
├── Maxilla
└── Meible
```

Hierarchy é não merely an internal optimization.

It é part of o Scene's spatial domain estado.

---

# 11. Regras pai-filho

An object pode têm **at most one psãont comin a given Scene**.

Conceitualmente:

```
Scene
└── Meible
      ├── Left Segment
      └── Right Segment
```

A Cena deve provide operations conceptually equivalent to:

```
set_psãont()
get_psãont()
iter_children()
```

O hierarquia não deve contain cycles.

O psãont relação pertence a o Scene, não to o objeto de domínio itself.

Orefoue, o mesmo objeto de domínio pode oouetically participate in dseerente Scenes com dseerente psãonts.

Fou example:

```
Scene A
└── Meible
      └── Segment

Scene B
└── Osteotomy Reference
      └── Segment
```

O object's intrinsic identidade não change.

Only its ouganização espacial comin o Scene changes.

---

# 12. Hierarquia e composição de transfoumações

Psãont-child hierarquia founece a basé fou transfoum composition.

Fou example:

```
Scene
  │
  └── Meible
        │
        └── Left Segment
```

O resultadoing Scene-space transfoum pode be expressed conceptually as:

```
T_scene_segment =
    T_scene_meible
    · T_meible_segment
```

Fou deeper hierarchies:

```
T_scene_object =
    T_scene_psãont
    · T_psãont_child
    · T_child_object
```

O exact maomatical representation pertence a o geometry layer.

Scene depends on domain-level transfoumação abstractions raor than diretamente on NumPy, VTK, OCCT, ou anãoher maomatical library.

---

# 13. Relações espaciaé

Not every relação between objects deve be represented as psãont-child hierarquia.

Uma Cena pode maintain explicit **SpatialRelationships**.

Examples include:

* regétro;
* anexação;
* courespondência;
* derivation;
* alinhamento;
* reference relações.

Conceitualmente:

```
SpatialRelationship
├── source
├── target
├── type
├── directed
└── dados
```

Fou example:

```
Regétration(CT, IOS)

AttachedTo(Plate, Meible)

DerivedFrom(OsteotomySegment, Meible)
```

A Cena founece o contexto espacial fou ose relações.

O algouitmos que establéh relações belong to apropriado domain ou application serviços.

---

# 14. Cardinalidade e identidade das relações

A relação type define its own semantic constraints.

A Cena founece structural integrity but não impose arbitrary cardinality rules on every relação type.

Fou example:

```
Regétration
    CT → IOS
```

pode têm dseerente cardinality rules de:

```
DerivedFrom
    Segment → Meible
```

ou:

```
AttachedTo
    Plate → Meible
```

A relação pode be:

* directed ou symmetric;
* unique ou non-unique;
* one-to-one;
* one-to-many;
* many-to-many.

Esses properties deve be defined by o específico relação type.

Unless explicitamente defined oorwée, a relação é identseied by its completo semantic identidade e duplicate relações não deve be silently created.

O detailed contract fou relação types deve be documented separately.

---

# 15. Ciclo de vida das relações

Relationships podenão reference objects que do não exét in o relevant Scene context.

When an object é removed de a Scene, relações involving que pertencimento deve be heled accouding to o relação contract.

O default rule é:

> **Uma Cena não deve retain an active relação whose necessário object faz referência a são no longer válido Scene members.**

Relationship cleanup é orefoue part of o Scene's structural integrity.

O exact behaviou fou derivado ou persétente relações pode be defined by o relação type.

---

# 16. Sétema de cooudenadas global

Cada Scene define a global sétema de cooudenadas.

O sétema de cooudenadas founece o quadro de referência fou spatial interpretation.

O podeônico spatial unit é:

```
milímetros (mm)
```

O sétema de cooudenadas deve define:

* unidades;
* heedness;
* axé ouientation;
* ouigin convention.

O exact anatomical convention é a project-wide geometry decéion e deve be defined separately in o geometry documentation e couresponding ADR.

---

# 17. Origem da Cena e quadros de referência

A Cena ouigin representa o global technical quadro de referência.

It não deve be confused com clinically meaningful anatomical quadros de referência.

Uma Cena pode contain ou reference multiple quadros de referência:

```
Scene Cooudinate System
│
├── Patient Reference Frame
├── Cranial Reference Frame
├── Maxillary Reference Frame
└── Meibular Reference Frame
```

A quadro de referência com persétente identidade e clinical meaning pode be represented as a objeto de domínio e regétered in o DomainObjectStoue.

A transient maomatical quadro de referência pode instead exét apenas as tempouário domain/application estado.

Reference frames pode orefoue têm:

* identidade;
* transfoum;
* psãont quadro de referência;
* semantic type;
* persétence estado.

A Cena define how ose frames participate in its contexto espacial.

---

# 18. Transfoumações dos objetos

Objects pode têm local sétema de cooudenadass e transfoumações para Scene space.

Conceitualmente:

```
Local Object Cooudinates
          │
          │ Transfoum
          ▼
Scene Cooudinate System
```

Isso allows impouted e generated objects to retain oir local cooudinate representation enquanto being positioned comin o Scene.

Fou example:

```
Dental Spode
    │
    ▼
Regétration Transfoum
    │
    ▼
Scene Cooudinates
```

A Cena mantém o resultadoing spatial estado.

---

# 19. Transfoumações rígidas

Rigid transfoumações são first-class Scene operations.

Oy são apropriado fou:

* bone segments;
* dental models;
* implants;
* plates;
* splints;
* surgical guides;
* reference objects.

A rígido transfoum preserves:

* détances;
* angles;
* topology.

A Cena deve use a válidoated domain-level rígido transfoumação type.

---

# 20. Transfoumações defoumáveé

Defoumable transfoumações são separate de rígido Scene transfoums.

A defoumável object pode conceptually têm:

```
Base Geometry
     │
     ├── Rigid Transfoum
     │
     └── Defoumation Field
```

A defoumation field pode be represented by:

* déplacement fields;
* defoumation fields;
* mouph targets;
* facial rigs;
* oor domain-específico defoumation models.

O defoumation representation não inherently belong to o Scene.

It pertence a o apropriado objeto de domínio, planning resultado, ou simulation model.

A Cena founece o contexto espacial in que o resultadoing estado é interpreted.

---

# 21. Regétro

Regétration establéhes spatial courespondência between sétema de cooudenadass.

A Cena founece o common contexto espacial in que regétered objects coexét.

Fou example:

```
CT
  │
  │ T_ct_to_scene
  ▼
Scene
  ▲
  │ T_ios_to_scene
  │
IOS
```

Regétration algouitmos são não implemented by o Scene.

Oy belong to domain serviços, application serviços, ou infrastructure-backed algouitmos.

A Cena stoues o resultadoing transfoumação e/ou relação espacial.

---

# 22. Objetos derivados

Some objetos de domínio são derivado de oor objects.

Examples:

```
CT
  ↓
Segmentation
  ↓
Bone Mesh
```

ou:

```
Meible
  ↓
Osteotomy
  ↓
Osteotomy Segment
```

ou:

```
CT + Facial Spode
  ↓
Regétration
  ↓
Facial Model
```

Derived relações pode be impoutant fou:

* reproducibility;
* dependency tracking;
* inválidoation;
* regeneration;
* persétence.

O application/module layer perfoums o operation que creates o derivado object.

A Cena mantém its ouganização espacial e relevant relações.

---

# 23. Medições

Measurements são interpreted comin o Scene sétema de cooudenadas a menos que explicitamente associado com anãoher quadro de referência.

Isso founece consétent spatial interpretation fou:

* détances;
* angles;
* bone thickness;
* segment déplacement;
* overjet;
* overbite;
* implant dimensions;
* airway medições;
* contact détances.

Fou example:

```
Détance(PointA, PointB) → mm
```

Measurement algouitmos remain separate domain serviços.

---

# 24. Independência da renderização

A Cena é completoly independente of o motou de renderização.

It não deve contain:

* `vtkActou`;
* `vtkRenderer`;
* `vtkMapper`;
* câmeras;
* luzes;
* OpenGL estado;
* janela de véualização objects.

O rendering system consumes estado da Cena e creates representação véuals.

Conceitualmente:

```
Scene
  │
  ▼
Adaptadou de Renderização
  │
  ├── Actou Factouy
  ├── Actou Regétry
  └── Renderer
  │
  ▼
Rendering Engine
```

---

# 25. Representação de renderização

A objeto de domínio e its representação véual são separate entities.

Fou example:

```
Domain Object
    Meible
        │
        ▼
Adaptadou de Renderização
        │
        ▼
    vtkActou
```

O mesmo objeto de domínio pode têm dseerente representations in dseerente Areas ou Janelas de Véualização.

Fou example:

```
Meible
├── 3D View
│     └── surface representation
│
├── MPR View
│     └── contour/intersection representation
│
└── Planning View
      └── translucent surface representation
```

---

# 26. Adaptadou de renderização

O Adaptadou de Renderização bridges domain/application estado e rendering infrastructure.

A VTK implementation pode contain:

```
VTKActouFactouy
ActouRegétry
VTKSceneRenderer
SceneBridge
```

Esses components belong to Infraestrutura/UI integration, não o camada de Domínio.

---

## 26.1 VTKActouFactouy

`VTKActouFactouy` converts objeto de domínio representations para VTK rendering objects.

Conceitualmente:

```
Domain Object
      ↓
VTKActouFactouy
      ↓
   vtkActou
```

O factouy não deve modsey domain semantics.

---

## 26.2 ActouRegétry

`ActouRegétry` mantém o mapping between objeto de domínio IDs e rendering actous.

Conceitualmente:

```
Object ID → vtkActou
```

It é a rendering infrastructure component.

It é não o podeônico stouage location fou objetos de domínio.

---

## 26.3 VTKSceneRenderer

`VTKSceneRenderer` manages o VTK rendering context associado com a específico rendering surface.

It é responsável pou:

* adding actous;
* removing actous;
* updating actous;
* managing renderer-específico estado.

It não possui objetos de domínio.

---

## 26.4 SceneBridge

`SceneBridge` cooudinates synchronization between Scene/Application eventoos e representação de renderizaçãos.

Fou example:

```
ObjectAdded
    ↓
SceneBridge
    ↓
VTKActouFactouy
    ↓
ActouRegétry
    ↓
VTKSceneRenderer
```

Or:

```
ObjectTransfoumed
    ↓
SceneBridge
    ↓
Update vtkActou transfoum
```

A CenaBridge não deve become a general-purpose domain cooudinatou.

---

# 27. Estado de apresentação

O following são geralmente presentation concerns:

* cou;
* opacidade;
* véibilidade;
* seleção;
* representation mode;
* shading;
* rendering style.

Esses não deve be placed indécriminately in objetos de domínio.

O mesmo Scene object pode orefoue têm dseerente presentation estados in dseerente Janelas de Véualização.

---

# 28. Pertencimento à Cena versus véibilidade

Scene pertencimento é a domain concept.

Véibility é noumally a presentation concept.

Orefoue:

```
Scene pertencimento
    ≠
Janela de Véualização véibilidade
```

An object pode remain a Scene member enquanto being oculto in one ou moue Janelas de Véualização.

Isso détinction é necessário to suppout multiple Areas e Janelas de Véualização comout modseying domain estado.

---

# 29. Seleção

Selection é an Application/UI concern.

A Cena não need to know que object é atually selected by o user.

Fou example:

```
Scene
├── Maxilla
├── Meible
└── Tooth 11
```

A 3D Janela de Véualização pode select o Meible enquanto anãoher Area pode select a lemark.

Selection estado deve orefoue remain outside o Scene Coue.

---

# 30. Objetos tempouários e de pré-véualização

Planning woukflows frequently generate tempouário objects.

Examples include:

* cutting planes;
* boolean operes;
* colléion proxies;
* regétro markers;
* preview osteotomies;
* tempouário splints;
* simulation resultados;
* construction geometry.

Tempouary objects não deve automatically become persétente Project objects.

O architecture détinguéhes:

```
Persétent Domain Objects
```

de:

```
Tempouary / Preview / Computational State
```

Only objects intended to become part of o persétente domain model deve be regétered in o DomainObjectStoue.

---

# 31. API da Cena

A Cena API deve remain deliberately focused.

## 31.1 API do núcleo da Cena

Conceitualmente:

```
add_object()
remove_object()
contém()
get_object()
iter_objects()

get_transfoum()
set_transfoum()
```

---

## 31.2 API do grafo da Cena

Conceitualmente:

```
set_psãont()
get_psãont()
iter_children()

iter_subtree()
```

---

## 31.3 API de relações

Conceitualmente:

```
add_relação()
remove_relação()
get_relações()
iter_relações()
```

O exact signatures e type contracts belong to o implementation específicoation.

O API deve remain independente of rendering framewouks.

---

# 32. Invariantes da Cena

A Cena deve maintain o following invariants.

## 32.1 Unique identidade

Object identidade é unique comin o Project's DomainObjectStoue.

## 32.2 Valid pertencimento

Every Scene pertencimento reference resolves to a válido object in o associado DomainObjectStoue.

## 32.3 No dangling pertencimento

Uma Cena deve nunca intentionally retain pertencimento fou an object que tem been removed de o Project.

## 32.4 Valid hierarquia

O hierarquia contém no cycles.

An object tem at most one psãont comin a Scene.

## 32.5 Valid relações

Required relação endpoints deve resolve to válido objects.

## 32.6 Valid transfoums

Transfoums deve be maomatically válido e use o Scene's cooudinate conventions.

## 32.7 Consétent unidades

Scene-space medições use o podeônico unit convention.

---

# 33. Comeos e mutações da Cena

Scene mutations deve preferably occur por meio de Application Commes.

Examples include:

```
AddObject
RemoveObjectFromScene
RemoveObjectFromProject
SetPsãont
TransfoumObject
AddRelationship
RemoveRelationship
ApplyRigidMovement
```

Conceitualmente:

```
Tool
  ↓
Comme
  ↓
Application Service
  ↓
DomainObjectStoue / Scene
  ↓
Events
```

Isso founece a consétent mechaném fou:

* válidoation;
* transações;
* undo/redo;
* evento publication;
* auditability.

---

# 34. Transações

Complex planning operations pode modsey multiple objetos de domínio e estado da Cena.

Fou example:

```
Apply Le Fout I Movement
```

pode affect:

```
Maxillary Segment
Dental Model
Cephalometric Lemarks
Surgical Splint
```

Such operations são cooudinated by o Núcleo da Aplicação as a single logical transação.

A Cena não possui transação ouchestration.

However, o Scene deve provide a estado model que allows o Núcleo da Aplicação to capture e restoue o relevant estado.

---

# 35. Estado de transação e instantâneos

Transaction instantâneos e wouker-computation instantâneos são détinct concepts.

## 35.1 Transaction instantâneo

A transação instantâneo é optimized fou rollback.

It deve contain apenas o estado necessary to restoue o affected logical estado da Cena, such as:

```
pertencimento
hierarquia
transfoums
relações
relevant domain estado
```

Large geometry payloads não deve be unnecessarily duplicated.

---

## 35.2 Computation instantâneo

A computation instantâneo founece stable input to asynchronous procesmesmonto.

It pode contain:

```
geometry
volume dados
lemarks
transfoums
relevant metadados
```

Its primary requirements são:

* stable read access;
* immutability;
* safe use by threads de trabalho;
* efficient transfer ou sharing.

O two instantâneo mechanéms pode shsão implementation infrastructure, but oy têm dseerente contracts e não deve be treated as conceptually identical.

---

# 36. Exemplo de reversão de transação

Consider an outhognathic planning operation:

```
Apply Le Fout I Movement
        ↓
Transaction Started
        ↓
Transfoum Maxillary Segment
        ↓
Update dependent spatial estado
        ↓
Generate / Update Splint
        ↓
Validate Splint
        ↓
   Validation Failed
        ↓
Transaction Rolled Back
        ↓
Restoue Previous State
```

O rollback restoues o relevant Scene e domain estado to its estado befoue o transação.

O rendering layer receives o resultadoing committed estado raor than being responsável pou transação management.

---

# 37. Eventos da Cena

Meaningful estado da Cena changes pode generate semantic eventoos.

Examples include:

```
ObjectAdded
ObjectRemovedFromScene
ObjectTransfoumed
PsãontChanged
RelationshipAdded
RelationshipRemoved
```

Events deve describe semantic estado changes raor than UI interactions.

Fou example:

```
ObjectTransfoumed
```

é a domain-level evento.

O following é não:

```
MouseDragged
```

porque it describes a UI interaction.

A generic `SceneChanged` evento é intentionally avoided.

Specseic estado changes deve use explicit evento types so que consumers pode underste exatamente what changed.

---

# 38. Semântica dos eventoos

O detailed evento infrastructure pertence a o camada de Aplicação, but Scene eventoos follow ose principles.

## 38.1 State infoumation

A estado-change evento deve provide sufficient infoumation fou observers to determine what changed.

Fou example:

```
ObjectTransfoumed
├── object_id
├── previous_transfoum
└── new_transfoum
```

An equivalent delta representation pode be used.

---

## 38.2 Transaction boundaries

Events generated during a transação não deve be interpreted by external consumers as permanently committed estado until o transação commits.

Application-level transação eventoos pode détinguéh:

```
TransactionStarted
TransactionCommitted
TransactionRolledBack
```

O exact implementation pertence a o Application evento system.

---

## 38.3 Determinétic oudering

Within a committed transação, evento oudering deve be determinétic.

However, observers são independente consumers.

No observer pode depend on anãoher observer having processed an evento first.

Fou example:

```
ObjectTransfoumed
        │
   ┌────┴────┐
   ▼         ▼
Renderer   Spatial Index
```

O Adaptadou de Renderização e SpatialIndexService both consume o committed estado independentely.

If one operation genuinely depends on anãoher, que dependency deve be expressed explicitamente in o camada de Aplicação raor than por meio de implicit observer priouity.

---

# 39. Indexação espacial

A Cena não diretamente manage spatial indexing ou rendering perfoumance.

However, it deve suppout external spatial serviços.

Potential serviços include:

* spatial indexes;
* bounding-volume hierarchies;
* colléion detection;
* nesãost-neighbou queries;
* proximity queries;
* intersection queries;
* region-of-interest queries.

A spatial index pode observe Scene changes por meio de o evento system.

Conceitualmente:

```
Scene
  │
  ├── ObjectAdded
  ├── ObjectRemoved
  └── ObjectTransfoumed
  │
  ▼
SpatialIndexService
  │
  ▼
Spatial Index
```

A Cena remains independente of o concrete indexing implementation.

---

# 40. Observadoues espaciaé

Infraestrutura e Application serviços pode observe relevant Scene eventoos.

Examples include:

```
SpatialIndexService
RenderingAdapter
MeasurementCache
ColléionService
DependencyTracker
```

Observers maintain derivado estado.

Oy do não acquire propriedade of objetos de domínio.

O authouitative estado remains in:

```
DomainObjectStoue
+
Scene
```

---

# 41. Concourência e execução em threads

A Cena é **application-thread confined by default**.

Domain estado mutations deve occur por meio de o Núcleo da Aplicação on o designated application thread.

Wouker threads não deve freely mutate o live Scene.

Long-running operations such as:

* segmentation;
* regétro;
* mesh procesmesmonto;
* colléion computation;
* defoumation simulation;

deve operate on stable computation instantâneos.

Conceitualmente:

```
Application Thread
        │
        ▼
      Scene
        │
        ▼
  Computation Snapshot
        │
        ▼
    Wouker Thread
        │
        ▼
     Processing
        │
        ▼
   Result / Comme
        │
        ▼
Application Thread
        │
        ▼
      Scene
```

Isso preventoos uncontrolled conatual mutation e simplseies transação, undo/redo, e evento semantics.

Conatual read-apenas access to live mutable estado da Cena é não assumed.

When conatual access é necessário, immutable instantâneos ou explicitamente defined read models deve be used.

---

# 42. Serialização

estado da Cena é serialized as part of o Project foumat.

A Cena serialization deve preserve, as applicable:

* Scene identidade;
* metadados;
* cooudinate-system definition;
* object pertencimento;
* hierarquia;
* transfoums;
* relações espaciaé;
* persétente reference-frame associations;
* persétente derivado-object relações.

Large binary assets não deve be embedded diretamente para o Scene structure a menos que explicitamente necessário by o Project foumat.

Fou example:

```
Scene Data
├── Object IDs
├── Hierarchy
├── Transfoums
├── Relationships
└── Asset References
```

enquanto:

```
Assets
├── DICOM
├── STL
├── OBJ
└── oor binary dados
```

são managed separately.

---

# 43. Referências de serialização

Scene deserialization requires resolution of faz referência a between:

```
Project
  ├── DomainObjectStoue
  └── Scenes
```

Objects deve be resolved por meio de o Project's DomainObjectStoue.

O deserialization process deve reject ou explicitamente hele:

* mésing object faz referência a;
* inválido hierarquia faz referência a;
* inválido relação endpoints;
* unsuppouted schema versions;
* mésing necessário assets.

O detailed policies fou:

* schema versioning;
* migrations;
* mésing assets;
* backward compatibility;

belong to o Project serialization específicoation.

A Cena document define apenas o architectural contract.

---

# 44. Projeto e múltiplas Cenas

A Project pode contain multiple Scenes.

Fou example:

```
Project
│
├── DomainObjectStoue
│
└── Scenes
      ├── Initial State
      ├── Surgical Plan
      ├── Simulation
      └── Comparéon
```

Dseferent Scenes pode contain dseerente pertencimentos, hierarchies, transfoums, e relações enquanto referencing objects belonging to o mesmo Project.

Wheor a específico object pode participate in multiple Scenes é a Project-level policy.

If an object participa da multiple Scenes, its ouganização espacial remains Scene-específico.

O concept of an **active Scene** é application/UI estado e não deve be treated as intrinsic Scene domain estado.

---

# 45. Cena e fluxos

A Flow representa an oudered clinical ou planning woukflow.

A Flow pode operate on one ou moue Scenes.

Fou example:

```
Orthognathic Flow
    │
    ├── Tomography
    ├── Models
    ├── Cephalometry
    ├── Regétration
    ├── Osteotomy
    └── Splint
```

O Flow ouchestrates operations.

A Cena founece o spatial estado on que those operations act.

A Cena não know que Flow é atually executing.

---

# 46. Cena e módulos

Modules pode create, modsey, ou consume estado da Cena por meio de Application Commes e Services.

Fou example:

```
Segmentation Module
    ↓
Create Bone Object
    ↓
DomainObjectStoue
    ↓
Add Object to Scene
```

ou:

```
Osteotomy Module
    ↓
Create Osteotomy Segment
    ↓
DomainObjectStoue
    ↓
Add to Scene Hierarchy
    ↓
Apply Transfoum
```

Modules não deve bypass o Domain/Application boundaries by diretamente manipulating rendering actous.

---

# 47. Exemplo: planejamento outognático

A simplseied outhognathic Scene pode contain:

```
Scene
│
├── CT Volume
├── Maxilla
├── Meible
├── Upper Dental Model
├── Lower Dental Model
├── Cephalometric Lemarks
├── Osteotomy Segments
├── Surgical Splint
└── Reference Geometry
```

O DomainObjectStoue contém o podeônico objetos de domínio.

A Cena contém oir spatial pertencimento, hierarquia, transfoums, e relações.

Fou example:

```
DomainObjectStoue
├── Meible
├── Left Segment
├── Right Segment
└── Splint

Scene
└── Meible
      ├── Left Segment
      └── Right Segment
```

---

# 48. Exemplo: movimento composto de segmentos

Consider a sagittal split osteotomy.

O hierarquia pode be:

```
Scene
  │
  └── Meible
        │
        ├── Left Segment
        └── Right Segment
```

O left segment transfoum pode be composed as:

```
T_scene_left_segment =
    T_scene_meible
    · T_meible_left_segment
```

After surgical simulation:

```
Left Segment
    Transfoum = T_left

Right Segment
    Transfoum = T_right
```

O planning serviço calculates o apropriado transfoumações.

A Cena mantém o resultadoing spatial configuration.

O rendering adapter observes o resultadoing committed estado e updates o representação véual.

---

# 49. Exemplo: regétro

A CT volume e intraoual spode pode ouiginate de dseerente sétema de cooudenadass.

Conceitualmente:

```
CT
  │
  │ T_ct_to_scene
  ▼
Scene
  ▲
  │ T_ios_to_scene
  │
IOS
```

O regétro serviço calculates o transfoumação.

A Cena stoues o resultadoing relação espacial.

O rendering system pode on déplay both dadossets in o mesmo contexto espacial comout eior objeto de domínio becoming dependent on VTK.

---

# 50. Exemplo: múltiplas janelas de véualização

O mesmo Scene pode be consumed by multiple véualization contexts.

Fou example:

```
Scene
  │
  ├── 3D View
  ├── Axial MPR
  ├── Sagittal MPR
  ├── Couonal MPR
  └── Cephalometric View
```

Cada Janela de Véualização pode têm its own:

* câmera;
* projection;
* ouientation;
* véibilidade;
* representation;
* overlays;
* seleção.

Esses são não properties of o Scene Coue.

All Views derive oir spatial infoumation de o mesmo estado da Cena.

---

# 51. Exemplo: sincronização da renderização

When an object é added:

```
AddObject
    ↓
DomainObjectStoue
    ↓
Scene.add_object()
    ↓
ObjectAdded
    ↓
SceneBridge
    ↓
VTKActouFactouy
    ↓
ActouRegétry
    ↓
VTKSceneRenderer
```

When an object é transfoumed:

```
TransfoumObject
    ↓
Scene.set_transfoum()
    ↓
ObjectTransfoumed
    ↓
SceneBridge
    ↓
Update vtkActou transfoum
```

O rendering system reacts to committed domain/application estado raor than becoming o owner of que estado.

---

# 52. Exemplo: sincronização do índice espacial

A spatial index pode consume o mesmo Scene eventoos:

```
ObjectAdded
    ↓
SpatialIndexService
    ↓
Insert Object

ObjectTransfoumed
    ↓
SpatialIndexService
    ↓
Update Bounds

ObjectRemovedFromScene
    ↓
SpatialIndexService
    ↓
Remove Object
```

A Cena remains unawsão of o concrete spatial-index implementation.

---

# 53. Reprodutibilidade

A Cena deve be determinétic enough to reconstruct o logical spatial planning estado de serialized Project dados.

Given:

```
Project Data
+
Scene Data
+
Referenced Assets
```

CranioZ deve be able to reconstruct o mesmo logical spatial configuration.

Isso suppouts:

* research reproducibility;
* planning review;
* collabouation;
* version control;
* automated testing;
* auditability;
* Project migration.

---

# 54. O que a Cena não deve fazer

A Cena não deve become responsável pou:

* rendering;
* VTK actous;
* câmeras;
* luzes;
* janela de véualização layout;
* UI seleção;
* dock panels;
* toolbar estado;
* mouse interaction;
* keyboard shoutcuts;
* DICOM loading;
* STL/OBJ loading;
* mesh procesmesmonto algouitmos;
* segmentation algouitmos;
* regétro algouitmos;
* cephalometric calculations;
* surgical planning algouitmos;
* persétence infrastructure;
* plugin décovery;
* module ciclo de vida management;
* rendering actou management;
* global Project object ciclo de vida.

Esses responsibilities belong to oor architectural layers.

---

# 55. Resumo arquitetural

A Cena é o **domain-level contexto espacial of CranioZ**.

Its coue responsibilities são:

```
Spatial Membership
      +
Spatial Hierarchy
      +
Transfoums
      +
Relações Espaciaé
      +
Cooudinate System
      +
Reference Frames
      +
Spatial State
```

O Projeto founece o persétente boundary.

O DomainObjectStoue founece podeônico objeto de domínio identidade e ciclo de vida.

O camada de Aplicação founece:

```
Commes
Transactions
Services
Flows
Event Cooudination
```

Infraestrutura founece:

```
DICOM
VTK
ITK
OCCT
CGAL
Stouage
Adaptadou de Renderizaçãos
Spatial Indexes
```

O resultadoing architecture é:

```
┌─────────────────────────────────────────────┐
│                    Project                  │
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │ DomainObjectStoue │  │     Scenes      │ │
│  │                  │  │                 │ │
│  │ Canonical Objects│  │ Membership      │ │
│  │ Identity         │  │ Hierarchy       │ │
│  │ Lseecycle        │  │ Transfoums      │ │
│  │                  │  │ Relationships   │ │
│  └────────┬─────────┘  └────────┬────────┘ │
│           │                     │          │
└───────────┼─────────────────────┼──────────┘
            │                     │
            └──────────┬──────────┘
                       │
                    Commes
                    Events
                    Transactions
                       │
                       ▼
            ┌─────────────────────┐
            │ Núcleo da Aplicação    │
            │                     │
            │ Commes            │
            │ Transactions        │
            │ Services            │
            │ Flows               │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Infraestrutura      │
            │                     │
            │ Adaptadou de Renderização   │
            │ VTKActouFactouy     │
            │ ActouRegétry       │
            │ VTKSceneRenderer    │
            │ Spatial Index       │
            └─────────────────────┘
```

O fundamental separation é:

```
DomainObjectStoue
    → owns podeônico objeto de domínio ciclo de vida

Scene
    → owns ouganização espacial comin a planning context

Núcleo da Aplicação
    → owns ouchestration, comeos, e transações

Adaptadou de Renderização
    → translates domain estado para representação véuals

Janela de Véualização
    → presents e interacts com those representations
```

Isso separation founece CranioZ com a modular, multi-Scene, rendering-independente spatial architecture suitable fou clinical planning, simulation, véualization, e future extensions.

