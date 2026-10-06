# Janela principal (`MainWindow`)

## 1. Objetivo

`MainWindow` é a janela de nível superior da aplicação e hospeda o CranioZ Workspace. Ela apresenta a estrutura principal da aplicação, incluindo o Workspace e os elementos de interface que pertencem à própria janela.

Este documento define as responsabilidades e os limites da janela principal. O documento do Workspace descreve Areas, Overlays, layout e composição da interface dos módulos. O documento de Clinical Workflows descreve a execução dos fluxos clínicos. O documento de `steps_panel` descreve o painel de navegação do workflow, hospedado como um Overlay compartilhado do Workspace.

Este texto é uma proposta arquitetural para validação técnica. Decisões de produto ainda não confirmadas estão identificadas como tais.

## 2. Responsabilidades

`MainWindow` é responsável por:

- controlar o ciclo de vida da janela de nível superior;
- hospedar o Workspace;
- apresentar os elementos de interface atribuídos à janela principal, como a barra de menus nativa e os controles de janela do sistema operacional, quando aplicáveis;
- encaminhar intenções globais do usuário às capacidades apropriadas da camada Application;
- coordenar solicitações de inicialização e encerramento com o runtime da aplicação;
- encaminhar ao runtime da aplicação solicitações de abertura e fechamento de projeto, sem gerenciar o ciclo de vida nem os dados do projeto;
- consumir e refletir nas superfícies que hospeda as configurações visuais e de idioma fornecidas pela aplicação, como tema, ícones e idioma ativo;
- apresentar o estado de operações relevantes para a aplicação, quando necessário, sem executar o trabalho pesado dentro da janela.

`MainWindow` é uma fronteira de apresentação e hospedagem. Ela não implementa regras clínicas, verificações de requisitos do workflow, operações de módulos nem alterações de estado do domínio ou do projeto. O `Project Manager` é a autoridade de aplicação para o ciclo de vida do projeto e coordena suas operações com catálogo, políticas de acesso, repositório e armazenamento.

## 3. Relação com o Workspace

```text
QApplication
    └── MainWindow
          ├── Elementos de interface da janela principal
          └── Workspace
                ├── Areas e seus Editors
                └── Overlays, incluindo o steps_panel compartilhado
```

A proposta é que o runtime da aplicação crie e mantenha uma instância do Workspace, e que `MainWindow` a receba e a instale em sua região de conteúdo. A janela pode encaminhar eventos de ciclo de vida, enquanto o Workspace gerencia suas próprias Areas, árvore de layout e posicionamento de Overlays.

O Workspace hospeda Areas e Overlays e não conhece módulos clínicos nem Flows. `MainWindow` também não é dona do workflow clínico. A camada Application carrega o Flow e o módulo ativos, coordena transições e fornece o estado de apresentação do workflow e o `ModuleUISpec` às partes da interface que precisam deles.

## 4. Relação com módulos e workflows clínicos

Os módulos não são donos de `MainWindow` e não a substituem quando são ativados. Um módulo fornece um `ModuleUISpec`; a camada Application entrega essa especificação ao Workspace para materialização.

A mesma janela principal e o mesmo Workspace permanecem ativos durante a troca de módulo. Em um workflow clínico:

1. O motor Python de workflow avalia a etapa atual e seus requisitos.
2. A camada Application ativa o módulo associado à etapa selecionada.
3. A camada Application fornece o `ModuleUISpec` do módulo ao Workspace.
4. O Workspace materializa a composição declarada pelo módulo.
5. O Overlay compartilhado `steps_panel` permanece disponível e recebe o estado de apresentação atualizado do workflow.

`MainWindow` pode hospedar o Workspace durante essas transições, mas não escolhe a próxima etapa nem o módulo. Essas decisões pertencem à camada Application e ao motor de workflow.

## 5. Elementos da janela e conteúdo do Workspace

Os elementos de interface da janela principal são aqueles que ficam fora da composição do Workspace, como os controles nativos da janela e, quando aplicável, a barra de menus nativa. O Workspace continua responsável por suas Areas e Overlays, incluindo o `steps_panel` compartilhado.

Uma visualização de console ou de estado, por exemplo, é hospedada em uma Area do Workspace quando declarada pelo módulo; ela não se torna uma barra de status de `MainWindow` sem um requisito explícito de nível da aplicação. A composição da Home Page e seus elementos de interface, incluindo a Top Bar quando aplicável, devem ser definidos na documentação da Home Page e/ou do Workspace, conforme a responsabilidade estabelecida nesses documentos.

As preferências de idioma, tema e conjunto de ícones são gerenciadas pelo serviço de configurações da aplicação, coordenado pela camada Application. `MainWindow` não é dona dessas preferências nem as persiste; ela e os componentes hospedados consomem os valores ativos e atualizam a apresentação quando a aplicação os altera. A aplicação disponibiliza os recursos de tradução, enquanto cada componente apresenta seus textos no idioma ativo.

## 6. Operações assíncronas e responsividade

`MainWindow` não executa operações demoradas nem cria, gerencia ou sincroniza threads. Carregamento de imagens, processamento, leitura e gravação de dados e outras tarefas que possam bloquear a interface são executados por serviços apropriados fora da janela.

A camada Application coordena essas operações e comunica à interface seus estados relevantes, como início, progresso, conclusão, cancelamento ou erro. `MainWindow` e os componentes do Workspace apresentam esse estado e encaminham as ações do usuário, como cancelar, sem bloquear a thread da interface. A implementação do trabalho assíncrono e a escolha da tecnologia de concorrência pertencem aos serviços e à arquitetura de execução, não a `MainWindow`.

## 7. Ciclo de vida

### 7.1 Inicialização

```text
QApplication inicia
    ↓
Runtime da aplicação e registros são inicializados
    ↓
Workspace e componentes compartilhados de interface são criados
    ↓
MainWindow é criada e recebe o Workspace
    ↓
Uma splash screen opcional apresenta o estado da inicialização
    ↓
Aplicação restaura o contexto selecionado através do Project Manager, se aplicável
    ↓
Aplicação ativa o módulo apropriado
    ↓
Workspace materializa o ModuleUISpec do módulo
    ↓
MainWindow é exibida e a splash screen é encerrada
```

A splash screen, se adotada, é uma interface temporária de inicialização coordenada pelo runtime da aplicação. Ela não é `MainWindow` nem parte do Workspace. Sua exibição e encerramento devem acompanhar o estado real da inicialização; falhas devem ser comunicadas pela interface apropriada. A decisão sobre exibir a janela principal antes ou depois da restauração completa permanece uma escolha de produto e implementação.

O Workspace pode existir antes de haver um projeto ou módulo ativo. O `steps_panel` compartilhado pode existir sem um workflow ativo e receber o conteúdo do Flow quando a camada Application o carregar. Quando há restauração de projeto, a aplicação solicita ao `Project Manager` a abertura do projeto e a construção do `Project Context`; a janela apenas hospeda a interface resultante.

### 7.2 Fechamento e encerramento

Quando o usuário solicita o fechamento da janela, `MainWindow` encaminha a solicitação ao runtime da aplicação e aguarda sua decisão antes de concluir o fechamento. Se houver um projeto ativo, o runtime coordena com o `Project Manager` o encerramento do contexto e o tratamento de alterações pendentes, de acordo com a política da aplicação. O `Project Manager` é responsável por validar e coordenar persistência; `MainWindow` apenas apresenta confirmações ou erros solicitados pela aplicação. Se o usuário cancelar ou uma operação necessária falhar, a janela permanece aberta. A janela não descarta silenciosamente estado do projeto, clínico ou de workflow.

O contrato de fechamento deve permitir que salvamentos ou operações em andamento terminem, sejam cancelados ou sejam recusados de acordo com a política da aplicação. O runtime só autoriza o fechamento depois que o `Project Manager` e os demais serviços envolvidos concluírem ou recusarem suas responsabilidades de encerramento. A janela só conclui o fechamento após receber essa autorização explícita.

O estado do layout do Workspace e o progresso clínico do workflow são persistidos por seus respectivos responsáveis. A geometria da janela e outras preferências de apresentação são armazenadas nas configurações de apresentação da aplicação, separadas do estado do caso clínico. O formato e o mecanismo concretos de armazenamento ficam a cargo da implementação.

## 8. Propriedade do estado

| Estado | Responsável |
| --- | --- |
| Visibilidade e geometria da janela principal | `MainWindow` e configurações de apresentação da aplicação |
| Idioma ativo, tema e conjunto de ícones | Serviço de configurações da aplicação, coordenado pela camada Application |
| Recursos de tradução | Aplicação; componentes de interface apresentam os textos traduzidos |
| Árvore de Areas, divisões e posicionamento de Overlays | Workspace |
| Composição da interface do módulo | `ModuleUISpec` do módulo, materializado pelo Workspace |
| Definição e progresso do workflow clínico | Motor de workflow da camada Application e persistência do projeto/caso |
| Ciclo de vida e consistência do projeto | `Project Manager` |
| Descoberta somente leitura de projetos | `Project Catalog` |
| Persistência e armazenamento físico do projeto | Project Repository e Project Storage, coordenados pelo `Project Manager` |
| Objetos e resultados clínicos | Domínio e serviços de módulos/aplicação |
| Estado de operações demoradas e assíncronas | Serviço responsável pela operação, coordenado pela camada Application |

`MainWindow` pode hospedar esses componentes, mas não é a fonte de verdade para seus estados.

## 9. Limites arquiteturais

- `MainWindow` depende do Workspace como componente de interface hospedado; a camada Domain não depende de `MainWindow`.
- `MainWindow` não cria, atualiza, exclui, abre nem persiste projetos diretamente; solicitações de ciclo de vida são encaminhadas ao runtime/camada Application e executadas pelo `Project Manager`.
- A Home Page descobre e seleciona projetos; o Workspace trabalha com o `Project Context` aberto. Nenhum deles substitui o `Project Manager` ou acessa diretamente a persistência.
- Módulos clínicos não manipulam diretamente os detalhes internos de `MainWindow`.
- Ações do usuário são encaminhadas por capacidades da camada Application, em vez de executar operações de domínio dentro de callbacks da janela.
- O estado do workflow é fornecido pela camada Application; `MainWindow` não inspeciona nem calcula requisitos clínicos.
- `MainWindow` não executa trabalho pesado nem gerencia threads; serviços especializados executam operações assíncronas e a camada Application coordena sua interação com a interface.
- Estado do layout do Workspace e progresso do workflow clínico são persistidos separadamente; o estado do projeto segue a fronteira de persistência coordenada pelo `Project Manager`.
- O fechamento da janela segue a política de salvamento e encerramento da aplicação.
- Requisitos de acessibilidade e internacionalização devem ser aplicados às interfaces apresentadas pela aplicação, incluindo `MainWindow`, Workspace e módulos. Seus critérios compartilhados devem ser definidos na arquitetura de apresentação e nos requisitos transversais do produto.

## 10. Considerações de teste

Testes de `MainWindow` devem se concentrar em hospedagem e ciclo de vida:

- Workspace é instalado como componente de conteúdo principal;
- elementos de interface de nível da janela aparecem nas regiões previstas;
- solicitações de inicialização e fechamento são encaminhadas ao runtime da aplicação;
- fechamento não prossegue quando o runtime/`Project Manager` informa cancelamento ou falha ao encerrar o contexto ativo;
- transições de módulo e workflow não recriam a janela principal;
- ações globais invocam capacidades da camada Application em vez de alterar o estado do domínio diretamente;
- estados de operações demoradas podem ser apresentados sem bloquear a interface;
- a janela não cria nem gerencia threads para realizar operações de serviço.

Layout do Workspace, comportamento dos Overlays, transições de workflow, avaliação de requisitos clínicos e execução de tarefas assíncronas devem ser testados em suas respectivas fronteiras arquiteturais.

## 11. Decisões pendentes para validação

- Confirmar se a splash screen será exibida e em quais etapas da inicialização.
- Confirmar o ponto em que `MainWindow` deve ser exibida em relação à restauração do projeto/caso e à ativação do módulo.
- Definir o contrato de coordenação entre runtime, `Project Manager` e interface para abertura/fechamento de projeto, incluindo cancelamento e falhas de persistência.
- Definir o contrato técnico assíncrono entre runtime, camada Application, serviços e interface, incluindo cancelamento e encerramento com operações em andamento.
- Definir os requisitos compartilhados de acessibilidade e internacionalização aplicáveis à interface.
- Confirmar em quais documentos ficam a composição da Home Page e a Top Bar, mantendo referências cruzadas apenas para documentos existentes.
