# utils/05_Module_4.py
import io
import zipfile
import copy
import numpy as np
import pandas as pd
import re
import os
from itertools import groupby
from ase import Atoms
from ase.units import Ry, Bohr, _hbar, _e, _amu
import matplotlib.pyplot as plt
import matplotlib as mpl
import math

import io
import re
from ase.io import read
import numpy as np

class ZPEManager:
    def __init__(self):
        self.delta = 0.01  # Displacement in Angstrom

    def generate_finite_displacements(self, out_content, template_content, n_to_displace):
        try:
            # 1. Parse final structure from .out
            f_out = io.StringIO(out_content)
            atoms = read(f_out, format='espresso-out', index='-1')
            total_atoms = len(atoms)

            # 2. Adjust 'nat' in the template using Regex
            # Finds 'nat = some_number' (case insensitive) and replaces with actual count
            template_adjusted = re.sub(
                r'(nat\s*=\s*)\d+', 
                f'\\1{total_atoms}', 
                template_content, 
                flags=re.IGNORECASE
            )

            # 3. Clean template: Remove existing ATOMIC_POSITIONS block
            template_clean = re.split(r'ATOMIC_POSITIONS', template_adjusted, flags=re.IGNORECASE)[0]
            template_clean = template_clean.strip()

            # 4. Define displacement directions with new naming suffixes
            # p = plus, m = minus
            directions = [
                ('x', 0, 1, 'p'), ('x', 0, -1, 'm'),
                ('y', 1, 1, 'p'), ('y', 1, -1, 'm'),
                ('z', 2, 1, 'p'), ('z', 2, -1, 'm')
            ]

            target_indices = range(total_atoms - n_to_displace, total_atoms)
            results = {}

            for idx in target_indices:
                # Use 1-based index for naming (QE convention)
                qe_idx = idx + 1 
                original_pos = atoms[idx].position.copy()

                for axis, axis_idx, sign, suffix in directions:
                    # Create displaced atoms object
                    displaced_atoms = atoms.copy()
                    move = np.zeros(3)
                    move[axis_idx] = self.delta * sign
                    displaced_atoms[idx].position += move

                    # Format the ATOMIC_POSITIONS block
                    pos_block = "\n\nATOMIC_POSITIONS {angstrom}\n"
                    for atom in displaced_atoms:
                        pos_block += f"{atom.symbol:4} {atom.position[0]:12.8f} {atom.position[1]:12.8f} {atom.position[2]:12.8f}\n"

                    # 5. New Filename Format: PWINPUT_atm[index]_[axis][suffix]
                    filename = f"PWINPUT_atm{qe_idx}_{axis}{suffix}.in"
                    results[filename] = template_clean + pos_block

            return results
        except Exception as e:
            print(f"Error: {e}")
            return None


class ZPEAnalyzer:
    """Logic for Step 2: Extracting Forces and Computing ZPE"""
    def __init__(self):
        # Define chemical species and their masses for OER intermediates
        raw_species = {
            "1-h2o": {"symbols": "OHH"}, "2-oh": {"symbols": "OH"},
            "3-o": {"symbols": "O"}, "4-ooh": {"symbols": "OOH"},
            "h": {"symbols": "H"}
        }
        self.species_params = {k: {"symbols": v["symbols"], 
                                "masses": Atoms(v["symbols"]).get_masses().tolist()} 
                              for k, v in raw_species.items()}
        self.step_order = {"1-h2o": 1, "2-oh": 2, "3-o": 3, "4-ooh": 4}
        self.site_pattern = r"([A-Z][a-z]?-\d+)"

    def _parse_path_info(self, path: str):
        lower_path = path.lower()
        parts = path.split('/')
        step = next((k for k in self.step_order if k in lower_path), "unknown")
        term = "atas" if "atas" in lower_path else "bawah" if "bawah" in lower_path else "unknown"
        site = None
        for part in reversed(parts):
            match = re.search(self.site_pattern, part, re.IGNORECASE)
            if match: site = match.group(1).capitalize(); break
        return step, site, term

    def _read_forces(self, zf, filepath, idx_move):
        """Extracts QE force vectors for specific atom indices."""
        forces = np.zeros((len(idx_move), 3))
        with zf.open(filepath) as f:
            lines = f.read().decode('utf-8', errors='ignore').splitlines()
            it = iter(lines)
            for line in it:
                if 'Forces acting' in line:
                    while 'type' not in line: line = next(it)
                    ia = 0
                    while 'atom' in line:
                        parts = line.split()
                        if len(parts) >= 9 and int(parts[1]) in idx_move:
                            forces[ia] = [float(parts[6])*Ry/Bohr, float(parts[7])*Ry/Bohr, float(parts[8])*Ry/Bohr]
                            ia += 1
                        try: line = next(it)
                        except StopIteration: break
        return forces

    def compute_zpe(self, zf, folder_path, species_key, idx_move, delta=0.01):
        """Constructs Hessian and solves for vibrational frequencies."""
        m = np.array(self.species_params[species_key]["masses"])
        n = 3 * len(idx_move)
        H = np.empty((n, n))
        r = 0
        for a in idx_move:
            for i in 'xyz':
                # Map naming convention to log files generated in Step 1
                f_m = f"{folder_path}/atom{a-idx_move[0]+1}_{i}_minus.out" # Adjust mapping to your naming
                f_p = f"{folder_path}/atom{a-idx_move[0]+1}_{i}_plus.out"
                
                # Fallback to standard LOG_atm naming if needed
                try: 
                    fm_forces = self._read_forces(zf, f_m, idx_move)
                    fp_forces = self._read_forces(zf, f_p, idx_move)
                except:
                    # Alternative naming fallback
                    f_m = f"{folder_path}/LOG_atm{a}_{i}m"; f_p = f"{folder_path}/LOG_atm{a}_{i}p"
                    fm_forces = self._read_forces(zf, f_m, idx_move); fp_forces = self._read_forces(zf, f_p, idx_move)

                H[r] = 0.5 * (fm_forces - fp_forces).ravel() / (2.0 * delta)
                r += 1

        H += H.T
        im = np.repeat(m**-0.5, 3)
        omega2, _ = np.linalg.eigh(im[:, None] * H * im)
        s = _hbar * 1e10 / np.sqrt(_e * _amu)
        hnu = s * omega2.astype(complex)**0.5
        return 0.5 * hnu.real.sum()

    def process_zip(self, zip_bytes):
        zpe_data = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            calc_folders = {os.path.dirname(f) for f in z.namelist() if "atom" in f or "LOG_atm" in f}
            for folder in calc_folders:
                step, site, term = self._parse_path_info(folder)
                if step == "unknown": continue
                
                # species_key logic (e.g. 1-h2o)
                idx_move = [1, 2, 3] # Simplified for OHH; in real use, map to n_slab + i
                try:
                    zpe_val = self.compute_zpe(z, folder, step, idx_move)
                    zpe_data.append({"Path": folder, "Step": step, "Site": site, "ZPE (eV)": zpe_val})
                except: continue
        return pd.DataFrame(zpe_data)
    


class GibbsAnalyzer:
    """Logic for Step 3: Gibbs Free Energy & Overpotential Analysis"""
    def __init__(self):
        self.ry_to_ev = 13.605698066
        self.colors = ["orange","green","blue","red","purple","salmon","pink","cyan","lime"] * 3
        self.markers = ["s"]*12 + ["^"]*12 + ["o"]*12

    def calculate_deltas(self, df_e, df_z, G_H2O, G_H2, U):
        # Clean dataframes
        df_e = df_e[df_e['Path'].notna() & (df_e['Path'] != "")].copy()
        df_z = df_z[df_z['Path'].notna() & (df_z['Path'] != "")].copy()

        # Merge Energy and ZPE
        merged = pd.merge(df_e, df_z[['Step', 'Site', 'ZPE (eV)']], on=['Step', 'Site'], how='left')
        merged['ZPE (eV)'] = merged['ZPE (eV)'].fillna(0.0)
        merged['E (eV)'] = merged['Energy (Ry)'] * self.ry_to_ev

        results = []
        G_O2 = 4.92 + 2 * G_H2O - 2 * G_H2
        G_PE = 0.5 * G_H2 

        for site, group in merged.groupby(['Site']):
            def get_val(step_name, col):
                val = group[group['Step'] == step_name][col].values
                return val[0] if len(val) > 0 else None

            E = [get_val('slab', 'E (eV)'), get_val('1-h2o', 'E (eV)'), 
                 get_val('2-oh', 'E (eV)'), get_val('3-o', 'E (eV)'), get_val('4-ooh', 'E (eV)')]
            Z = [0.0, get_val('1-h2o', 'ZPE (eV)'), get_val('2-oh', 'ZPE (eV)'), 
                 get_val('3-o', 'ZPE (eV)'), get_val('4-ooh', 'ZPE (eV)')]
            
            if None in E: continue

            # OER 5-Step Logic
            dg = []
            dg.append(E[1] + Z[1] - (G_H2O + E[0])) # Step 1
            dg.append(E[2] + Z[2] + (G_PE - U) - (E[1] + Z[1])) # Step 2
            dg.append(E[3] + Z[3] + (G_PE - U) - (E[2] + Z[2])) # Step 3
            dg.append(E[4] + Z[4] + (G_PE - U) - G_H2O - (E[3] + Z[3])) # Step 4
            dg.append(E[0] + G_O2 + (G_PE - U) - (E[4] + Z[4])) # Step 5

            max_step = max(dg[1:])
            overpotential = max_step - 1.23
            
            # Generate Profile Data
            levels = [0.0]
            for val in dg: levels.append(levels[-1] + val)
            x_plot, y_plot = [], []
            for i, l in enumerate(levels):
                x_plot.extend([2*i, 2*i+1])
                y_plot.extend([l, l])

            results.append({
                "label": site, "deltaG": dg, "overpotential": overpotential,
                "dataX": x_plot, "dataY": y_plot
            })
        return results

    def create_plot(self, plot_data, title, U_shift=0.0):
        plt.rcParams['font.size'] = 14
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for i, data in enumerate(plot_data):
            c = self.colors[i % len(self.colors)]
            x, y_orig = data['dataX'], data['dataY']
            
            # Apply U_shift to the Y coordinates
            y = [val - (U_shift * (j // 2)) if j > 1 else val for j, val in enumerate(y_orig)]
            
            ax.plot(x, y, color=c, linewidth=3, label=data['label'])
            # Dotted connecting lines
            for j in range(len(x)//2 - 1):
                ax.plot([x[2*j+1], x[2*j+2]], [y[2*j+1], y[2*j+2]], color=c, linestyle='--', alpha=0.5)

        ax.set_ylabel("Gibbs Free Energy (eV)")
        ax.set_title(title)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        return fig
