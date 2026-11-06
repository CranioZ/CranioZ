"""Debug script: load a DICOM series and display it in an isolated MPRView."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# >>> CORREÇÃO CRÍTICA <<<
# O PySide6 6.5+ usa Core Profile por padrão. O VTK 9 com
# QVTKRenderWindowInteractor ainda espera Compatibility Profile no
# Windows. Essa incompatibilidade produz tela branca silenciosa.
# Forçar Compatibility Profile ANTES de criar o QApplication faz o
# QVTKRenderWindowInteractor renderizar corretamente.
import vtk
vtk.vtkObject.GlobalWarningDisplayOff()

os.environ.setdefault("VTK_DEFAULT_OPENGL_WINDOW", "vtkWin32OpenGLRenderWindow")

from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat

QApplication_attr = None  # placeholder para evitar import circular

from PySide6.QtWidgets import QApplication

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(2, 1)  # OpenGL 2.1 = Compatibility Profile
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
QSurfaceFormat.setDefaultFormat(_fmt)

# A partir daqui, o QApplication pode ser criado.
from PySide6.QtWidgets import QMainWindow
from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)
from cranioz.ui.editors.mpr_viewer.view import MPRView

print(">>> PySide6 + VTK configurados para Compatibility Profile", flush=True)

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def main() -> int:
    print(">>> 1. Iniciando main()", flush=True)

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        print(f">>> ERRO: caminho inválido: {dicom_path}", flush=True)
        return 1

    print(">>> 2. Lendo DICOM...", flush=True)
    reader = DicomSeriesReader()
    try:
        volume, report = reader.read(dicom_path)
    except DicomSeriesReaderError as exc:
        print(f">>> ERRO ao ler DICOM: {exc}", flush=True)
        return 1

    print(f">>> 3. Volume carregado: dims={volume.dimensions}", flush=True)

    print(">>> 4. Criando QApplication (Compatibility Profile)...", flush=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    print(">>> 5. QApplication OK", flush=True)

    print(">>> 6. Criando MPRView...", flush=True)
    view = MPRView(view_id="view.axial", view_type="axial")
    print(">>> 7. MPRView OK", flush=True)

    print(">>> 8. Configurando QMainWindow...", flush=True)
    window = QMainWindow()
    window.setWindowTitle("CranioZ - MPR Debug (Axial)")
    window.setCentralWidget(view.content_widget())
    window.resize(800, 800)

    print(">>> 9. Exibindo janela...", flush=True)
    window.show()
    print(">>> 10. Janela exibida", flush=True)

    print(">>> 11. Anexando volume...", flush=True)
    view.set_volume(volume)
    print(f">>> 12. Volume anexado. has_volume={view.has_volume}, "
          f"slice={view.slice_index}/{view.max_slice}", flush=True)

    print(">>> 13. Entrando em app.exec()...", flush=True)
    exit_code = app.exec()
    print(f">>> 14. app.exec() retornou {exit_code}", flush=True)
    return exit_code


if __name__ == "__main__":
    code = main()
    # NÃO chame sys.exit(code): o PyCharm pode interpretar como erro de teste.
    # Deixe o processo terminar naturalmente.