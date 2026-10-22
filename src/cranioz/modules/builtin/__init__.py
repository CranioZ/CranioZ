"""Built-in modules.

The application bootstrap populates ModuleRegistry from BUILTIN_MANIFESTS
(modules.md v10 §10.5). Each entry is a ModuleManifest imported from the
corresponding subpackage's manifest.py.
"""

from __future__ import annotations

from cranioz.modules.base.module_manifest import ModuleManifest

# Populated as each module's manifest is implemented.
BUILTIN_MANIFESTS: tuple[ModuleManifest, ...] = ()
