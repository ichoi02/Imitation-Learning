import pandas as pd
import numpy as np
from pathlib import Path
import os
from scipy.spatial.transform import Rotation

SIMULATION_FPS = 50
DATASET_FPS = 100

BASE = Path(__file__).resolve().parent
MOT_DIR = BASE / "mot"
TRAJ_DIR = BASE / "trajectories"

class Data:
    def __init__(self, idx_start=1, idx_end=None):
        self.data = {}
        self.index = []
        self.seq_len = {}
        self.pelvis_quats = {}
        self.column_names = None
        self.traj_column_names = None

        if idx_end == None:
            idx_end = len(os.listdir(MOT_DIR))
        
        n = 0
        for i in range(idx_start, idx_end + 1):
            try:
                # read data from files
                mot_path = str(MOT_DIR / f"{i:05d}.mot")
                column_names, time, q = self.read_mot(mot_path)
                traj_path = str(TRAJ_DIR / f"{i:05d}_BodyKinematics_pos_global.sto")
                traj_column_names, traj = self.read_sto(traj_path)

                # store column names
                if self.column_names == None:
                    self.column_names = column_names
                if self.traj_column_names == None:
                    self.traj_column_names = traj_column_names

                # convert to rad
                q[:, 0:3] = np.deg2rad(q[:, 0:3])
                q[:, 6:] = np.deg2rad(q[:, 6:])
                
                # convert rotation from opensim to scone
                q[:, 0:3], r, self.pelvis_quats[i] = self._convert_rotation(q[:, 0:3])

                # compute gradients
                q_dot = np.gradient(q, time, axis=0)
                traj_dot = np.gradient(traj, time, axis=0)
                
                # convert velocity to local coordinates
                q_dot[:, 3:6] = self._global_to_local(q_dot[:, 3:6], r)

                # compute angular velocities
                angvel = self._calculate_angular_velocity(self.pelvis_quats[i], DATASET_FPS)
                
                # sore data
                self.data[i] = {"time": time, 
                                "q": q, "q_dot": q_dot, 
                                "traj": traj, "traj_dot": traj_dot,
                                "angvel": angvel}
                self.seq_len[i] = len(time)
                self.index.append(i)
                n += 1

            except FileNotFoundError:
                continue

        print(f"Loaded {n} files.")

    def read_mot(self, mot_path):
        text_header = []
        with open(mot_path, "r") as f:
            for i, line in enumerate(f):
                text_header.append(line.strip())
                if "endheader" in line.lower():
                    skiprows = i + 1
                    break
        
        column_names = pd.read_csv(mot_path, sep='\s+', skiprows=skiprows, nrows=0).columns.tolist()
        
        data = pd.read_csv(mot_path, sep='\s+', skiprows=skiprows)
        time = data.values[:,0]
        q = data.values[:,1:]
        column_names = column_names[1:]
        return column_names, time, q
    
    def read_sto(self, sto_path):
        text_header = []
        with open(sto_path, "r") as f:
            for i, line in enumerate(f):
                text_header.append(line.strip())
                if "endheader" in line.lower():
                    skiprows = i + 1
                    break
        traj_column_names = pd.read_csv(sto_path, sep='\t', skiprows=skiprows, nrows=0).columns.tolist()
        
        data = pd.read_csv(sto_path, sep='\t', skiprows=skiprows)
        traj = data.values[:, 1:]
        traj_column_names = traj_column_names[1:]
        return traj_column_names, traj

    def _convert_rotation(self, input):
        r = Rotation.from_euler('ZXY', input, degrees=False)
        out = r.as_euler('YXZ', degrees=False)
        quats = r.as_quat()
        return out[:, [2, 1, 0]], r, quats

    def _global_to_local(self, vel, r):
        v_local = r.apply(vel, inverse=True)
        return v_local

    def get_pos_vel(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        pos = self.data[idx]["q"][time_idx].copy()
        vel = self.data[idx]["q_dot"][time_idx].copy()
        return pos, vel
    
    def get_pelvis_rotation(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        pos = self.data[idx]["q"][time_idx, 0:3].copy()
        vel = self.data[idx]["q_dot"][time_idx, 0:3].copy()
        return pos, vel
    
    def get_pelvis_translation(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        pos = self.data[idx]["q"][time_idx, 3:6].copy()
        vel = self.data[idx]["q_dot"][time_idx, 3:6].copy()
        return pos, vel
    
    def get_joint_angles(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        pos = self.data[idx]["q"][time_idx, 6:].copy()
        vel = self.data[idx]["q_dot"][time_idx, 6:].copy()
        return pos, vel
    
    def get_trajectory(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        com_pos = self.data[idx]['traj'][time_idx, -3:].copy()
        calcn_r_pos = self.data[idx]['traj'][time_idx, 0:3].copy()
        calcn_l_pos = self.data[idx]['traj'][time_idx, 6:9].copy()
        com_vel = self.data[idx]['traj_dot'][time_idx, -3:].copy()
        calcn_r_vel = self.data[idx]['traj_dot'][time_idx, 0:3].copy()
        calcn_l_vel = self.data[idx]['traj_dot'][time_idx, 6:9].copy()
        return com_pos, calcn_r_pos, calcn_l_pos, com_vel, calcn_r_vel, calcn_l_vel
    
    def get_pelvis_quats(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        pelvis_quat = self.pelvis_quats[idx][time_idx].copy()
        return pelvis_quat
    
    def get_angvel(self, idx, time):
        time_idx = int(time * DATASET_FPS) - 1
        angvel = self.data[idx]['angvel'][time_idx].copy()
        return angvel
    
    def _calculate_angular_velocity(self, quaternions, fs):
        def quat_conjugate(q):
            return np.array([q[..., 0], -q[..., 1], -q[..., 2], -q[..., 3]]).T

        def quat_multiply(q1, q2):
            w1, x1, y1, z1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
            w2, x2, y2, z2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
            w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
            x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
            y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
            z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
            return np.stack([w, x, y, z], axis=-1)

        q_continuous = np.copy(quaternions)
        for i in range(1, len(q_continuous)):
            if np.dot(q_continuous[i-1], q_continuous[i]) < 0:
                q_continuous[i] *= -1 
        dt = 1.0 / fs
        
        q_derivative = np.gradient(q_continuous, axis=0) / dt
        q_conj = quat_conjugate(q_continuous)
        q_omega = 2 * quat_multiply(q_derivative, q_conj)
        angular_velocity = q_omega[:, 1:]
        return angular_velocity