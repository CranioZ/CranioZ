"""Presentation settings owned by the Professional Editor."""

from __future__ import annotations

from cranioz.infrastructure.settings.keys import (
    PROFESSIONAL_UI_COLLAPSED_SECTIONS,
    PROFESSIONAL_UI_LAST_SECTION,
    PROFESSIONAL_UI_NAVIGATION_ORDER,
    PROFESSIONAL_UI_VISIBLE_SECTIONS,
)
from cranioz.infrastructure.settings.protocol import SettingsService

DEFAULT_SECTION = "professional"


class ProfessionalEditorSettings:
    """Typed access to the ``professional.*`` presentation namespace."""

    def __init__(self, settings: SettingsService) -> None:
        self._settings = settings

    def last_section(self) -> str:
        value = self._settings.get(PROFESSIONAL_UI_LAST_SECTION, DEFAULT_SECTION)
        return value if isinstance(value, str) and value else DEFAULT_SECTION

    def set_last_section(self, section: str) -> None:
        if not section:
            raise ValueError("section must not be empty")
        self._settings.set(PROFESSIONAL_UI_LAST_SECTION, section)
        self._settings.save()

    def navigation_order(self) -> tuple[str, ...]:
        value: object = self._settings.get(PROFESSIONAL_UI_NAVIGATION_ORDER, [])
        return self._string_tuple(value)

    def set_navigation_order(self, section_ids: tuple[str, ...]) -> None:
        self._settings.set(PROFESSIONAL_UI_NAVIGATION_ORDER, list(section_ids))
        self._settings.save()

    def collapsed_sections(self) -> tuple[str, ...]:
        value: object = self._settings.get(PROFESSIONAL_UI_COLLAPSED_SECTIONS, [])
        return self._string_tuple(value)

    def set_collapsed_sections(self, section_ids: tuple[str, ...]) -> None:
        self._settings.set(PROFESSIONAL_UI_COLLAPSED_SECTIONS, list(section_ids))
        self._settings.save()

    def visible_sections(self) -> tuple[str, ...]:
        value: object = self._settings.get(PROFESSIONAL_UI_VISIBLE_SECTIONS, [])
        return self._string_tuple(value)

    def set_visible_sections(self, section_ids: tuple[str, ...]) -> None:
        self._settings.set(PROFESSIONAL_UI_VISIBLE_SECTIONS, list(section_ids))
        self._settings.save()

    @staticmethod
    def _string_tuple(value: object) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        return tuple(item for item in value if isinstance(item, str) and item)
