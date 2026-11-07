from __future__ import annotations

import logging
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pydicom
import vtk
from PySide6.QtCore import QTimer, Qt
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
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty,
    vtkWindowToImageFilter,
)
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
_logger = logging.getLogger("CranioZ.Compare.Int16")

_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")
_SCREENSHOT = Path(r"C:\CranioZ\debug_int16_render.png")


def _gpu_memory_mb() -> str:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL, timeout=2,
        ).decode().strip()
        return f"{out} MB"
    except Exception:
        return "N/A"


def load_volume() -> tuple[np.ndarray, tuple]:
    files = sorted(p for p in _DICOM_PATH.iterdir() if p.suffix.lower() == '.dcm')
    slices = [pydicom.dcmread(str(f)) for f in files]

    iop = np.array(slices[0].ImageOrientationPatient)
    normal = np.cross(iop[:3], iop[3:])
    slices.sort(key=lambda s: np.dot(np.array(s.ImagePositionPatient), normal))

    data = np.stack([s.pixel_array for s in slices], axis=0)
    slope = float(getattr(slices[0], 'RescaleSlope', 1.0))
    intercept = float(getattr(slices[0], 'RescaleIntercept', 0.0))
    data = (data.astype(np.float32) * slope + intercept).astype(np.int16)

    spacing_xy = (float(slices[0].PixelSpacing[0]), float(slices[0].PixelSpacing[1]))
    pos_first = np.array(slices[0].ImagePositionPatient, dtype=np.float64)
    pos_second = np.array(slices[1].ImagePositionPatient, dtype=np.float64)
    spacing_z = float(np.linalg.norm(pos_second - pos_first))

    spacing = (spacing_xy[1], spacing_xy[0], spacing_z)
    return data, spacing


def build_int16_image(data: np.ndarray, spacing: tuple) -> tuple[vtkImageData, dict]:
    tracemalloc.start()
    t0 = time.perf_counter()

    data = np.ascontiguousarray(data, dtype=np.int16)
    nz, ny, nx = data.shape
    flat = data.ravel(order="C")  # NÃO transpor
    vtk_array = numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_SHORT)

    image = vtkImageData()
    image.SetDimensions(nx, ny, nz)
    image.SetSpacing(*spacing)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.GetPointData().SetScalars(vtk_array)

    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics = {
        "mode": "int16",
        "elapsed_ms": elapsed * 1000,
        "peak_ram_mb": peak / 1e6,
        "input_bytes": data.nbytes,
        "output_bytes": vtk_array.GetNumberOfTuples() * vtk_array.GetDataTypeSize(),
        "scalar_range": vtk_array.GetRange(),
    }
    _logger.info(f"[INT16] conversão: {elapsed*1000:.1f} ms, RAM pico: {peak/1e6:.1f} MB")
    _logger.info(f"[INT16] input: {data.nbytes/1e6:.1f} MB, output: {metrics['output_bytes']/1e6:.1f} MB")
    _logger.info(f"[INT16] scalar range: {metrics['scalar_range']}")
    return image, metrics


class Int16Window(QMainWindow):
    def __init__(self, vtk_image: vtkImageData, raw_min: int, raw_max: int):
        super().__init__()
        self.vtk_image = vtk_image
        self.raw_min = raw_min
        self.raw_max = raw_max

        self.setWindowTitle("CranioZ - Comparação int16")
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
        self.slider_max.setValue(4000)
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

        self.slider_min.valueChanged.connect(self.update_tf)
        self.slider_max.valueChanged.connect(self.update_tf)
        self.update_tf()

        self.renderer.ResetCamera()
        camera = self.renderer.GetActiveCamera()
        camera.Elevation(25)
        camera.Azimuth(45)
        self.renderer.ResetCameraClippingRange()

        # --- Benchmark ---
        self._frame_times: list[float] = []
        self._bench_start: float = 0.0
        self._bench_timer = QTimer(self)
        self._bench_timer.timeout.connect(self._bench_tick)

    def start_benchmark(self):
        _logger.info(f"[INT16] GPU VRAM antes do benchmark: {_gpu_memory_mb()}")
        self._frame_times.clear()
        self._bench_start = time.perf_counter()
        self._bench_timer.start(0)

    def _bench_tick(self):
        if (time.perf_counter() - self._bench_start) >= 2.0:
            self._bench_timer.stop()
            self._finish_benchmark()
            return

        t0 = time.perf_counter()
        self.renderer.GetActiveCamera().Azimuth(6)
        self.interactor.GetRenderWindow().Render()
        dt = time.perf_counter() - t0
        self._frame_times.append(dt)

    def _finish_benchmark(self):
        times = self._frame_times
        if not times:
            _logger.warning("[INT16] Nenhum frame capturado.")
            return
        avg = sum(times) / len(times)
        p95 = sorted(times)[min(int(len(times) * 0.95), len(times) - 1)]
        fps = 1.0 / avg if avg > 0 else 0
        _logger.info(f"[INT16] Total de frames: {len(times)}")
        _logger.info(f"[INT16] FPS médio: {fps:.1f}")
        _logger.info(f"[INT16] Frame avg: {avg*1000:.1f} ms, p95: {p95*1000:.1f} ms")
        _logger.info(f"[INT16] GPU VRAM após benchmark: {_gpu_memory_mb()}")

        w2i = vtkWindowToImageFilter()
        w2i.SetInput(self.interactor.GetRenderWindow())
        w2i.Update()
        writer = vtkPNGWriter()
        writer.SetFileName(str(_SCREENSHOT))
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()
        _logger.info(f"[INT16] screenshot: {_SCREENSHOT}")

    def update_tf(self):
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
    _logger.info("=== Benchmark: int16 ===")
    data, spacing = load_volume()
    vtk_image, metrics = build_int16_image(data, spacing)

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    raw_min, raw_max = int(data.min()), int(data.max())
    window = Int16Window(vtk_image, raw_min, raw_max)
    window.show()
    window.interactor.Initialize()

    QTimer.singleShot(100, window.start_benchmark)
    QTimer.singleShot(4000, window.close)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())