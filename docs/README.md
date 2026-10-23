# CranioZ Documentation

Technical documentation for the CranioZ platform. This directory contains the
architecture contracts, decision records, domain specifications, and developer
guides that define how the system is built.

Documentation is normative. When a document and the code disagree, the document
is the contract and the code is the defect. When two documents disagree, the ADR
that resolved the conflict wins, and the losing document is corrected.

---

## 1. Structure

```
docs/
├── README.md                  (this file)
├── PRINCIPLES.md              Founding principles of the project
├── GLOSSARY.md                Canonical definitions of all terms
├── adr/                       Architecture Decision Records (ADR-0001 … ADR-0012)
├── architecture/              Architecture contracts and specifications
│   ├── overview.md            High-level system architecture
│   ├── implementation.md      Phased execution plan and status
│   ├── commands/              Command mechanism (ADR-0007)
│   ├── scene/                 Scene and DomainObjectStore (ADR-0008)
│   ├── modules/               Module contract and lifecycle
│   ├── clinical_workflows/    Flows, steps_panel, orthognathic reference
│   ├── domain/                Patient and Project domain specifications
│   ├── objects/               Object model and Datatypes
│   ├── ui/                    Workspace, Areas, Editors, Toolbars, Tools
│   ├── appearance/            Themes, tokens, surfaces, overlays, widgets
│   ├── internationalization/  i18n contract and catalog format
│   ├── main_window/           MainWindow responsibilities
│   ├── home_page/             HomePage responsibilities
│   └── config/                Configuration and folder structure
├── developer/                 Contributor-facing guides
│   └── testing.md             Testing strategy and conventions
└── adr/startup_project_opening_workflow.md    Boot-to-Workspace flow
```

## 2. Where to start

    If you need to…	                                    Read
    Understand the project's founding rules	            PRINCIPLES.md
    Understand what a term means	                    GLOSSARY.md
    Understand the layers and boundaries	            architecture/overview.md
    Understand why a decision was made	                adr/ (start at ADR-0001)
    Understand the current implementation status	    architecture/implementation.md
    Work on the Workspace or Editors	                architecture/ui/workspace/workspace.md, architecture/ui/editors/editors.md
    Work on Commands, Tasks, or Telemetry	            adr/ADR-0007, adr/ADR-0011, adr/ADR-0012
    Work on the Scene	                                adr/ADR-0008, architecture/scene/scene.md
    Work on the Patient or Project domain	            architecture/domain/patient/patient.md, architecture/domain/project/project.md
    Write or review tests	                            developer/testing.md

## 3. Document types
Every document declares its type in its header. The types are:

* **Principle** — a founding rule that other documents must not contradict
* (PRINCIPLES.md).
* Reference — a canonical definition, kept current (GLOSSARY.md).
* **ADR** — a recorded architectural decision with context, rationale, and consequences. ADRs are immutable after acceptance; new decisions are recorded as new ADRs, not by editing old ones.
* Architecture specification — a detailed contract for a subsystem (commands.md, scene.md, modules.md, workspace.md, editors.md, …).
* **Domain specification** — the conceptual model of a domain entity (patient.md, project.md).
* **Roadmap** — an execution plan and status record (implementation.md).
* **Developer guide** — practical guidance for contributors (testing.md).

## 4. Conventions
* **Language**. All documentation is written in English. User-facing labels are localized; identifiers and internal terminology are not.
* **Normative terms**. MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY follow RFC 2119.
* **Cross-references**. Documents reference each other by relative path and section, never by page number.
* **Glossary first**. A new term is added to GLOSSARY.md before it is used in a document. A deprecated term is moved to GLOSSARY.md §9 and must not be reintroduced.
* **ADRs are append-only**. A wrong decision is superseded by a new ADR that explicitly states which ADR it replaces.
* **Status fields**. ADRs and specifications declare Status: (Proposed, Accepted, Deprecated) and Last updated:. A document without a status is a draft and must not be used as a contract.

## 5. Keeping documentation in sync
Documentation is part of the code. A change that alters a contract must update
the documents in the same commit. The Definition of Done in
architecture/implementation.md §8 makes this explicit:

Documentation is updated (including ADRs if a new decision was made).

When the code and the document disagree:

1. If the document is correct, the code is a defect. Fix the code.
2. If the code reflects a new decision, write a new ADR and update the affected document. Do not silently edit the old ADR.

## 6. Reviewing documentation
A document is reviewable when:

* It declares its type, status, and scope.
* Its terms are defined in GLOSSARY.md or are standard technical terms.
* It references the ADRs it depends on.
* It does not contradict PRINCIPLES.md or an Accepted ADR.
* It states its error contracts and boundaries explicitly.
* It distinguishes what is a contract from what is an implementation.

## 7. Known gaps
The following are tracked in architecture/implementation.md §10:

* ADR-0003 is Proposed, not Accepted.
* Some documents still reference EditorHost, which ADR-0001 removed.
* architecture/domain/project/project.md and architecture/README.md contain editorial artifacts that must be removed.
* The i18n test directory is empty; the i18n contract has no automated validation yet.