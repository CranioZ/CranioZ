"""Manifest for the ``orthognathic_guide`` built-in module.

Declares the module identity, version, and dependencies
(see ``modules.md`` v10 §5). Contributions (Commands, Tools, Editors,
UI specs) are declared by the module implementation once it exists;
they do not appear here (``modules.md`` v10 §5.4).

The module is not yet implemented. ``MANIFEST`` is declared with the
fields that are already fixed (identity, dependencies, entry point)
so that ``ModuleRegistry`` can register it and dependent modules can
declare a dependency on it. The module cannot be loaded until its
``OrthognathicGuideModule`` class exists.
"""

from __future__ import annotations

from cranioz.modules.base.module_manifest import (
    ModuleDependency,
    ModuleManifest,
)

MANIFEST = ModuleManifest(
    module_id="orthognathic_guide",
    version="1.0.0",
    label_key="modules.orthognathic_guide.label",
    description_key="modules.orthognathic_guide.description",
    entry_point=("cranioz.modules.builtin.orthognathic_guide.module:OrthognathicGuideModule"),
    dependencies=(
        ModuleDependency("osteotomies", ">=1.0.0"),
        ModuleDependency("cephalometry", ">=1.0.0"),
    ),
)
