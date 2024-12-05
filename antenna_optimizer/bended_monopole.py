import time

import numpy as np
from PyNEC import *
from scipy.spatial.transform import Rotation

from antenna_optimizer.antenna_model import Excitation, Antenna_Model


class BendingPoint:
    def __init__(self, distance: float, rotational_angle_rad: float, bending_angle_rad: float):
        self.distance = distance
        self.rotational_angle_rad = rotational_angle_rad
        self.bending_angle_rad = bending_angle_rad


class BendedMonopole(Antenna_Model):
    bending_radius = 0.01
    segment_len = 0.02
    wire_radius = 0.01

    def __init__(self, bending_points: list[BendingPoint], **kwargs):
        self.bending_points = bending_points
        self.tag = 1
        self.ex = None
        self._cursor = np.zeros(3)
        self._cursor_dir = np.eye(3)
        super().__init__(**kwargs)

    def geometry(self, nec=None):
        self._cursor = np.zeros(3)
        if nec is None:
            nec = self.nec
        self.tag = 1
        self.ex = Excitation(1, 1)
        segments = self.bending_points_to_segments_list()
        self.add_bended_segments(nec, segments)

    def bending_points_to_segments_list(self) -> np.ndarray:
        segments = [np.zeros(3)]
        for bp in self.bending_points:
            segments.append(segments[-1] + np.array([0.0, 0.0, bp.distance]))
        segments = np.stack(segments)
        for i, bp in enumerate(self.bending_points):
            bending_rot = Rotation.from_euler(
                angles=[0.0, bp.bending_angle_rad, 0.0],
                degrees=True,
                seq="xyz"
            )
            rot = Rotation.from_euler(
                angles=[0.0, 0.0, bp.rotational_angle_rad],
                degrees=True,
                seq="xyz"
            )
            segments = rot.apply(segments)
            segments[i:] = bending_rot.apply(segments[i:] - segments[i]) + segments[i]
        return segments

    def add_bended_segments(self, nec: nec_context, segments: np.ndarray):
        geo = nec.get_geometry()

        for p0, p1 in zip(segments[:-1], segments[1:]):
            n_seg = int(np.linalg.norm(p1 - p0) / self.segment_len)
            geo.wire(self.tag
                     , 30
                     , p0[0], p0[1], p0[2]
                     , p1[0], p1[1], p1[2]
                     , self.wire_radius
                     , 1, 1)

            self.tag += 1



if __name__ == '__main__':
    def main():
        antenna = BendedMonopole([
            BendingPoint(2 * 0.12491352, 0, 0),
        ],
            frq_min=[1100], frq_max=[2500]
        )

        with open('bended_test.nec', 'w') as f:
            text = antenna.as_nec(compute=True)
            f.write(text)
            f.write('\n')
        t0 = time.time()
        antenna.compute()
        print(f'Compute time: {time.time() - t0}')
        antenna.swr_plot()
        print(antenna.max_f_r_gain())
    main()
