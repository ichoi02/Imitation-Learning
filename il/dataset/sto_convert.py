""" 
sto_convert.py: Converts SCONE .sto file to OpenSim .sto file
Use this to view SCONE result and compare with reference motion
"""

from scipy.spatial.transform import Rotation
from il.dataset.dataloader import Data
from pathlib import Path
import argparse
import pandas as pd
import numpy as np

def read_sto(sto_path):
    text_header = []
    with open(sto_path, "r") as f:
        for i, line in enumerate(f):
            text_header.append(line.strip())
            if "endheader" in line.lower():
                skiprows = i + 1
                break
                
    data = pd.read_csv(sto_path, sep='\t', skiprows=skiprows)
    column_names = data.columns.tolist()
    data = data.values
    return column_names, data

def write_sto(sto_path, column_names, data):
    df = pd.DataFrame(data, columns=column_names)
    with open(sto_path, 'w') as f:
        f.write(f"{Path(sto_path).stem}\n")
        f.write("version=1\n")
        f.write(f"nRows={df.shape[0]}\n")
        f.write(f"nColumns={df.shape[1]}\n")
        f.write("inDegrees=no\n")
        f.write("endheader\n")
        df.to_csv(f, sep='\t', index=False, header=True, lineterminator='\n')

def convert_rotation_inv(input):
    r = Rotation.from_euler('YXZ', input, degrees=False)
    out = r.as_euler('ZXY', degrees=False)
    return out[:, [2, 1, 0]]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("output_file", type=str)
    args = parser.parse_args()

    column_names, data = read_sto(args.input_file)
    
    tlr_indices = [column_names.index(col) for col in ["pelvis_tilt", "pelvis_list", "pelvis_rotation"]]
    data[:, tlr_indices] = convert_rotation_inv(data[:, tlr_indices])

    write_sto(args.output_file, column_names, data)

if __name__ == "__main__":
    main()