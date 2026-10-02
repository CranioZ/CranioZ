# Editors

## 1. Visão geral

Os Editors são componentes funcionais da interface do CranioZ responsáveis por apresentar e permitir a interação com determinado tipo de conteúdo ou atividade.

Um Editor define **o que o usuário está fazendo** dentro de uma `Area`. Ele não define **onde está localizado** na interface.

A arquitetura de interface segue a seguinte hierarquia:

```text
Workspace
└── Layout
    └── Area
        └── EditorHost
            └── Editor
                ├── Toolbar
                │   └── Tools
                ├── Content
                └── Overlays
```

Essa separação permite que o mesmo Editor seja utilizado em diferentes configurações de interface sem depender de uma posição específica.

Por exemplo, um `MPRViewerEditor` pode ocupar uma Area central, lateral ou inferior dependendo do Layout, sem que o Editor precise conhecer ou controlar essa posição.

A Area é fornecida pelo Workspace; o Editor não a cria nem a gerencia.

---

## 2. Responsabilidades

Um Editor é responsável por:

- definir uma experiência funcional de edição ou visualização;
- apresentar determinado tipo de conteúdo;
- fornecer interação específica para esse conteúdo;
- declarar sua Toolbar e as Tools que ela referencia;
- traduzir interações do usuário em Commands;
- reagir a alterações relevantes do estado da aplicação;
- manter o estado específico da apresentação quando necessário.

Um Editor **não é responsável por**:

- determinar sua posição na interface;
- criar ou gerenciar Areas;
- definir o Layout do Workspace;
- controlar docking ou divisão espacial;
- gerenciar outros Editors;
- implementar lógica clínica pertencente a Modules;
- modificar diretamente o estado clínico da Scene;
- materializar diretamente widgets Qt.

A separação pode ser resumida como:

```text
Area    → onde
Editor  → o quê
Tool    → intenção do usuário
Command → alteração de estado
Module  → funcionalidade clínica
Scene   → estado clínico
```

---

## 3. Editor versus Area

`Area` e `Editor` possuem responsabilidades diferentes.

### Area

A `Area` é uma unidade estrutural da interface.

Ela controla aspectos como:

- posição;
- tamanho;
- visibilidade;
- docking;
- divisão;
- apresentação;
- relacionamento espacial com outras Areas.

A Area não deve possuir conhecimento específico sobre cirurgia, imagem, cefalometria, segmentação ou qualquer outra funcionalidade clínica.

### Editor

O Editor representa uma função da interface.

Ele controla aspectos como:

- visualização;
- interação;
- ferramentas;
- seleção;
- manipulação;
- navegação;
- apresentação de informações.

Um Editor não deve assumir que está no centro, na lateral ou na parte inferior da janela.

```text
Area
└── EditorHost
    └── Editor
```

A Area fornece o espaço de apresentação; o Editor fornece a experiência funcional.

---

## 4. EditorHost

A comunicação entre Area e Editor ocorre por meio de um `EditorHost`.

```text
Area
└── EditorHost
    └── Editor
```

O `EditorHost` funciona como camada de hospedagem e adaptação entre a infraestrutura espacial do Workspace e a implementação do Editor.

Suas responsabilidades incluem:

- hospedar a instância do Editor;
- conectar o Editor à Area;
- administrar o ciclo de vida visual;
- fornecer o contexto necessário para o Editor;
- materializar a Toolbar declarada pelo Editor;
- conectar Toolbar e Content;
- adaptar a implementação do Editor ao sistema de Layout.

O EditorHost não deve assumir responsabilidades clínicas.

O Editor declara sua Toolbar; o EditorHost materializa essa Toolbar no espaço fornecido pela Area, respeitando o Layout.

---

## 5. Interface base

Todos os Editors devem derivar de uma abstração comum.

Uma implementação conceitual pode ser representada por:

```python
class Editor(ABC):
    editor_id: str
    title: str

    def initialize(self, context: "EditorContext") -> None:
        ...

    def activate(self) -> None:
        ...

    def deactivate(self) -> None:
        ...

    def dispose(self) -> None:
        ...
```

A interface concreta poderá evoluir conforme as necessidades do sistema.

O objetivo da classe base não é impor uma implementação visual específica, mas estabelecer um contrato comum para registro, criação e ciclo de vida.

### Ciclo de vida

```text
initialize(context) → chamado uma vez, ao criar o Editor
activate()          → Editor torna-se ativo
deactivate()        → Editor torna-se inativo
dispose()           → Editor é destruído
```

Um Editor pode permanecer hospedado enquanto está inativo. O estado visual transitório pode ou não persistir entre `deactivate()` e `activate()`, conforme a natureza do Editor.

`deactivate()` não implica `dispose()`.

---

## 6. EditorRegistry

Os Editors são registrados no `EditorRegistry`.

O Registry é responsável por:

- registrar Editors disponíveis;
- localizar um Editor por `editor_id`;
- fornecer metadados;
- criar novas instâncias;
- controlar factories;
- validar Editors solicitados por Layouts.

Exemplo conceitual:

```text
EditorRegistry
│
├── viewport_3d
├── mpr_viewer
├── properties
├── scene
├── node
├── animation
└── cephalometry
```

O Registry permite que o sistema trabalhe com identificadores estáveis em vez de depender diretamente das classes concretas.

Por exemplo:

```python
editor_id = "viewport_3d"
```

em vez de:

```python
Viewport3DEditor(...)
```

na definição do Layout.

O Registry fornece definições ou factories. Ele não mantém instâncias de execução; a criação das instâncias é realizada pelo Workspace ou pelo Host correspondente.

---

## 7. Layout e Editors

O Layout define quais Editors aparecem e onde eles são hospedados.

Entretanto, o Layout não instancia diretamente as classes dos Editors.

O fluxo é:

```text
Layout
   │
   │ editor_id
   ▼
EditorRegistry
   │
   │ create()
   ▼
Instância do Editor
```

Dessa forma, a definição do Layout permanece declarativa.

Exemplo conceitual:

```python
AreaSpec(
    area_id="main_view",
    editor_id="viewport_3d",
)
```

O Layout conhece:

```text
"viewport_3d"
```

mas não precisa conhecer:

```text
Viewport3DEditor
```

Essa responsabilidade pertence ao `EditorRegistry`.

---

## 8. LayoutTree

O `LayoutTree` é a fonte de verdade da composição espacial da interface.

Ele descreve:

- Areas;
- relações entre Areas;
- divisão espacial;
- docking;
- visibilidade;
- Editors associados às Areas;
- overlays;
- configuração do Layout.

Conceitualmente:

```text
LayoutTree
│
├── Area
│   └── Editor: MPRViewer
│
├── Area
│   └── Editor: Viewport3D
│
└── Area
    └── Editor: Properties
```

O LayoutTree não contém widgets Qt concretos. Ele representa a estrutura lógica da interface.

---

## 9. Materialização do Layout

A criação da interface ocorre em etapas distintas:

```text
LayoutTree
    │
    ▼
LayoutBuilder
    │
    ▼
Areas / EditorHosts
    │
    ▼
LayoutRenderer
    │
    ▼
Qt Widgets
```

### LayoutTree

Representação declarativa da composição.

### LayoutBuilder

Interpreta o LayoutTree e cria a estrutura necessária.

### LayoutRenderer

Projeta essa estrutura na interface Qt.

Essa separação evita que a estrutura lógica do Workspace fique acoplada à implementação específica do Qt.

---

## 10. Toolbar

A Toolbar pertence ao Editor. Cada Editor define sua própria Toolbar, composta por Tools que podem ser compartilhadas com outros Editors.

```text
Editor
├── Toolbar
│   └── Tools
├── Content
└── Overlays
```

A Toolbar é uma especificação declarativa pertencente ao Editor. Sua materialização é responsabilidade do EditorHost, que a projeta no espaço fornecido pela Area por meio do LayoutRenderer.

As Tools não pertencem a uma Toolbar específica. Elas pertencem a um catálogo compartilhado, o `ToolRegistry`, e podem ser referenciadas por Toolbars de diferentes Editors.

Exemplo:

```text
Viewport3DEditor
├── ViewportToolbar
│   ├── select_tool
│   ├── transform_tool
│   └── measure_tool
└── 3D View

MPRViewerEditor
├── MPRToolbar
│   ├── select_tool
│   └── measure_tool
└── 2D Views
```

A Toolbar não deve ser tratada como uma `ToolbarArea` especial nem como responsabilidade do Layout. Ela é parte da experiência do Editor e pode ser apresentada conforme o Layout e o estado atual da interface, sem que o Editor precise conhecer os detalhes dessa apresentação.

### Múltiplas Toolbars por Editor

Um Editor pode declarar mais de uma Toolbar:

```text
Editor
├── Toolbar1: Tool2, Tool4
├── Toolbar2: Tool1, Tool2, Tool4
└── Content
```

A composição de cada Toolbar é independente, mesmo quando as mesmas definições de Tool são referenciadas.

---

## 11. Tools

Tools representam intenções ou operações iniciadas pelo usuário.

Uma Tool é uma unidade funcional independente. Ela não pertence a uma Toolbar específica e pode ser referenciada por várias Toolbars.

```text
Tools
├── Tool1
├── Tool2
├── Tool3
├── Tool4
└── Tool5

Toolbar1: Tool2, Tool4
Toolbar2: Tool1, Tool2, Tool4
```

A definição de cada Tool reside no `ToolRegistry`. A Toolbar que a utiliza é responsável por criar a instância da Tool.

Assim, `Tool2` na `Toolbar1` e `Tool2` na `Toolbar2` compartilham a mesma definição, mas são instâncias independentes:

```text
ToolRegistry
├── Tool1 (definição)
├── Tool2 (definição)
├── Tool3 (definição)
├── Tool4 (definição)
└── Tool5 (definição)

Toolbar1 cria Tool2 e Tool4
Toolbar2 cria Tool1, Tool2 e Tool4
```

### Fluxo de resolução

```text
Toolbar
   │ resolve tool_id
   ▼
ToolRegistry
   │ retorna factory/classe
   ▼
Toolbar cria a Tool
```

### Comportamento

Uma Tool não deve modificar diretamente o estado clínico. O fluxo preferencial é:

```text
User
  ↓
Tool
  ↓
Command
  ↓
CommandStack
  ↓
Scene
  ↓
EventBus
  ↓
Editors
```

Quando ativada, uma Tool recebe um contexto controlado fornecido pelo Editor por meio da Toolbar. Esse contexto pode conter referências a consultas da Scene, serviços de Selection, despacho de Commands, inscrições em Events e serviços especializados. A Tool não deve assumir conhecimento sobre a posição do Editor na interface.

### Ciclo de vida

```text
Tool.__init__        → criada pela Toolbar
Tool.activate(ctx)   → ativada pelo usuário
Tool.deactivate()    → desativada
Tool.dispose()       → destruída com a Toolbar
```

O estado transitório da Tool pode ou não persistir entre `deactivate()` e `activate()`, conforme a natureza da Tool. Tools de medição geralmente reiniciam; Tools de seleção geralmente preservam seu estado.

### Isolamento de estado

Como cada Toolbar cria suas próprias instâncias de Tool, o estado de execução não é compartilhado acidentalmente entre Toolbars diferentes. Isso é especialmente importante quando a mesma Tool aparece em contextos distintos, como uma `MeasureTool` tanto no `Viewport3DEditor` quanto no `MPRViewerEditor`.

A decisão arquitetural é:

> A Toolbar cria suas próprias instâncias de Tool a partir das definições fornecidas pelo ToolRegistry. A mesma Tool pode ser referenciada por diferentes Toolbars, mas cada Toolbar mantém instâncias independentes.

---

## 12. Conteúdo do Editor

O conteúdo apresentado por um Editor varia conforme sua finalidade.

### Viewport 3D

```text
Viewport3DEditor
├── 3D viewport
├── camera
├── selection
├── overlays
└── tools
```

### MPR Viewer

```text
MPRViewerEditor
├── axial view
├── sagittal view
├── coronal view
├── crosshair
├── slice navigation
└── image tools
```

### Properties

```text
PropertiesEditor
├── object information
├── transform
├── appearance
└── clinical properties
```

### Node Editor

```text
NodeEditor
├── node canvas
├── nodes
├── links
├── node tools
└── graph navigation
```

O conteúdo específico não deve ser confundido com a Area que o hospeda.

---

## 13. Editors previstos

A arquitetura não deve exigir que todos os Editors existam desde o início. Entretanto, os seguintes são candidatos naturais para o CranioZ.

### Visualização

- `Viewport3DEditor`
- `MPRViewerEditor`
- `ImageViewerEditor`
- `SceneEditor`

### Planejamento

- `CephalometryEditor`
- `OsteotomyEditor`
- `SplintEditor`
- `ImplantEditor`
- `SurgicalGuideEditor`

### Modelagem e geometria

- `MeshEditor`
- `NodeEditor`
- `SculptEditor`

### Informação

- `PropertiesEditor`
- `OutlinerEditor`
- `PatientEditor`
- `DocumentEditor`

### Animação e simulação

- `AnimationEditor`

Essa lista é extensível e não pretende ser exaustiva.

---

## 14. Editors e Modules

`Module` e `Editor` não são equivalentes.

Um **Module** representa uma funcionalidade do CranioZ.

Um **Editor** representa uma experiência de interface utilizada para trabalhar com essa funcionalidade.

A relação entre eles é:

```text
Module
 ├── Commands
 ├── Tools
 ├── Services
 └── Editor specifications
```

Um Module pode declarar que determinada funcionalidade utiliza um Editor, mas não possui nem instancia o Editor.

Por exemplo:

```text
Orthognathic Module
    │
    ├── declares: viewport_3d
    ├── declares: mpr_viewer
    └── declares: cephalometry
```

A criação efetiva das instâncias pertence ao Workspace e ao `EditorRegistry`.

Isso permite que diferentes Modules utilizem o mesmo Editor sem duplicar sua implementação.

---

## 15. Editors compartilhados

Os Editors devem ser projetados para reutilização.

Por exemplo, o `Viewport3DEditor` pode ser utilizado em:

- planejamento ortognático;
- implantes faciais;
- osteossíntese;
- reconstrução mandibular;
- planejamento de rinoplastia;
- planejamento de guias cirúrgicas;
- análise de modelos.

O Editor fornece a experiência genérica de interação.

A lógica específica da aplicação é fornecida por:

- Modules;
- Tools;
- Commands;
- Services;
- Scene;
- contexto da aplicação.

---

## 16. EditorContext

Um Editor pode receber um contexto de execução contendo referências controladas para os serviços de que necessita.

O contexto deve ser pequeno e orientado a interfaces. Ele não deve se transformar em um barramento global de comunicação ou em um God Object.

Um contexto conceitual é:

```text
EditorContext
├── SceneQuery
├── SelectionService
├── CommandDispatcher
├── EventSubscription
├── ViewStateStore
└── EditorServices
```

O Editor deve depender de abstrações e evitar dependências diretas de componentes concretos da aplicação sempre que possível.

O Editor não deve receber acesso indiscriminado à Scene inteira, a todos os Services, ao Workspace completo, a detalhes concretos do Qt ou a componentes internos de outros Editors.

Essa separação facilita:

- testes;
- reutilização;
- plugins;
- manutenção;
- evolução arquitetural.

Exemplo conceitual:

```python
class Viewport3DEditor(Editor):
    def initialize(self, context: EditorContext) -> None:
        self._scene_query = context.scene_query
        self._selection = context.selection_service
        self._commands = context.command_dispatcher
        self._events = context.event_subscription
```

O Editor recebe apenas o contexto de que necessita.

Sempre que possível, uma Tool deve receber um `ToolContext` ainda mais restrito:

```text
ToolContext
├── SceneQuery
├── SelectionService
├── CommandDispatcher
└── ToolServices
```

---

## 17. Estado do Editor

O estado clínico deve ser separado do estado puramente visual.

### Estado clínico

Pertence à aplicação e à `Scene`.

Exemplos:

- posição de uma mandíbula;
- plano de osteotomia;
- posição de um implante;
- landmarks;
- modelos anatômicos;
- splints.

### Estado visual

Pode pertencer ao Editor.

Exemplos:

- zoom;
- câmera;
- slice atual;
- seleção visual;
- modo de apresentação;
- visibilidade temporária;
- configuração da viewport.

Essa separação evita que informações transitórias da interface sejam confundidas com os dados clínicos do projeto.

---

## 18. Overlays

Overlays são elementos temporários ou flutuantes apresentados sobre um Editor.

Exemplos:

- gizmos;
- crosshairs;
- medidas;
- marcadores;
- indicadores;
- menus contextuais;
- informações temporárias.

Conceitualmente:

```text
Area
└── EditorHost
    └── Editor
        ├── Toolbar
        ├── Content
        └── Overlays
```

Overlays não devem ser transformados em Editors apenas porque ocupam uma região visual sobre o conteúdo.

### Diretrizes

- Overlays são gerenciados pelo Editor ou pelo EditorHost, conforme sua natureza.
- Overlays interativos, como gizmos, podem participar do hit testing.
- Overlays possuem uma ordem de renderização, ou z-order, definida pelo Editor.
- Overlays não devem alterar diretamente o estado clínico; Overlays interativos utilizam Commands quando uma alteração clínica é necessária.

---

## 19. Independência espacial

Um dos princípios fundamentais dos Editors é:

> **Um Editor não deve saber onde está.**

O mesmo Editor pode aparecer como:

```text
┌─────────────────────────────┐
│        Viewport3DEditor     │
│                             │
└─────────────────────────────┘
```

ou:

```text
┌──────────────┬──────────────┐
│              │              │
│     MPR      │   Viewport   │
│              │      3D      │
│              │              │
└──────────────┴──────────────┘
```

ou:

```text
┌─────────────────────────────┐
│         Viewport 3D         │
├─────────────────────────────┤
│          MPR Viewer         │
└─────────────────────────────┘
```

sem modificar a implementação do Editor.

A composição pertence ao Workspace.

---

## 20. ToolRegistry

O `ToolRegistry` mantém as definições de Tools disponíveis no sistema.

Ele é responsável por:

- registrar definições de Tools;
- localizar uma definição por `tool_id`;
- fornecer factories ou classes;
- validar Tools referenciadas por Toolbars.

Conceitualmente:

```text
ToolRegistry
├── select_tool
├── transform_tool
├── measure_tool
├── landmark_tool
└── ...
```

O ToolRegistry não mantém instâncias de execução. Ele fornece definições ou factories; a Toolbar cria e mantém as instâncias que utiliza.

```text
Toolbar
   │ resolve tool_id
   ▼
ToolRegistry
   │ retorna factory/classe
   ▼
Toolbar cria a Tool
```

Essa separação permite:

- reutilização de definições entre Toolbars;
- isolamento de estado por instância;
- testes com Tools simuladas;
- evolução independente entre definição e uso.

---

## 21. Princípios arquiteturais

Os seguintes princípios devem orientar a implementação:

### 21.1 Editor é funcional, não espacial

A posição pertence à Area e ao Layout.

### 21.2 Editor não instancia outros Editors

A composição é responsabilidade do Workspace e do Layout.

### 21.3 Module não possui Editors

Modules declaram necessidades de interface; o Workspace resolve e cria as instâncias dos Editors.

### 21.4 Layout é declarativo

Layouts utilizam identificadores estáveis e especificações, evitando referências diretas a classes concretas.

### 21.5 O Registry cria instâncias

Classes concretas não aparecem nas definições de Layout.

### 21.6 Editor não contém lógica clínica

A lógica clínica pertence aos Modules, Services, Domain e camadas da Application.

### 21.7 Alterações persistentes de estado utilizam Commands

Quando uma interação altera o estado persistente da aplicação, o Editor deve utilizar Commands em vez de modificar diretamente a Scene clínica.

### 21.8 Events notificam alterações

Events não substituem Commands e não devem funcionar como mecanismo primário de escrita.

### 21.9 Estado visual e estado clínico permanecem separados

A interface pode manter estado transitório sem contaminar o modelo clínico.

### 21.10 Hosts controlam a apresentação espacial

Docking, floating e múltiplos monitores não devem contaminar a implementação do Editor.

### 21.11 Editors devem ser reutilizáveis

Um tipo de Editor deve poder ser utilizado por vários Modules e Layouts.

### 21.12 O contexto deve ser mínimo

As dependências são fornecidas por interfaces específicas.

### 21.13 Qt é um detalhe de apresentação

A arquitetura lógica dos Editors deve permanecer o mais independente possível dos widgets Qt concretos.

### 21.14 O Editor declara a Toolbar; o EditorHost a materializa

O Editor não cria widgets Qt de Toolbar. Ele declara a composição; o EditorHost materializa sua apresentação.

### 21.15 O ToolRegistry fornece definições; a Toolbar cria instâncias

Uma definição de Tool é registrada uma vez e pode ser reutilizada. A instância de execução pertence à Toolbar que a utiliza.

### 21.16 Editors devem ser testáveis sem Qt

O contrato do Editor deve permitir testes unitários sem dependência de widgets concretos.

---

## 22. Fluxo completo

A arquitetura pode ser resumida pelo seguinte fluxo:

```text
                    ┌───────────────┐
                    │     Module    │
                    └───────┬───────┘
                            │
                      declara Editor
                            │
                            ▼
                    ┌───────────────┐
                    │  LayoutTree   │
                    └───────┬───────┘
                            │
                         editor_id
                            ▼
                    ┌───────────────┐
                    │ EditorRegistry│
                    └───────┬───────┘
                            │
                          create
                            ▼
┌───────────┐       ┌───────────────┐
│   Area    │──────▶│  EditorHost   │
└───────────┘       └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Editor     │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Toolbar        Content       Overlays
              │
              │ resolve tool_id
              ▼
        ┌───────────────┐
        │  ToolRegistry │
        └───────┬───────┘
                │ retorna factory/classe
                ▼
        Toolbar cria Tool(s)
                │
                │ activate(context)
                ▼
             Command
                │
                ▼
              Scene
                │
                ▼
             EventBus
                │
                ▼
             Editors
```

Essa arquitetura permite que o CranioZ mantenha uma interface altamente configurável sem transformar o Workspace em um conjunto de componentes específicos de cada Module clínico.

O princípio central é:

```text
Workspace = composição
Layout    = organização
Area      = espaço
Editor    = experiência funcional
Toolbar   = composição de Tools
Tool      = intenção
Command   = alteração
Module    = funcionalidade
Scene     = estado clínico
```

Esse modelo deve ser considerado a base para a evolução do sistema de Editors do CranioZ.
