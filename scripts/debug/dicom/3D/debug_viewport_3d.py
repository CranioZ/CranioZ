from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pydicom
import vtk
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty,
)
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
_logger = logging.getLogger("CranioZ.Debug.3D.FinalCorrect")

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def load_dicom_manually(dicom_path: Path) -> tuple[np.ndarray, tuple]:
    """Lê DICOMs diretamente, ordena e empilha."""
    _logger.info("=== LEITURA MANUAL DOS DICOMS ===")

    files = sorted(p for p in dicom_path.iterdir() if p.is_file() and p.suffix.lower() == '.dcm')
    if not files:
        raise RuntimeError(f"Nenhum arquivo .dcm encontrado em {dicom_path}")

    _logger.info(f"Encontrados {len(files)} arquivos")

    slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(str(f))
            if hasattr(ds, 'PixelData'):
                slices.append(ds)
        except Exception:
            pass

    _logger.info(f"Carregados {len(slices)} slices válidos")

    # Ordenar
    if hasattr(slices[0], 'ImageOrientationPatient'):
        iop = np.array(slices[0].ImageOrientationPatient, dtype=np.float64)
        normal = np.cross(iop[:3], iop[3:])

        def get_slice_pos(ds):
            ipp = np.array(ds.ImagePositionPatient, dtype=np.float64)
            return np.dot(ipp, normal)

        slices.sort(key=get_slice_pos)
    else:
        slices.sort(key=lambda s: int(getattr(s, 'InstanceNumber', 0)))

    rows = slices[0].Rows
    cols = slices[0].Columns
    pixel_data = np.stack([s.pixel_array for s in slices], axis=0)

    slope = float(getattr(slices[0], 'RescaleSlope', 1.0))
    intercept = float(getattr(slices[0], 'RescaleIntercept', 0.0))
    _logger.info(f"Rescale: slope={slope}, intercept={intercept}")

    # Aplicar rescale para HU
    pixel_data = (pixel_data.astype(np.float32) * slope + intercept).astype(np.int16)
    _logger.info(f"Volume em HU: range=({pixel_data.min()}, {pixel_data.max()})")

    if hasattr(slices[0], 'PixelSpacing'):
        spacing_xy = tuple(float(x) for x in slices[0].PixelSpacing)
    else:
        spacing_xy = (1.0, 1.0)

    if len(slices) > 1:
        pos_first = np.array(slices[0].ImagePositionPatient, dtype=np.float64)
        pos_second = np.array(slices[1].ImagePositionPatient, dtype=np.float64)
        spacing_z = float(np.linalg.norm(pos_second - pos_first))
    else:
        spacing_z = float(getattr(slices[0], 'SliceThickness', 1.0))

    spacing = (spacing_xy[1], spacing_xy[0], spacing_z)
    _logger.info(f"Spacing: {spacing}")

    return pixel_data, spacing



def create_vtk_image_uint8(
    pixel_data: np.ndarray,
    spacing: tuple[float, float, float],
) -> tuple[vtkImageData, int, int]:
    """Cria vtkImageData com a ordem de voxels compatível com o VTK."""
    data = np.ascontiguousarray(pixel_data, dtype=np.int16)

    raw_min = int(data.min())
    raw_max = int(data.max())

    # Normalização para uint8 (isolamento temporário do bug de ordem)
    if raw_max > raw_min:
        normalized = (
            (data.astype(np.float32) - raw_min)
            / (raw_max - raw_min)
            * 255.0
        )
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)
    else:
        normalized = np.zeros(data.shape, dtype=np.uint8)

    nz, ny, nx = normalized.shape

    # C-order preserva X como dimensão mais rápida, compatível com o VTK.
    flat_data = normalized.ravel(order="C")

    vtk_array = numpy_to_vtk(
        flat_data,
        deep=True,
        array_type=vtk.VTK_UNSIGNED_CHAR,
    )

    image = vtkImageData()
    image.SetDimensions(nx, ny, nz)
    image.SetSpacing(*spacing)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.GetPointData().SetScalars(vtk_array)

    _logger.info(
        f"vtkImageData: dims={image.GetDimensions()}, "
        f"spacing={image.GetSpacing()}, "
        f"range={vtk_array.GetRange()}"
    )

    return image, raw_min, raw_max



class FinalCorrectWindow(QMainWindow):
    def __init__(self, vtk_image: vtkImageData, raw_min: int, raw_max: int):
        super().__init__()
        self.vtk_image = vtk_image
        self.raw_min = raw_min
        self.raw_max = raw_max

        self.setWindowTitle("CranioZ - Debug 3D (Correção Definitiva)")
        self.resize(1200, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.interactor = QVTKRenderWindowInteractor()
        layout.addWidget(self.interactor, stretch=1)

        self.renderer = vtkRenderer()
        self.renderer.SetBackground(0.1, 0.1, 0.15)
        self.interactor.GetRenderWindow().AddRenderer(self.renderer)

        # Sliders (0-255)
        controls_layout = QHBoxLayout()
        self.slider_min = QSlider(Qt.Orientation.Horizontal)
        self.slider_min.setRange(0, 255)
        self.slider_min.setValue(50)
        self.label_min = QLabel(f"Min: {self.slider_min.value()}")

        self.slider_max = QSlider(Qt.Orientation.Horizontal)
        self.slider_max.setRange(0, 255)
        self.slider_max.setValue(200)
        self.label_max = QLabel(f"Max: {self.slider_max.value()}")

        controls_layout.addWidget(self.label_min)
        controls_layout.addWidget(self.slider_min)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.label_max)
        controls_layout.addWidget(self.slider_max)
        layout.addLayout(controls_layout)
        self.setCentralWidget(central)

        # --- Mapper (GPU, agora sem erro de textura) ---
        self.mapper = vtkSmartVolumeMapper()
        self.mapper.SetInputData(self.vtk_image)
        self.mapper.SetBlendModeToComposite()

        # --- Propriedades ---
        self.volume_property = vtkVolumeProperty()
        self.volume_property.SetInterpolationTypeToLinear()
        self.volume_property.SetScalarOpacityUnitDistance(1.0)
        self.volume_property.ShadeOn()
        self.volume_property.SetAmbient(0.2)
        self.volume_property.SetDiffuse(0.8)
        self.volume_property.SetSpecular(0.1)
        self.volume_property.SetSpecularPower(10.0)

        self.color = vtkColorTransferFunction()
        self.opacity = vtkPiecewiseFunction()
        self.volume_property.SetColor(self.color)
        self.volume_property.SetScalarOpacity(self.opacity)

        self.volume_actor = vtkVolume()
        self.volume_actor.SetMapper(self.mapper)
        self.volume_actor.SetProperty(self.volume_property)
        self.renderer.AddVolume(self.volume_actor)

        # Conexões
        self.slider_min.valueChanged.connect(self.update_transfer_function)
        self.slider_max.valueChanged.connect(self.update_transfer_function)

        self.update_transfer_function()

        # Câmera
        self.renderer.ResetCamera()
        camera = self.renderer.GetActiveCamera()
        camera.Elevation(25)
        camera.Azimuth(45)
        self.renderer.ResetCameraClippingRange()

    def update_transfer_function(self):
        vmin = self.slider_min.value()
        vmax = self.slider_max.value()

        if vmax <= vmin:
            vmax = vmin + 1
            self.slider_max.setValue(vmax)

        self.label_min.setText(f"Min: {vmin}")
        self.label_max.setText(f"Max: {vmax}")

        self.color.RemoveAllPoints()
        self.opacity.RemoveAllPoints()

        # A cor: preto no ar, marrom no tecido mole, branco no osso
        self.color.AddRGBPoint(vmin, 0.0, 0.0, 0.0)
        self.color.AddRGBPoint(vmin + (vmax - vmin) * 0.6, 0.8, 0.5, 0.4)
        self.color.AddRGBPoint(vmax, 1.0, 1.0, 1.0)

        # A opacidade: 0 no min, 0.05 no meio, 0.8 no max
        self.opacity.AddPoint(vmin, 0.0)
        self.opacity.AddPoint(vmin + (vmax - vmin) * 0.6, 0.05)
        self.opacity.AddPoint(vmax, 0.8)

        self.interactor.GetRenderWindow().Render()


def main() -> int:
    _logger.info("=== INÍCIO: Script de debug 3D (Correção Definitiva) ===")

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        _logger.error(f"Diretório inválido: {dicom_path}")
        return 1

    try:
        pixel_data, spacing = load_dicom_manually(dicom_path)
    except Exception as e:
        _logger.error(f"Erro na leitura manual: {e}")
        import traceback
        traceback.print_exc()
        return 1

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    vtk_image, raw_min, raw_max = create_vtk_image_uint8(pixel_data, spacing)

    window = FinalCorrectWindow(vtk_image, raw_min, raw_max)
    window.show()

    window.interactor.Initialize()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())