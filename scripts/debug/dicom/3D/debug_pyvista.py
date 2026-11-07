import numpy as np
import pydicom
import pyvista as pv
from pathlib import Path
import logging

# Configuração de log simples
logging.basicConfig(level=logging.INFO)

DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def load_volume():
    files = sorted(p for p in DICOM_PATH.iterdir() if p.suffix.lower() == '.dcm')
    slices = [pydicom.dcmread(str(f)) for f in files]

    # Ordenar por posição (simplificado)
    iop = np.array(slices[0].ImageOrientationPatient)
    normal = np.cross(iop[:3], iop[3:])
    slices.sort(key=lambda s: np.dot(np.array(s.ImagePositionPatient), normal))

    # Empilhar
    volume_data = np.stack([s.pixel_array for s in slices], axis=0)

    # Rescale para HU (aproximado)
    slope = float(getattr(slices[0], 'RescaleSlope', 1.0))
    intercept = float(getattr(slices[0], 'RescaleIntercept', 0.0))
    volume_data = (volume_data.astype(np.float32) * slope + intercept).astype(np.int16)

    # Spacing
    spacing = (float(slices[0].PixelSpacing[0]), float(slices[0].PixelSpacing[1]), 1.0)  # Z=1.0 para simplificar
    return volume_data, spacing


def main():
    data, spacing = load_volume()
    logging.info(f"Volume shape: {data.shape}, range: {data.min()} to {data.max()}")

    # Converte para o formato do PyVista
    grid = pv.ImageData()
    # O PyVista espera (X, Y, Z), então transpomos
    grid.dimensions = np.array(data.transpose(2, 1, 0).shape)
    grid.spacing = spacing
    # Adiciona os dados (achatados)
    grid.point_data["values"] = data.transpose(2, 1, 0).flatten(order="F")

    # Renderização
    plotter = pv.Plotter()
    plotter.add_volume(grid, cmap="bone", opacity="sigmoid", shade=True)
    plotter.show()


if __name__ == "__main__":
    main()