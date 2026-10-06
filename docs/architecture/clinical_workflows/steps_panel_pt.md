# Painel de Etapas (`steps_panel`)

## Objetivo e responsabilidade

O `steps_panel` é um componente da UI da workspace que apresenta e controla a navegação por um fluxo de trabalho. O mesmo painel pode servir a diferentes fluxos clínicos. Para o planejamento de cirurgia ortognática, por exemplo, ele apresenta uma sequência única de etapas e acompanha o usuário enquanto a workspace ativa o módulo associado a cada etapa.

O painel não contém regras clínicas nem calcula por conta própria se uma etapa foi concluída. A definição declarativa do fluxo é escrita em JSON; o motor do fluxo, implementado em Python, valida a definição, avalia requisitos, mantém o estado do caso e solicita à workspace a ativação do módulo correspondente.

## Modelo conceitual

O fluxo é organizado nesta hierarquia:

1. **Fluxo:** sequência de trabalho orientada a um objetivo clínico.
2. **Etapa:** unidade de trabalho dentro do fluxo, com um ou mais passos.
3. **Passo:** ação, entrada, configuração ou verificação realizada pelo usuário ou pelo sistema.
4. **Requisito:** condição verificável que determina se um passo ou uma etapa pode avançar ou ser concluída.

Como padrão, cada etapa está associada a um módulo. O fluxo permanece uma lista unificada, ainda que cada etapa abra um módulo diferente. O mesmo módulo pode aparecer em mais de uma etapa. A estrutura permite exceções, como uma etapa que use mais de um módulo, mas esse não é o caso usual.

Ao concluir uma etapa, o motor Python verifica os requisitos. Se a conclusão for válida, atualiza o progresso e solicita à workspace a ativação do módulo da próxima etapa. O `steps_panel` continua presente e atualiza a etapa selecionada e os estados apresentados.

## Responsabilidades dos componentes

### Definição JSON do fluxo

Descreve os dados declarativos do fluxo: identificador e versão, nome, etapas ordenadas, módulo associado a cada etapa, passos, textos e imagens de orientação, requisitos, alternativas, dependências, ações e critérios de conclusão.

### Motor Python do fluxo

- carrega e valida a definição JSON;
- verifica se módulos, verificadores e ações referenciados são conhecidos pela aplicação;
- avalia requisitos e determina estados;
- valida comandos de avançar ou concluir;
- determina a próxima etapa e solicita a troca de módulo à workspace;
- persiste o progresso e notifica a UI sobre mudanças.

### Workspace

Organiza a área de trabalho, mantém o painel e as demais áreas visuais e ativa o módulo solicitado pelo motor. A workspace não decide regras clínicas.

### Painel `steps_panel`

Apresenta a sequência, o conteúdo da etapa ativa, os requisitos e o progresso. Envia comandos do usuário ao motor e reflete o estado que recebe dele.

### Módulos

Executam as operações específicas de cada área e informam ao motor resultados verificáveis. Os módulos não definem a sequência global do fluxo.

## Requisitos, alternativas e conclusão

Cada requisito declara se é obrigatório ou opcional. Requisitos obrigatórios aplicáveis precisam ser satisfeitos para concluir a etapa. Requisitos opcionais podem permanecer pendentes sem bloquear a conclusão. Alternativas permitem satisfazer um mesmo objetivo por métodos diferentes.

Por exemplo, uma TC de face pode ser obrigatória para iniciar o planejamento. O escaneamento intrabucal pode ser opcional se as arcadas dentárias também puderem ser segmentadas da TC. Se o usuário escolher o escaneamento intrabucal, o alinhamento dele à TC passa a ser requisito obrigatório para integrar esse caminho.

O motor Python avalia os requisitos por meio de verificadores implementados e registrados pela aplicação. O JSON referencia esses verificadores por identificadores conhecidos; não contém código executável. Uma referência desconhecida ou inválida deve ser reportada como erro de configuração, nunca presumida como satisfeita.

## Estados e transições

O motor Python é a única autoridade para calcular o estado do fluxo. O painel apenas representa esse estado. São definidos os seguintes estados para uma etapa:

| Estado | Significado |
| --- | --- |
| `pending` | A etapa ainda não foi iniciada. |
| `active` | A etapa está selecionada para execução. |
| `blocked` | A etapa não pode ser iniciada ou concluída porque uma dependência ou requisito obrigatório não foi satisfeito. |
| `completed` | Os critérios de conclusão da etapa foram verificados e satisfeitos. |

Passos usam `pending`, `active` e `completed`; podem também usar `blocked` quando dependerem de outro passo ou requisito. O estado agregado da etapa é derivado do estado dos passos e dos requisitos: ela só pode ser `completed` quando todos os requisitos obrigatórios aplicáveis estiverem satisfeitos e os passos requeridos concluídos. Requisitos opcionais não bloqueiam a conclusão.

Transições normais da etapa:

```text
pending -> active -> completed
   |         |
   +------> blocked
blocked -> pending ou active, após resolver a causa do bloqueio
```

Se um dado usado como evidência for alterado ou removido, o motor reavalia os requisitos. Uma etapa previamente concluída pode voltar a `active` ou `blocked` se seus critérios deixarem de ser verdadeiros; essa mudança deve ser persistida e registrada no histórico. Reabrir uma etapa concluída para revisão é permitido conforme as regras do fluxo, e não apaga seu histórico.

## Estrutura e exemplo de JSON

Os arquivos JSON são a fonte versionada da definição dos fluxos. O exemplo abaixo demonstra uma etapa que aceita dois caminhos alternativos para obter as arcadas. Os identificadores de verificadores e ações correspondem a implementações registradas no sistema Python.

```json
{
  "id": "orthognathic_planning",
  "name": "Planejamento ortognático",
  "version": 1,
  "steps": [
    {
      "id": "patient_data",
      "title": "Dados do paciente",
      "module": "patient_data_module",
      "description": "Selecione os dados que serão usados no planejamento.",
      "guidance": [
        {
          "type": "text",
          "text": "A TC de face é obrigatória. Para as arcadas, use escaneamento intrabucal ou segmentação da TC."
        },
        {
          "type": "image",
          "src": "assets/patient_data_guide.svg",
          "alt": "Fontes de dados usadas no planejamento ortognático.",
          "caption": "Dados de entrada"
        }
      ],
      "requirements": [
        {
          "id": "face_ct_available",
          "required": true,
          "check": "case_has_face_ct"
        },
        {
          "id": "dental_arches_available",
          "required": true,
          "satisfy_any": [
            "intraoral_scans_aligned",
            "dental_arches_segmented_from_ct"
          ]
        },
        {
          "id": "intraoral_scans_available",
          "required": false,
          "check": "case_has_intraoral_scans"
        }
      ],
      "actions": [
        {
          "id": "import_face_ct",
          "label": "Importar TC",
          "handler": "import_face_ct"
        }
      ],
      "completion": {
        "all_required_satisfied": true
      }
    },
    {
      "id": "cephalometry",
      "title": "Cefalometria",
      "module": "cephalometry_module",
      "depends_on": ["patient_data"],
      "description": "Adquira e revise os pontos cefalométricos.",
      "requirements": [
        {
          "id": "cephalometric_points_reviewed",
          "required": true,
          "check": "cephalometry_points_reviewed"
        }
      ],
      "completion": {
        "all_required_satisfied": true
      }
    },
    {
      "id": "osteotomy",
      "title": "Osteotomias",
      "module": "osteotomy_module",
      "depends_on": ["cephalometry"],
      "description": "Planeje e revise as osteotomias.",
      "requirements": [
        {
          "id": "osteotomy_plan_reviewed",
          "required": true,
          "check": "osteotomy_plan_reviewed"
        }
      ],
      "completion": {
        "all_required_satisfied": true
      }
    }
  ]
}
```

O esquema definitivo do JSON deve ser validado pelo motor Python. Os campos de texto são apresentados ao usuário; IDs de etapas, módulos, verificadores e handlers conectam a definição declarativa às implementações permitidas. A sequência no JSON é a fonte da ordem; dependências explícitas são validadas para detectar referências inexistentes ou ciclos.

## Orientações, imagens e localização

Uma etapa ou passo pode fornecer título, descrição, instruções, legenda e imagens PNG ou SVG. Textos e caminhos de recursos são dados declarativos; não podem conter instruções executáveis.

As imagens são recursos do pacote do fluxo. O validador resolve o caminho relativo, normaliza-o e confirma que o caminho final permanece dentro do diretório permitido do pacote. O validador também aplica uma allowlist de extensões e tipos de mídia, rejeita caminhos absolutos, traversal (`..`) e links que escapem do pacote. Recurso ausente ou inválido gera erro de validação legível; o sistema não carrega um caminho arbitrário do sistema de arquivos.

Os textos são armazenados diretamente no JSON do fluxo nesta versão da arquitetura. Uma futura localização pode usar catálogos separados ligados pelos mesmos IDs estáveis de fluxo, etapa e passo. Os textos localizados não alteram os IDs nem a lógica de conclusão. A política de versionamento dos catálogos será definida quando a aplicação implementar múltiplos idiomas.

## Persistência, retomada e histórico

O progresso é armazenado por caso clínico, separado dos arquivos JSON que definem os fluxos. Fechar e reabrir o sistema não deve reiniciar o trabalho: ao abrir novamente um caso, o motor restaura o fluxo e sua versão, a etapa e o passo ativos, as escolhas feitas, os estados e as referências aos dados produzidos ou usados pelos módulos.

O estado atual deve ser separado do histórico de evidências:

- **Snapshot do progresso:** representa a posição e o estado atuais do caso para restauração rápida.
- **Histórico de eventos/evidências:** registra alterações relevantes, como requisito satisfeito ou invalidado, etapa iniciada ou concluída, usuário responsável, horário e referências aos objetos que sustentam a decisão.

Essa combinação mantém o progresso atual simples de carregar e preserva rastreabilidade. A tecnologia concreta de armazenamento segue a arquitetura de persistência da aplicação, mas deve suportar essas duas funções e gravação consistente. Imagens médicas e malhas não são duplicadas pelo painel; os registros de progresso armazenam referências estáveis a objetos gerenciados pelos módulos, usando IDs persistentes do sistema de dados. Caminhos locais temporários não servem como identidade de um objeto clínico.

Cada caso fica associado à versão da definição usada para iniciá-lo. Uma nova versão não deve reinterpretar silenciosamente casos em andamento. Alterações incompatíveis exigem manter a definição original para aquele caso ou realizar uma migração explícita, validada e registrada.

## Concorrência

O sistema deve detectar quando mais de um usuário altera o mesmo caso. A gravação do progresso verifica a versão do estado lido; se outro usuário já o tiver alterado, o sistema não sobrescreve silenciosamente a atualização mais recente. Deve recarregar e reavaliar requisitos e estados, informando o conflito quando as alterações não puderem ser combinadas automaticamente.

Uma conclusão de etapa é sempre revalidada no momento da gravação. Assim, se um usuário concluir Cefalometria enquanto outro altera os pontos usados como evidência, o motor avalia o estado mais recente antes de avançar para Osteotomias. O registro histórico identifica o autor e a alteração que causou a mudança de estado.

## Contrato entre o motor e o painel

O motor fornece ao painel:

- nome do fluxo e etapa/passo ativos;
- títulos, descrições, instruções e recursos de orientação;
- ordem, módulo associado e estado de cada etapa e passo;
- requisitos aplicáveis, obrigatoriedade, resultado e motivo de pendência;
- ações habilitadas e explicação de ações bloqueadas;
- progresso restaurado do caso.

O painel envia comandos, como selecionar uma etapa, avançar ou solicitar conclusão. O motor valida cada comando, atualiza e persiste o estado, solicita à workspace a ativação do módulo correspondente e devolve o novo estado ao painel. A UI não marca etapas como concluídas localmente.

## Características visuais e acessibilidade

Com base nos protótipos, o painel:

- possui barra de título com o nome “Painel de etapas” e controles do painel;
- pode ser expandido e recolhido;
- pode ser movido e redimensionado na workspace;
- apresenta etapas numa lista vertical ordenada;
- expande a etapa ativa para mostrar passos, instruções e controles;
- mantém as demais etapas em formato compacto;
- oferece rolagem interna para conteúdo que excede o espaço disponível;
- mostra estados de maneira compreensível, sem depender apenas da cor.

O painel deve ser operável por teclado, manter foco visível e ordem de foco previsível, expor nomes e estados compreensíveis a leitores de tela e usar contraste legível. Mudanças de etapa e mensagens de validação devem ser anunciadas sem deslocar o foco de forma inesperada. Textos alternativos descrevem as imagens instrutivas; imagens decorativas são identificadas como tais.

## Fluxo de planejamento ortognático

Uma configuração inicial pode conter estas etapas, cada uma associada ao seu módulo:

1. Dados do paciente.
2. Alinhamento dos modelos.
3. Segmentações.
4. Cefalometria.
5. Osteotomias.
6. Guia cirúrgica.

Cada etapa pode conter vários passos e requisitos. Ao satisfazer os requisitos obrigatórios e solicitar a conclusão, o usuário avança para a próxima etapa e a workspace ativa automaticamente o módulo correspondente, mantendo o mesmo `steps_panel`.

## Princípios de projeto

- **Fluxo unificado:** uma única sequência ordenada é apresentada pelo painel.
- **Uma etapa, um módulo por padrão:** exceções são declaradas explicitamente no JSON.
- **Separação de responsabilidades:** JSON define; Python valida e coordena; a workspace ativa módulos; o painel apresenta e envia comandos.
- **Flexibilidade clínica:** requisitos obrigatórios, opcionais e alternativos são verificáveis.
- **Retomada e rastreabilidade:** o progresso sobrevive ao encerramento e suas mudanças deixam evidências.
- **Segurança de recursos:** imagens só são carregadas de pacotes validados.
- **Acessibilidade:** informação e controles são utilizáveis por diferentes tecnologias assistivas e modos de entrada.
- **Consistência:** estado mostrado pelo painel sempre vem do motor do fluxo.