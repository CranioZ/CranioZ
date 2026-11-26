"""Declarative contributions of the Professional Module."""

from __future__ import annotations

from cranioz.application.professional import UpdateProfessionalProfileCommand
from cranioz.modules.builtin import BUILTIN_MANIFESTS
from cranioz.modules.builtin.professional import (
    MANIFEST,
    ProfessionalModule,
)
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.professional import PROFESSIONAL_UI_SPEC


def test_professional_manifest_is_registered_as_builtin() -> None:
    assert MANIFEST in BUILTIN_MANIFESTS
    assert MANIFEST.entry_point == (
        "cranioz.modules.builtin.professional.module:ProfessionalModule"
    )


def test_professional_module_contributes_service_and_command() -> None:
    module = ProfessionalModule()

    assert UpdateProfessionalProfileCommand in module.commands()


def test_professional_ui_spec_hosts_editor_in_central_area() -> None:
    assert len(PROFESSIONAL_UI_SPEC.areas) == 1
    area = PROFESSIONAL_UI_SPEC.areas[0]

    assert area.placement is Placement.CENTRAL
    assert area.editor_layout.editor_id == "editor.professional"
