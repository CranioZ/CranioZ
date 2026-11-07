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
_logger = logging.getLogger("CranioZ.Debug.3D.ManualDicom")

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def load_dicom_manually(dicom_path: Path) -> tuple[np.ndarray, tuple, tuple]:
    """
    Lê os arquivos DICOM diretamente com pydicom, ordena pelo
    ImagePositionPatient (projeção no eixo Z) e empilha os pixels.
    """
    _logger.info("=== LEITURA MANUAL DOS DICOMS ===")

    # 1. Listar arquivos
    files = sorted(p for p in dicom_path.iterdir() if p.is_file() and p.suffix.lower() == '.dcm')
    if not files:
        raise RuntimeError(f"Nenhum arquivo .dcm encontrado em {dicom_path}")

    _logger.info(f"Encontrados {len(files)} arquivos .dcm")

    # 2. Carregar todos os slices
    slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(str(f))
            if hasattr(ds, 'PixelData'):
                slices.append(ds)
        except Exception as e:
            _logger.warning(f"Ignorando {f.name}: {e}")

    _logger.info(f"Carregados {len(slices)} slices válidos")

    # 3. Ordenar pelo ImagePositionPatient (Z)
    # Vamos usar o primeiro vetor da ImageOrientationPatient para projetar a posição
    if not hasattr(slices[0], 'ImageOrientationPatient'):
        _logger.warning("Sem ImageOrientationPatient, usando InstanceNumber")
        slices.sort(key=lambda s: int(getattr(s, 'InstanceNumber', 0)))
    else:
        # Direção normal ao plano do slice
        iop = np.array(slices[0].ImageOrientationPatient, dtype=np.float64)
        normal = np.cross(iop[:3], iop[3:])

        def get_slice_pos(ds):
            ipp = np.array(ds.ImagePositionPatient, dtype=np.float64)
            return np.dot(ipp, normal)

        slices.sort(key=get_slice_pos)
        _logger.info(f"Ordenado por ImagePositionPatient. Projeções Z: "
                     f"min={get_slice_pos(slices[0]):.2f}, "
                     f"max={get_slice_pos(slices[-1]):.2f}")

    # 4. Verificar dimensões consistentes
    rows = slices[0].Rows
    cols = slices[0].Columns
    _logger.info(f"Dimensões por slice: {rows}x{cols}")

    for s in slices:
        if s.Rows != rows or s.Columns != cols:
            raise RuntimeError(f"Slice com dimensões inconsistentes: {s.Rows}x{s.Columns} vs {rows}x{cols}")

    # 5. Empilhar pixels (nz, ny, nx)
    pixel_data = np.stack([s.pixel_array for s in slices], axis=0)
    _logger.info(f"Volume montado: shape={pixel_data.shape}, dtype={pixel_data.dtype}")
    _logger.info(f"Range: min={pixel_data.min()}, max={pixel_data.max()}")

    # 6. Aplicar o rescale (slope + intercept) para ter os valores reais
    slope = float(getattr(slices[0], 'RescaleSlope', 1.0))
    intercept = float(getattr(slices[0], 'RescaleIntercept', 0.0))
    _logger.info(f"Rescale: slope={slope}, intercept={intercept}")

    if slope != 1.0 or intercept != 0.0:
        pixel_data = pixel_data.astype(np.float32) * slope + intercept
        pixel_data = pixel_data.astype(np.int16)
        _logger.info(f"Após rescale: min={pixel_data.min()}, max={pixel_data.max()}")

    # 7. Calcular o spacing real
    if hasattr(slices[0], 'PixelSpacing'):
        spacing_xy = tuple(float(x) for x in slices[0].PixelSpacing)
    else:
        spacing_xy = (1.0, 1.0)

    # Spacing em Z: distância entre as fatias (não o SliceThickness!)
    if len(slices) > 1:
        pos_first = np.array(slices[0].ImagePositionPatient, dtype=np.float64)
        pos_second = np.array(slices[1].ImagePositionPatient, dtype=np.float64)
        spacing_z = float(np.linalg.norm(pos_second - pos_first))
    else:
        spacing_z = float(getattr(slices[0], 'SliceThickness', 1.0))

    spacing = (spacing_xy[1], spacing_xy[0], spacing_z)  # (x, y, z)
    _logger.info(f"Spacing real: {spacing}")

    return pixel_data, spacing, (rows, cols)


def create_vtk_image(pixel_data: np.ndarray, spacing: tuple) -> vtkImageData:
    """Cria vtkImageData a partir do array empilhado manualmente."""
    # Transpor (nz, ny, nx) -> (nx, ny, nz)
    data_transposed = np.ascontiguousarray(pixel_data.transpose(2, 1, 0))
    data_vtk = data_transposed.astype(np.int16)

    nx, ny, nz = data_vtk.shape
    flat_data = data_vtk.ravel(order="C")
    vtk_array = numpy_to_vtk(flat_data, deep=1)

    image = vtkImageData()
    image.SetDimensions(nx, ny, nz)
    image.SetSpacing(spacing[0], spacing[1], spacing[2])
    image.SetOrigin(0, 0, 0)
    image.GetPointData().SetScalars(vtk_array)

    return image


class ManualDicomWindow(QMainWindow):
    def __init__(self, vtk_image: vtkImageData, raw_min: int, raw_max: int):
        super().__init__()
        self.vtk_image = vtk_image
        self.raw_min = raw_min
        self.raw_max = raw_max

        self.setWindowTitle("CranioZ - Leitura Manual de DICOM (Sem Sorter)")
        self.resize(1200, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.interactor = QVTKRenderWindowInteractor()
        layout.addWidget(self.interactor, stretch=1)

        self.renderer = vtkRenderer()
        self.renderer.SetBackground(0.1, 0.1, 0.15)
        self.interactor.GetRenderWindow().AddRenderer(self.renderer)

        controls_layout = QHBoxLayout()
        self.slider_min = QSlider(Qt.Orientation.Horizontal)
        self.slider_min.setRange(raw_min, raw_max)
        self.slider_min.setValue(-500)
        self.label_min = QLabel(f"Min: {self.slider_min.value()}")

        self.slider_max = QSlider(Qt.Orientation.Horizontal)
        self.slider_max.setRange(raw_min, raw_max)
        self.slider_max.setValue(3000)
        self.label_max = QLabel(f"Max: {self.slider_max.value()}")

        controls_layout.addWidget(self.label_min)
        controls_layout.addWidget(self.slider_min)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.label_max)
        controls_layout.addWidget(self.slider_max)
        layout.addLayout(controls_layout)
        self.setCentralWidget(central)

        self.mapper = vtkSmartVolumeMapper()
        self.mapper.SetInputData(self.vtk_image)
        self.mapper.SetBlendModeToComposite()

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

        self.slider_min.valueChanged.connect(self.update_transfer_function)
        self.slider_max.valueChanged.connect(self.update_transfer_function)

        self.update_transfer_function()

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

        self.color.AddRGBPoint(vmin, 0.0, 0.0, 0.0)
        self.color.AddRGBPoint(vmin + (vmax - vmin) * 0.6, 0.8, 0.5, 0.4)
        self.color.AddRGBPoint(vmax, 1.0, 1.0, 1.0)

        self.opacity.AddPoint(vmin, 0.0)
        self.opacity.AddPoint(vmin + (vmax - vmin) * 0.6, 0.05)
        self.opacity.AddPoint(vmax, 0.8)

        self.interactor.GetRenderWindow().Render()


def main() -> int:
    _logger.info("=== INÍCIO: Teste de Leitura Manual de DICOM ===")

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        _logger.error(f"Diretório inválido: {dicom_path}")
        return 1

    try:
        pixel_data, spacing, dims = load_dicom_manually(dicom_path)
    except Exception as e:
        _logger.error(f"Erro na leitura manual: {e}")
        import traceback
        traceback.print_exc()
        return 1

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    vtk_image = create_vtk_image(pixel_data, spacing)
    raw_min = int(pixel_data.min())
    raw_max = int(pixel_data.max())

    window = ManualDicomWindow(vtk_image, raw_min, raw_max)
    window.show()

    window.interactor.Initialize()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())