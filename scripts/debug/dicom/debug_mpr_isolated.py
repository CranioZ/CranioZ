"""Teste isolado: instanciar o MPRView e chamar content_widget()."""
import sys

print(">>> 1. Script iniciado", flush=True)

from PySide6.QtWidgets import QApplication
print(">>> 2. PySide6 OK", flush=True)

from cranioz.ui.editors.mpr_viewer.view import MPRView
print(">>> 3. MPRView importado", flush=True)

print(">>> 4. Criando QApplication...", flush=True)
app = QApplication.instance() or QApplication([])
print(">>> 5. QApplication criada", flush=True)

print(">>> 6. Instanciando MPRView...", flush=True)
view = MPRView(view_id="view.test", view_type="axial")
print(">>> 7. MPRView instanciada", flush=True)

print(">>> 8. Chamando content_widget()...", flush=True)
widget = view.content_widget()
print(f">>> 9. content_widget OK: {type(widget).__name__}", flush=True)

print(">>> 10. Chamando dispose()...", flush=True)
view.dispose()
print(">>> 11. dispose OK", flush=True)

print(">>> 12. Tudo concluído", flush=True)