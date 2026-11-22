
---

## Resumo das mudanças aplicadas ao `next_steps.md`

| Seção | Mudança |
|---|---|
| Cabeçalho | `Last updated: 2026-11-20` |
| §1.2 | Baseline `1,692` passed (era `1,635`); nota da medição anterior e da não-remoção da cobertura |
| §1.3 | Acrescentado "Project Catalog synchronization via `ProjectIndex` (ADR-0016, Sprint I)" à lista de capabilities concluídas; nota final atualizada |
| §2.1 | Nova linha "Sprint I — ProjectIndex ✅ Complete (2026-11-20)" com contagem 1692 |
| §2.5 (nova) | Seção de closure do Sprint I: 1692 passed, fixture migration, bootstrap order, `refresh()` removido |
| §3.1 | Sprint I → ✅ Complete (2026-11-20); Sprint J → 🚧 Pending com dep `Sprint I ✅`; Sprint K idem; cadeia atualizada para "J and K form a functional chain" |
| §4.1, bullet "ProjectIndex" | "Now implemented per ADR-0016" (era "Now specified by ADR-0016") |
| §5.1 | Status → ✅ Complete (2026-11-20); deliverables agora marcados como implementados; adicionada "Closure note (2026-11-20)" com validação final, fixture migration, bootstrap order |
| §5.2 | Status → 🚧 Pending, dep `Sprint I ✅`; acrescentada nota do mecanismo de staleness (`_possibly_stale` → `ensure_fresh()`) como caminho de recuperação |
| §5.3 | Status → 🚧 Pending, deps `Sprint I ✅ and Sprint J` |
| §5.4 | Status → 🚧 Pending (nota "unblocked by refactoring" mantida); acrescentada nota de paralelismo com J–K |
| §6 (intro) | "Sprint I is complete. The remaining work is the functional chain J → K" |
| §6.1 | Sprint I removido da tabela; Sprint J com dep `Sprint I ✅`; Sprint K com dep `Sprint J` |
| §6.2 | Current cycle reescrito: 1) Sprint I complete, 2) Start Sprint J, 3) Start Sprint K after J, 4) Sprint L in parallel |
| §8.2 (nova) | Checklist de closure de sprint (6 itens), incluindo o grep gate do `implementation_plan.md` §8 |