import numpy as np
from scipy.integrate import ode

class OERKineticModel:
    def __init__(self, dg0_values, site_name, T=298.15):
        # We take the 5 deltas directly from Module 5 session state
        self.DG0 = dg0_values 
        self.site_name = site_name
        self.T = T
        self.kB_eV = 8.617333262145e-5
        
        # Idx defines which steps are electrochemical (1) vs chemical (0)
        # Step 1: Physical adsorption (0)
        # Steps 2-5: Proton-Electron Transfers (1)
        self.Idx = [0, 1, 1, 1, 1] 
        self.GF0 = [0.0, 0.0, 0.0, 0.0, 0.0] # Activation barriers
        self.beta = 0.5 # Symmetry factor (Charge Transfer Coefficient)
        self.x_H2O = 1.0
        self.x_O2 = 2.34E-05 # Solubility of O2 in water

    def get_rate_constants(self, U):
        kF, kR = np.zeros(5), np.zeros(5)
        # Apply Nernstian shift (deltaG - U) for electrochemical steps
        dg_pot = [val - U if self.Idx[i] == 1 else val for i, val in enumerate(self.DG0)]
        
        # Calculate transition state energy per step
        gf_pot = [self.GF0[i] - self.beta*(U - self.DG0[i]) if self.Idx[i] == 1 else self.GF0[i] for i in range(5)]
        
        for i in range(5):
            # Equilibrium constant
            K = np.exp(-dg_pot[i] / (self.kB_eV * self.T))
            # Effective activation energy
            ga = max(dg_pot[i], gf_pot[i], 0)
            
            if self.Idx[i] == 1:
                # Potential-dependent ET rate
                kF[i] = 1.00E09 * np.exp(-ga / (self.kB_eV * self.T))
            else:
                # Physical adsorption rate (diffusion limited)
                kF[i] = 5.76 * 1e9 
            
            kR[i] = kF[i] / K
        return kF, kR

    def get_odes(self, t, y, kF, kR):
        r = np.zeros(5)
        # y indices: 0:H2O*, 1:OH*, 2:O*, 3:OOH*, 4:* (Empty Site)
        r[0] = kF[0]*self.x_H2O*y[4] - kR[0]*y[0]
        r[1] = kF[1]*y[0] - kR[1]*y[1]
        r[2] = kF[2]*y[1] - kR[2]*y[2]
        r[3] = kF[3]*y[2]*self.x_H2O - kR[3]*y[3]
        r[4] = kF[4]*y[3] - kR[4]*y[4]*self.x_O2
        
        # dTheta/dt (Conservation of sites)
        return [r[0]-r[1], r[1]-r[2], r[2]-r[3], r[3]-r[4], r[4]-r[0]]

    def solve_coverage(self, U_range):
        res_data = {"H2O": [], "OH": [], "O": [], "OOH": [], "star": [], "TOF": []}
        
        for u in U_range:
            kF, kR = self.get_rate_constants(u)
            # Stiff ODE solver (BDF) for kinetic stabilization
            solver = ode(self.get_odes).set_integrator('vode', method='bdf', atol=1e-12, rtol=1e-12)
            # Initial state: 100% empty sites (y[4]=1)
            solver.set_initial_value([0, 0, 0, 0, 1], 0).set_f_params(kF, kR)
            
            # Integrate to a large time to ensure steady-state
            y = solver.integrate(1e6) 
            
            # TOF is the flux of the final step (Oxygen release)
            tof = kF[4] * y[3] - kR[4] * y[4] * self.x_O2
            
            res_data["H2O"].append(y[0])
            res_data["OH"].append(y[1])
            res_data["O"].append(y[2])
            res_data["OOH"].append(y[3])
            res_data["star"].append(y[4])
            res_data["TOF"].append(max(tof, 1e-10))
            
        return res_data