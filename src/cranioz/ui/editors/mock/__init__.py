"""Mock Editors for layout debugging.

These are minimal, non-production Editors used to isolate layout
issues (Block 5.5) from Editor-specific issues (especially the
TomographyEditor). They render a colored rectangle with a label,
so the developer can see at a glance whether:

- Each Area has the expected percentage width/height.
- The Area backgrounds are distinct (central lighter, laterals medium).
- The Top Bar fits inside the Central Area.
- The grid (if any) expands to fill the Central Area.

They are intentionally simple: no VTK, no real data, no state.
"""

from cranioz.ui.editors.mock.console import MockConsoleEditor
from cranioz.ui.editors.mock.mpr import MockMPREditor
from cranioz.ui.editors.mock.objetos import MockObjetosEditor
from cranioz.ui.editors.mock.posicao import MockPosicaoEditor

__all__ = [
    "MockConsoleEditor",
    "MockMPREditor",
    "MockObjetosEditor",
    "MockPosicaoEditor",
]