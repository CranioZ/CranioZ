O que você acha? Modules

## 1. Visão geral

Os **Modules** são componentes funcionais do CranioZ responsáveis por implementar uma **funcionalidade clínica** ou um **domínio de aplicação**.

Um Module define **o que o sistema faz**, não **como a interface se apresenta** nem **onde os componentes são posicionados**.

A arquitetura de Modules segue a seguinte hierarquia conceitual:

```
Application
└── Modules
    ├── Commands
    ├── Tools
    ├── Services
    ├── Domain
    └── Capabilities
```

Essa separação é fundamental para permitir que a mesma funcionalidade clínica seja utilizada por diferentes configurações de interface sem que o Module dependa de detalhes de apresentação.

Por exemplo, o `OrthognathicModule` pode declarar que necessita das capacidades `3d-visualization`, `image-slice-view` e `landmark-overlay`, sem conhecer as classes concretas dos Editors que as fornecem nem onde eles serão hospedados.

---

## 2. Responsabilidades

Um Module é responsável por:

- implementar uma funcionalidade clínica ou domínio de aplicação;
- declarar Commands específicos do domínio;
- declarar Tools específicas do domínio;
- fornecer Services utilizados por outras partes do sistema;
- declarar as capacidades de interface necessárias à sua funcionalidade;
- declarar suas dependências em relação a outros Modules;
- expor sua API para outros Modules e para a Application;
- manter seu próprio estado de execução.

Um Module **não é responsável por**:

- criar ou gerenciar `Areas`;
- definir o Layout do Workspace;
- instanciar Editors;
- instanciar Tools;
- controlar docking ou divisão espacial;
- gerenciar outros Modules;
- registrar-se em registries diretamente;
- implementar lógica de apresentação pertencente a Editors;
- modificar diretamente o estado clínico fora do fluxo de Commands.

A separação pode ser resumida como:


```
Module  → funcionalidade clínica
Command → alteração de estado
Service → capacidade reutilizável
Tool    → intenção do usuário
Editor  → experiência de interface
Scene   → estado clínico
```

---

## 3. Module versus Editor

`Module` e `Editor` não são equivalentes.

### Module

O Module representa uma **funcionalidade do CranioZ**.

Ele controla aspectos como:

- lógica clínica;
- Commands;
- Services;
- Tools;
- regras de domínio;
- integração com outros Modules;
- declaração de capacidades de interface.

O Module não possui nem instancia Editors.

### Editor

O Editor representa uma **experiência de interface** utilizada para trabalhar com essa funcionalidade.

Ele controla aspectos como:

- visualização;
- interação;
- ferramentas;
- seleção;
- manipulação;
- navegação;
- apresentação de informações.


```
Module  → funcionalidade
Editor  → experiência de interface
```

A relação é de **declaração**, não de posse:

```
Module
 ├── Commands
 ├── Tools
 ├── Services
 ├── Domain
 └── Capabilities
```


O Module pode declarar que determinada funcionalidade necessita de certas capacidades de interface, mas **não possui nem instancia os Editors** que as fornecem.

---

## 4. ModuleHost

A comunicação entre `Application` e `Module` pode ser realizada por meio de um `ModuleHost`.


```
Application
└── ModuleHost
    └── Module
```


O `ModuleHost` funciona como camada de hospedagem e adaptação entre a infraestrutura da Application e a implementação funcional do Module.

Suas responsabilidades incluem:

- hospedar a instância do Module;
- conectar o Module à Application;
- administrar o ciclo de vida lógico;
- fornecer o contexto necessário para o Module;
- adaptar a implementação do Module ao sistema de Modules.

O `ModuleHost` **não registra** Commands, Tools ou Services. O registro é responsabilidade do `ModuleLoader`.

O `ModuleHost` não deve assumir responsabilidades de interface.

---

## 5. Interface base

Todos os Modules devem derivar de uma abstração comum.

Uma implementação conceitual pode ser representada por:


```
class Module(ABC):
    id: str
    name: str
    version: str

    def initialize(self, context: "ModuleContext") -> None:
        ...

    def activate(self) -> None:
        ...

    def deactivate(self) -> None:
        ...

    def dispose(self) -> None:
        ...
```

A interface concreta poderá evoluir conforme as necessidades do sistema.

O objetivo da classe base não é impor uma implementação específica, mas estabelecer um contrato comum para registro, criação e ciclo de vida.

### Ciclo de vida síncrono

```
constructed → initialized → active ⇄ inactive → disposed
```


### Ciclo de vida com carregamento

Como alguns Modules podem ser carregados sob demanda ou em background, o ciclo completo é:

text

```
registered → loaded → initialized → active ⇄ inactive → unloaded → disposed
```


### Contratos do ciclo de vida

| **Método**            | **Pode falhar?** | **Idempotente?** | **Pode ser chamado múltiplas vezes?** |
| :-------------------- | :--------------- | :--------------- | :------------------------------------ |
| `initialize(context)` | Sim              | Não              | Não                                   |
| `activate()`          | Sim              | Não              | Não                                   |
| `deactivate()`        | Não              | Sim              | Não (no-op se já inativo)             |
| `dispose()`           | Não              | Sim              | Sim                                   |

Regras adicionais:

- `activate()` só é válido após `initialized`.
- `deactivate()` só é válido após `active`.
- Um Module **inativo não recebe eventos**; deve desinscrever-se em `deactivate()`.
- Services permanecem disponíveis durante `deactivate()`, mas não após `dispose()`.
- `initialize()` pode falhar; o `ModuleLoader` trata a falha e reporta via `EventBus`.

---

## 6. Registro: regra única

Para evitar ambiguidade sobre quem registra o quê, adota-se a seguinte regra:

```
Module        → declara
ModuleLoader  → registra
Registry      → resolve
ModuleHost    → hospeda
```


Ou seja:

- O **Module declara** seus Commands, Tools, Services e capacidades.
- O **ModuleLoader registra** esses elementos nos registries apropriados.
- Os **Registries resolvem** por identificador.
- O **ModuleHost hospeda** a instância do Module.

O Module **não conhece diretamente** `ToolRegistry`, `EditorRegistry` ou `CommandStack`. Ele recebe abstrações via contexto.


```
Module
   │ declares
   ├── Commands  → CommandRegistry
   ├── Tools     → ToolRegistry
   ├── Services  → ServiceRegistry
   └── Capabilities → CapabilityRegistry

ModuleLoader
   │ registers
   ▼
Registries
```


---

## 7. ModuleRegistry

Os Modules são registrados no `ModuleRegistry`.

O Registry é responsável por:

- registrar Modules disponíveis;
- localizar um Module por `module_id`;
- fornecer metadados;
- controlar dependências entre Modules;
- validar Modules solicitados pela Application;
- controlar a ordem de inicialização.

Exemplo conceitual:

```
ModuleRegistry
│
├── orthognathic
├── implants
├── osteosynthesis
├── cephalometry
├── simulation
└── ...
```

O Registry permite que o sistema trabalhe com identificadores estáveis em vez de depender diretamente das classes concretas.

Por exemplo:

python

```
module_id = "orthognathic"
```

em vez de:


```
OrthognathicModule(...)
```


na configuração da Application.

---

## 8. Application e Modules

A Application é responsável por definir **quais Modules estão disponíveis e em qual ordem são carregados**.

Entretanto, a Application não instancia diretamente as classes dos Modules.

O fluxo é:

```
Application
   │
   │ module_id
   ▼
ModuleRegistry
   │
   │ create()
   ▼
Module
```


Dessa forma, a configuração da Application permanece declarativa.

Exemplo conceitual:

python

```
ModuleSpec(
    module_id="orthognathic",
    enabled=True,
)
```

A Application conhece:

text

```
"orthognathic"
```


mas não precisa conhecer:

```
OrthognathicModule
```

Essa responsabilidade pertence ao `ModuleRegistry`.

---

## 9. ModuleTree

O `ModuleTree` **descreve** a composição funcional da aplicação e as dependências entre Modules.

Ele descreve:

- Modules disponíveis;
- dependências entre Modules;
- política de carregamento;
- ordem de inicialização;
- visibilidade;
- estado habilitado/desabilitado;
- capacidades declaradas.

Conceitualmente:

```
ModuleTree
│
├── Module: Orthognathic
│   ├── depends on: Cephalometry
│   ├── depends on: Simulation
│   └── requires: 3d-visualization, image-slice-view
│
├── Module: Implants
│   └── depends on: Simulation
│
└── Module: Cephalometry
```


O `ModuleTree` **não controla** Commands, Tools ou Services. Ele apenas descreve a composição e as dependências. O registro efetivo pertence ao processo de carregamento.

O `ModuleTree` não contém widgets Qt concretos.

Ele representa a estrutura lógica funcional da aplicação.

---

## 10. Materialização de Modules

A ativação de Modules ocorre em etapas distintas:

text

```
ModuleTree
    │
    ▼
ModuleLoader
    │
    ▼
ModuleHosts
    │
    ▼
Modules ativos
```

### ModuleTree

Representação declarativa da composição funcional.

### ModuleLoader

Interpreta o ModuleTree, registra Commands, Tools e Services nos registries apropriados, resolve dependências e executa a política de carregamento.

### ModuleHost

Hospeda a instância do Module e a conecta à Application.

Essa separação evita que a estrutura lógica funcional fique acoplada à implementação específica de carregamento.

---

## 11. Carregamento e ciclo de vida assíncrono

Nem todo Module precisa estar carregado o tempo todo. Módulos de IA, bibliotecas pesadas de malhas 3D e funcionalidades ocasionais podem ser carregados sob demanda ou em background.

### Políticas de carregamento

```
module:
  id: ai-segmentation
  load: lazy | eager | async
  trigger: startup | project_open | user_action | background
  on_failure: notify_user | retry | disable
  timeout: 30s
```

### Estratégias

| **Estratégia** | **Comportamento**       | **Uso típico**                                |
| :------------- | :---------------------- | :-------------------------------------------- |
| **Eager**      | Carrega no startup      | Funcionalidades essenciais, módulos leves     |
| **Lazy**       | Carrega no primeiro uso | Módulos pesados, funcionalidades ocasionais   |
| **Async**      | Carrega em background   | Módulos que podem estar prontos eventualmente |

### Combinado


```
startup:
  - orthognathic    (eager)
  - cephalometry    (eager)

background:
  - mesh-processing (async)

on demand:
  - ai-segmentation (lazy)
  - simulation      (lazy)
```

### Estados observáveis

text

```
registered → loaded → initialized → active ⇄ inactive → unloaded → disposed
```


Diferenças cruciais:

- `registered` não implica `loaded`.
- `loaded` não implica `initialized`.
- `activate()` só é válido após `initialized`.
- `unloaded` não implica `disposed`.

### Regras

- Carregamento assíncrono é **cancelável**.
- Falhas são reportadas via `EventBus`, não propagadas.
- Dependências entre Modules com políticas diferentes devem ser resolvidas explicitamente.
- A UI deve poder representar `loading`, `failed`, `cancelled`.

### Dependências assíncronas

Se `ModuleA` depende de `ModuleB`, e `ModuleB` é lazy:

yaml

```
depends_on:
  - id: simulation
    required: true
    load_policy: promote  # promote | defer | optional
```



| **Política** | **Comportamento**                               |
| :----------- | :---------------------------------------------- |
| **promote**  | B é promovido a eager se A é eager              |
| **defer**    | A só é ativado quando B estiver carregado       |
| **optional** | A declara dependência opcional e trata ausência |

### Cancelamento

O `ModuleLoader` deve expor:

```
ModuleLoader.load(module_id) → Task[Module]
    estados: pending → loading → loaded | failed | cancelled

ModuleLoader.cancel(module_id)
```


O `initialize()` assíncrono deve cooperar com cancelamento (token) e liberar recursos parcialmente alocados.

---

## 12. Commands

Commands representam **alterações de estado** no CranioZ.

Um Module **declara** os Commands específicos do seu domínio.

Exemplos:
```
OrthognathicModule
├── MoveMandibleCommand
├── SetOsteotomyPlaneCommand
├── ApplySplintCommand
└── ResetPositionCommand

ImplantModule
├── PlaceImplantCommand
├── MoveImplantCommand
└── RemoveImplantCommand
```


Um Command deve:

- ser atômico;
- ser reversível (quando aplicável);
- ser rastreável;
- ser registrado no `CommandStack`.

O fluxo preferencial é:


```
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


Isso mantém undo/redo, rastreabilidade e comunicação entre componentes independentes.

---

## 13. Tools

Tools representam **intenções ou operações iniciadas pelo usuário**.

Um Module **declara** Tools específicas do seu domínio, que serão disponibilizadas para as Toolbars dos Editors.


```
OrthognathicModule
├── OsteotomyTool
├── SplintTool
└── LandmarkTool
```


As Tools declaradas por um Module são **registradas pelo ModuleLoader** no `ToolRegistry`.

A definição da Tool é única; a instanciação é responsabilidade da Toolbar que a utiliza.

```
Module
   │ declares tool
   ▼
ModuleLoader
   │ registers
   ▼
ToolRegistry
   │ fornece definição
   ▼
Toolbar
   │ instancia
   ▼
Tool
```

Uma Tool não deve modificar diretamente o estado clínico. Ela traduz a intenção do usuário em Command.

---

## 14. Services

Services representam **capacidades reutilizáveis** fornecidas por um Module.

Exemplos:

text

```
CephalometryModule
├── LandmarkDetectionService
├── CephalometricAnalysisService
└── MeasurementService

ImplantModule
├── ImplantLibraryService
├── ImplantPlacementService
└── ImplantValidationService
```

Um Service pode:

- ser consumido por outros Modules;
- ser consumido por Editors via `EditorContext`;
- ser substituído por implementações alternativas;
- ser testado isoladamente.

Services devem ser expostos por abstrações, evitando dependência direta de implementações concretas.

---

## 15. Domain

O Domain representa o **modelo conceitual** do Module.

Ele contém:

- entidades;
- value objects;
- regras de negócio;
- invariantes;
- políticas de domínio.

Exemplos:


```
OrthognathicDomain
├── Mandible
├── Maxilla
├── OsteotomyPlane
├── Splint
└── OrthognathicPlan
```

### Fronteira entre Domain, Scene e Services

| **Componente** | **Responsabilidade**                    | **Depende de**                |
| :------------- | :-------------------------------------- | :---------------------------- |
| **Domain**     | Regras, entidades, invariantes          | Nada (puro)                   |
| **Scene**      | Estado clínico persistente (instâncias) | Domain                        |
| **Services**   | Coordenação, análise, integração        | Domain, Scene (via abstração) |
| **Commands**   | Transição controlada da Scene           | Domain, Scene                 |

Regras explícitas:

- O Domain **não deve depender** da Scene.
- A Scene contém **instâncias persistentes** do modelo clínico.
- Services **coordenam** operações, análises e integrações.
- Commands fazem a **transição controlada** do estado da Scene.

Essa distinção será especialmente importante para simulação, análise cefalométrica e IA.

O Domain **não depende** de:

- Editors;
- Toolbars;
- Tools;
- widgets Qt;
- Layout;
- Areas.

O Domain é a parte mais estável e independente do Module.

---

## 16. Capabilities

Em vez de um Module depender diretamente de IDs específicos de Editors, ele declara **capacidades** que necessita.

```
requires:
  - 3d-visualization
  - image-slice-view
  - landmark-overlay
```


O Workspace resolve essas capacidades para Editors concretos.

```
Module
   │ declares capability
   ▼
CapabilityRegistry
   │ resolves to editor_id
   ▼
Workspace
   │ instantiates editor
   ▼
Editor
```


Isso reduz o acoplamento a nomes específicos de componentes e permite que diferentes configurações de interface atendam à mesma capacidade.

### Exemplo


```
Orthognathic Module
    │
    ├── requires: 3d-visualization
    ├── requires: image-slice-view
    └── requires: landmark-overlay
```

O Module **não sabe** se `3d-visualization` será atendida por um `Viewport3DEditor` ou por outro Editor futuro.

---

## 17. Contextos separados

O contexto de um Module deve ser **mínimo e específico**, evitando concentrar dependências desnecessárias.


```
ModuleContext
├── ModuleState
├── CancellationToken
├── ProgressReporter
└── ServiceContext

DomainContext
├── Scene (via abstração)
└── Domain

EditorContext
├── Scene
├── Selection
├── CommandStack
├── EventBus
└── Services

ToolContext
├── Scene
├── Selection
├── CommandStack
└── EventBus
```


O Module recebe **apenas o que precisa**. Isso evita que o `ModuleContext` se torne uma "Application disfarçada".

### Exemplo conceitual de uso

```
class OrthognathicModule(Module):
    def initialize(self, context: ModuleContext) -> None:
        self._state = context.module_state
        self._services = context.services
        self._cancel = context.cancellation_token

    def activate(self) -> None:
        self._events.subscribe("scene_changed", self._on_scene_changed)
        ...
```


O Module não recebe a aplicação inteira, apenas o contexto necessário.

---

## 18. Estado do Module

É importante separar o estado clínico do estado de execução do Module.

### Estado clínico

Pertence à Scene.

Exemplos:

- posição de uma mandíbula;
- plano de osteotomia;
- posição de um implante;
- landmarks;
- modelos anatômicos;
- splint.

### Estado do Module

Pode pertencer ao Module.

Exemplos:

- configuração do Module;
- cache de análise;
- estado de simulação;
- preferências do domínio.

### Estado visual

Pertence aos Editors.

Exemplos:

- zoom;
- câmera;
- slice atual;
- seleção visual;
- modo de apresentação.

Essa separação evita que informações transitórias de interface ou de execução sejam confundidas com dados clínicos do projeto.

---

## 19. Dependências entre Modules

Modules podem depender de outros Modules.

Exemplo:

text

```
OrthognathicModule
├── depends on CephalometryModule
├── depends on SimulationModule
└── depends on ImagingModule
```

svgsvg

As dependências devem ser:

- declaradas explicitamente;
- resolvidas pelo `ModuleLoader`;
- respeitadas na ordem de inicialização;
- validadas antes da ativação.

Dependências circulares devem ser detectadas e rejeitadas.

### Dependência ausente

Quando uma dependência não está disponível:

| **Política**      | **Comportamento**                            |
| :---------------- | :------------------------------------------- |
| `required: true`  | Module não é ativado; erro reportado         |
| `required: false` | Module é ativado com funcionalidade reduzida |

---

## 20. Persistência e versionamento

Como os Modules podem possuir configuração, estado de execução e Services, é necessário prever:

- identificador e versão do Module;
- migração de dados;
- compatibilidade de Commands persistidos;
- serialização de configurações;
- comportamento quando uma dependência não está disponível.

### Identificador e versão

yaml

```
module:
  id: orthognathic
  version: 2.1.0
  compatible_with:
    - ">=1.0.0 <3.0.0"
```

svgsvg

### Migração de dados

Projetos CranioZ antigos devem continuar abrindo após a evolução dos Modules.

text

```
Project (v1.0)
   │ load
   ▼
ModuleMigration
   │ apply migrations
   ▼
Project (v2.1)
```

svgsvg

### Compatibilidade de Commands

Commands persistidos podem ter sido definidos em versões anteriores do Module. O sistema deve:

- versionar Commands;
- fornecer migração quando a assinatura mudar;
- rejeitar Commands incompatíveis com mensagem clara.

### Serialização de configuração

yaml

```
module_config:
  orthognathic:
    default_landmarks: [...]
    auto_update: true
```

svgsvg

### Dependência ausente

Se um Module não estiver disponível ao abrir um projeto, o sistema deve:

- notificar o usuário;
- preservar os dados do projeto;
- permitir reabertura quando o Module estiver disponível.

---

## 21. Independência de interface

Um dos princípios fundamentais dos Modules é:

> **Um Module não deve saber como sua funcionalidade é apresentada.**

O mesmo Module pode ser utilizado com:

- diferentes Layouts;
- diferentes Editors;
- diferentes Toolbars;
- diferentes configurações de Workspace.

Sem modificar a implementação do Module.

A composição de interface pertence ao Workspace.

---

## 22. Registries

Os registries têm papéis distintos:

text

```
ModuleRegistry     → registra Modules
ToolRegistry       → registra definições de Tools
EditorRegistry     → registra Editors
CommandRegistry    → registra Commands
ServiceRegistry    → registra Services
CapabilityRegistry → registra capacidades de interface
```

svgsvg

Um Module pode:

- declarar Tools que serão registradas no `ToolRegistry`;
- declarar Commands que serão registrados no `CommandRegistry`;
- declarar Services que serão registrados no `ServiceRegistry`;
- declarar capacidades que serão resolvidas pelo `CapabilityRegistry`.

O Module **não instancia** nem Tools nem Editors.

O registro efetivo é responsabilidade do `ModuleLoader`.

text

```
Module
   │ declares
   ├── tools        → ToolRegistry
   ├── commands     → CommandRegistry
   ├── services     → ServiceRegistry
   └── capabilities → CapabilityRegistry
```

svgsvg

A instanciação pertence:

- das Tools → à Toolbar;
- dos Editors → ao Workspace/EditorHost.

---

## 23. Princípios arquiteturais

Os seguintes princípios devem orientar a implementação:

### 23.1 Module é funcional, não espacial

A posição pertence à `Area` e ao `Layout`.

### 23.2 Module não instancia Editors

A composição de interface é responsabilidade do Workspace/Layout.

### 23.3 Module não contém lógica de apresentação

A lógica de apresentação pertence aos Editors.

### 23.4 Module declara necessidades de interface

Modules declaram capacidades; o Workspace resolve e instancia.

### 23.5 Alterações de estado passam por Commands

Quando uma interação altera o estado persistente da aplicação, o Module deve utilizar Commands em vez de modificar diretamente a Scene.

### 23.6 Modules devem ser reutilizáveis

Um Module deve poder ser utilizado por diferentes configurações de interface e diferentes fluxos clínicos.

### 23.7 Estado clínico e estado do Module devem permanecer separados

O Module pode manter estado de execução sem contaminar o modelo clínico.

### 23.8 Qt é detalhe de implementação

A arquitetura lógica do Module deve permanecer o mais independente possível dos detalhes de apresentação do Qt.

### 23.9 ModuleLoader resolve dependências

Dependências entre Modules devem ser declaradas e resolvidas pelo `ModuleLoader`.

### 23.10 Modules devem ser testáveis sem interface

O contrato do Module deve permitir testes unitários sem dependência de widgets concretos.

### 23.11 Module declara, ModuleLoader registra, Registry resolve

O Module não conhece diretamente os registries.

### 23.12 Carregamento é declarativo, execução é responsabilidade do Loader

O `ModuleTree` declara a política de carregamento; o `ModuleLoader` a executa.

### 23.13 Módulos pesados devem suportar carregamento lazy ou assíncrono

Nenhum Module pesado deve bloquear o startup da aplicação.

### 23.14 Carregamento assíncrono deve ser cancelável

Toda operação de carregamento deve poder ser cancelada de forma limpa.

### 23.15 Estados intermediários devem ser observáveis

A UI deve poder representar `loading`, `failed`, `cancelled` etc.

### 23.16 Falhas de carregamento não devem derrubar a aplicação

Falha em um Module deve ser isolada e reportada, não propagada.

### 23.17 Domain não depende da Scene

O Domain é puro; a Scene contém instâncias do Domain.

### 23.18 Modules devem prever persistência e versionamento

Projetos antigos devem continuar abrindo após a evolução dos Modules.

---

## 24. Fluxo completo

A arquitetura pode ser resumida pelo seguinte fluxo:

text

```
                    ┌───────────────┐
                    │  Application  │
                    └───────┬───────┘
                            │
                      declares module
                            │
                            ▼
                    ┌───────────────┐
                    │  ModuleTree   │
                    └───────┬───────┘
                            │
                         module_id
                            │
                            ▼
                    ┌───────────────┐
                    │ ModuleLoader  │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         registers     resolves      load policy
              │             │             │
              ▼             ▼             ▼
        Registries    Dependencies   eager/lazy/async
              │
              ▼
                    ┌───────────────┐
                    │ ModuleRegistry│
                    └───────┬───────┘
                            │ create
                            ▼
┌───────────┐       ┌───────────────┐
│Application│──────▶│  ModuleHost   │
└───────────┘       └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Module     │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Commands       Tools        Services
              │             │             │
              │             │             │
              │             ▼             │
              │        ToolRegistry       │
              │             │             │
              │             ▼             │
              │         Toolbar           │
              │             │             │
              ▼             ▼             ▼
          CommandStack   Command      Consumers
              │             │
              └──────┬──────┘
                     ▼
                   Scene
                     │
                     ▼
                  EventBus
                     │
                     ▼
                  Editors
```

svgsvg

Essa arquitetura permite que o CranioZ mantenha uma funcionalidade clínica altamente reutilizável sem transformar os Modules em conjuntos de componentes específicos de interface.

O princípio central é:

text

```
Application  = orquestração
Module       = funcionalidade clínica
Command      = alteração de estado
Tool         = intenção
Service      = capacidade reutilizável
Domain       = modelo conceitual
Capability   = necessidade de interface
Editor       = experiência de interface
Scene        = estado clínico
```

svgsvg

Esse modelo deve ser considerado a base para a evolução do sistema de Modules do CranioZ.