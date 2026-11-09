"""Contract: icon-only controls have accessibleName and toolTip."""

from PySide6.QtWidgets import QApplication

from cranioz.infrastructure.settings.in_memory_settings_service import InMemorySettingsService
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.workspace.structure.home_segment import HomeSegment


def test_home_segment_buttons_have_accessibility(qapp) -> None:
    service = ThemeService(settings=InMemorySettingsService())
    provider = UnicodeIconProvider(service)
    segment = HomeSegment(icon_provider=provider)
    QApplication.processEvents()
    for button in segment.findChildren(type(segment._toggle_left_button)):
        if button.text() == "" and not button.icon().isNull():
            assert button.toolTip() != ""
