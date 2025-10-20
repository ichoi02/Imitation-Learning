""" c3d2trc.py: Read raw c3d data to create trc files """

import argparse
import os
from pathlib import Path
import opensim as osim

BASE = Path(__file__).resolve().parent
C3D_DIR = BASE / "c3d"
XML_DIR = BASE / "xml"
TRC_DIR = BASE / "trc"

def remap_coordinates(table_vec3):
    """Remap coordinates from (X, Y, Z) to (-X, Z, Y)"""
    n_rows = table_vec3.getNumRows()
    n_cols = table_vec3.getNumColumns()
    for r in range(n_rows):
        row = table_vec3.updRowAtIndex(r)
        for c in range(n_cols):
            v = row[c]
            row[c] = osim.Vec3(-v.get(0), v.get(2), v.get(1))

def get_subject_id(idx):
    # open the mmm.xml file
    filepath = os.path.join(XML_DIR, f'{idx:05d}_mmm.xml')

    # parse id
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    line = lines[2]
    subject_id = line.split("'")[1].split('_')[-1]
    return int(subject_id)

def write_trc(idx: int):
    c3d_path = C3D_DIR / f"{idx:05d}_raw.c3d"

    adapter = osim.C3DFileAdapter()
    tables = adapter.read(str(c3d_path))

    markers_tbl = adapter.getMarkersTable(tables)

    remap_coordinates(markers_tbl)

    subject_id = get_subject_id(idx)
    TRC_DIR.mkdir(parents=True, exist_ok=True)
    trc_path = TRC_DIR / f"{idx:05d}_{subject_id:05d}.trc"
    osim.TRCFileAdapter().write(markers_tbl, str(trc_path))
    print(f"Wrote {trc_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int, default=1)
    parser.add_argument("end", type=int)
    args = parser.parse_args()

    for i in range(args.start, args.end + 1):
        try:
            write_trc(i)
        except Exception as e:
            print(f"Skipping motion index: {i}")
            continue
