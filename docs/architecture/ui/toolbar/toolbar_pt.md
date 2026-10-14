# Toolbar

## 1. Visão geral

Uma **Toolbar** é um elemento da interface gráfica responsável por disponibilizar um conjunto de ações de acesso rápido ao usuário.

No CranioZ, a Toolbar atua como uma **interface de apresentação de Tools**, permitindo que operações frequentemente utilizadas sejam executadas diretamente a partir da interface.

A Toolbar não implementa a lógica das operações que disponibiliza. Ela apenas apresenta os elementos de interação e encaminha a ação do usuário para a `Tool`, `Command` ou outro mecanismo apropriado.

Essa separação mantém a interface desacoplada da lógica de domínio e permite que uma mesma operação seja disponibilizada em diferentes partes da interface.

```text
Toolbar
   │
   ├── Tool Button
   ├── Tool Button
   ├── Separator
   ├── Tool Button
   └── Tool Button
          │
          ▼
        Tool
          │
          ▼
       Command
          │
          ▼
     Application
          │
          ▼
        Domain
```

---

## 2. Papel da Toolbar

A Toolbar existe principalmente para oferecer **acesso rápido às operações relevantes para o contexto atual**.

Ela pode apresentar:

* Tools;
* comandos de uso frequente;
* ações de navegação;
* controles de visualização;
* ações específicas de um Editor;
* ações fornecidas por módulos;
* ações fornecidas por plugins.

A Toolbar não deve ser utilizada como local para implementar regras clínicas, regras de negócio ou processamento de dados.

Essas responsabilidades pertencem às camadas correspondentes da aplicação.

---

## 3. Toolbar e Tool

Uma **Tool** representa uma ação operacional que pode ser disponibilizada ao usuário. A **Toolbar** representa uma das possíveis formas de apresentar essa Tool na interface.

Portanto, uma Tool não pertence necessariamente a uma Toolbar específica. A mesma Tool pode ser disponibilizada, dependendo do contexto, em:

* uma Toolbar;
* um menu;
* um menu contextual;
* um painel;
* um atalho de teclado;
* outro componente de interface.

```text
                 ┌── Toolbar
                 │
Tool ────────────┼── Menu
                 │
                 ├── Context Menu
                 │
                 └── Keyboard Shortcut
```

Essa relação evita que a definição da operação fique acoplada ao componente visual utilizado para executá-la.

---

## 4. Toolbar e Editor

As Toolbars do CranioZ são frequentemente associadas a um **Editor**.

Um Editor declara quais Tools necessita para realizar sua função. A Toolbar utiliza essa definição para disponibilizar as Tools correspondentes ao usuário.

Por exemplo, um Editor de visualização 3D pode utilizar:

```text
[ Select ] [ Move ] [ Rotate ] [ Measure ] | [ View ] [ Reset ]
```

Enquanto um Editor de tomografia pode utilizar:

```text
[ Window/Level ] [ Zoom ] [ Pan ] [ Crosshair ] | [ MPR ] [ Reset ]
```

A Toolbar, entretanto, continua sendo um componente de interface. A implementação das operações permanece nas respectivas Tools, Commands ou serviços.

A relação pode ser representada como:

```text
Tool Registry
      │
      ▼
   Editor
      │
      │ declara as Tools utilizadas
      ▼
   Toolbar
      │
      │ apresenta as Tools
      ▼
    User
```

---

## 5. Toolbar e contexto

Uma Toolbar pode ser **contextual**. Isso significa que seu conteúdo pode mudar de acordo com:

* o Editor ativo;
* o objeto selecionado;
* o modo de interação;
* o módulo ativo;
* o Flow atual;
* o estado do Workspace;
* as capacidades disponíveis.

Por exemplo, ao selecionar uma osteotomia, determinadas Tools relacionadas ao planejamento ósseo podem tornar-se disponíveis.

Quando nenhum objeto compatível está selecionado, essas Tools podem permanecer ocultas ou desabilitadas.

A Toolbar deve refletir o contexto operacional atual sem assumir responsabilidades sobre a determinação desse contexto.

---

## 6. Estado das ações

Os elementos apresentados por uma Toolbar devem refletir o estado atual da aplicação.

Uma ação pode estar:

* disponível;
* indisponível;
* desabilitada;
* selecionada;
* ativada;
* marcada;
* oculta.

Por exemplo:

```text
[ Select ] [ Move ] [ Rotate ] [ Measure ]
    ✓
```

ou:

```text
[ Select ] [ Move ] [ Rotate ] [ Measure ]
                     ─────────
                     disabled
```

A determinação da disponibilidade da ação deve ser baseada nas capacidades e condições da aplicação, e não em regras implementadas diretamente na Toolbar.

---

## 7. Toolbar Items

Os elementos individuais de uma Toolbar são denominados **Toolbar Items**.

Um Toolbar Item pode representar uma ação ou um elemento de organização visual.

Os principais tipos incluem:

### 7.1 Action Item

Representa uma ação executável.

```text
[ Select ]
```

Normalmente está associado a uma Tool ou Command.

### 7.2 Toggle Item

Representa uma ação que possui estado ligado/desligado.

```text
[ Grid ✓ ]
```

O estado visual deve refletir o estado real da funcionalidade.

### 7.3 Separator

Separa grupos funcionalmente distintos de ações.

```text
[ Select ] [ Move ] [ Rotate ] | [ Measure ] [ Angle ]
```

Separadores devem ser utilizados com moderação, principalmente para estabelecer agrupamentos semânticos.

### 7.4 Menu Item

Permite acessar um conjunto de ações relacionadas.

```text
[ Transform ▼ ]
```

Pode ser utilizado quando a apresentação direta de todas as ações ocuparia espaço excessivo.

---

## 8. Organização das Tools

As Tools apresentadas em uma Toolbar devem ser agrupadas de acordo com sua função.

Por exemplo:

```text
[ Select ] [ Move ] [ Rotate ]
                     |
                     ├── Manipulation

[ Measure ] [ Angle ] [ Distance ]
                     |
                     ├── Measurement

[ Reset ] [ Fit ]
                     |
                     └── View
```

A organização deve privilegiar:

* frequência de utilização;
* proximidade funcional;
* contexto clínico;
* contexto do Editor;
* consistência entre diferentes módulos.

A Toolbar não deve simplesmente reproduzir a lista completa de Tools disponíveis.

Ela deve apresentar as operações relevantes para o contexto atual.

---

## 9. Toolbar e módulos

Módulos podem disponibilizar funcionalidades que são representadas por Tools e posteriormente utilizadas por Editors e Toolbars.

As Tools, entretanto, não pertencem necessariamente à estrutura interna de um módulo. O CranioZ mantém um conjunto comum de Tools disponíveis para utilização pelos diferentes componentes da aplicação.

Por exemplo, funcionalidades relacionadas à osteotomia podem disponibilizar Tools como:

```text
[ Create Osteotomy ]
[ Edit Osteotomy ]
[ Preview ]
[ Apply ]
```

Um Editor que trabalhe com planejamento de osteotomias pode declarar essas Tools entre as que utiliza.

```text
Module
   │
   │ fornece funcionalidade
   ▼
Tool
   │
   │ disponível no sistema
   ▼
Editor
   │
   │ declara utilização
   ▼
Toolbar
```

Essa separação permite que a funcionalidade fornecida por um módulo seja utilizada por diferentes Editors sem acoplar a Tool a uma Toolbar específica.

---

## 10. Toolbar e plugins

Plugins podem fornecer funcionalidades adicionais que sejam disponibilizadas por meio de Tools.

Essas Tools podem ser registradas no sistema e posteriormente utilizadas pelos Editors que necessitarem delas.

Conceitualmente:

```text
Core ────────────┐
                 │
Modules ─────────┼──► Tools ───► Editors ───► Toolbars
                 │
Plugins ─────────┘
```

Um plugin não deve depender da implementação interna de uma Toolbar específica.

A integração deve ocorrer por meio das interfaces públicas do framework.

---

## 11. Toolbar principal e Toolbars contextuais

O CranioZ pode possuir diferentes níveis de Toolbar.

### 11.1 Main Toolbar

Uma Toolbar associada à aplicação ou ao Workspace principal.

Pode conter operações de uso geral, como:

* abrir e salvar projetos;
* desfazer e refazer;
* seleção;
* navegação;
* operações gerais de visualização.

### 11.2 Editor Toolbar

Uma Toolbar associada a um determinado Editor.

Contém as Tools específicas utilizadas pela função daquele Editor.

### 11.3 Contextual Toolbar

Uma Toolbar ou conjunto de ações apresentado de acordo com o contexto atual.

Pode depender do:

* objeto selecionado;
* modo ativo;
* módulo;
* Flow;
* estado do procedimento.

Essa separação permite que a interface permaneça compacta sem remover funcionalidades avançadas.

---

## 12. Toolbar e Layout

A Toolbar é um componente de interface e pode ser hospedada em diferentes regiões do Workspace, conforme o Layout.

Sua posição não altera sua função.

Por exemplo:

```text
Workspace
│
├── Header
│
├── Toolbar
│
├── Area
│   └── Editor
│
└── Area
    └── Editor
```

Uma Toolbar também pode estar associada a um Editor específico:

```text
Area
│
├── Toolbar
│
└── Editor
```

O Layout determina **onde** a Toolbar é apresentada.

O contexto funcional determina **quais ações** ela apresenta.

---

## 13. Toolbar e Commands

Quando uma ação da Toolbar altera o estado persistente da aplicação, sua execução deve normalmente ocorrer por meio de um `Command`.

Por exemplo:

```text
Toolbar
   │
   ▼
Tool
   │
   ▼
Command
   │
   ▼
Application State
```

Isso permite que operações executadas pela Toolbar participem dos mecanismos de:

* undo;
* redo;
* histórico de operações;
* validação;
* registro de eventos.

A Toolbar não deve manipular diretamente o estado do domínio para executar essas operações.

---

## 14. Toolbar e estado da aplicação

A Toolbar deve ser reativa ao estado da aplicação.

Quando o contexto muda, os itens relevantes devem ser atualizados.

Exemplo:

```text
Selection = None

[ Cut ]      disabled
[ Copy ]     disabled
[ Delete ]   disabled
```

Após selecionar um objeto compatível:

```text
Selection = Mandible

[ Cut ]      enabled
[ Copy ]     enabled
[ Delete ]   enabled
```

A Toolbar apresenta o estado recebido da aplicação; ela não deve duplicar ou manter uma segunda fonte de verdade para esse estado.

---

## 15. Toolbar Configuration

A composição de uma Toolbar deve ser configurável.

Uma Toolbar pode ser construída a partir de uma especificação contendo:

* identificação;
* título;
* posição;
* contexto;
* grupos de ações;
* Tools;
* separadores;
* menus;
* condições de disponibilidade.

Exemplo conceitual:

```python
ToolbarSpec(
    id="modeling",
    title="Modeling",
    items=[
        "tool.select",
        "tool.move",
        "tool.rotate",
        Separator(),
        "tool.measure",
    ],
)
```

A especificação descreve **como as Tools devem ser organizadas e apresentadas**, enquanto a implementação da Toolbar determina **como essa configuração será materializada na interface**.

A especificação não deve duplicar a definição das Tools. As Tools são definidas e registradas independentemente da Toolbar.

---

## 16. Princípios de projeto

A implementação das Toolbars do CranioZ deve seguir alguns princípios:

### 16.1 Separação de responsabilidades

A Toolbar apresenta ações.

As Tools executam operações.

Os Commands representam alterações transacionais do estado.

Os serviços executam operações especializadas.

O domínio representa os conceitos e regras fundamentais da aplicação.

### 16.2 Contextualidade

A Toolbar deve apresentar apenas as ações relevantes ao contexto atual sempre que possível.

### 16.3 Consistência

A mesma Tool deve possuir comportamento consistente independentemente do local em que seja apresentada.

### 16.4 Baixa intrusão visual

A Toolbar deve fornecer acesso rápido às operações sem competir visualmente com o conteúdo principal do Editor.

### 16.5 Extensibilidade

Módulos e plugins devem poder disponibilizar novas Tools sem modificar diretamente a implementação da Toolbar.

### 16.6 Estado único

A Toolbar não deve manter uma cópia independente do estado da aplicação.

### 16.7 Reutilização

Uma mesma Tool deve poder ser apresentada em diferentes componentes de interface.

### 16.8 Independência das Tools

As Tools devem ser definidas independentemente das Toolbars.

Um Editor seleciona as Tools que necessita, e uma Toolbar apresenta essas Tools.

---

## 17. Arquitetura conceitual

A relação entre os principais elementos pode ser representada da seguinte forma:

```text
                         Tool Registry
                              │
                ┌─────────────┼─────────────┐
                │             │             │
             Tool A        Tool B        Tool C
                │             │             │
                └─────────────┼─────────────┘
                              │
                         Editor
                              │
                   declares required Tools
                              │
                              ▼
                          Toolbar
                              │
                         presents Tools
                              │
                              ▼
                            User
```

Módulos e plugins podem contribuir com novas Tools:

```text
Core ────────────┐
                 │
Module ──────────┼──► Tool Registry ───► Editor ───► Toolbar
                 │
Plugin ──────────┘
```

A Toolbar, portanto, constitui uma **camada de apresentação das Tools disponíveis**, e não um mecanismo de implementação dessas operações.

A arquitetura pode ser resumida da seguinte forma:

```text
Tools      → o que pode ser feito
Editor     → quais Tools são necessárias
Toolbar    → como as Tools são apresentadas
User       → interage com as Tools
```
