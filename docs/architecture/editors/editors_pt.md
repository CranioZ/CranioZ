# Editores

## 1. Visão geral

Os Editores são componentes funcionais da interface do usuário do CranioZ, responsáveis por apresentar e permitir a interação com um tipo específico de conteúdo ou atividade.

Um Editor define o que o usuário está fazendo dentro de uma Área. Ele não define onde está localizado na interface.

A arquitetura da interface segue esta hierarquia:

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

Por exemplo, um `MPRViewerEditor` pode ocupar uma Área central, lateral ou inferior, dependendo do Layout, sem que o Editor conheça ou controle essa posição.

A Área é fornecida pelo Workspace; o Editor não a cria nem a gerencia.

## 2. Responsabilidades

Um Editor é responsável por:

- definir uma experiência funcional de edição ou visualização;
- apresentar um tipo específico de conteúdo;
- fornecer interação específica para esse conteúdo;
- declarar e materializar sua própria Toolbar e as Tools que ela referencia;
- traduzir as interações do usuário em Commands;
- reagir a mudanças relevantes no estado da aplicação;
- manter o estado específico da apresentação quando necessário.

Um Editor não é responsável por:

- determinar sua posição na interface;
- criar ou gerenciar Areas;
- definir o Layout do Workspace;
- controlar docking ou divisão espacial;
- gerenciar outros Editors;
- implementar lógica clínica pertencente aos Modules;
- modificar diretamente o estado clínico da Scene.

A separação pode ser resumida da seguinte forma:

```text
Area    → onde
Editor  → o quê
Tool    → intenção do usuário
Command → mudança de estado
Module  → funcionalidade clínica
Scene   → estado clínico
```

## 3. Editor versus Area

Area e Editor possuem responsabilidades diferentes.

### Area

Uma Area é uma unidade estrutural da interface.

Ela controla aspectos como:

- posição;
- tamanho;
- visibilidade;
- docking;
- divisão;
- apresentação;
- relações espaciais com outras Areas.

Uma Area não deve conter conhecimento específico sobre cirurgia, imagens, cefalometria, segmentação ou qualquer outra funcionalidade clínica.

### Editor

Um Editor representa uma função da interface.

Ele controla aspectos como:

- visualização;
- interação;
- ferramentas;
- seleção;
- manipulação;
- navegação;
- apresentação de informações.

Um Editor não deve presumir que está localizado no centro, na lateral ou na parte inferior da janela.

```text
Area
└── EditorHost
    └── Editor
```

A Area fornece o espaço de apresentação; o Editor fornece a experiência funcional.

## 4. EditorHost

A comunicação entre uma Area e um Editor ocorre por meio de um `EditorHost`.

```text
Area
└── EditorHost
    └── Editor
```

O `EditorHost` atua como uma camada de hospedagem e adaptação entre a infraestrutura espacial do Workspace e a implementação do Editor.

Suas responsabilidades incluem:

- hospedar a instância do Editor;
- conectar o Editor à Area;
- gerenciar o ciclo de vida visual;
- fornecer o contexto necessário ao Editor;
- adaptar a implementação do Editor ao sistema de Layout.

O `EditorHost` não deve assumir responsabilidades clínicas.

O `EditorHost` não materializa Toolbars. Ele apenas hospeda o Editor. Cada Editor declara e materializa sua própria Toolbar dentro do seu espaço de conteúdo.

## 5. Interface base

Todos os Editors devem derivar de uma abstração comum.

Uma implementação conceitual pode ser representada da seguinte forma:

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

    # Conteúdo e elementos internos da interface
    def content_widget(self) -> "QWidget":
        ...

    def toolbar_specs(self) -> list["ToolbarSpec"]:
        return []

    def overlays(self) -> list["Overlay"]:
        return []
```

A interface concreta pode evoluir de acordo com as necessidades do sistema.

O objetivo da classe base não é impor uma implementação visual específica, mas estabelecer um contrato comum para registro, criação e gerenciamento do ciclo de vida, além de declarar a composição interna do Editor: Content, Toolbars e Overlays.

### Ciclo de vida

```text
initialize(context) → chamado uma vez quando o Editor é criado
activate()          → o Editor se torna ativo
deactivate()        → o Editor se torna inativo
dispose()           → o Editor é destruído
```

Um Editor pode continuar hospedado enquanto estiver inativo. O estado visual temporário pode ou não persistir entre `deactivate()` e `activate()`, dependendo da natureza do Editor.

`deactivate()` não implica `dispose()`.

## 6. EditorRegistry

Os Editors são registrados no `EditorRegistry`.

O Registry é responsável por:

- registrar os Editors disponíveis;
- localizar um Editor por meio de `editor_id`;
- fornecer metadados;
- criar novas instâncias;
- gerenciar factories;
- validar os Editors solicitados pelos Layouts.

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

O Registry permite que o sistema trabalhe com identificadores estáveis, em vez de depender diretamente de classes concretas.

Por exemplo:

```python
editor_id = "viewport_3d"
```

em vez de:

```python
Viewport3DEditor(...)
```

na definição do Layout.

O Registry fornece definições ou factories. Ele não mantém instâncias em execução; a criação das instâncias é realizada pelo Workspace ou pelo host correspondente.

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

Isso mantém a definição do Layout declarativa.

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

## 8. LayoutTree

O `LayoutTree` é a fonte de verdade para a composição espacial da interface.

Ele descreve:

- Areas;
- relações entre Areas;
- divisões espaciais;
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

O `LayoutTree` não contém widgets Qt concretos. Ele representa a estrutura lógica da interface.

## 9. Materialização do Layout

A interface é criada em etapas distintas:

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

Interpreta o `LayoutTree` e cria a estrutura necessária.

### LayoutRenderer

Projeta essa estrutura na interface Qt.

Essa separação impede que a estrutura lógica do Workspace fique acoplada à implementação específica do Qt.

É importante observar que a estrutura interna do Editor — Toolbar, Content e Overlays — é materializada pelo próprio Editor, e não pelo `LayoutRenderer`. O `LayoutRenderer` apenas gerencia a árvore de Areas e hospeda o Editor dentro do `EditorHost`.

## 10. Toolbar

Uma Toolbar é um widget interno de um Editor, e não uma Area.

Cada Editor decide se deseja possuir sua própria Toolbar. O Workspace nunca hospeda Toolbars.

```text
Editor
├── Toolbar
│   └── Tools
├── Content
└── Overlays
```

A Toolbar é uma especificação declarativa pertencente ao Editor. Sua materialização é responsabilidade do próprio Editor, que projeta a Toolbar dentro do seu espaço de conteúdo, respeitando a orientação declarada: `HORIZONTAL` ou `VERTICAL`.

As Tools não pertencem a uma Toolbar específica. Elas pertencem a um catálogo compartilhado, o `ToolRegistry`, e podem ser referenciadas por Toolbars de diferentes Editors.

Exemplo:

```text
Viewport3DEditor
├── ViewportToolbar (VERTICAL)
│   ├── select_tool
│   ├── transform_tool
│   └── measure_tool
├── ViewportToolbar (HORIZONTAL)
│   ├── reset_view
│   └── fit_view
└── 3D View

MPRViewerEditor
├── MPRToolbar (VERTICAL)
│   ├── select_tool
│   └── measure_tool
└── 2D Views
```

Uma Toolbar não deve ser tratada como uma `ToolbarArea` especial nem como uma responsabilidade do Layout. Ela faz parte da experiência do Editor e é apresentada dentro do próprio Editor, que não conhece nem depende da posição que ocupa no Workspace.

### Múltiplas Toolbars por Editor

Um Editor pode declarar mais de uma Toolbar, com orientações independentes:

```text
Editor
├── Toolbar Vertical:   Tool2, Tool4
├── Content
├── Overlays
└── Toolbar Horizontal: Tool1, Tool2, Tool4
```

A composição de cada Toolbar é independente, mesmo quando as mesmas definições de Tools são referenciadas.

## 11. Tools

As Tools representam intenções ou operações iniciadas pelo usuário.

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

Cada definição de Tool reside no `ToolRegistry`. A Toolbar que utiliza a Tool é responsável por criar sua instância.

Assim, a `Tool2` da `Toolbar1` e a `Tool2` da `Toolbar2` compartilham a mesma definição, mas são instâncias independentes:

```text
ToolRegistry
├── Tool1 (definition)
├── Tool2 (definition)
├── Tool3 (definition)
├── Tool4 (definition)
└── Tool5 (definition)

Toolbar1 creates Tool2 and Tool4
Toolbar2 creates Tool1, Tool2, and Tool4
```

### Fluxo de resolução

```text
Toolbar (dentro de um Editor)
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
Usuário
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

Quando ativada, uma Tool recebe um contexto controlado fornecido pelo Editor por meio da Toolbar. Esse contexto pode conter referências a consultas da Scene, serviços de seleção, despacho de Commands, assinaturas de eventos e serviços especializados.

Uma Tool não deve presumir conhecimento sobre a posição do Editor na interface.

### Ciclo de vida

```text
Tool.__init__        → criada pela Toolbar
Tool.activate(ctx)   → ativada pelo usuário
Tool.deactivate()    → desativada
Tool.dispose()       → destruída com a Toolbar
```

O estado temporário de uma Tool pode ou não persistir entre `deactivate()` e `activate()`, dependendo da natureza da Tool. Tools de medição geralmente são reiniciadas; Tools de seleção geralmente preservam seu estado.

### Isolamento de estado

Como cada Toolbar cria suas próprias instâncias de Tools, o estado de execução não é compartilhado acidentalmente entre diferentes Toolbars. Isso é especialmente importante quando a mesma Tool aparece em diferentes contextos, como uma `MeasureTool` em um `Viewport3DEditor` e em um `MPRViewerEditor`.

A decisão arquitetural é, portanto:

> A Toolbar cria suas próprias instâncias de Tools a partir das definições fornecidas pelo ToolRegistry. A mesma Tool pode ser referenciada por diferentes Toolbars, mas cada Toolbar mantém instâncias independentes.

## 12. Conteúdo do Editor

O conteúdo apresentado por um Editor varia de acordo com sua finalidade.

### Viewport 3D

```text
Viewport3DEditor
├── viewport 3D
├── câmera
├── seleção
├── overlays
└── tools
```

### MPR Viewer

```text
MPRViewerEditor
├── visualização axial
├── visualização sagital
├── visualização coronal
├── crosshair
├── navegação pelos slices
└── ferramentas de imagem
```

### Propriedades

```text
PropertiesEditor
├── informações do objeto
├── transformação
├── aparência
└── propriedades clínicas
```

### Editor de Nodes

```text
NodeEditor
├── canvas de nodes
├── nodes
├── links
├── ferramentas de nodes
└── navegação pelo grafo
```

O conteúdo específico não deve ser confundido com a Area que o hospeda.

## 13. Editors planejados

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

## 14. Editors e Modules

Module e Editor não são equivalentes.

Um Module representa uma funcionalidade do CranioZ.

Um Editor representa uma experiência de interface utilizada para trabalhar com essa funcionalidade.

A relação entre eles é:

```text
Module
 ├── Commands
 ├── Tools
 ├── Services
 └── Editor specifications
```

Um Module pode declarar que uma funcionalidade utiliza determinado Editor, mas não é proprietário nem instancia o Editor.

Por exemplo:

```text
Orthognathic Module
    │
    ├── declara: viewport_3d
    ├── declara: mpr_viewer
    └── declara: cephalometry
```

O Workspace e o `EditorRegistry` são responsáveis por criar as instâncias reais.

Isso permite que diferentes Modules utilizem o mesmo Editor sem duplicar sua implementação.

## 15. Editors compartilhados

Os Editors devem ser projetados para reutilização.

Por exemplo, o `Viewport3DEditor` pode ser utilizado para:

- planejamento ortognático;
- implantes faciais;
- osteossíntese;
- reconstrução mandibular;
- planejamento de rinoplastia;
- planejamento de guias cirúrgicos;
- análise de modelos.

O Editor fornece a experiência genérica de interação.

A lógica específica da aplicação é fornecida por:

- Modules;
- Tools;
- Commands;
- Services;
- Scene;
- contexto da aplicação.

## 16. EditorContext

Um Editor pode receber um contexto de execução contendo referências controladas aos serviços de que necessita.

O contexto deve ser pequeno e orientado a interfaces. Ele não deve se tornar um barramento global de comunicação nem um God Object.

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

Um exemplo conceitual:

```python
class Viewport3DEditor(Editor):
    def initialize(self, context: EditorContext) -> None:
        self._scene_query = context.scene_query
        self._selection = context.selection_service
        self._commands = context.command_dispatcher
        self._events = context.event_subscription
```

O Editor recebe apenas o contexto de que necessita.

Uma Tool deve receber um `ToolContext` ainda mais restrito sempre que possível:

```text
ToolContext
├── SceneQuery
├── SelectionService
├── CommandDispatcher
└── ToolServices
```

## 17. Estado do Editor

O estado clínico deve ser separado do estado puramente visual.

### Estado clínico

Pertence à aplicação e à Scene.

Exemplos:

- a posição da mandíbula;
- um plano de osteotomia;
- a posição de um implante;
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
- configuração do viewport;
- layout interno da Toolbar.

Essa separação impede que informações temporárias da interface sejam confundidas com os dados clínicos do projeto.

## 18. Overlays

Overlays são elementos temporários ou flutuantes apresentados sobre um Editor.

Os exemplos incluem:

- gizmos;
- crosshairs;
- medições;
- marcadores;
- indicadores;
- menus de contexto;
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

Os Overlays são gerenciados pelo Editor. O `EditorHost` pode coordenar o ciclo de vida visual, mas não é responsável pela semântica dos Overlays.

Overlays interativos, como gizmos, podem participar do hit testing.

Os Overlays possuem uma ordem de renderização, ou z-order, definida pelo Editor.

Os Overlays não devem alterar diretamente o estado clínico; Overlays interativos devem utilizar Commands quando uma alteração clínica for necessária.

## 19. Independência espacial

Um dos princípios fundamentais dos Editors é:

> Um Editor não deve saber onde está.

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

## 20. ToolRegistry

O `ToolRegistry` mantém as definições de Tools disponíveis no sistema.

Ele é responsável por:

- registrar definições de Tools;
- localizar uma definição por meio de `tool_id`;
- fornecer factories ou classes;
- validar as Tools referenciadas pelas Toolbars.

Conceitualmente:

```text
ToolRegistry
├── select_tool
├── transform_tool
├── measure_tool
├── landmark_tool
└── ...
```

O `ToolRegistry` não mantém instâncias em execução. Ele fornece definições ou factories; a Toolbar cria e possui as instâncias que utiliza.

```text
Toolbar (dentro de um Editor)
   │ resolve tool_id
   ▼
ToolRegistry
   │ retorna factory/classe
   ▼
Toolbar cria a Tool
```

Essa separação permite:

- reutilizar definições entre Toolbars;
- isolar o estado por instância;
- testar com Tools simuladas;
- evoluir independentemente as definições e os usos.

## 21. Princípios arquiteturais

Os seguintes princípios devem orientar a implementação.

### 21.1 Um Editor é funcional, não espacial

A posição pertence à Area e ao Layout.

### 21.2 Um Editor não instancia outros Editors

A composição é responsabilidade do Workspace e do Layout.

### 21.3 Um Module não possui Editors

Os Modules declaram necessidades de interface; o Workspace resolve e cria as instâncias dos Editors.

### 21.4 O Layout é declarativo

Os Layouts utilizam identificadores e especificações estáveis, evitando referências diretas a classes concretas.

### 21.5 O Registry cria instâncias

Classes concretas não aparecem nas definições dos Layouts.

### 21.6 Um Editor não contém lógica clínica

A lógica clínica pertence aos Modules, Services, Domain e às camadas de Application.

### 21.7 Alterações persistentes de estado utilizam Commands

Quando uma interação altera o estado persistente da aplicação, o Editor deve utilizar Commands em vez de modificar diretamente a Scene clínica.

### 21.8 Events notificam alterações

Events não substituem Commands e não devem funcionar como o mecanismo primário de escrita.

### 21.9 O estado visual e o estado clínico permanecem separados

A interface pode manter um estado temporário sem contaminar o modelo clínico.

### 21.10 Os Hosts controlam a apresentação espacial

Docking, janelas flutuantes e múltiplos monitores não devem contaminar a implementação do Editor.

### 21.11 Os Editors devem ser reutilizáveis

Um tipo de Editor deve poder ser utilizado por vários Modules e Layouts.

### 21.12 O contexto deve ser mínimo

As dependências são fornecidas por meio de interfaces específicas.

### 21.13 Qt é um detalhe de apresentação

A arquitetura lógica dos Editors deve permanecer o mais independente possível dos widgets concretos do Qt.

### 21.14 O Editor declara e materializa sua própria Toolbar

O Editor declara a composição da Toolbar e a materializa dentro do seu próprio espaço de conteúdo, respeitando a orientação declarada. O `EditorHost` não materializa Toolbars; ele apenas hospeda o Editor.

### 21.15 O ToolRegistry fornece definições; a Toolbar cria instâncias

Uma definição de Tool é registrada uma vez e pode ser reutilizada. A instância de execução pertence à Toolbar que a utiliza.

### 21.16 Os Editors devem ser testáveis sem Qt

A lógica do Editor — inicialização, ativação, gerenciamento de estado e tratamento de interações — deve ser testável sem dependências de widgets Qt concretos.

A materialização específica do Qt — Content, Toolbar e Overlays — deve ser isolada para que possa ser simulada ou substituída em testes unitários.

## 22. Fluxo completo

A arquitetura pode ser resumida pelo seguinte fluxo:

```text
                    ┌───────────────┐
                    │    Module     │
                    └───────┬───────┘
                            │
                    declara o Editor
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
│   Area    │──────▶│  EditorHost   │  (apenas hospeda)
└───────────┘       └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Editor     │  (declara e
                    │               │   materializa seu
                    │               │   próprio chrome interno)
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Toolbar        Content       Overlays
          (Editor)       (Editor)      (Editor)
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

Essa arquitetura permite que o CranioZ mantenha uma interface altamente configurável sem transformar o Workspace em uma coleção de componentes específicos de Modules clínicos individuais.

O princípio central é:

```text
Workspace = composição
Layout    = organização
Area      = espaço
Editor    = experiência funcional
Toolbar   = composição de Tools (interna ao Editor)
Tool      = intenção
Command   = mudança
Module    = funcionalidade
Scene     = estado clínico
```

Este modelo deve ser considerado a base para a evolução do sistema de Editors do CranioZ.
