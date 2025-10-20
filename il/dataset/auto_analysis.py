import numpy as np
import pandas as pd
import opensim as osim
from pathlib import Path
import opensim as osim
from il.dataset import c3d2trc
import argparse

BASE    = str(Path(__file__).resolve().parent.parent)
MOT_DIR = BASE + "/dataset/mot/"
TRAJ_DIR = BASE + "/dataset/trajectories/"
TRAJ_SET_PATH = TRAJ_DIR + "/traj_set.xml"
MODEL_DIR = BASE + "/models/"

def generate_trajectory(idx: int, subject_id: int):
    model_path = MODEL_DIR + f"H2190_kit_{subject_id:05d}.osim"
    model = osim.Model(model_path)
    an = osim.AnalyzeTool(TRAJ_SET_PATH)
    an.setName(f"{idx:05d}")
    an.setModel(model)

    mot_path = MOT_DIR + f"{idx:05d}.mot"
    an.setCoordinatesFileName(mot_path)
    
    start_time, end_time = get_times(mot_path)
    an.setInitialTime(start_time)
    an.setFinalTime(end_time)

    an.setResultsDir(TRAJ_DIR)
    an.run()

def get_times(mot_path):
    data = np.array(pd.read_csv(mot_path, sep='\t', skiprows=10))
    start_time = data[0, 0]
    end_time = data[-1, 0]
    return start_time, end_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int, default=1)
    parser.add_argument("end", type=int)
    args = parser.parse_args()

    for i in range(args.start, args.end + 1):
        try:
            subject_id = c3d2trc.get_subject_id(i)
            generate_trajectory(i, subject_id)
            print(f"Analysis done for index: {i} subject ID: {subject_id}")
        except FileNotFoundError:
            pass