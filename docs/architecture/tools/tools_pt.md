Tools
1. Visão geral

Uma Tool representa uma ação operacional que pode ser disponibilizada ao usuário por um módulo do CranioZ.

Tools são a principal interface entre o usuário e as operações executáveis de um módulo. Elas podem ser apresentadas em diferentes regiões da interface — por exemplo, em uma toolbar, painel lateral, menu contextual ou outro Editor — sem que sua definição dependa de uma posição específica no Workspace.

Uma Tool não representa o módulo em si, nem necessariamente implementa diretamente a operação clínica ou geométrica. Ela define como uma operação é apresentada, identificada e acionada no contexto da aplicação.

A execução efetiva deve ser delegada à camada apropriada da aplicação, normalmente por meio de Commands, Services ou outros mecanismos definidos pelos contratos do framework.

A relação conceitual é:

User
  │
  ▼
Tool
  │
  ▼
Command / Service
  │
  ▼
Domain

Essa separação permite que a mesma operação seja acionada por diferentes mecanismos sem duplicação de lógica.

2. Objetivos

O sistema de Tools deve:

fornecer uma interface uniforme para ações executáveis;
permitir que módulos exponham suas funcionalidades à UI;
separar apresentação e interação da lógica de negócio;
permitir diferentes formas de apresentação da mesma Tool;
facilitar descoberta e registro de funcionalidades;
permitir habilitação/desabilitação contextual;
fornecer metadados suficientes para construção automática da UI;
permitir acionamento por interação humana ou por sistemas automatizados;
manter as operações independentes de uma localização específica no Workspace;
possibilitar integração futura com automação e MCP.

Uma Tool deve ser suficientemente declarativa para que a aplicação consiga determinar o que ela é, quando pode ser utilizada e como deve ser apresentada, sem que o módulo precise conhecer detalhes específicos da UI.

3. Tool não é Command

Tool e Command são conceitos relacionados, mas diferentes.

Tool

Representa uma ação disponibilizada ao usuário.

Responde principalmente às perguntas:

O que esta ação faz?
Como ela é identificada?
Como aparece na interface?
Quando está disponível?
Como pode ser acionada?
Command

Representa uma operação executável pela aplicação.

Responde principalmente às perguntas:

Qual operação será executada?
Quais são seus parâmetros?
Como pode ser desfeita?
Como participa do histórico de operações?
Quais eventos são produzidos?

Assim:

Tool
 └── executa → Command

mas:

Command
 └── não depende necessariamente de uma Tool

Um Command pode ser executado por:

Tool;
atalho de teclado;
menu;
macro;
workflow;
automação;
MCP;
script;
outra operação interna.

Da mesma forma, uma Tool pode representar uma interação mais complexa que resulte na execução de um ou vários Commands.

4. Tool como contrato

No framework, Tool deve ser tratada inicialmente como um contrato.

Uma Tool deve definir, no mínimo:

identifier
label
description
icon
category
availability
execution

A implementação concreta pode variar.

Conceitualmente:

class Tool(ABC):
    identifier: str
    label: str
    description: str
    icon: str | None
    category: str | None

    def is_available(self, context) -> bool:
        ...

    def execute(self, context) -> None:
        ...

A interface definitiva deve permanecer pequena. Recursos adicionais devem ser adicionados apenas quando houver necessidade arquitetural real.

5. Identidade

Cada Tool deve possuir um identificador único e estável.

Exemplo:

orthognathic.cephalometry.add_landmark

ou:

osteotomy.create_lefort_i

O identificador deve:

ser único dentro do sistema;
ser estável entre versões sempre que possível;
não depender do texto apresentado ao usuário;
não depender da posição da Tool na interface;
poder ser utilizado por Commands, menus, plugins e automações.

O label é destinado à apresentação.

Exemplo:

identifier:
    orthognathic.cephalometry.add_landmark

label:
    Add Landmark

A alteração do texto apresentado ao usuário não deve alterar a identidade da Tool.

6. Apresentação

Uma Tool não deve determinar diretamente onde será exibida.

Por exemplo, uma Tool pode ser apresentada:

em uma toolbar;
em um menu;
em um painel;
em um menu contextual;
em uma Command Palette;
em um Editor;
em uma interface de módulo.

A decisão de posicionamento pertence à camada de UI e ao sistema de Workspace/Layout.

Portanto:

Tool
 └── define a ação

Layout / Workspace
 └── define onde a ação aparece

Isso é particularmente importante no CranioZ porque o mesmo conjunto de Tools poderá ser utilizado em diferentes layouts e contextos.

7. Tool e Editor

Editors e Tools possuem responsabilidades diferentes. Um Editor fornece um espaço de interação especializado. Uma Tool fornece uma ação que pode ser utilizada nesse contexto.

Por exemplo:

3D Editor
 ├── Select
 ├── Move
 ├── Rotate
 ├── Measure
 └── Landmark

ou:

Cephalometric Editor
 ├── Add Landmark
 ├── Move Landmark
 ├── Remove Landmark
 ├── Measure Angle
 └── Measure Distance

O Editor não deve precisar implementar novamente cada operação.

Da mesma forma, uma Tool não deve assumir que será utilizada exclusivamente por um determinado Editor, salvo quando sua própria definição exigir um contexto específico.

8. Contexto de execução

Tools frequentemente dependem do estado atual do sistema. Por exemplo, uma Tool de osteotomia pode somente estar disponível quando:

* existe uma mandíbula carregada;
* o modelo está em um estado válido;
* o módulo de osteotomia está ativo;
* o usuário possui uma seleção válida;
* o Editor atual suporta a operação.

A Tool deve, portanto, consultar um contexto de execução.

Conceitualmente:

    Tool
       │
       ├── Context
       │     ├── Project
       │     ├── Selection
       │     ├── Scene
       │     ├── Active Editor
       │     ├── Active Module
       │     └── Application State
       │
       └── Execution

Isso permite que a disponibilidade seja determinada dinamicamente.

Exemplo:

    def is_available(self, context: ToolContext) -> bool:
        return (
            context.selection.has_mandible
            and context.scene.has_patient
        )

A UI pode utilizar essa informação para habilitar, desabilitar ou ocultar a Tool conforme o contexto.

9. Estado da Tool

A disponibilidade de uma Tool deve ser distinta de sua existência.

Uma Tool pode:

    Registered
        ↓
    Available
        ↓
    Enabled
        ↓
    Executed

ou estar registrada, mas indisponível no contexto atual.

Exemplo:

    Create Le Fort I Osteotomy
        Registered: yes
        Available: no
        Enabled: no

quando não existe uma maxila válida.

O estado deve ser determinado pelo contexto da aplicação, e não mantido como estado arbitrário dentro da UI.

10. Execução

A execução de uma Tool não deve concentrar lógica clínica ou geométrica complexa.

O fluxo preferencial é:

User
  │
  ▼
Tool
  │
  ▼
Command
  │
  ├── Domain
  ├── Service
  └── Infrastructure

Exemplo:

Tool:
    Create Le Fort I Osteotomy

Command:
    CreateOsteotomyCommand

Domain:
    Osteotomy
    Bone
    Geometry

Service:
    OsteotomyService

A Tool funciona como uma camada de interação.

Isso evita que a UI contenha lógica de domínio.

11. Tools interativas

Nem todas as Tools correspondem a uma ação instantânea.

Algumas representam uma interação contínua com o usuário.

Exemplos:

* Select;
* Move;
* Rotate;
* Draw;
* Measure;
* Place Landmark;
* Define Osteotomy Plane;
* Paint Segmentation;
* Sculpt;
* Place Implant.

Nesses casos, a Tool pode possuir um ciclo de vida próprio.

Conceitualmente:

    Idle
      ↓
    Activated
      ↓
    Interacting
      ↓
    Completed
      ↓
    Deactivated
    
    Exemplo:
    
    Define Osteotomy Plane
        ↓
    Tool activated
        ↓
    User selects points
        ↓
    Plane preview
        ↓
    User confirms
        ↓
    Command executed
        ↓
    Tool deactivated

A Tool pode, portanto, funcionar como uma pequena máquina de estados de interação, enquanto a alteração persistente do modelo continua sendo responsabilidade da camada de aplicação/domínio.

## 12. Modalidade de execução

As Tools podem ser classificadas de acordo com sua interação.

### 12.1 Action Tool

Executa uma ação diretamente.

    Save
    Undo
    Add Landmark
    Create Plate
    12.2 Interactive Tool

Permanece ativa enquanto o usuário interage com a cena.

    Select
    Move
    Measure
    Place Landmark
    Draw Osteotomy
    12.3 Toggle Tool

Alterna entre dois estados.

Show/Hide
Snap
Visibility
Orthographic/Perspective

### 12.4 Stateful Tool

Mantém um estado de interação mais complexo.

Segmentation Brush
Sculpt
Registration
Osteotomy Planning

Essa classificação é útil para o comportamento da UI, mas não deve criar subclasses desnecessárias se uma interface comum for suficiente.

## 13. Tool e Command History

Quando uma Tool produz uma alteração persistente no projeto, essa alteração deve preferencialmente ocorrer através de um Command.

Exemplo:

    User clicks "Move Landmark"
            ↓
    Move Landmark Tool
            ↓
    MoveLandmarkCommand
            ↓
    Landmark moved
            ↓
    Command Stack

Isso permite:

* Undo;
* Redo;
* histórico;
* macros;
* automação;
* auditoria da operação;
* integração futura com MCP.

A Tool não deve implementar diretamente o mecanismo de Undo/Redo.

## 14. Tool Groups

Tools podem ser agrupadas semanticamente.

Exemplo:

    Cephalometry
    ├── Add Landmark
    ├── Move Landmark
    ├── Delete Landmark
    ├── Measure Distance
    └── Measure Angle

ou:

    Osteotomy
    ├── Create Osteotomy
    ├── Edit Osteotomy
    ├── Move Segment
    ├── Rotate Segment
    └── Confirm Osteotomy

O agrupamento é principalmente uma preocupação de apresentação e descoberta.

A Tool continua sendo uma unidade independente.

## 15. Tool Categories

Uma Tool pode possuir uma categoria para facilitar sua organização.

Exemplos:

* Selection
* Navigation
* Measurement
* Annotation
* Modeling
* Planning
* Segmentation
* Analysis
* Visualization
* Documentation

As categorias não devem ser excessivamente rígidas.

Um módulo pode definir categorias próprias quando necessário, desde que não conflitem com as categorias globais do framework.

## 16. Tool Parameters

Algumas Tools precisam de parâmetros.

Exemplo:

    Create Plate
        thickness = 1.5 mm
        hole_diameter = 2.0 mm
        locking = true

A Tool não deve necessariamente possuir todos esses parâmetros internamente.

Quando apropriado, ela pode abrir uma interface de configuração ou produzir um Command parametrizado.

Exemplo:

    Create Plate Tool
            ↓
    Plate Configuration
            ↓
    CreatePlateCommand(
        thickness=1.5,
        hole_diameter=2.0,
        locking=True
    )

Isso mantém a definição da operação separada da apresentação dos parâmetros.

## 17. Tool Registry

O CranioZ deve possuir um mecanismo de registro de Tools.

Conceitualmente:

    ToolRegistry
    ├── register(tool)
    ├── unregister(identifier)
    ├── get(identifier)
    ├── find(...)
    └── list(...)

O Registry permite que:

módulos registrem suas Tools;
plugins adicionem Tools;
a UI descubra Tools disponíveis;
menus e toolbars sejam construídos dinamicamente;
sistemas de automação encontrem ações disponíveis.

Exemplo:

    Module
       ↓
    register Tools
       ↓
    ToolRegistry
       ↓
       UI

## 18. Tools fornecidas por módulos

Cada módulo pode declarar as Tools que disponibiliza.

Exemplo:

    Cephalometry Module
    
    Tools:
        Add Landmark
        Move Landmark
        Delete Landmark
        Measure Distance
        Measure Angle

O módulo é responsável por declarar as Areas necessárias. Exemplo Módulo segmentação precisa da Area de Segmentação que possui a toolbar de Segmentação e nesta toolbar algumas tools.

Isso permite:

    Module
     ├── Commands
     ├── Tools
     ├── Services
     └── Capabilities

sem transformar o módulo em uma extensão direta da UI.

## 19. Tools fornecidas por plugins

Plugins podem registrar Tools da mesma forma que módulos internos.

Exemplo:

    Plugin
        ↓
    ToolRegistry
        ↓
    Custom Tool

Isso permite que terceiros adicionem funcionalidades sem modificar o Core do CranioZ.

Exemplo hipotético:

AI Segmentation Plugin
    └── Automatic Segmentation Tool

ou:

Rhinoplasty Plugin
    ├── Nasal Landmark Tool
    ├── Nasal Osteotomy Tool
    └── Soft Tissue Simulation Tool

## 20. Tool Manifest

Quando uma Tool pertence a um plugin, seus metadados podem ser declarados no manifest do plugin.

Exemplo conceitual:

tools:
  - id: rhinoplasty.add_landmark
    label: Add Landmark
    category: annotation

  - id: rhinoplasty.simulate
    label: Simulate
    category: simulation

O manifest descreve a Tool, mas não deve substituir sua implementação.

## 21. Tool e Capability

Capability descreve uma capacidade que um módulo ou componente oferece. Tool representa uma forma de utilizar uma capacidade por meio de uma ação.

Exemplo:

Capability:
    cephalometric_analysis

Tools:
    Add Landmark
    Measure Angle
    Calculate Analysis

Uma Capability responde:

"O sistema consegue fazer isso?"

Uma Tool responde:

"Qual ação o usuário pode executar para fazer isso?"

Essa distinção será especialmente importante para automação e MCP.

## 22. Tool e Service

_Services_ implementam operações ou regras de aplicação que não devem pertencer à Tool.

Exemplo:

Tool:
    Register Models

Service:
    RegistrationService

A Tool inicia a operação.

O Service executa a lógica necessária.

Register Models Tool
        ↓
RegisterModelsCommand
        ↓
RegistrationService
        ↓
Registration algorithm

## 23. Tool e MCP

O sistema de Tools deve ser projetado de forma que possa futuramente ser exposto a agentes ou sistemas externos.

Entretanto, Tool e MCP Tool não devem ser considerados necessariamente a mesma abstração.

Uma Tool do CranioZ representa uma ação da aplicação.

Uma interface MCP representa uma ação disponibilizada para um agente externo.

A arquitetura pode permitir:

    CranioZ Tool
          │
          ▼
    Command / Application Service
          ▲
          │
    MCP Tool

Assim, o MCP não precisa controlar diretamente a UI.

Um agente poderia solicitar:

create_osteotomy(...)

e a aplicação executar a mesma operação fundamental utilizada por uma Tool da interface gráfica.

Isso reduz duplicação e mantém as operações sujeitas às mesmas validações.

## 24. Segurança e validação

Tools não devem ser consideradas uma fronteira de segurança ou validação suficiente.

Uma operação crítica deve ser validada também nas camadas de aplicação/domínio.

Por exemplo:

    UI Tool
        ↓
    Command
        ↓
    Application validation
        ↓
    Domain validation
        ↓
    Operation

Isso é necessário porque Commands podem ser acionados por mecanismos diferentes da UI.

## 25. Exemplo: Tool de Landmark

Um exemplo simples:

Tool
    Add Landmark

Context:
    active patient
    active 3D editor
    valid anatomical model

Interaction:
    user clicks on model

Result:
    AddLandmarkCommand

Fluxo:

Add Landmark Tool
        │
        │ user interaction
        ▼
Landmark position
        │
        ▼
AddLandmarkCommand
        │
        ▼
Cephalometric Landmark
        │
        ▼
Scene / Project

A Tool não precisa conhecer os detalhes de persistência do Landmark.

26. Exemplo: Tool de osteotomia
Define Osteotomy Tool
        │
        ▼
User selects anatomical region
        │
        ▼
Interactive preview
        │
        ▼
User confirms
        │
        ▼
CreateOsteotomyCommand
        │
        ▼
Osteotomy domain object
        │
        ▼
Scene update

A mesma operação poderá posteriormente ser acionada por:

Toolbar
Menu
Shortcut
Workflow
MCP
Script

sem que a lógica de osteotomia seja duplicada.

27. Organização do código

A definição dos contratos deve permanecer na infraestrutura de módulos do framework:

src/cranioz/modules/

├── base/
│   ├── module.py
│   ├── module_state.py
│   └── lifecycle.py
│
├── contracts/
│   ├── command.py
│   ├── tool.py
│   ├── service.py
│   └── capability.py
│
├── specs/
│   └── module_spec.py

O contrato de Tool deve permanecer pequeno e estável.

Implementações específicas devem permanecer nos módulos que as utilizam.

Exemplo:

src/cranioz/modules/
└── cephalometry/
    ├── tools/
    │   ├── add_landmark.py
    │   ├── move_landmark.py
    │   └── measure_angle.py
    │
    ├── commands/
    │   └── ...
    │
    └── services/
        └── ...

A organização exata dos diretórios pode variar conforme a maturidade do módulo, mas a separação conceitual deve ser preservada.

28. Princípios arquiteturais

O sistema de Tools do CranioZ deve seguir os seguintes princípios:

1. Tool é uma interface de interação

Não é o domínio e não deve conter lógica clínica complexa.

2. Tool não é Command

Uma Tool pode disparar um Command, mas o Command deve permanecer independente da UI.

3. Tool não pertence a uma Area

Uma Tool pode ser apresentada em qualquer Area ou Editor compatível.

4. Tool deve ser contextual

Sua disponibilidade pode depender do estado atual do projeto, seleção, Editor ou módulo.

5. Tool deve possuir identidade estável

O identificador deve ser independente do texto e da posição na interface.

6. Tool deve ser descobrível

Tools devem poder ser registradas e consultadas pelo framework.

7. Tool deve ser reutilizável

A mesma operação deve poder ser acionada por diferentes mecanismos.

8. Validação não deve depender da UI

Operações importantes devem ser validadas nas camadas de aplicação/domínio.

9. Plugins podem fornecer Tools

O mecanismo deve funcionar tanto para módulos internos quanto para extensões externas.

10. Tools devem ser compatíveis com automação

A arquitetura deve permitir que Commands e Services sejam utilizados futuramente por workflows, scripts e MCP.

29. Resumo conceitual

A arquitetura pode ser resumida da seguinte forma:

                         ┌───────────────┐
                         │     User      │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │     Tool      │
                         │               │
                         │ interaction   │
                         │ presentation  │
                         │ availability  │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    Command    │
                         │               │
                         │ execution     │
                         │ undo/redo     │
                         └───────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
             ┌───────────────┐       ┌───────────────┐
             │    Service    │       │    Domain     │
             │               │       │               │
             │ application   │       │ clinical      │
             │ logic         │       │ semantics     │
             └───────────────┘       └───────────────┘

Em paralelo:

Module
 ├── Tools
 ├── Commands
 ├── Services
 └── Capabilities

E na interface:

Workspace
   │
   ├── Area
   │    └── Editor
   │         └── Tool
   │
   ├── Area
   │    └── Editor
   │         └── Tool
   │
   └── Area
        └── Editor
             └── Tool

A ideia central é que Tool seja a unidade de ação/interação do framework, enquanto Command seja a unidade de execução e histórico, Service seja a unidade de lógica de aplicação reutilizável, Domain seja a unidade de significado clínico e computacional, e Capability descreva aquilo que um módulo é capaz de oferecer.

Essa separação fornece ao CranioZ uma base adequada para uma aplicação desktop modular, extensível por plugins e preparada para workflows e automação sem acoplar a arquitetura clínica à interface gráfica.