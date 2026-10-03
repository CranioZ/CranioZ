Este documento consolida o fluxo de inicialização da aplicação e o fluxo de abertura de projeto, desde o boot até o Workspace pronto para uso. É a especificação operacional que conecta a arquitetura (project.md) à implementação real.

1. Fluxo de Inicialização da Aplicação (Boot)
text
1. CranioZ inicia
        ↓
2. Carrega configurações
        ↓
3. Obtém o Project Root
   C:\Users\<user>\Documents\CranioZ\Projects
        ↓
4. Project Catalog lista os projetos
        ↓
5. Home Page exibe a lista
1.1 Detalhamento
Passo 1 — CranioZ inicia
text
main.py
   │
   ├── bootstrap application
   ├── initialize dependency container
   ├── initialize logging
   └── initialize event bus
Passo 2 — Carrega configurações
text
ConfigurationLoader.load()
   │
   ├── read config/app.json
   │       ├── language
   │       ├── theme
   │       ├── recent_projects_limit
   │       └── ...
   ├── read config/paths.json
   │       ├── project_root
   │       ├── flows_root
   │       └── cache_root
   └── read config/user.json
           ├── user_id
           ├── preferences
           └── ...
Passo 3 — Obtém o Project Root
O ProjectPathResolver é inicializado com o root vindo da configuração.

text
ProjectPathResolver.initialize(project_root)
   │
   ├── default: C:\Users\<user>\Documents\CranioZ\Projects
   └── override: config/paths.json → project_root
Regras:

O Project Root é resolvido uma vez no boot e permanece estável durante a sessão.

Se o diretório não existir, é criado com a estrutura mínima.

Se não for acessível, a aplicação falha com erro claro (ProjectRootInaccessible).

Passo 4 — Project Catalog lista os projetos
text
ProjectCatalog.list_projects()
   │
   ├── read <project_root>/info.json
   │       └── se ausente ou corrompido:
   │             └── rebuild_index()
   │                   └── scan <project_root>/*/project.json
   │
   └── return list[ProjectSummary]
Regras:

O Catalog é um read model. Ele não carrega dados clínicos.

Se info.json estiver ausente, o Catalog reconstrói o índice varrendo as pastas.

Se estiver corrompido, o Catalog faz backup e reconstrói.

Passo 5 — Home Page exibe a lista
text
HomePage
   │
   ├── recebe list[ProjectSummary]
   ├── renderiza cards/lista
   ├── habilita busca/filtro
   └── aguarda seleção do usuário
Regras:

A Home Page não acessa o filesystem diretamente.

A Home Page não mantém lista autoritativa própria.

A Home Page apenas exibe o que o Catalog fornece.

2. Fluxo de Abertura de Projeto
text
6. Usuário seleciona um projeto
        ↓
7. Project Manager abre o projeto
        ↓
8. Project Repository carrega project.json
        ↓
9. Project Manager cria o ProjectContext
        ↓
10. Usuário/Project Manager define o Clinical Flow
        ↓
11. ProjectContext + Clinical Flow → Workspace
        ↓
12. Workspace inicializa os módulos do Flow
        ↓
13. Módulos carregam os dados necessários
        ↓
14. Workspace pronta para uso
2.1 Detalhamento
Passo 6 — Usuário seleciona um projeto
text
HomePage
   │
   ├── user clicks project card
   ├── (opcional) user selects clinical flow
   └── emit signal: project_selected(project_id)
Regras:

A seleção é apenas uma intenção. Nada é carregado ainda.

O project_id é o único dado transferido neste passo.

Passo 7 — Project Manager abre o projeto
text
ProjectManager.open_project(project_id)
   │
   ├── check access policy
   │       └── can_open(user, project_id)
   ├── check ProjectInUse
   │       └── se já aberto, retornar contexto existente ou erro
   ├── delegate to ProjectRepository.get(project_id)
   └── build ProjectContext
Regras:

Apenas o Project Manager inicia a abertura.

Verificações de política e concorrência ocorrem antes do carregamento.

Falhas retornam exceções de aplicação (ProjectNotFound, ProjectAccessDenied, ProjectInUse).

Passo 8 — Project Repository carrega project.json
text
ProjectRepository.get(project_id)
   │
   ├── resolve path: <project_root>/<uuid>/
   ├── read project.json
   │       ├── project_id
   │       ├── project_name
   │       ├── patient_id
   │       ├── status
   │       ├── clinical_procedure
   │       ├── schema_version
   │       └── timestamps
   ├── read patient_record.json
   │       ├── patient metadata
   │       ├── medical history
   │       └── logical paths
   ├── read workflow.json
   │       ├── workflow_id
   │       ├── current_step
   │       └── config
   ├── check schema_version
   │       └── se antigo: ProjectMigrationService.migrate()
   └── return Project (domain object)
Regras:

O Repository não decide se o projeto deve ser aberto. Apenas carrega.

Migrações de schema ocorrem aqui, de forma transparente.

Se algum arquivo estiver corrompido, retorna ProjectCorrupted.

Passo 9 — Project Manager cria o ProjectContext
text
ProjectManager.build_context(project)
   │
   ├── extract metadata (read-only)
   ├── extract patient_summary
   ├── extract project_state
   ├── resolve application services
   ├── collect object_references
   └── return ProjectContext
Contrato do ProjectContext:

python
@dataclass(frozen=True)
class ProjectContext:
    project_id: ProjectId
    metadata: ProjectMetadata          # read-only
    patient_summary: PatientSummary
    project_state: ProjectState
    workflow_id: WorkflowId | None     # pode ser None até seleção
    workflow_config: WorkflowConfig | None
    service_locator: ApplicationServices
    object_references: list[ObjectReference]
Regras:

O ProjectContext é um snapshot de inicialização, não o projeto em si.

É imutável (frozen) para o Workspace.

Não contém caminhos físicos — apenas referências lógicas.

Passo 10 — Define o Clinical Flow
O fluxo pode ser definido de duas formas:

A) Definido pelo usuário na Home Page (antes da abertura):

text
HomePage
   │
   ├── user selects project
   ├── user selects flow
   └── emit signal: project_selected(project_id, flow_id)
B) Resolvido pelo Project Manager (após abertura):

text
ProjectManager.open_project(project_id)
   │
   ├── ...
   ├── WorkflowResolver.resolve(project)
   │       └── determina flow com base em:
   │             ├── project.clinical_procedure
   │             ├── workflow.json (se já houver)
   │             └── preferências do usuário
   └── attach workflow to context
Regras:

A Home Page não implementa lógica de workflow.

O WorkflowResolver é a autoridade de resolução.

Se nenhum flow for resolvido, o Workspace abre em modo "seleção de flow".

Passo 11 — ProjectContext + Clinical Flow → Workspace
text
ProjectManager
   │
   ├── publish ProjectOpened event
   │       └── subscribers: HomePage, Catalog, ...
   │
   └── handoff to Workspace
           │
           │ ProjectContext
           │ + ClinicalFlow
           ▼
       Workspace
Regras:

O handoff é explícito. O Workspace não busca o contexto.

O evento ProjectOpened é publicado para outros subsistemas.

O Workspace se torna o consumidor do contexto.

Passo 12 — Workspace inicializa os módulos do Flow
text
Workspace.initialize(context, flow)
   │
   ├── setup layout
   ├── load flow definition
   │       └── flow.json
   ├── instantiate modules
   │       ├── ImagingModule
   │       ├── SegmentationModule
   │       ├── RegistrationModule
   │       ├── CephalometryModule
   │       └── OsteotomyModule
   ├── inject context into modules
   └── subscribe modules to event bus
Regras:

Os módulos são passivos: recebem o contexto, não o buscam.

Cada módulo é inicializado com o ProjectContext e seu WorkflowConfig.

Módulos podem subscrever eventos relevantes (WorkflowStepChanged, etc.).

Passo 13 — Módulos carregam os dados necessários
text
ImagingModule.initialize(context)
   │
   ├── resolve logical paths via ProjectPathResolver
   │       ├── resolve("imaging/ct")
   │       └── resolve("imaging/cbct")
   ├── load image metadata (não os pixels ainda)
   ├── register with workspace layout
   └── ready

SegmentationModule.initialize(context)
   │
   ├── resolve("segmentation/maxilla")
   ├── load segmentation results (se existirem)
   └── ready

OsteotomyModule.initialize(context)
   │
   ├── resolve("planning/osteotomies")
   ├── load planning data (se existir)
   └── ready
Regras:

Módulos carregam dados sob demanda (lazy loading quando possível).

Módulos nunca constroem caminhos físicos — sempre usam ProjectPathResolver.

Módulos nunca persistem diretamente — sempre usam comandos de aplicação.

Passo 14 — Workspace pronta para uso
text
Workspace
   │
   ├── layout renderizado
   ├── módulos inicializados
   ├── dados carregados (parcialmente)
   ├── event bus ativo
   └── aguardando interação do usuário
3. Diagrama Unificado
text
CranioZ
  │
  ▼
Home Page
  │
  │ ProjectSummary
  ▼
Project Catalog
  │
  │ project_id
  ▼
Project Manager
  │
  │ open(project_id)
  ▼
Project Repository
  │
  │ project.json + metadata
  ▼
Project Manager
  │
  │ ProjectContext
  │ + Clinical Flow
  ▼
Workspace
  │
  ▼
Modules
  │
  ├── Imaging
  ├── Segmentation
  ├── Registration
  ├── Cephalometry
  └── Osteotomy
4. Fluxo Detalhado com Responsabilidades
text
┌─────────────────────────────────────────────────────────────────┐
│ BOOT                                                            │
├─────────────────────────────────────────────────────────────────┤
│ main.py                                                         │
│   ├── bootstrap application                                     │
│   ├── ConfigurationLoader.load()                                │
│   ├── ProjectPathResolver.initialize(project_root)              │
│   ├── ProjectCatalog.initialize()                               │
│   └── HomePage.show()                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ DISCOVERY                                                       │
├─────────────────────────────────────────────────────────────────┤
│ HomePage                                                        │
│   ├── request: ProjectCatalog.list_projects()                   │
│   ├── receive: list[ProjectSummary]                             │
│   ├── render: cards/lista                                       │
│   └── await: user selection                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ SELECTION                                                       │
├─────────────────────────────────────────────────────────────────┤
│ HomePage                                                        │
│   ├── user clicks project                                       │
│   ├── (optional) user selects flow                              │
│   └── emit: project_selected(project_id, flow_id?)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ OPENING                                                         │
├─────────────────────────────────────────────────────────────────┤
│ ProjectManager                                                  │
│   ├── check access policy                                       │
│   ├── check ProjectInUse                                        │
│   ├── ProjectRepository.get(project_id)                         │
│   │       ├── read project.json                                 │
│   │       ├── read patient_record.json                          │
│   │       ├── read workflow.json                                │
│   │       └── check schema_version (migrate if needed)          │
│   ├── WorkflowResolver.resolve(project)                         │
│   ├── build ProjectContext                                      │
│   └── publish ProjectOpened event                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ HANDOFF                                                         │
├─────────────────────────────────────────────────────────────────┤
│ ProjectManager                                                  │
│   └── Workspace.initialize(ProjectContext, ClinicalFlow)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ WORKSPACE INITIALIZATION                                        │
├─────────────────────────────────────────────────────────────────┤
│ Workspace                                                       │
│   ├── setup layout                                              │
│   ├── load flow definition                                      │
│   ├── instantiate modules                                       │
│   ├── inject context                                            │
│   └── subscribe to event bus                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ MODULE INITIALIZATION                                           │
├─────────────────────────────────────────────────────────────────┤
│ Modules                                                         │
│   ├── ImagingModule.initialize(context)                         │
│   ├── SegmentationModule.initialize(context)                    │
│   ├── RegistrationModule.initialize(context)                    │
│   ├── CephalometryModule.initialize(context)                    │
│   └── OsteotomyModule.initialize(context)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ READY                                                           │
├─────────────────────────────────────────────────────────────────┤
│ Workspace                                                       │
│   └── awaiting user interaction                                 │
└─────────────────────────────────────────────────────────────────┘
5. Sequência Temporal (Mermaid)
6. Pontos de Falha e Tratamento
Ponto	Falha possível	Tratamento
Boot	ProjectRootInaccessible	Erro fatal com diálogo
Catalog	info.json corrompido	Rebuild index
Catalog	info.json ausente	Rebuild index
Selection	Nenhum projeto	Home Page mostra estado vazio
Opening	ProjectNotFound	Notificar Home Page
Opening	ProjectAccessDenied	Notificar Home Page
Opening	ProjectInUse	Oferecer abrir em modo leitura ou aguardar
Opening	ProjectCorrupted	Notificar, oferecer restauração
Opening	ProjectIncompatibleSchema	Notificar, bloquear abertura
Migration	Falha na migração	Reverter do backup
Workspace	Falha na inicialização de módulo	Isolar módulo, continuar com os demais
Modules	Falha ao carregar dados	Módulo mostra estado de erro
7. Regras Arquiteturais Aplicadas
Este fluxo respeita os invariantes definidos em project.md:

✅ Apenas o Project Manager inicia a abertura.

✅ A Home Page é somente-leitura (não escreve, não persiste).

✅ O Project Catalog é um read model.

✅ O Project Repository apenas persiste/recupera.

✅ O ProjectContext é imutável para o Workspace.

✅ O Workspace não busca estado, apenas consome.

✅ Os Módulos são passivos.

✅ Caminhos físicos são resolvidos pelo ProjectPathResolver.

✅ A comunicação entre componentes ocorre via Event Bus.

✅ O Clinical Flow é resolvido pelo WorkflowResolver.

8. Resumo
O fluxo de inicialização e abertura de projeto no CranioZ segue uma sequência clara:

text
BOOT       → configuração, path resolver, catalog
DISCOVERY  → catalog lista, home page exibe
SELECTION  → usuário escolhe projeto (+ flow)
OPENING    → project manager coordena, repository carrega
CONTEXT    → project manager constrói ProjectContext
HANDOFF    → project manager entrega ao workspace
WORKSPACE  → workspace inicializa layout e módulos
MODULES    → módulos carregam dados sob demanda
READY      → workspace pronto para uso
O princípio central é:

A Home Page descobre, o Project Manager coordena, o Repository carrega, o Workspace consome, os Módulos executam.