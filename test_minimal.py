import sys

print(">>> Script iniciado", flush=True)
print(f">>> Python: {sys.version}", flush=True)
print(">>> Caminho:", __file__, flush=True)

from PySide6.QtWidgets import QApplication
print(">>> PySide6 importado OK", flush=True)

app = QApplication.instance() or QApplication([])
print(">>> QApplication criada OK", flush=True)

from cranioz.ui.editors.mpr_viewer.view import MPRView
print(">>> MPRView importado OK", flush=True)

print(">>> Script finalizado", flush=True)
sys.exit(0)