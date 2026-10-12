# Janela Principal (MainWindow)

## 1. Propósito
A *MainWindow* é a janela de nível superior da aplicação e hospeda o Espaço de Trabalho (Workspace) do CranioZ. Ela apresenta a estrutura principal da aplicação, incluindo o Espaço de Trabalho e os elementos de interface (UI) que pertencem à própria janela.

Este documento define as responsabilidades e os limites da janela principal. O documento do Espaço de Trabalho descreve as Áreas, as Sobreposições (Overlays), o layout e a composição da interface dos módulos. O documento de Fluxos de Trabalho Clínicos descreve a execução dos fluxos de trabalho. O documento *steps_panel* descreve o painel de navegação do fluxo de trabalho, hospedado como uma Sobreposição compartilhada do Espaço de Trabalho.

## 2. Responsabilidades
A MainWindow é responsável por:

* gerenciar o ciclo de vida da janela de nível superior;
* hospedar o Espaço de Trabalho;
* apresentar elementos de interface atribuídos à janela principal, como a barra de menu nativa e os controles de janela do sistema operacional, quando aplicável;
* encaminhar intenções globais do usuário para as funcionalidades apropriadas da camada de aplicação;
* coordenar solicitações de inicialização e encerramento com o ambiente de execução (runtime) da aplicação;
* encaminhar solicitações de abertura e fechamento de projetos para o ambiente de execução da aplicação, sem gerenciar o ciclo de vida ou os dados do projeto;
* consumir e refletir as configurações visuais e de idioma fornecidas pela aplicação nas superfícies que hospeda, como tema, ícones e idioma ativo;
* apresentar o estado relevante de operação da aplicação quando necessário, sem realizar processamento pesado dentro da janela.

A MainWindow é um limite de apresentação e hospedagem. Ela não implementa regras clínicas, verificações de requisitos de fluxo de trabalho, operações de módulos ou alterações no estado do domínio ou do projeto. O Gerenciador de Projetos (Project Manager) é a autoridade da aplicação para o ciclo de vida do projeto.

## 3. Relação com o Espaço de Trabalho
```
QApplication
└── MainWindow
├── Controles de janela nativos do SO
├── Barra de menu nativa do SO (opcional)
└── Espaço de Trabalho (área de conteúdo)
├── Barra Superior (estrutural)
├── Árvore de Layout de Áreas
│   └── Áreas (com árvores de layout de editor internas)
└── Sobreposições (Overlays)
└── steps_panel
```
A MainWindow fornece a estrutura da aplicação: controles de janela nativos e, quando aplicável, a barra de menu do sistema operacional. Todo o restante pertence ao Espaço de Trabalho.

O Espaço de Trabalho é responsável por:

* a Barra Superior (Top Bar) — um componente estrutural, não uma Sobreposição; * a Árvore de Layout da Área e as Árvores de Layout do Editor;
* Sobreposições (Overlays), incluindo o `steps_panel` compartilhado.

A `MainWindow` hospeda o `Workspace` e repassa eventos de ciclo de vida. Ela não interpreta a estrutura interna do `Workspace`.

O `Workspace` não tem conhecimento sobre módulos clínicos ou Fluxos. A `MainWindow` também não detém a responsabilidade pelo fluxo de trabalho clínico. A camada de Aplicação carrega o Fluxo e o módulo ativos, coordena transições e fornece ao `Workspace` o estado de apresentação do fluxo de trabalho e a `ModuleUISpec`.

## 4. Relação com módulos e fluxos de trabalho clínicos
Os módulos não detêm a `MainWindow` nem a substituem quando são ativados. Um módulo fornece uma `ModuleUISpec`; a camada de Aplicação repassa essa especificação ao `Workspace` para materialização.

A mesma janela principal e o mesmo `Workspace` permanecem ativos à medida que o módulo em uso é alterado. Em um fluxo de trabalho clínico:

1. O motor de fluxo de trabalho em Python avalia a etapa atual e seus requisitos.
2. A camada de Aplicação ativa o módulo associado à etapa selecionada.
3. A camada de Aplicação fornece a `ModuleUISpec` do módulo ao `Workspace`.
4. O `Workspace` materializa a composição declarada pelo módulo.
5. A sobreposição `steps_panel` compartilhada permanece disponível e recebe o estado atualizado de apresentação do fluxo de trabalho.

A `MainWindow` pode hospedar o `Workspace` durante essas transições, mas não escolhe a próxima etapa nem seleciona o módulo. Essas decisões cabem à camada de Aplicação e ao motor de fluxo de trabalho.

## 5. Elementos da janela e conteúdo do Workspace
Os elementos de interface (UI) da janela principal limitam-se a:

* **Controles de janela nativos do SO** — barra de título, minimizar/maximizar/fechar.
* **Barra de menus nativa do SO** — quando aplicável.

Não há barra de status na `MainWindow`. A função tradicional da barra de status é desempenhada por uma Área do `Workspace` (tipicamente a Área inferior), declarada pelo módulo. A `MainWindow` não hospeda visualizações de status.

A composição da Página Inicial e seus elementos de UI, incluindo seu próprio cabeçalho quando aplicável, são definidos na documentação da Página Inicial e/ou do `Workspace`.

As preferências de idioma, tema e conjunto de ícones são gerenciadas pelo serviço de configurações da aplicação, coordenado pela camada de Aplicação. A `MainWindow` não detém nem persiste essas preferências; ...ele e seus componentes hospedados consomem os valores ativos e atualizam sua apresentação quando a aplicação os altera.

## 6. Operações assíncronas e responsividade
A **MainWindow** não executa operações de longa duração nem cria, gerencia ou sincroniza threads. O carregamento e processamento de imagens, as operações de leitura e escrita de dados e outras tarefas que poderiam bloquear a interface do usuário são realizados por serviços apropriados externos à janela.

A camada de Aplicação coordena essas operações e comunica o estado relevante à interface do usuário, como...