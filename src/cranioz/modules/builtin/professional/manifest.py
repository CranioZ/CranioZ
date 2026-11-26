"""Manifest for the built-in Professional Module."""

from __future__ import annotations

from cranioz.modules.core import ModuleManifest

MANIFEST = ModuleManifest(
    module_id="professional",
    version="1.0.0",
    label_key="professional.tabs.professional",
    description_key="professional.profile.subtitle",
    entry_point="cranioz.modules.builtin.professional.module:ProfessionalModule",
)
