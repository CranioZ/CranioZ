"""AreaWidget."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_layout_renderer import AreaLayoutRenderer
from cranioz.ui.workspace.areas.editor_stack import EditorStack
from cranioz.ui.workspace.areas.placement import Placement

_logger = logging.getLogger(__name__)


class AreaWidget(QWidget):
    """Qt widget that materializes a single Area."""

    active_editor_changed = Signal(str, str)
    editor_close_requested = Signal(str, str)
    editor_add_requested = Signal(str)

    def __init__(
        self,
        area: Area,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        *,
        icon_provider: IconProvider,
        debug_colors: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # Sprint H: Repassar o IconProvider para o renderer
        self._icon_provider = icon_provider
        self._area = area
        self._debug_colors = debug_colors
        self._content_widgets: dict[str, QWidget] = {}

        self._area_layout_renderer = AreaLayoutRenderer(icon_provider=icon_provider)

        self.setObjectName(f"area_widget.{area.area_id}")

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setProperty("area_placement", self._area.placement.value)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.style().unpolish(self)
        self.style().polish(self)

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        if debug_colors:
            self._apply_debug_background()

        self.refresh()

    # ----- Public API -----------------------------------------------

    @property
    def area_id(self) -> str:
        return self._area.area_id

    def area_placement(self) -> Placement:
        return self._area.placement

    def area(self) -> Area:
        return self._area

    def refresh(self) -> None:
        print(f"\n[DEBUG AreaWidget] refresh({self._area.area_id})")
        print(f"[DEBUG AreaWidget] Editores na Area: {len(self._area.editors())}")
        print(f"[DEBUG AreaWidget] Layout Spec: {self._area.editor_layout_spec}")

        if not self._area.visible:
            print("[DEBUG AreaWidget] Área invisível, abortando refresh.")
            return

        # O ERRO ESTAVA AQUI! Não podemos chamar dispose nos editores
        # que vamos usar logo em seguida no renderer!
        # for editor in self._area.editors():
        #     try:
        #         editor.dispose()
        #     except Exception:
        #         _logger.exception("Editor.dispose() failed for %r", editor.editor_id)

        self._clear_layout()

        if self._area.is_empty():
            print("[DEBUG AreaWidget] Área vazia -> renderizando placeholder.")
            self._root_layout.addWidget(self._build_empty_placeholder())
            self.style().unpolish(self)
            self.style().polish(self)
            return

        if self._debug_colors:
            debug_label = QLabel(f"[{self._area.area_id}]")
            debug_label.setStyleSheet(
                "QLabel { background: rgba(255,255,255,200); font-weight: bold; padding: 2px; }"
            )
            self._root_layout.addWidget(debug_label)

        # Chama o renderer (que deve ler o editor_layout_spec)
        print("[DEBUG AreaWidget] Chamando AreaLayoutRenderer.render()")
        content = self._area_layout_renderer.render(self._area, self._content_widgets)

        print(f"[DEBUG AreaWidget] Renderer retornou: {type(content)}")
        self._root_layout.addWidget(content)

        QTimer.singleShot(0, self._force_vtk_render)
        QTimer.singleShot(100, self._force_vtk_render)

        self.style().unpolish(self)
        self.style().polish(self)

    # ----- Internals ------------------------------------------------

    def _force_vtk_render(self) -> None:
        found = 0
        for child in self.findChildren(QWidget):
            render_window = getattr(child, "GetRenderWindow", None)
            if render_window is None:
                continue
            found += 1
            try:
                rw = render_window()
                if rw is not None:
                    rw.Render()
            except Exception:
                _logger.exception("VTK first-frame render failed for %r", child)

    def _apply_debug_background(self) -> None:
        palette = {
            Placement.LEFT: "#dbe9f4",
            Placement.CENTRAL: "#dff0d8",
            Placement.RIGHT: "#fcf3cf",
            Placement.BOTTOM: "#e8daef",
        }
        color = palette.get(self._area.placement)
        if color is None:
            return
        qcolor = QColor(color)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, qcolor)
        self.setPalette(pal)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"QWidget#{self.objectName()} {{ background-color: {color}; }}")

    def _clear_layout(self) -> None:
        # Sprint H: Se houver um EditorStack, descarte-o primeiro.
        stack = self._content_widgets.pop("__editor_stack__", None)
        if isinstance(stack, EditorStack):
            try:
                stack.dispose()
            except Exception:
                _logger.exception("EditorStack.dispose() failed in AreaWidget")

        for editor in self._area.editors():
            content = self._content_widgets.pop(editor.editor_id, None)
            if content is None:
                continue
            try:
                content.setParent(None)
            except RuntimeError:
                _logger.exception(
                    "content_widget for %r was already deleted; skipping detach",
                    editor.editor_id,
                )

        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _build_empty_placeholder(self) -> QWidget:
        label = QLabel(f"{self._area.title} (empty)")
        label.setObjectName(f"area_widget.{self._area.area_id}.placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        return label
