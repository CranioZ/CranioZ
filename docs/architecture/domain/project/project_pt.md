# 1 Propósito

O subsistema de Project Management é responsável pelo ciclo de vida do projeto clínico do CranioZ e por controlar como os dados relacionados ao paciente entram, saem e persistem na aplicação.

Um Project é o container clínico persistente que identifica um caso de planejamento relacionado a um paciente e seus dados clínicos, metadados, estado de workflow e referências a objetos do projeto.

O gerenciamento de projeto é intencionalmente separado da Home Page e do Workspace.

**A regra arquitetural fundamental é**


Um único ator de nível de aplicação é dono do ciclo de vida do projeto do paciente: criação, modificação e exclusão.

A Home Page apenas descobre e seleciona projetos.
O Workspace apenas opera sobre um projeto já selecionado e seu workflow clínico.

# 2 Responsabilidades Arquiteturais

**O CranioZ separa o gerenciamento de projeto em cinco responsabilidades**


| Componente | Responsabilidade | Muta projetos? |
|---|---|---|
| Project Manager | Dono do ciclo de vida e comandos de nível de projeto | Sim |
| Project Catalog | Visão somente-leitura dos projetos disponíveis | Não |
| Project Repository | Persiste e recupera dados do projeto | Não* |
| Project Storage | Infraestrutura de armazenamento físico (pastas, arquivos) | Não* |
| Project Path Resolver | Resolve caminhos lógicos em caminhos absolutos | Não |
| Home Page | Exibe e seleciona projetos para o usuário | Não |
| Workspace | Executa workflows clínicos usando o projeto selecionado | Não |

> O Repository e o Storage executam operações de persistência solicitadas pelo Project Manager. Eles não decidem quando um projeto é criado, modificado ou excluído.


Essa distinção é fundamental. Persistência é uma preocupação de infraestrutura; ownership do ciclo de vida é uma responsabilidade de aplicação/domínio.

# 3 Separação Conceitual: Patient, Project, Context

Uma confusão recorrente em sistemas clínicos é tratar Patient e Project como sinônimos. O CranioZ não faz isso.

```
Patient
   │
   │ referenced by
   ▼
Project
   │
   ├── Patient data
   ├── Clinical metadata
   ├── Imaging studies
   ├── Anatomical models
   ├── Planning data
   ├── Workflow state
   └── Application metadata
Definições:

Patient é uma entidade de domínio. Representa a pessoa e seus dados clínicos identificáveis.

Project é o container clínico persistente do CranioZ. Referencia um Patient e contém todo o estado clínico associado ao caso de planejamento.

Project Context é o snapshot de runtime construído pelo Project Manager e entregue ao Workspace para inicialização.

Regra: o ciclo de vida do Patient dentro do CranioZ é administrado no contexto do Project. Não há um PatientManager separado.
```

**A separação exata entre**


```
Patient
Project
Project Data
Domain Objects
Clinical Workflow
é definida pela documentação de domínio correspondente (domain/patient.md, domain/project.md, domain/scene.md).
```

# 4 O Project Manager

O Project Manager é a única autoridade responsável pelo ciclo de vida de um projeto.

**É o único componente de aplicação autorizado a realizar**


- criação de projeto

- inicialização de projeto

- atualização de metadados de projeto

- arquivamento de projeto, quando suportado

- exclusão de projeto

- restauração de projeto, quando suportado

- validação de nível de projeto

- persistência de projeto

- carregamento de projeto em contexto ativo

- manutenção de consistência de nível de projeto

Outros componentes podem solicitar essas operações através do Project Manager, mas não devem implementar sua própria lógica de ciclo de vida.

## 4.1 Ownership ≠ Implementação

Ownership do ciclo de vida não significa que o Project Manager implementa diretamente todas as operações de infraestrutura. Ele coordena os serviços necessários:

```
                         ┌───────────────────┐
                         │   Project Manager │
                         │                   │
                         │ Lifecycle Authority│
                         │ Application       │
                         │ Coordinator       │
                         └─────────┬─────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │           │              │
        ▼              ▼           ▼           ▼              ▼
  Project         Project     Access      Event Bus    Workflow
  Repository      Storage     Policy                   Resolver
        │              │
        ▼              ▼
  Persistence    Filesystem
                 Infrastructure
O Project Manager atua como fronteira de aplicação através da qual operações de ciclo de vida são realizadas.
```

# 5 Project Identity

Todo projeto tem um identificador único e estável.

**O identificador é usado para localizar e referenciar o projeto independentemente de**


nome do paciente;

nome de exibição do projeto;

diretório no sistema de arquivos;

workflow atual;

workspace atual;

representação na UI.

**Um projeto pode ter metadados legíveis por humanos, como**


```
Project ID
Project Name
Patient ID
Patient Name
Created At
Updated At
Project Status
Clinical Procedure
Last Opened At
Schema Version
Apenas os campos necessários para descoberta devem ser expostos ao Project Catalog e à Home Page. A Home Page não deve precisar carregar o projeto clínico completo apenas para exibir a lista.
```

# 6 Project Storage

A persistência do projeto é realizada através de um Project Repository, apoiado por um Project Storage físico.

O Repository é uma abstração de infraestrutura responsável por traduzir dados do projeto entre a representação de aplicação/domínio e o mecanismo de armazenamento persistente.

O Storage é responsável pela topografia física: criação, verificação e exclusão de pastas e arquivos.

**Implementações possíveis incluem**


projetos baseados em filesystem;

projetos baseados em banco de dados;

armazenamento remoto;

armazenamento institucional;

armazenamento em nuvem (futuro).

O Project Manager não deve depender de uma tecnologia de armazenamento específica.

```
Project Manager
       │
       ▼
Project Repository interface
       │
       ├── Filesystem Repository
       ├── Database Repository
       └── Remote Repository
       │
       ▼
Project Storage (infraestrutura física)
       │
       ├── ProjectFolderManager
       └── ProjectPathResolver
6.1 Contrato do Repository
python
class ProjectRepository(Protocol):
    def create(self, project: Project) -> None: ...
    def get(self, project_id: ProjectId) -> Project: ...
    def update(self, project: Project) -> None: ...
    def delete(self, project_id: ProjectId) -> None: ...
    def exists(self, project_id: ProjectId) -> bool: ...
    def list_metadata(self) -> list[ProjectSummary]: ...
6.2 O que o Repository NÃO decide
text
"Should this project be created?"
"Is this project allowed to be deleted?"
"Should this project be opened?"
"Which workflow should be active?"
Essas decisões pertencem ao Project Manager e suas políticas de aplicação.
```

## 6.3 Sobre o patient_record.json

O arquivo patient_record.json é uma representação de persistência, não uma autoridade arquitetural.

O domínio não deve saber que esse arquivo existe. Se a implementação inicial usa:

```
Projects/
  7f8a.../
    project.json
    patient_record.json
    imaging/
    models/
    planning/
isso é uma decisão de infraestrutura/persistência. Uma futura implementação em banco de dados simplesmente não terá esse arquivo — e o domínio não precisa mudar.
```

# 7 Project Path Resolver

O Project Path Resolver é responsável por converter caminhos lógicos em caminhos absolutos no sistema de arquivos.

```
logical resource
       ↓
ProjectPathResolver
       ↓
absolute storage path
Exemplos:

python
resolve("imaging/ct")          →  /data/projects/7f8a/imaging/ct
resolve("models/maxilla")      →  /data/projects/7f8a/models/maxilla
resolve("planning/splint")     →  /data/projects/7f8a/planning/splint
O Workspace e os módulos clínicos não devem construir caminhos físicos manualmente. Eles consultam o Path Resolver.
```

# 8 Project Catalog

O Project Catalog é uma projeção somente-leitura dos projetos disponíveis.

Seu propósito é descoberta eficiente de projetos.

**Pode fornecer**


- identificadores de projeto

- nomes de projeto

- informações de exibição do paciente

- timestamps de criação/atualização

- status do projeto

informação de último acesso;

resumo de procedimento/workflow;

thumbnails ou outras informações leves de preview.

O Catalog não contém autoridade para criar, atualizar ou excluir projetos.

## 8.1 Contrato

```python
class ProjectCatalog(Protocol):
    def list_projects(self) -> list[ProjectSummary]: ...
    def get_project_summary(self, project_id: ProjectId) -> ProjectSummary: ...
    def search_projects(self, query: str) -> list[ProjectSummary]: ...
8.2 Implementações possíveis
query no repositório;

banco de metadados indexado;

índice de filesystem;

projeção em cache;

outro mecanismo otimizado para leitura.
```

## 8.3 Regra

O Project Catalog é um read model, não o dono do ciclo de vida do projeto.

# 9 Home Page

A Home Page é a interface de descoberta e seleção de projetos.

**Suas responsabilidades são limitadas a:**


* solicitar a lista de projetos disponíveis;
* exibir resumos de projeto;
* permitir busca/filtro de projetos;
* permitir seleção de projeto;
* permitir seleção de workflow;
* solicitar abertura do projeto selecionado;
* transferir controle para o Workspace.

**A Home Page não deve**


* criar projetos;
* modificar projetos;
* excluir projetos;
* escrever arquivos de projeto diretamente;
* acessar armazenamento de projeto diretamente;
* implementar persistência de projeto;
* modificar registros de paciente;
* determinar regras de ciclo de vida de projeto;
* manter seu próprio banco de dados de projetos.

## 9.1 Fluxo de Listagem

```
Home Page
    │
    │ read-only query
    ▼
Project Catalog
    │
    ▼
Project summaries
A Home Page não deve construir a lista autoritativa de projetos por conta própria.
```

## 9.2 Serviços da Home Page

**A Home Page pode ser apoiada por serviços de aplicação leves**


Project Service — lista projetos, carrega metadados de catálogo, cria/exclui registros de projeto no catálogo (mas não cria/exclui pastas físicas).

Flow Service — lista workflows disponíveis, carrega metadados de flow, cria/exclui registros de flow no catálogo (mas não cria/exclui pastas físicas).

Esses serviços são consumidores do Project Management, não autoridades.

# 10 Criando um Projeto

A criação de projeto é exclusivamente tratada pelo Project Manager.

```
User
  │
  ▼
Home Page / Project Management UI
  │
  │ create request
  ▼
Project Manager
  │
  ├── validate input
  ├── check access policy
  ├── generate project identity
  ├── initialize project structure
  ├── initialize patient/project metadata
  └── persist project
          │
          ├── Project Repository.create(...)
          └── Project Storage.ensure_structure(...)
          │
          ▼
   ProjectCreated event (Event Bus)
          │
          ▼
   Project Catalog updates
Após criação bem-sucedida, o Project Catalog se torna ciente do novo projeto através do Event Bus. A Home Page não insere o projeto diretamente em sua própria lista.
```

# 11 Atualizando um Projeto

Todas as modificações de nível de projeto passam pelo Project Manager.

**Exemplos**


- alteração de metadados de projeto

- alteração de informações de paciente/projeto

- alteração de status de projeto

- alteração de configuração de nível de projeto

- atualização de metadados após operações clínicas

- renomeação de projeto

O Workspace pode gerar mudanças clínicas, mas não deve implementar persistência de projeto de forma independente.

```
Workspace
   │
   │ application command
   ▼
Application / Project Management boundary
   │
   ▼
Project Manager
   │
   ├── validate
   ├── check access policy
   └── update
        │
        ├── Project Repository.update(...)
        └── ProjectUpdated event (Event Bus)
Isso evita que múltiplos componentes escrevam estado de projeto de forma independente.
```

# 12 Excluindo um Projeto

A exclusão de projeto é exclusivamente controlada pelo Project Manager.

A Home Page não deve excluir dados de projeto diretamente.

```
Home Page
    │
    │ delete request
    ▼
Project Manager
    │
    ├── authorization / policy checks
    ├── validation
    ├── dependency checks
    ├── Project Repository.delete(...)
    ├── Project Storage.delete_structure(...)
    └── ProjectDeleted event (Event Bus)
A Home Page apenas inicia a interação do usuário. A exclusão real permanece responsabilidade do Project Manager.
```

Essa distinção impede que componentes de UI se tornem fontes independentes de comportamento de persistência.

## 12.1 Consistência na Exclusão

A ordem das operações importa. O Project Manager deve garantir que:

O projeto não esteja em uso (ProjectInUse).

A política de acesso permita a exclusão (ProjectAccessDenied).

O registro seja removido do repositório.

A estrutura física seja removida do storage.

O evento ProjectDeleted seja publicado.

Falhas parciais devem ser tratadas de forma transacional ou compensatória.

# 13 Abrindo um Projeto

Selecionar um projeto na Home Page não é equivalente a carregar o projeto inteiro na UI.

**A operação deve ocorrer em estágios**


```
1. User selects project
             │
             ▼
2. Home Page requests project opening
             │
             ▼
3. Project Manager loads project
             │
             ▼
4. Project Manager resolves project context
             │
             ▼
5. Clinical workflow is selected/resolved
             │
             ▼
6. Project Manager publishes ProjectOpened event
             │
             ▼
7. Workspace receives ProjectContext
             │
             ▼
8. Workspace initializes the selected workflow
O Project Manager é responsável por construir a informação necessária para entrar no Workspace.
```

# 14 Project Context

Após a seleção do projeto, o Project Manager fornece ao Workspace um Project Context (ou contexto equivalente de nível de aplicação).

## 14.1 Contrato

```
ProjectContext:
  - project_id: ProjectId
  - metadata: ProjectMetadata (read-only)
  - patient_summary: PatientSummary
  - project_state: ProjectState
  - workflow_id: WorkflowId
  - workflow_config: WorkflowConfig
  - service_locator: ApplicationServices
  - object_references: list[ObjectReference]
14.2 Regras
O Project Context é um snapshot de inicialização, não o projeto em si.
```

O Project Context é read-only para o Workspace.

O Workspace não se torna dono do projeto. Ele se torna consumidor/executor do contexto selecionado.

Mudanças persistentes devem passar por comandos de aplicação, não por mutação direta do contexto.

## 14.3 Diagrama

```
Project Manager
       │
       │ ProjectContext
       │ + ClinicalWorkflow
       ▼
   Workspace
15. Clinical Workflow Handoff
Um projeto pode estar associado a um ou mais workflows clínicos.

Exemplos:

text
Orthognathic Surgery
Facial Implant Planning
Osteosynthesis Planning
Airway Analysis
Cephalometric Analysis
Fibula Reconstruction
A Home Page não deve implementar lógica de workflow.
```

**O processo de seleção de projeto deve resolver**


```
Project
   +
Clinical Workflow
   =
Workspace Initialization Context
text
Selected Project
      │
      ├── Patient
      ├── Project Data
      └── Orthognathic Workflow
                 │
                 ▼
             Workspace
O Workspace então carrega e executa o workflow usando sua arquitetura normal de módulos/flows.
```

## 15.1 Workflow Resolver

O Workflow Resolver é um serviço de aplicação consultado pelo Project Manager para determinar qual workflow está associado ao projeto e como configurá-lo.

```python
class WorkflowResolver(Protocol):
    def resolve(self, project: Project) -> Workflow: ...
    def list_available(self) -> list[WorkflowSummary]: ...
16. Application Event Bus
A comunicação entre o Project Manager e os demais componentes ocorre através de um Application Event Bus.
```

## 16.1 Eventos de Projeto

```
ProjectCreated
ProjectOpened
ProjectUpdated
ProjectClosed
ProjectDeleted
WorkflowSelected
16.2 Fluxo
text
Project Manager
      │
      ▼
Application Event Bus
      │
      ├── Home Page
      ├── Workspace
      ├── Project Catalog
      └── other subscribers
16.3 Regras
Eventos são de domínio/aplicação, não de UI.

Subscribers não devem assumir ordem de entrega além da garantida pelo bus.

Eventos não substituem comandos: eles notificam, não autorizam.
```

# 17 Workspace

O Workspace é responsável pelo ambiente de trabalho clínico ativo.

**Pode**


exibir dados do projeto;

executar workflows clínicos;

invocar módulos;

manipular objetos de domínio através de comandos de aplicação;

exibir imagens e dados 3D;

realizar operações de planejamento;

gerenciar layout do workspace;

manter estado temporário de UI;

comunicar-se com serviços de aplicação.

**O Workspace não deve**


criar projetos independentes;

excluir projetos diretamente;

manter a lista autoritativa de projetos;

implementar persistência de projeto;

decidir políticas de ciclo de vida de projeto;

tornar-se um segundo Project Manager.

O Workspace pode causar mudanças persistentes em dados clínicos, mas essas mudanças devem passar pelos serviços de aplicação/domínio e pela fronteira de persistência apropriada.

## 17.1 Módulos como Componentes Passivos

Os módulos clínicos comportam-se como componentes passivos. Eles:

recebem o ProjectContext (via Workspace);

reagem a eventos de aplicação relevantes;

inicializam-se automaticamente quando o contexto está pronto;

delegam consultas físicas adicionais ao ProjectPathResolver.

Eles não buscam estado ativamente, não constroem caminhos físicos e não persistem dados diretamente.

# 18 Quem Lê o Projeto?

**A leitura de projeto ocorre em diferentes níveis**


| Nível | Quem lê | O quê |
|---|---|---|
| Descoberta | Home Page → Project Catalog | Metadados leves |
| Autoritativo | Project Manager → Project Repository | Estado completo do projeto |
| Runtime | Project Manager → Workspace | Project Context |
| Clínico | Workspace → Módulos | Dados do contexto + Path Resolver |
O Workspace não deve contornar a fronteira do Project Management para obter ou persistir estado de projeto.

# 19 Quem Armazena o Projeto?

O Project Repository armazena a representação persistente do projeto.
O Project Storage armazena a estrutura física.
O Project Manager controla quando e por que a persistência ocorre.

```
Project Manager
    = lifecycle authority

Project Repository
    = persistence mechanism

Project Storage
    = physical storage infrastructure

Project Catalog
    = read-only discovery projection

Home Page
    = project discovery and selection UI

Workspace
    = clinical execution environment
20. Single Writer Principle
O CranioZ segue um princípio de single lifecycle-writer para projetos.
```

**Apenas o Project Manager pode realizar mutações de ciclo de vida de projeto**


```
Create Project
Update Project Metadata
Delete Project
Archive Project
Restore Project
Open Project
Close Project
Persist Project Lifecycle State
Isso não significa que apenas uma classe no sistema pode modificar objetos de domínio. Módulos clínicos e serviços de aplicação podem legitimamente modificar estado de domínio através de seus contratos definidos.

Significa que deve haver apenas uma fronteira autoritativa de aplicação para operações de ciclo de vida.
```

**Isso previne implementações concorrentes de ciclo de vida em**


```
Home Page
Workspace
Modules
UI dialogs
Repositories
Plugins
Plugins e módulos devem usar a API pública do Project Management, em vez de acessar o armazenamento de projeto diretamente.
```

# 21 Project Management API

**A API exata é definida pela arquitetura de aplicação, mas a interface conceitual deve se parecer com**


```python
class ProjectManager:
    def create_project(self, request: CreateProjectRequest) -> Project: ...
    def open_project(self, project_id: ProjectId) -> ProjectContext: ...
    def update_project(self, request: UpdateProjectRequest) -> None: ...
    def delete_project(self, project_id: ProjectId) -> None: ...
    def close_project(self, project_id: ProjectId) -> None: ...
Descoberta somente-leitura pode ser exposta separadamente:

python
class ProjectCatalog:
    def list_projects(self) -> list[ProjectSummary]: ...
    def get_project_summary(self, project_id: ProjectId) -> ProjectSummary: ...
    def search_projects(self, query: str) -> list[ProjectSummary]: ...
Persistência permanece atrás de:

python
class ProjectRepository:
    def create(self, project: Project) -> None: ...
    def get(self, project_id: ProjectId) -> Project: ...
    def update(self, project: Project) -> None: ...
    def delete(self, project_id: ProjectId) -> None: ...
A separação é intencional.
```

# 22 Project Lifecycle Sequence

**Uma sessão normal de usuário deve seguir esta sequência conceitual**


```
┌────────────┐
│   Home     │
└─────┬──────┘
      │
      │ list projects
      ▼
┌─────────────────┐
│ Project Catalog │
└─────┬───────────┘
      │
      │ ProjectSummary[]
      ▼
┌────────────┐
│   Home     │
└─────┬──────┘
      │
      │ select project + workflow
      ▼
┌─────────────────┐
│ Project Manager │
└─────┬───────────┘
      │
      │ load project
      ▼
┌──────────────────┐
│ Project Repository│
└─────┬────────────┘
      │
      │ Project
      ▼
┌─────────────────┐
│ Project Manager │
└─────┬───────────┘
      │
      │ ProjectContext
      │ + ClinicalFlow
      ▼
┌─────────────┐
│  Workspace  │
└─────────────┘
O Workspace então realiza trabalho clínico sem se tornar responsável pelo ciclo de vida do projeto.
```

# 23 Persistência e Mudanças no Workspace

O trabalho clínico realizado dentro do Workspace pode gerar mudanças persistentes.

```
Workspace
   │
   │ "Apply Le Fort I osteotomy"
   ▼
Application Command
   │
   ▼
Domain / Planning Service
   │
   ▼
Project State
   │
   ▼
Project Persistence Boundary
O Workspace não deve implementar:

python
open("project.json", "w")
ou comportamento equivalente de persistência direta.
```

A persistência deve permanecer atrás da fronteira de persistência da aplicação.

Isso é particularmente importante porque uma operação clínica pode eventualmente envolver múltiplas mudanças coordenadas e, portanto, exigir orquestração transacional.

# 24 Caching e a Lista de Projetos

A Home Page pode usar resumos de projeto em cache para desempenho.

Um cache não se torna o armazenamento autoritativo de projetos.

```
Project Repository
        │
        ▼
Project Catalog
        │
        ▼
Project Summary Cache
        │
        ▼
Home Page
Se um projeto é criado, modificado ou excluído, o Project Management é responsável por garantir que o catálogo/cache eventualmente reflita o novo estado (via Event Bus).
```

A Home Page não deve manter manualmente uma lista duplicada autoritativa.

# 25 Separação de Responsabilidades UI vs Aplicação

**A seguinte regra deve ser aplicada em todo o CranioZ**


Componentes de UI solicitam operações de projeto; eles não implementam operações de projeto.

| Componente | Responsabilidades |
|---|---|
| Home Page | Display, Search, Select, Request |
| Project Manager | Validate, Create, Open, Update, Delete, Close, Coordinate, Persist |
| Repository | Store, Retrieve, Update persistence, Delete persistence |
| Storage | Create structure, Delete structure, Verify integrity |
| Path Resolver | Resolve logical → absolute, List contents |
| Workspace | Present, Interact, Execute clinical workflows, Request application operations |
Essa separação mantém o gerenciamento de projeto independente da UI e impede que o Workspace se torne um segundo núcleo de aplicação.

# 26 Tratamento de Erros e Falhas

Falhas de ciclo de vida de projeto devem ser reportadas através da camada de Project Management/aplicação.

## 26.1 Exceções de Domínio/Aplicação

```
ProjectNotFound
ProjectAlreadyExists
ProjectValidationError
ProjectStorageError
ProjectCorrupted
ProjectAccessDenied
ProjectInUse
ProjectDeletionError
WorkflowNotFound
WorkflowConfigurationError
26.2 Regras
A Home Page deve apresentar feedback apropriado ao usuário, mas não deve interpretar erros de armazenamento ou ciclo de vida por conta própria.
```

O Workspace deve receber erros de nível de aplicação, não exceções específicas de infraestrutura, sempre que possível.

Erros de infraestrutura devem ser traduzidos para erros de aplicação na fronteira apropriada.

# 27 Concorrência e Consistência

O Project Manager é também a fronteira natural para impor consistência de nível de projeto.

**Implementações futuras podem precisar lidar com**


- acesso simultâneo

- file locking

- concorrência otimista

- números de versão de projeto

- recuperação após escritas interrompidas

- autosave

- persistência transacional

- migração de projeto entre versões de schema

Esses mecanismos pertencem à arquitetura de Project Management e persistência, não à Home Page ou ao Workspace.

## 27.1 Schema Version

O Project deve carregar um schema_version. O Project Manager é responsável por:

detectar versões antigas;

acionar migrações;

recusar abertura de projetos incompatíveis com mensagem clara.

# 28 Segurança e Privacidade

Como projetos podem conter informações relacionadas a pacientes, o gerenciamento de projeto deve também servir como fronteira para controle de acesso e auditabilidade.

**A arquitetura deve permitir enforcement futuro de**


- permissões de acesso a projeto

- identidade de usuário

- acesso baseado em papéis

- audit logging

- exclusão controlada

- exportação de dados

- políticas de retenção de dados

## 28.1 Interface de Política

```python
class ProjectAccessPolicy(Protocol):
    def can_create(self, user: User) -> bool: ...
    def can_open(self, user: User, project_id: ProjectId) -> bool: ...
    def can_update(self, user: User, project_id: ProjectId) -> bool: ...
    def can_delete(self, user: User, project_id: ProjectId) -> bool: ...
A Home Page e o Workspace não devem implementar essas políticas de forma independente.
```

# 29 Invariantes Arquiteturais

**Os seguintes invariantes são obrigatórios**


Existe um único Project Manager autoritativo para operações de ciclo de vida de projeto.

A Home Page é somente-leitura em relação ao ciclo de vida de projeto.

O Workspace não é um project manager.

A Home Page não acessa persistência de projeto diretamente.

O Workspace não acessa persistência de projeto diretamente.

O Project Catalog é somente-leitura.

O Project Repository é um mecanismo de persistência, não uma autoridade de ciclo de vida.

O Project Storage é infraestrutura física, não uma autoridade de ciclo de vida.

A criação de projeto passa pelo Project Manager.

A exclusão de projeto passa pelo Project Manager.

A manutenção de metadados de projeto passa pelo Project Manager.

A seleção de projeto produz um Project Context para o Workspace.

O workflow clínico selecionado é transferido junto com o project context.

Plugins e módulos não devem contornar a API do Project Management.

A lista autoritativa de projetos não é mantida pela Home Page.

Estado persistente de projeto deve ter um único dono de ciclo de vida em nível de aplicação.

O domínio não deve conhecer detalhes de persistência (ex.: patient_record.json).

A comunicação entre Project Manager e outros componentes ocorre via Application Event Bus.

Módulos clínicos são passivos: reagem a contexto/eventos, não buscam estado.

Caminhos físicos são resolvidos exclusivamente pelo Project Path Resolver.

# 30 Relação com Outros Documentos de Arquitetura

Este documento define o ciclo de vida do projeto e o modelo de ownership em nível de aplicação.

**Deve ser lido em conjunto com**


domain/project.md — representação de domínio de um Project;

domain/patient.md — conceitos de domínio relacionados a paciente;

domain/scene.md — cena e pertencimento de objetos;

application/ — serviços de aplicação e orquestração;

infrastructure/ — implementações de persistência e storage;

flows/ — execução de workflows clínicos;

workspace.md — ciclo de vida do workspace e contexto;

modules.md — módulos clínicos e contratos de módulo;

adr/ — decisões arquiteturais que governam persistência, transações e ciclo de vida de projeto.

# 31 Sumário

O CranioZ trata gerenciamento de projeto como uma responsabilidade de nível de aplicação com uma única autoridade de ciclo de vida.

**A arquitetura é intencionalmente assimétrica**


```
                     PROJECT MANAGEMENT
                            │
                  ┌─────────┴─────────┐
                  │                   │
             Project Manager    Project Catalog
                  │                   │
                  │                   ▼
                  │              Home Page
                  │
                  ▼
           Project Repository
                  │
                  ▼
            Project Storage
                  │
                  ▼
            Persistent Data


Project Manager
      │
      │ ProjectContext
      │ + ClinicalWorkflow
      ▼
  Workspace
      │
      ▼
Clinical Modules / Flows
O princípio central é:
```

A Home Page descobre projetos, o Project Manager possui seu ciclo de vida, o Repository persiste, o Storage armazena, e o Workspace trabalha com o projeto selecionado sem gerenciá-lo.

Essa separação estabelece um modelo de ownership claro, previne lógica duplicada de gerenciamento de projeto e fornece uma base estável para tecnologias futuras de persistência, workflows clínicos, plugins, transações, controle de acesso e auditabilidade.
