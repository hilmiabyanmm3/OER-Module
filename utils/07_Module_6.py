# utils/07_Module_6.py

import numpy as np
from scipy.integrate import ode
from scipy.integrate import solve_ivp

class OERKineticModel:
    def __init__(self, dg0_values, site_name, T=298.15):
        self.DG0 = dg0_values 
        self.site_name = site_name
        self.T = T
        self.kB_eV = 8.617333262145e-5
        self.Idx = [0, 1, 1, 1, 1]
        self.GF0 = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.beta = 0.5
        self.x_H2O = 1.0
        self.x_O2 = 2.34E-05

    def get_rate_constants(self, U):
        kF, kR = np.zeros(5), np.zeros(5)
        dg_pot = [val - U if self.Idx[i] == 1 else val for i, val in enumerate(self.DG0)]
        gf_pot = [self.GF0[i] - self.beta*(U - self.DG0[i]) if self.Idx[i] == 1 else self.GF0[i] for i in range(5)]
        
        for i in range(5):
            K = np.exp(-dg_pot[i] / (self.kB_eV * self.T))
            ga = max(dg_pot[i], gf_pot[i], 0)
            if self.Idx[i] == 1:
                kF[i] = 1.00E09 * np.exp(-ga / (self.kB_eV * self.T))
            else:
                kF[i] = 5.76 * 1e9 
            kR[i] = kF[i] / K
        return kF, kR

    def get_odes(self, t, y, kF, kR):
        r = np.zeros(5)
        r[0] = kF[0]*self.x_H2O*y[4] - kR[0]*y[0]
        r[1] = kF[1]*y[0] - kR[1]*y[1]
        r[2] = kF[2]*y[1] - kR[2]*y[2]
        r[3] = kF[3]*y[2]*self.x_H2O - kR[3]*y[3]
        r[4] = kF[4]*y[3] - kR[4]*y[4]*self.x_O2
        return [r[0]-r[1], r[1]-r[2], r[2]-r[3], r[3]-r[4], r[4]-r[0]]

    def solve_coverage(self, U_range):
        res_data = {"H2O": [], "OH": [], "O": [], "OOH": [], "star": [], "TOF": []}

        for u in U_range:
            kF, kR = self.get_rate_constants(u)

            sol = solve_ivp(
                fun=self.get_odes,
                t_span=(0.0, 1e3),
                y0=[0, 0, 0, 0, 1],
                method="BDF",
                args=(kF, kR),
                atol=1e-8,
                rtol=1e-8,
                dense_output=False,
            )
            y = sol.y[:, -1]

            tof = kF[4] * y[3] - kR[4] * y[4] * self.x_O2

            res_data["H2O"].append(y[0])
            res_data["OH"].append(y[1])
            res_data["O"].append(y[2])
            res_data["OOH"].append(y[3])
            res_data["star"].append(y[4])
            res_data["TOF"].append(max(tof, 1e-10))

        return res_data