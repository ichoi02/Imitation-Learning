import numpy as np
import pandas as pd
import opensim as osim
from pathlib import Path
import opensim as osim
from il.dataset import c3d2trc
import argparse

BASE    = str(Path(__file__).resolve().parent.parent)
TRC_DIR = BASE + "/dataset/trc/"
MOT_DIR = BASE + "/dataset/mot/"
IK_SET_PATH = BASE + "/dataset/IK_set.xml"
MODEL_DIR = BASE + "/models/"

def auto_IK(idx: int, subject_id: int):
    trc_path = TRC_DIR + f"{idx:05d}_{subject_id:05d}.trc"

    model_path = MODEL_DIR + f"H2190_kit_{subject_id:05d}.osim"
    model = osim.Model(model_path)
    ik = osim.InverseKinematicsTool(IK_SET_PATH)
    ik.setName(f"{idx:05d}")
    ik.set_marker_file(trc_path)
    ik.setModel(model)

    data = np.array(pd.read_csv(trc_path, sep='\t', skiprows=6))
    start_time = data[0, 1]
    end_time = data[-1, 1]
    ik.setStartTime(start_time)
    ik.setEndTime(end_time)

    mot_path = MOT_DIR + f"{idx:05d}.mot"
    ik.setOutputMotionFileName(mot_path)
    ik.run()
    print(f"IK done for index: {idx} subject ID: {subject_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int, default=1)
    parser.add_argument("end", type=int)
    args = parser.parse_args()

    for i in range(args.start, args.end + 1):
        try:
            #c3d2trc.write_trc(idx)
            subject_id = c3d2trc.get_subject_id(i)
            auto_IK(i, subject_id)
        except FileNotFoundError:
            continue
