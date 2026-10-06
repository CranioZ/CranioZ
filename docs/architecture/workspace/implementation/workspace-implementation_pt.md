# Workspace — Plano de Implementação

> **Status:** Rascunho
> **Relacionados:** [workspace.md](../architecture/workspace.md)
> **Escopo:** Implementação em fases do subsistema Workspace

---

## 1. Propósito

Este documento descreve **como** o Workspace descrito em
[workspace.md](../architecture/workspace.md) é implementado, em qual
ordem, e com quais marcos.

Cada fase:

- Entrega um incremento **testável**.
- Tem critérios de aceitação claros.
- Não quebra a fase anterior.
- Pode ser revisada e integrada independentemente.

---

## 2. Princípios Norteadores

A implementação segue quatro regras:

1. **Fatias verticais em vez de camadas horizontais.**
   Cada fase entrega uma fatia vertical funcional (UI + lógica +
   teste), não "todos os modelos primeiro, depois todas as views".

2. **Sem dependências para frente.**
   Uma fase nunca depende de uma fase que ainda não foi completada.

3. **Testável a cada passo.**
   Toda fase entrega testes que provam que funciona.

4. **Decisões reversíveis.**
   Se uma decisão se mostrar errada, pode ser mudada sem reescrever
   fases anteriores.

---

## 3. Visão Geral das Fases

| Fase | Nome | Status |
|---|---|---|
| 1 | Modelo Base | Não iniciada |
| 2 | Editor Host | Não iniciada |
| 3 | Editor Registry | Não iniciada |
| 4 | Árvore de Layout | Não iniciada |
| 5 | Construtor de Layout | Não iniciada |
| 6 | Renderizador de Layout | Não iniciada |
| 7 | Regiões e Overlays | Não iniciada |
| 8 | Persistência | Não iniciada |
| 9 | Recursos Avançados | Não iniciada |

Cada fase é independente e testável. As fases 1–7 não têm
dependências externas. As fases 8–9 exigem subsistemas externos
(Scene, VTK, Project).

---

## 4. Dependências Externas

Algumas fases dependem de subsistemas fora do Workspace.

| Fase | Depende de | Observações |
|---|---|---|
| 1 | Nada | — |
| 2 | Nada | — |
| 3 | Nada | — |
| 4 | Nada | — |
| 5 | Nada | Só precisa da Fase 4 |
| 6 | Nada | Só precisa da Fase 4 |
| 7 | Nada | Só precisa da Fase 4 |
| **8** | **Project** (mínimo), **schema JSON** | Ainda não implementado |
| **9** | **Scene** (mínimo), **renderização VTK** | Ainda não implementado |

**Implicação:** as fases 8 e 9 não podem ser completadas sem
coordenação com os subsistemas Project e Scene.

**Recomendação:** implementar as fases 1–7 primeiro (sem dependências
externas), depois avaliar o escopo das fases 8–9.

---

## 5. Evolução Arquitetural

O Workspace evolui **adicionando capacidades**, não mudando o modelo
central. A `LayoutTree` (árvore N-ária de splits) é estável a partir
da Fase 4.

### 5.1 Estado inicial

```text
+---------+--------------+---------+
| LEFT    | CENTRAL      | RIGHT   |
+---------+--------------+---------+
| BOTTOM                            |
+-----------------------------------+
```

- Áreas declaradas pelo `ModuleUISpec`.
- Renderizadas via `QSplitter`.
- Sem abas, sem flutuação, sem arrastar-e-soltar.

**Propósito:** provar o conceito, validar a API, rodar os testes.

### 5.2 Adicionando abas e troca de módulo

A Top Bar (Overlay do Painel Superior) hospeda abas de módulos. Nenhuma
mudança na API do Workspace.

### 5.3 Adicionando toolbars e viewports

Toolbars viram chrome interno de `Editor`. Viewports viram `Editor`.
Nenhuma mudança na API do Workspace.

### 5.4 Adicionando splits arbitrários

- Splits podem ser aninhados arbitrariamente.
- Arrastar-e-soltar entre `Leaf`s.
- Áreas flutuantes.
- Árvores customizadas.

**Nenhuma dessas mudanças altera a API do Workspace.**

---

## 6. Fase 1 — Modelo Base

**Objetivo:** os tipos centrais do Workspace existem e podem ser
instanciados.

### 6.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/workspace/placement.py` | Enum `Placement` |
| `ui/workspace/area.py` | Classe `Area` (concreta, mínima) |
| `ui/workspace/area_manager.py` | `AreaManager` |
| `ui/workspace/area_spec.py` | Dataclass `AreaSpec` |

### 6.2 Critérios de aceitação

- [ ] `Placement` tem `LEFT`, `CENTRAL`, `RIGHT`, `BOTTOM`.
- [ ] `Area` tem `id`, `title`, `visible`, `editor_host` (stub).
- [ ] `Area` **não** armazena `placement`.
- [ ] `AreaManager` registra, desregistra e recupera Areas.
- [ ] ID duplicado levanta `ValueError` com mensagem clara.

### 6.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_placement_enum_has_expected_members` | `tests/unit/ui/test_placement.py` | Unit |
| `test_area_has_id_and_title` | `tests/unit/ui/test_area.py` | Widget |
| `test_area_does_not_store_placement` | `tests/unit/ui/test_area.py` | Widget |
| `test_area_manager_register` | `tests/unit/ui/test_area_manager.py` | Unit |
| `test_area_manager_duplicate_id_raises` | `tests/unit/ui/test_area_manager.py` | Unit |
| `test_area_manager_unregister` | `tests/unit/ui/test_area_manager.py` | Unit |

### 6.4 Riscos

- **Problemas de plugin de plataforma Qt no Windows.** Mitigação:
  fixar versão do PySide6.
- **CI headless.** Mitigação: `QT_QPA_PLATFORM=offscreen`.

---

## 7. Fase 2 — Editor Host

**Objetivo:** `EditorHost` gerencia uma lista de Editors, com um ativo.

### 7.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/editors/base_editor.py` | ABC `Editor` |
| `ui/editors/editor_host.py` | `EditorHost` |
| `ui/workspace/area.py` | Estendido: hospeda um `EditorHost` |

### 7.2 Critérios de aceitação

- [ ] `Editor` é abstrato, com `id`, `title`, `widget()`.
- [ ] `EditorHost` faz `add_editor`, `remove_editor`, `list_editors`.
- [ ] `EditorHost` tem um `active_editor` (só um por vez).
- [ ] `EditorHost` mostra abas quando ≥ 2 editores.
- [ ] `EditorHost` não mostra abas quando ≤ 1 editor.
- [ ] `detach_editor` retorna o editor sem destruí-lo.

### 7.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_editor_is_abstract` | `tests/unit/ui/test_editor.py` | Unit |
| `test_add_editor` | `tests/unit/ui/test_editor_host.py` | Widget |
| `test_remove_editor` | `tests/unit/ui/test_editor_host.py` | Widget |
| `test_set_active_editor` | `tests/unit/ui/test_editor_host.py` | Widget |
| `test_detach_does_not_destroy_editor` | `tests/unit/ui/test_editor_host.py` | Widget |

---

## 8. Fase 3 — Editor Registry

**Objetivo:** `EditorRegistry` resolve `editor_id` para classes
concretas de Editor e cria instâncias.

### 8.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/editors/editor_registry.py` | `EditorRegistry` |

### 8.2 Critérios de aceitação

- [ ] `register(editor_id, editor_type)` registra uma classe.
- [ ] `resolve(editor_id)` retorna a classe.
- [ ] `create(editor_id)` retorna uma nova instância.
- [ ] Resolver `editor_id` desconhecido levanta `KeyError`.

### 8.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_register_and_resolve` | `tests/unit/ui/test_editor_registry.py` | Unit |
| `test_resolve_unknown_raises` | `tests/unit/ui/test_editor_registry.py` | Unit |
| `test_create_returns_instance` | `tests/unit/ui/test_editor_registry.py` | Widget |

---

## 9. Fase 4 — Árvore de Layout

**Objetivo:** `LayoutTree` (árvore N-ária de splits) pode ser
construída a partir de listas de `AreaSpec`.

### 9.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/workspace/layout_tree.py` | `LayoutTree`, `Leaf`, `Split`, `SplitDirection` |

### 9.2 Critérios de aceitação

- [ ] `Leaf` contém exatamente uma `Area`.
- [ ] `Split` tem uma direção e ≥ 2 filhos.
- [ ] `LayoutTree.from_specs(specs, areas)` constrói a árvore correta.
- [ ] `[central]` → `Leaf`.
- [ ] `[left, central, right]` → `Split(HORIZONTAL)` com 3 filhos.
- [ ] `[central, bottom]` → `Split(VERTICAL)`.
- [ ] Spec sem `CENTRAL` levanta `ValueError`.

### 9.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_from_specs_single_central` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_from_specs_left_central_right` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_from_specs_with_bottom` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_from_specs_requires_central` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_to_dict_round_trip` | `tests/unit/ui/test_layout_tree.py` | Unit |

---

## 10. Fase 5 — Construtor de Layout

**Objetivo:** `LayoutBuilder` consome um `ModuleUISpec` e produz uma
`LayoutTree`.

### 10.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/workspace/module_ui_spec.py` | `ModuleUISpec`, `AreaSpec` (estendido) |
| `ui/workspace/layout_builder.py` | `LayoutBuilder` |

### 10.2 Critérios de aceitação

- [ ] `LayoutBuilder.build(spec, editor_registry)` retorna uma
  `LayoutTree`.
- [ ] Resolve os `editor_id` via `EditorRegistry`.
- [ ] Cria instâncias de `Area` com `EditorHost` populado.
- [ ] Rejeita specs sem `CENTRAL`.

### 10.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_build_single_central` | `tests/integration/ui/test_layout_builder.py` | Integração |
| `test_build_left_central_right` | `tests/integration/ui/test_layout_builder.py` | Integração |
| `test_build_creates_areas_with_editors` | `tests/integration/ui/test_layout_builder.py` | Integração |

---

## 11. Fase 6 — Renderizador de Layout

**Objetivo:** `LayoutRenderer` renderiza uma `LayoutTree` em widgets
`QSplitter` aninhados.

### 11.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/workspace/layout_renderer.py` | `LayoutRenderer` |

### 11.2 Critérios de aceitação

- [ ] `Leaf` renderiza como o widget `Area`.
- [ ] `Split` renderiza como um `QSplitter` (H ou V).
- [ ] Renderizador mantém um cache de widgets
  (`split_widgets`, `area_widgets`).
- [ ] Cache é reconstruível a partir da árvore.
- [ ] Renderizador nunca inventa estrutura.

### 11.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_render_single_area` | `tests/integration/ui/test_layout_renderer.py` | Integração |
| `test_render_split_horizontal` | `tests/integration/ui/test_layout_renderer.py` | Integração |
| `test_render_split_vertical` | `tests/integration/ui/test_layout_renderer.py` | Integração |
| `test_cache_rebuildable` | `tests/integration/ui/test_layout_renderer.py` | Integração |

---

## 12. Fase 7 — Regiões e Overlays

**Objetivo:** `Region` derivada da árvore; `Overlay` se posiciona
sobre uma Região.

### 12.1 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/workspace/region.py` | `Region` |
| `ui/workspace/overlay.py` | ABC `Overlay` |
| `ui/workspace/overlay_manager.py` | `OverlayManager` |
| `ui/workspace/top_overlay.py` | `TopOverlay` (Painel Superior) |

### 12.2 Critérios de aceitação

- [ ] `LayoutTree.find_regions()` retorna regiões geométricas.
- [ ] `Region.bounds` é calculado a partir das Areas renderizadas.
- [ ] `OverlayManager.register` adiciona um Overlay.
- [ ] `TopOverlay` se posiciona sobre `Region.CENTRAL`.
- [ ] Overlays se reposicionam quando o layout muda.

### 12.3 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_find_regions_single_central` | `tests/unit/ui/test_region.py` | Unit |
| `test_find_regions_left_central_right` | `tests/unit/ui/test_region.py` | Unit |
| `test_overlay_registers` | `tests/unit/ui/test_overlay.py` | Unit |
| `test_top_overlay_positions_over_central` | `tests/integration/ui/test_overlay.py` | Integração |
| `test_overlay_repositions_on_layout_change` | `tests/integration/ui/test_overlay.py` | Integração |

---

## 13. Fase 8 — Persistência

**Objetivo:** a `LayoutTree` serializa para JSON e desserializa de
volta.

### 13.1 Dependência externa

- Um modelo mínimo de `Project` (arquivo JSON com metadados).
- Um sistema de versionamento de schema JSON.

### 13.2 Entregáveis

| Arquivo | Propósito |
|---|---|
| `ui/workspace/layout_io.py` | Serializar / desserializar layout |
| `infrastructure/persistence/json/project_io.py` | I/O de arquivo de projeto |

### 13.3 Critérios de aceitação

- [ ] Layout serializa para JSON.
- [ ] Layout desserializa de JSON.
- [ ] Round-trip preserva todas as Areas.
- [ ] Areas desconhecidas são ignoradas com aviso.
- [ ] JSON malformado levanta `ValueError` com mensagem clara.

### 13.4 Testes

| Teste | Arquivo | Tipo |
|---|---|---|
| `test_layout_serialization` | `tests/unit/ui/test_layout_io.py` | Unit |
| `test_layout_deserialization` | `tests/unit/ui/test_layout_io.py` | Unit |
| `test_layout_round_trip` | `tests/integration/ui/test_layout_io.py` | Integração |
| `test_layout_ignores_unknown_areas` | `tests/integration/ui/test_layout_io.py` | Integração |
| `test_layout_malformed_json_raises` | `tests/unit/ui/test_layout_io.py` | Unit |

### 13.5 Riscos

**Médio.** Exige um subsistema de Project que ainda não existe.

**Mitigação:** implementar um modelo mínimo de `Project`. Modelo
completo depois.

---

## 14. Fase 9 — Recursos Avançados

**Objetivo:** recursos de layout para usuários avançados.

### 14.1 Entregáveis

| Recurso | Propósito |
|---|---|
| Arrastar-e-soltar entre Leaves | Mover Areas interativamente |
| Areas flutuantes | Destacar Areas em janelas separadas |
| Suporte multi-monitor | Lembrar posição por monitor |
| Árvores customizadas | Arranjos definidos pelo usuário |
| Presets de árvore por Flow | Árvores diferentes por fluxo clínico |

### 14.2 Critérios de aceitação

- [ ] Usuário consegue arrastar uma Area de uma Leaf para outra.
- [ ] Usuário consegue destacar uma Area em uma janela flutuante.
- [ ] Posição da janela flutuante é lembrada por monitor.
- [ ] Usuário consegue salvar a árvore atual como preset.

---

## 15. Dependências Entre Fases

```text
Fase 1 (Modelo Base)
    |
    v
Fase 2 (Editor Host)
    |
    v
Fase 3 (Editor Registry)
    |
    v
Fase 4 (Árvore de Layout)
    |
    +----------------+----------------+
    |                                   |
    v                                   v
Fase 5 (Construtor)              Fase 6 (Renderizador)
    |                                   |
    +----------------+------------------+
                     |
                     v
              Fase 7 (Regiões e Overlays)
                     |
                     v
              Fase 8 (Persistência)
                     |
                     v
              Fase 9 (Recursos Avançados)
```

As fases 5 e 6 podem ser desenvolvidas em paralelo se as dependências
permitirem.

---

## 16. Resumo da Estratégia de Testes

| Nível | Ferramenta | Cobertura |
|---|---|---|
| Unit | pytest | Modelos, lógica de layout, IO |
| Widget | pytest-qt | Areas, Workspace, Editors |
| Integração | pytest-qt | Registro, layout, persistência |
| Visual | (posterior) | Screenshots de regressão |

**Meta de cobertura:** ≥ 80% para `ui/workspace/`.

Ver [workspace-testing.md](../workspace-testing.md) para detalhes.

---

## 17. Definition of Done

Uma fase é considerada **concluída** quando:

- [ ] Todos os entregáveis estão implementados.
- [ ] Todos os critérios de aceitação passam.
- [ ] Todos os testes passam no CI.
- [ ] Código é revisado.
- [ ] Documentação é atualizada.
- [ ] CHANGELOG tem uma entrada.
- [ ] Um ADR é escrito se a fase introduzir uma decisão arquitetural.

---

## 18. Marcos

| Marco | Fases | Observações |
|---|---|---|
| M1 — Modelo base roda | Fase 1 | Tipos centrais existem. |
| M2 — EditorHost funciona | Fases 2, 3 | Editors e registry. |
| M3 — Árvore de layout constrói | Fase 4 | `LayoutTree.from_specs` funciona. |
| M4 — Module spec constrói UI | Fase 5 | `LayoutBuilder` funciona. |
| M5 — Árvore renderiza em Qt | Fase 6 | `LayoutRenderer` funciona. |
| M6 — Overlays se posicionam | Fase 7 | Regiões e TopOverlay. |
| M7 — Layout persiste | Fase 8 | Round-trip JSON. |
| M8 — Layout avançado | Fase 9 | Arrastar-e-soltar, flutuação, multi-monitor. |

Cada marco é um ponto natural de parada. O Workspace é utilizável em
todos os marcos a partir de M1.

---

## 19. Recomendações

Dado o escopo:

1. **Implementar as fases 1–7 primeiro.** Não têm dependências
   externas (exceto Qt/PySide6) e entregam um Workspace totalmente
   funcional.
2. **Deixar a fase 8 como stub se necessário.** Implementar um modelo
   mínimo de `Project` para permitir persistência sem o subsistema
   completo de Project.
3. **Adiar a fase 9.** Recursos avançados (arrastar-e-soltar,
   flutuação) exigem design de UX significativo e devem ser
   adicionados depois que o núcleo estiver estável.

---

## 20. Questões Abertas

### 20.1 O `LayoutRenderer` deve ser stateless ou stateful?

**Opção A:** Stateless — função pura `tree → widget`.
**Opção B:** Stateful — mantém um cache de widgets para reúso.

**Tendência atual:** Opção B. Mantém um cache, mas o cache é
reconstruível a partir da árvore a qualquer momento.

### 20.2 Como testar Areas flutuantes no CI?

Ambientes de CI headless não têm múltiplos monitores.

**Tendência atual:** mockar a geometria de tela, testar flags de
janela em vez de posições reais.

### 20.3 Animação de troca de Editor deve ser adicionada?

**Opção A:** Sim — transição fade ou slide.
**Opção B:** Não — troca instantânea.

**Tendência atual:** Opção B.

### 20.4 A fase 8 deve bloquear o release inicial?

**Opção A:** Sim — persistência é necessária para um release útil.
**Opção B:** Não — o Workspace pode sair sem persistência;
persistência é adicionada em fase posterior.

**Tendência atual:** Opção B.

### 20.5 `LayoutBuilder` e `LayoutRenderer` devem ser fundidos?

**Opção A:** Manter separados — build é operação pura de dados;
render é operação de UI.
**Opção B:** Fundir em uma classe única.

**Tendência atual:** Opção A. Responsabilidades separadas.
