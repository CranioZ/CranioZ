# Modules

## 1. Visão geral

Os **Modules** são componentes funcionais do CranioZ responsáveis por implementar uma funcionalidade clínica ou um domínio de aplicação.

Um Module define **o que o sistema faz**, mas não como a interface se apresenta nem onde os componentes são posicionados.

A arquitetura de Modules segue a seguinte hierarquia conceitual:

```text
Application
└── Modules
    ├── Commands
    ├── Tools
    ├── Services
    ├── Domain
    ├── Capabilities
    └── Editors
```

Essa separação permite que a mesma funcionalidade clínica seja utilizada por diferentes configurações de interface, sem que o Module dependa de detalhes de apresentação.

Por exemplo, o `OrthognathicModule` pode declarar que necessita das capacidades `3d-visualization`, `image-slice-view` e `landmark-overlay`, sem conhecer as classes concretas dos Editors que as fornecem nem onde serão hospedados.

## 2. Responsabilidades

Um Module é responsável por:

- implementar uma funcionalidade clínica ou domínio de aplicação;
- declarar Commands específicos do domínio;
- declarar Tools específicas do domínio;
- fornecer Services utilizados por outras partes do sistema;
- declarar as capacidades de interface necessárias à sua funcionalidade;
- declarar os Editors e Panels que expõem sua funcionalidade;
- declarar suas dependências em relação a outros Modules;
- expor sua API para outros Modules e para a Application;
- manter seu próprio estado de execução.

Um Module não é responsável por:

- criar ou gerenciar Areas;
- definir o Layout do Workspace;
- instanciar Editors ou Panels;
- materializar Toolbars, pois a Toolbar é interna ao Editor;
- instanciar Tools;
- controlar docking ou divisão espacial;
- gerenciar outros Modules;
- controlar a disponibilidade visual de Editors ou Panels;
- decidir qual Editor concreto atende a uma determinada capability;
- registrar-se diretamente em registries;
- implementar lógica de apresentação pertencente aos Editors;
- modificar diretamente o estado clínico fora do fluxo de Commands.

A separação pode ser resumida da seguinte forma:

```text
Module  → funcionalidade clínica
Command → alteração de estado
Service → capacidade reutilizável
Tool    → intenção do usuário
Editor  → experiência de interface
Panel   → Editor de informação contextual
Scene   → estado clínico
```

## 3. Module versus Editor

Module e Editor não são equivalentes.

### 3.1 Module

O Module representa uma funcionalidade do CranioZ.

Ele controla aspectos como:

- lógica clínica;
- Commands;
- Services;
- Tools;
- regras de domínio;
- integração com outros Modules;
- declaração de capacidades de interface;
- declaração de Editors e Panels que expõem sua funcionalidade.

O Module não possui nem instancia Editors.

### 3.2 Editor

O Editor representa uma experiência de interface utilizada para trabalhar com determinada funcionalidade.

Ele controla aspectos como:

- visualização;
- interação;
- ferramentas;
- seleção;
- manipulação;
- navegação;
- apresentação de informações.

```text
Module → funcionalidade
Editor  → experiência de interface
```

A relação é de declaração, não de posse:

```text
Module
├── Commands
├── Tools
├── Services
├── Domain
├── Capabilities
└── Editors
```

O Module pode declarar que determinada funcionalidade necessita de certas capacidades de interface, mas não possui nem instancia os Editors que as fornecem.

### 3.3 Nota sobre Panels

A arquitetura atual trata `Panel` como uma especialização semântica de `Editor`, representada por um Editor com `editor_kind = PANEL`.

Um Panel é um Editor cujo propósito é exibir informações contextuais ou ferramentas auxiliares, em vez de constituir o conteúdo principal de uma Area.

Essa distinção não cria uma hierarquia de classes separada. Se, no futuro, Panel se tornar um conceito de primeira classe, este documento deverá ser atualizado.

## 4. ModuleHost

A comunicação entre Application e Module pode ser realizada por meio de um `ModuleHost`.

```text
Application
└── ModuleHost
    └── Module
```

O ModuleHost funciona como camada de hospedagem e adaptação entre a infraestrutura da Application e a implementação funcional do Module.

Suas responsabilidades incluem:

- hospedar a instância do Module;
- conectar o Module à Application;
- administrar o ciclo de vida lógico;
- fornecer o contexto necessário para o Module;
- adaptar a implementação do Module ao sistema de Modules.

O ModuleHost não registra Commands, Tools, Services, Capabilities, Editors ou Panels. O registro é responsabilidade do ModuleLoader.

O ModuleHost também não deve assumir responsabilidades de interface.

## 5. Interface base

Todos os Modules devem derivar de uma abstração comum.

Uma implementação conceitual pode ser representada por:

```python
from abc import ABC


class Module(ABC):
    id: str
    name: str
    version: str

    # Lifecycle
    def initialize(self, context: "ModuleContext") -> None: ...

    def activate(self) -> None: ...

    def deactivate(self) -> None: ...

    def dispose(self) -> None: ...

    # Declarations
    def commands(self) -> list["CommandSpec"]:
        return []

    def tools(self) -> list["ToolSpec"]:
        return []

    def services(self) -> list["ServiceSpec"]:
        return []

    def capabilities(self) -> list["CapabilitySpec"]:
        return []

    def editors(self) -> list["EditorSpec"]:
        return []

    def panels(self) -> list["PanelSpec"]:
        return []

    def dependencies(self) -> list["ModuleDependency"]:
        return []
```

A interface concreta poderá evoluir conforme as necessidades do sistema.

O objetivo da classe base não é impor uma implementação específica, mas estabelecer um contrato comum para registro, criação e ciclo de vida, além de declarar explicitamente os elementos que o ModuleLoader deve registrar nos registries apropriados.

### 5.1 Ciclo de vida síncrono

```text
constructed → initialized → active ⇄ inactive → disposed
```

### 5.2 Ciclo de vida com carregamento

Como alguns Modules podem ser carregados sob demanda ou em background, o ciclo completo é:

```text
registered → loading → loaded → initialized → active ⇄ inactive
                                      ↓
                                  unloaded → disposed

loading
├──→ failed
└──→ cancelled
```

### 5.3 Contratos do ciclo de vida

| Método | Pode falhar? | Idempotente? | Pode ser chamado múltiplas vezes? |
|---|---:|---:|---:|
| `initialize(context)` | Sim | Não | Não |
| `activate()` | Sim | Não | Não |
| `deactivate()` | Não | Sim | Não; deve ser no-op se já estiver inativo |
| `dispose()` | Não | Sim | Sim |

Regras adicionais:

- `activate()` só é válido após `initialized`;
- `deactivate()` só é válido após `active`;
- um Module inativo não recebe eventos e deve desinscrever-se durante `deactivate()`;
- Services permanecem disponíveis durante `deactivate()`, mas não após `dispose()`;
- `initialize()` pode falhar; o ModuleLoader trata a falha e a reporta por meio do EventBus.

## 6. Registro: regra única

Para evitar ambiguidades sobre quem registra cada elemento, adota-se a seguinte regra:

```text
Module       → declara
ModuleLoader → registra
Registries   → resolvem
ModuleHost   → hospeda
```

O `EditorRegistry` registra os Editors e Panels declarados pelo Module.

Ou seja:

- o Module declara seus Commands, Tools, Services, Capabilities, Editors e Panels;
- o ModuleLoader registra esses elementos nos registries apropriados;
- os Registries resolvem os elementos por identificador;
- o ModuleHost hospeda a instância do Module.

O Module não conhece diretamente o `ToolRegistry`, o `EditorRegistry` ou o `CommandStack`. Ele recebe abstrações por meio do contexto.

```text
Module
   │ declara
   ├── Commands     → CommandRegistry
   ├── Tools        → ToolRegistry
   ├── Services     → ServiceRegistry
   ├── Capabilities → CapabilityRegistry
   └── Editors      → EditorRegistry

ModuleLoader
   │ registra
   ▼
Registries
```

## 7. ModuleRegistry

Os Modules são registrados no `ModuleRegistry`.

O Registry é responsável por:

- registrar `ModuleSpec`, contendo metadados e não apenas identificadores;
- localizar um `ModuleSpec` por `module_id`;
- fornecer metadados, como versão, autor, política de carregamento e dependências;
- validar Modules solicitados pela Application;
- controlar dependências entre Modules;
- controlar a ordem de inicialização.

Exemplo conceitual:

```text
ModuleRegistry
│
├── ModuleSpec(id="orthognathic",   version="2.1.0", load="eager")
├── ModuleSpec(id="implants",       version="1.4.2", load="lazy")
├── ModuleSpec(id="osteosynthesis", version="1.0.0", load="lazy")
├── ModuleSpec(id="cephalometry",   version="1.2.0", load="eager")
├── ModuleSpec(id="simulation",     version="0.9.0", load="async")
└── ...
```

O Registry permite que o sistema trabalhe com identificadores estáveis, em vez de depender diretamente das classes concretas.

Por exemplo:

```python
module_id = "orthognathic"
```

Em vez de:

```python
OrthognathicModule(...)
```

na configuração da Application.

## 8. Application e Modules

A Application é responsável por definir quais Modules estão disponíveis e em qual ordem são carregados.

Entretanto, a Application não instancia diretamente as classes dos Modules.

O fluxo é:

```text
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

```python
ModuleSpec(
    module_id="orthognathic",
    enabled=True,
)
```

A Application conhece `"orthognathic"`, mas não precisa conhecer `OrthognathicModule`. Essa responsabilidade pertence ao ModuleRegistry.

### 8.1 Module Catalog

A Application expõe um catálogo de Modules disponíveis para o usuário, agrupados por categoria.

O catálogo é uma projeção somente leitura do ModuleRegistry, filtrada por:

- Modules que o usuário tem permissão para utilizar;
- Modules cujas dependências estão resolvidas;
- Modules aplicáveis ao contexto atual, como tipo de projeto e Flow selecionado.

O usuário pode adicionar um Module ao Workspace atual. Isso não cria uma instância do Module: apenas solicita ao ModuleLoader que o carregue, seguindo a política de carregamento declarada.

O catálogo é populado por:

- Modules do sistema, que são built-in e sempre disponíveis;
- Modules registrados por Plugins.

O catálogo não mantém estado próprio. Ele apenas reflete o que o ModuleRegistry fornece.

## 9. ModuleTree

O `ModuleTree` descreve a composição funcional da aplicação e as dependências entre Modules.

Ele descreve:

- Modules disponíveis;
- dependências entre Modules;
- política de carregamento;
- ordem de inicialização;
- visibilidade;
- estado habilitado ou desabilitado;
- capacidades declaradas.

Conceitualmente:

```text
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

O ModuleTree referencia os `ModuleSpec` armazenados no ModuleRegistry. O ModuleTree descreve a composição e as dependências; o ModuleRegistry descreve cada Module individualmente.

O ModuleTree não controla Commands, Tools, Services, Capabilities, Editors ou Panels. Ele apenas descreve a composição e as dependências. O registro efetivo pertence ao processo de carregamento.

O ModuleTree não contém widgets Qt concretos. Ele representa a estrutura lógica funcional da aplicação.

## 10. Materialização de Modules

A ativação de Modules ocorre em etapas distintas:

```text
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

- **ModuleTree:** representação declarativa da composição funcional;
- **ModuleLoader:** interpreta o ModuleTree, registra Commands, Tools, Services, Capabilities, Editors e Panels nos registries apropriados, resolve dependências e executa a política de carregamento;
- **ModuleHost:** hospeda a instância do Module e a conecta à Application.

Essa separação evita que a estrutura lógica funcional fique acoplada à implementação específica de carregamento.

## 11. Carregamento e ciclo de vida assíncrono

Nem todo Module precisa estar carregado o tempo todo.

Módulos de IA, bibliotecas pesadas de malhas 3D e funcionalidades ocasionais podem ser carregados sob demanda ou em background.

### 11.1 Políticas de carregamento

O carregamento é definido por dois eixos independentes:

- **quando:** `eager` ou `lazy`;
- **como:** `sync` ou `async`.

| Estratégia | Quando carrega | Modo | Uso típico |
|---|---|---|---|
| `Eager (sync)` | Startup | Síncrono | Módulos essenciais e leves |
| `Eager (async)` | Startup | Assíncrono | Módulos essenciais, porém pesados |
| `Lazy (sync)` | Primeiro uso | Síncrono | Módulos pesados de uso ocasional |
| `Lazy (async)` | Primeiro uso | Assíncrono | Módulos pesados e ocasionais que podem ser pré-carregados |

Exemplo:

```yaml
module:
  id: ai-segmentation
  load_when: lazy | eager
  load_mode: sync | async
  trigger: startup | project_open | user_action | background
  on_failure: notify_user | retry | disable
  timeout: 30s
```

Configuração combinada:

```yaml
startup:
  - orthognathic    # eager, sync
  - cephalometry    # eager, sync
  - simulation      # eager, async

on_demand:
  - ai-segmentation # lazy, async
  - mesh-processing  # lazy, async
```

### 11.2 Estados observáveis

```text
registered → loading → loaded → initialized → active ⇄ inactive
                                      ↓
                                  unloaded → disposed

loading
├──→ failed
└──→ cancelled
```

Diferenças importantes:

- `registered` não implica `loaded`;
- `loading` é um estado intermediário observável;
- `loaded` não implica `initialized`;
- `activate()` só é válido após `initialized`;
- `unloaded` não implica `disposed`.

### 11.3 Regras

- o carregamento assíncrono é cancelável;
- falhas são reportadas pelo EventBus, não propagadas diretamente;
- dependências entre Modules com políticas diferentes devem ser resolvidas explicitamente;
- a UI deve poder representar os estados `loading`, `failed` e `cancelled`.

### 11.4 Dependências assíncronas

Se o `ModuleA` depende do `ModuleB`, e o ModuleB é `lazy`:

```yaml
depends_on:
  - id: simulation
    required: true
    load_policy: promote # promote | defer | optional
```

| Política | Comportamento |
|---|---|
| `promote` | O ModuleB é promovido a `eager` se o ModuleA for `eager` |
| `defer` | O ModuleA só é ativado quando o ModuleB estiver carregado |
| `optional` | O ModuleA declara uma dependência opcional e trata a ausência |

### 11.5 Cancelamento

O ModuleLoader deve expor:

```text
ModuleLoader.load(module_id) → Task[Module]

Estados:
pending → loading → loaded | failed | cancelled
```

Também deve expor:

```text
ModuleLoader.cancel(module_id)
```

O `initialize()` assíncrono deve cooperar com o cancelamento por meio de um token e liberar os recursos parcialmente alocados.

## 12. Commands

Commands representam alterações de estado no CranioZ.

Um Module declara os Commands específicos do seu domínio.

Exemplos:

```text
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

- representar uma unidade lógica de intenção do usuário;
- ser executável como uma transação atômica, implementada pela camada de Application e não pelo Command;
- ser reversível quando aplicável;
- ser rastreável, contendo identificador, autor e timestamp;
- participar do CommandStack para permitir undo e redo.

O fluxo preferencial é:

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

Esse fluxo mantém undo/redo, rastreabilidade e comunicação entre componentes independentes.

## 13. Tools

Tools representam intenções ou operações iniciadas pelo usuário.

Um Module declara Tools específicas do seu domínio, que serão disponibilizadas para as Toolbars dos Editors.

```text
OrthognathicModule
├── OsteotomyTool
├── SplintTool
└── LandmarkTool
```

As Tools declaradas por um Module são registradas pelo ModuleLoader no ToolRegistry.

A definição da Tool é única. A instanciação é responsabilidade da Toolbar interna do Editor que a utiliza.

```text
Module
   │ declara Tool
   ▼
ModuleLoader
   │ registra
   ▼
ToolRegistry
   │ fornece definição
   ▼
Editor
   │ declara toolbar_specs()
   ▼
Toolbar interna ao Editor
   │ resolve tool_id
   ▼
ToolRegistry
   │ fornece factory
   ▼
Toolbar
   │ instancia
   ▼
Tool
```

Uma Tool não deve modificar diretamente o estado clínico. Ela deve traduzir a intenção do usuário em um Command.

## 14. Services

Services representam capacidades reutilizáveis fornecidas por um Module.

Exemplos:

```text
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
- ser consumido por Editors por meio de abstrações específicas fornecidas pelo EditorContext;
- ser substituído por implementações alternativas;
- ser testado isoladamente.

Services devem ser expostos por meio de abstrações, evitando dependência direta de implementações concretas.

O `EditorContext` deve expor apenas os Services necessários para aquele Editor específico, e não o ServiceRegistry inteiro. Isso mantém o contexto pequeno e impede que o Editor obtenha acesso indiscriminado a toda a aplicação.

## 15. Domain

O Domain representa o modelo conceitual do Module.

Ele contém:

- entidades;
- value objects;
- regras de negócio;
- invariantes;
- políticas de domínio.

Exemplo:

```text
OrthognathicDomain
├── Mandible
├── Maxilla
├── OsteotomyPlane
├── Splint
└── OrthognathicPlan
```

### 15.1 Fronteira entre Domain, Scene, Services e Commands

| Componente | Responsabilidade | Depende de |
|---|---|---|
| **Domain** | Regras, entidades e invariantes | Bibliotecas puramente computacionais, como NumPy para matemática |
| **Scene** | Estado clínico persistente, formado por instâncias do Domain | Domain |
| **Services** | Coordenação, análise e integração | Domain, Scene por meio de abstração e portas da Application |
| **Commands** | Intenção de transição controlada da Scene | Domain e Scene por meio do CommandHandler |

Regras explícitas:

- o Domain não deve depender da Scene;
- a Scene contém instâncias persistentes do modelo clínico;
- Services coordenam operações, análises e integrações;
- Commands realizam a transição controlada do estado da Scene.

O Domain não depende de:

- Editors;
- Toolbars;
- Tools;
- widgets Qt;
- Layout;
- Areas.

O Domain é a parte mais estável e independente do Module.

## 16. Capabilities

Em vez de um Module depender diretamente de IDs específicos de Editors, ele declara as capacidades de que necessita.

Exemplo:

```yaml
requires:
  - 3d-visualization
  - image-slice-view
  - landmark-overlay
```

O CapabilityRegistry não resolve diretamente uma capability para um `editor_id`. Ele apenas valida que a capability é conhecida e está registrada.

A resolução `capability → Editor` concreto pertence ao Workspace, porque é uma decisão de composição de UI e não de definição da capability.

```text
Module
   │ declara capability
   ▼
CapabilityRegistry
   │ valida requisitos de capability
   ▼
Workspace / ModuleUISpecResolver
   │ resolve capability → editor_id
   ▼
EditorRegistry
   │ cria
   ▼
Editor
```

Isso reduz o acoplamento a nomes específicos de componentes e permite que diferentes configurações de interface atendam à mesma capacidade.

O Module não sabe se `3d-visualization` será atendida por um `Viewport3DEditor` ou por outro Editor futuro. Quem resolve essa relação é o Workspace, consultando o EditorRegistry.

## 17. Editors e Panels declarados pelo Module

Um Module pode declarar Editors e Panels por meio de `EditorSpec` e `PanelSpec`.

### 17.1 EditorSpec

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class EditorSpec:
    editor_id: str
    title: str
    region_hint: "EditorRegion | None"  # CENTRAL, LEFT, RIGHT, BOTTOM
    capabilities: list[str]
    editor_kind: "EditorKind" = "EditorKind.CONTENT"
```

O ModuleLoader registra esses Editors no EditorRegistry.

O Module não instancia o Editor. Ele apenas declara que o Editor existe e qual é sua região preferida.

### 17.2 PanelSpec

Um Panel é um Editor com `editor_kind = PANEL`. Panels são declarados da mesma forma, mas com metadados adicionais que indicam sua região canônica e seu propósito contextual.

```python
@dataclass(frozen=True)
class PanelSpec(EditorSpec):
    editor_kind: "EditorKind" = "EditorKind.PANEL"
    region_canonical: "EditorRegion | None" = None
```

### 17.3 Exemplo

```python
class OrthognathicModule(Module):
    def editors(self) -> list[EditorSpec]:
        return [
            EditorSpec(
                editor_id="editor.osteotomy",
                title="Osteotomia",
                region_hint=EditorRegion.CENTRAL,
                capabilities=[
                    "3d-visualization",
                    "landmark-overlay",
                ],
                editor_kind=EditorKind.CONTENT,
            ),
        ]

    def panels(self) -> list[PanelSpec]:
        return [
            PanelSpec(
                editor_id="panel.osteotomy_patterns",
                title="Padrões de osteotomia",
                region_canonical=EditorRegion.RIGHT,
            ),
            PanelSpec(
                editor_id="panel.object_position",
                title="Posição dos objetos",
                region_canonical=EditorRegion.RIGHT,
            ),
        ]
```

### 17.4 Registro

O ModuleLoader registra esses Editors e Panels no EditorRegistry. A criação efetiva das instâncias permanece com o Workspace, por meio do EditorHost.

## 18. Disponibilidade de Tools, Editors e Panels

Tools, Editors e Panels podem declarar disponibilidade contextual.

Isso permite que a UI apresente elementos indisponíveis em um estado visual distinto, como cinza, e não os instancie até que se tornem disponíveis.

### 18.1 Disponibilidade

```python
class Editor(ABC):
    def is_available(self, context: "EditorContext") -> bool:
        return True
```

Se `is_available()` retornar `False`:

- o Editor não será instanciado;
- se já estiver instanciado, permanecerá inativo;
- a UI o apresentará como indisponível.

### 18.2 Habilitação

A habilitação é diferente da disponibilidade. Ela indica se o Editor pode ser ativado imediatamente em um contexto no qual está visível.

```python
class Editor(ABC):
    def is_enabled(self, context: "EditorContext") -> bool:
        return True
```

### 18.3 Exemplos

```text
OsteotomyEditor
    available: sim
    enabled:   não
    motivo: nenhuma maxila segmentada ainda

SegmentaçãoEditor
    available: sim
    enabled:   sim
```

A UI utiliza essas informações para habilitar, desabilitar ou ocultar Editors conforme o contexto.

## 19. Contextos separados

O contexto de um Module deve ser mínimo e específico, evitando a concentração de dependências desnecessárias.

```text
ModuleContext
├── ModuleState
├── CancellationToken
├── ProgressReporter
└── ServiceContext

DomainContext
├── Scene, por meio de abstração
└── Domain

EditorContext
├── Scene
├── Selection
├── CommandStack
├── EventBus
└── Services, por meio de abstrações específicas

ToolContext
├── Scene
├── Selection
├── CommandStack
└── EventBus
```

O Module recebe apenas o que precisa. Isso evita que o ModuleContext se torne uma “Application disfarçada”.

Exemplo conceitual:

```python
class OrthognathicModule(Module):
    def initialize(self, context: ModuleContext) -> None:
        self._state = context.module_state
        self._services = context.services
        self._cancel = context.cancellation_token

    def activate(self) -> None:
        self._events.subscribe(
            "scene_changed",
            self._on_scene_changed,
        )
```

O Module não recebe a aplicação inteira, apenas o contexto necessário.

## 20. Estado do Module

É importante separar o estado clínico do estado de execução do Module.

### 20.1 Estado clínico

Pertence à Scene.

Exemplos:

- posição de uma mandíbula;
- plano de osteotomia;
- posição de um implante;
- landmarks;
- modelos anatômicos;
- splint.

### 20.2 Estado do Module

Pode pertencer ao Module.

Exemplos:

- configuração do Module;
- cache de análise;
- estado de simulação;
- preferências do domínio.

### 20.3 Estado visual

Pertence aos Editors.

Exemplos:

- zoom;
- câmera;
- slice atual;
- seleção visual;
- modo de apresentação.

Essa separação evita que informações transitórias de interface ou de execução sejam confundidas com os dados clínicos do projeto.

## 21. Dependências entre Modules

Modules podem depender de outros Modules.

Exemplo:

```text
OrthognathicModule
├── depends on CephalometryModule
├── depends on SimulationModule
└── depends on ImagingModule
```

As dependências devem ser:

- declaradas explicitamente;
- resolvidas pelo ModuleLoader;
- respeitadas na ordem de inicialização;
- validadas antes da ativação.

### 21.1 Dependência ausente

| Política | Comportamento |
|---|---|
| `required: true` | O Module não é ativado e o erro é reportado |
| `required: false` | O Module é ativado com funcionalidade reduzida |

### 21.2 Dependência circular

Dependências circulares devem ser detectadas e, por padrão, rejeitadas.

Casos legítimos de colaboração mútua devem ser implementados por meio de:

- eventos do EventBus, utilizando comunicação indireta;
- interfaces compartilhadas, como um Service consumido por ambos;
- um terceiro Module que coordene os dois.

Nunca deve ser utilizada uma dependência direta circular entre Modules.

## 22. Persistência e versionamento

Como os Modules podem possuir configuração, estado de execução e Services, é necessário prever:

- identificador e versão do Module;
- migração de dados;
- compatibilidade de Commands persistidos;
- serialização de configurações;
- comportamento quando uma dependência não estiver disponível.

### 22.1 Identificador e versão

```yaml
module:
  id: orthognathic
  version: 2.1.0
  compatible_with:
    - ">=1.0.0 <3.0.0"
```

### 22.2 Migração de dados

Projetos CranioZ antigos devem continuar abrindo após a evolução dos Modules.

```text
Project v1.0
   │ load
   ▼
ModuleMigration
   │ apply migrations
   ▼
Project v2.1
```

### 22.3 Compatibilidade de Commands

Commands persistidos podem ter sido definidos em versões anteriores do Module.

O sistema deve:

- versionar Commands;
- fornecer migração quando a assinatura mudar;
- rejeitar Commands incompatíveis com uma mensagem clara.

### 22.4 Serialização de configuração

```yaml
module_config:
  orthognathic:
    default_landmarks: []
    auto_update: true
```

### 22.5 Versionamento de Capability, Tool e Service

Assim como Commands, esses elementos também devem ser versionados.

```yaml
capability:
  id: 3d-visualization
  version: 1.2.0
```

O ModuleLoader valida a compatibilidade antes de registrar os elementos. Capabilities incompatíveis geram um erro de configuração explícito.

### 22.6 Dependência ausente

Se um Module não estiver disponível ao abrir um projeto, o sistema deve:

- notificar o usuário;
- preservar os dados do projeto;
- permitir a reabertura quando o Module estiver disponível.

## 23. Independência de interface

Um dos princípios fundamentais dos Modules é:

> Um Module não deve saber como sua funcionalidade é apresentada.

O mesmo Module pode ser utilizado com:

- diferentes Layouts;
- diferentes Editors;
- diferentes Toolbars;
- diferentes configurações de Workspace.

Tudo isso deve ser possível sem modificar a implementação do Module.

A composição de interface pertence ao Workspace.

## 24. Registries

Os registries têm papéis distintos:

```text
ModuleRegistry     → registra Modules
CommandRegistry    → registra Commands
ToolRegistry       → registra definições de Tools
ServiceRegistry    → registra Services
CapabilityRegistry → registra capacidades de interface
EditorRegistry     → registra Editors e Panels
```

Um Module pode:

- declarar Tools que serão registradas no ToolRegistry;
- declarar Commands que serão registrados no CommandRegistry;
- declarar Services que serão registrados no ServiceRegistry;
- declarar capacidades que serão resolvidas pelo CapabilityRegistry;
- declarar Editors e Panels que serão registrados no EditorRegistry.

O Module não instancia Tools nem Editors.

O registro efetivo é responsabilidade do ModuleLoader.

```text
Module
   │ declara
   ├── Tools        → ToolRegistry
   ├── Commands     → CommandRegistry
   ├── Services     → ServiceRegistry
   ├── Capabilities → CapabilityRegistry
   └── Editors      → EditorRegistry
```

A instanciação pertence:

- das Tools: à Toolbar interna do Editor;
- dos Editors: ao Workspace ou EditorHost.

## 25. Princípios arquiteturais

Os seguintes princípios devem orientar a implementação.

### 25.1 Module é funcional, não espacial

A posição pertence à Area e ao Layout.

### 25.2 Module não instancia Editors

A composição de interface é responsabilidade do Workspace e do Layout.

### 25.3 Module não contém lógica de apresentação

A lógica de apresentação pertence aos Editors.

### 25.4 Module declara necessidades de interface

Modules declaram capacidades; o Workspace resolve e instancia os Editors correspondentes.

### 25.5 Alterações de estado passam por Commands

Quando uma interação altera o estado persistente da aplicação, o Module deve utilizar Commands em vez de modificar diretamente a Scene.

### 25.6 Modules devem ser reutilizáveis

Um Module deve poder ser utilizado por diferentes configurações de interface e diferentes fluxos clínicos.

### 25.7 Estado clínico e estado do Module devem permanecer separados

O Module pode manter estado de execução sem contaminar o modelo clínico.

### 25.8 Qt é detalhe de implementação

A arquitetura lógica do Module deve permanecer o mais independente possível dos detalhes de apresentação do Qt.

### 25.9 ModuleLoader resolve dependências

Dependências entre Modules devem ser declaradas e resolvidas pelo ModuleLoader.

### 25.10 Modules devem ser testáveis sem interface

O contrato do Module deve permitir testes unitários sem dependência de widgets concretos.

### 25.11 Module declara, ModuleLoader registra, Registry resolve

O Module não conhece diretamente os registries.

### 25.12 Carregamento é declarativo; execução é responsabilidade do Loader

O ModuleTree declara a política de carregamento; o ModuleLoader a executa.

### 25.13 Módulos pesados devem suportar carregamento lazy ou assíncrono

Nenhum Module pesado deve bloquear o startup da aplicação.

### 25.14 Carregamento assíncrono deve ser cancelável

Toda operação de carregamento deve poder ser cancelada de forma limpa.

### 25.15 Estados intermediários devem ser observáveis

A UI deve poder representar os estados `loading`, `failed` e `cancelled`.
