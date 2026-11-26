"""Built-in modules.

The main_window bootstrap populates ModuleRegistry from BUILTIN_MANIFESTS
(modules.md v10 §10.5). Each entry is a ModuleManifest imported from the
corresponding subpackage's manifest.py.
"""

from __future__ import annotations

from cranioz.modules.builtin.professional.manifest import (
    MANIFEST as PROFESSIONAL_MANIFEST,
)
from cranioz.modules.core import ModuleManifest

BUILTIN_MANIFESTS: tuple[ModuleManifest, ...] = (PROFESSIONAL_MANIFEST,)
