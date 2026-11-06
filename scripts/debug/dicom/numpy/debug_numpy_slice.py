"""Debug: prova que a fatia 32 do Volume contém anatomia, sem VTK.

Se o Matplotlib mostrar o crânio, o dado está íntegro e o bug
está no pipeline VTK (vtkImageReslice / câmera).
"""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from cranioz.infrastructure.imaging.dicom.dicom_series_reader import DicomSeriesReader

_DEFAULT = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")
_SLICE_INDEX = 32

def main():
    reader = DicomSeriesReader()
    volume, report = reader.read(_DEFAULT)
    print(f"Volume: dims={volume.dimensions}, spacing={volume.spacing}")

    # O Volume.data é (nz, ny, nx). Fatia axial = data[k, :, :].
    slice_2d = volume.data[_SLICE_INDEX, :, :]
    print(f"Slice {_SLICE_INDEX} shape: {slice_2d.shape}")
    print(f"Slice range: ({slice_2d.min()}, {slice_2d.max()})")

    plt.figure(figsize=(8, 8))
    plt.imshow(
        slice_2d,
        cmap="gray",
        origin="lower",
        vmin=np.percentile(slice_2d, 1),
        vmax=np.percentile(slice_2d, 99),
    )
    plt.title(f"Axial slice {_SLICE_INDEX} — NumPy puro")
    plt.colorbar()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()