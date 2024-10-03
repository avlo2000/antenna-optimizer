import PyNEC
import numpy as np
from PyNEC import *

import math

from scipy.spatial.transform import Rotation

from antenna_optimizer.antenna_model import Excitation, Antenna_Model


class BendingPoint:
    def __init__(self, distance: float, rotational_angle_rad: float, bending_angle_rad: float):
        self.distance = distance
        self.rotational_angle_rad = rotational_angle_rad
        self.bending_angle_rad = bending_angle_rad


class BendedMonopole(Antenna_Model):
    bending_radius = 0.01
    segment_len = 0.003
    wire_radius = 0.0015

    def __init__(self, bending_points: list[BendingPoint], **kwargs):
        self.bending_points = bending_points
        self.tag = 1
        self.ex = None
        self._cursor = np.zeros(3)
        super().__init__(**kwargs)

    def geometry(self, nec=None):
        self._cursor = np.zeros(3)
        if nec is None:
            nec = self.nec
        self.tag = 1
        self.ex = Excitation(1, 1)
        for bp in self.bending_points:
            self.add_bended_segment(nec, bp)

    def add_bended_segment(self, nec: nec_context, bending_point: BendingPoint):
        geo = nec.get_geometry()
        n_seg = int(bending_point.distance / self.segment_len)
        p1 = self._cursor + np.array([0.0, 0.0, bending_point.distance])
        geo.wire(self.tag
                 , n_seg
                 , self._cursor[0], self._cursor[1], self._cursor[2]
                 , p1[0], p1[1], p1[2]
                 , self.wire_radius
                 , 1, 1)
        self._cursor = p1
        self.tag += 1


if __name__ == '__main__':
    def main():
        antenna = BendedMonopole([
            BendingPoint(0.1, np.rad2deg(10), np.rad2deg(20)),
            BendingPoint(0.2, np.rad2deg(10), np.rad2deg(20)),
            BendingPoint(0.2, np.rad2deg(10), np.rad2deg(20)),
        ])

        print(antenna.as_nec(compute=False))
    main()
