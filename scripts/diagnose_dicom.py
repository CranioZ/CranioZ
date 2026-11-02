"""Diagnose a DICOM series: check ordering and geometry."""

from __future__ import annotations

from pathlib import Path

import pydicom


def main() -> int:
    folder = Path("C:/Users/JozeiasNote2026/Downloads/TC")
    files = sorted(folder.glob("*.dcm"))
    print(f"{len(files)} files")

    positions = []
    instances = []
    for i, f in enumerate(files):
        ds = pydicom.dcmread(str(f), stop_before_pixels=True)
        ipp = getattr(ds, "ImagePositionPatient", None)
        inst = getattr(ds, "InstanceNumber", None)
        positions.append(ipp)
        instances.append(inst)
        if i < 5 or i >= len(files) - 2:
            print(f"file {i}: ImagePositionPatient={ipp}, InstanceNumber={inst}")

    # Check if positions are monotonic and distinct.
    pos_z = []
    for p in positions:
        if p is None or len(p) < 3:
            pos_z = None
            break
        pos_z.append(float(p[2]))

    if pos_z is None:
        print("ImagePositionPatient is MISSING or incomplete on some slices.")
    else:
        print(f"pos_z: min={min(pos_z):.3f} max={max(pos_z):.3f}")
        print(f"pos_z distinct: {len(set(pos_z))} / {len(pos_z)}")
        diffs = [pos_z[i + 1] - pos_z[i] for i in range(len(pos_z) - 1)]
        if diffs:
            print(f"pos_z diffs: min={min(diffs):.6f} max={max(diffs):.6f}")
            non_zero = [d for d in diffs if abs(d) > 1e-6]
            if non_zero:
                print(f"non-zero diffs: {len(non_zero)} / {len(diffs)}")

    # Check InstanceNumber.
    valid_inst = [x for x in instances if x is not None]
    print(f"InstanceNumber present: {len(valid_inst)} / {len(instances)}")
    if valid_inst:
        print(f"InstanceNumber range: {min(valid_inst)} - {max(valid_inst)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
