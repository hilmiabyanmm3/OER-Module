# utils/07_Module_6.py
import numpy as np
from scipy.integrate import ode

class OERKineticModel:
    def __init__(self, dg0_values, site_name, T=298.15):
        self.DG0 = dg0_values  # List of 5 Delta G values from thermodynamics
        self.site_name = site_name
        self.T = T
        self.kB_eV = 8.617333262145e-5  # eV/K
        self.Idx = [0, 1, 1, 1, 1]      # Step types (0: Chemical, 1: Electrochemical)
        self.GF0 = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.beta = 0.5                 # Transfer coefficient
        self.x_H2O = 1.0                # Activity of Water
        self.x_O2 = 2.34E-05            # Activity of Oxygen

    def get_rate_constants(self, U):
        kF, kR = np.zeros(5), np.zeros(5)
        # Potential-dependent Free Energy
        dg_pot = [val - U if self.Idx[i] == 1 else val for i, val in enumerate(self.DG0)]
        # Activation Energy (Butler-Volmer kinetics)
        gf_pot = [self.GF0[i] - self.beta*(U - self.DG0[i]) if self.Idx[i] == 1 else self.GF0[i] for i in range(5)]
        
        for i in range(5):
            K = np.exp(-dg_pot[i] / (self.kB_eV * self.T))
            ga = max(dg_pot[i], gf_pot[i], 0)
            
            if self.Idx[i] == 1:
                kF[i] = 1.00E09 * np.exp(-ga / (self.kB_eV * self.T))
            else:
                kF[i] = 5.76 * 1e9 # H2O Adsorption frequency
            kR[i] = kF[i] / K
        return kF, kR

    def get_odes(self, t, y, kF, kR):
        """Mass balance equations for surface species."""
        r = np.zeros(5)
        r[0] = kF[0]*self.x_H2O*y[4] - kR[0]*y[0]
        r[1] = kF[1]*y[0] - kR[1]*y[1]
        r[2] = kF[2]*y[1] - kR[2]*y[2]
        r[3] = kF[3]*y[2]*self.x_H2O - kR[3]*y[3]
        r[4] = kF[4]*y[3] - kR[4]*y[4]*self.x_O2
        
        return [r[0]-r[1], r[1]-r[2], r[2]-r[3], r[3]-r[4], r[4]-r[0]]

    def solve_coverage(self, U_range):
        thetas = {"H2O": [], "OH": [], "O": [], "OOH": [], "star": []}
        for u in U_range:
            kF, kR = self.get_rate_constants(u)
            # Using BDF method for stiff ODEs (common in chemical kinetics)
            solver = ode(self.get_odes).set_integrator('vode', method='bdf', atol=1e-12, rtol=1e-12)
            solver.set_initial_value([0, 0, 0, 0, 1], 0).set_f_params(kF, kR)
            res = solver.integrate(1e6) # Integrate to long time for steady-state
            
            thetas["H2O"].append(res[0])
            thetas["OH"].append(res[1])
            thetas["O"].append(res[2])
            thetas["OOH"].append(res[3])
            thetas["star"].append(res[4])
        return thetas