# utils/04_Module_3.py
import io
import zipfile
import tempfile
import re
import os
import numpy as np
from ase import Atoms, Atom
from ase.io import read, write
from itertools import groupby
import pandas as pd



class AdsorbateGenerator:
    def __init__(self):
        self.base_atoms = None
        self.slab_fixed_indices = []
        
        # --- Group A (y > 0.5 * lattice_y) ---
        self.offsets_A = {
            "H2O":  [("O", -0.60,  0.00, 1.80), ("H", -1.30,  0.60, 2.00), ("H", -1.30, -0.60, 2.00)],
            "OH1":  [("O", -0.60,  0.00, 1.80), ("H", -1.30,  0.60, 2.00)],
            "OH2":  [("O", -0.60,  0.00, 1.80), ("H", -1.30, -0.60, 2.00)],
            "O":    [("O", -0.80,  0.00, 1.60)],
            "OOH1": [("O", -1.03, -0.82, 1.25), ("O", -1.31, -0.09, 2.38), ("H", -2.15,  0.40, 2.08)],
            "OOH2": [("O", -1.03,  0.82, 1.25), ("O", -1.31,  0.09, 2.38), ("H", -2.15, -0.40, 2.08)]
        }

        # --- Group B (y < 0.5 * lattice_y) ---
        self.offsets_B = {
            "H2O":  [("O",  0.60,  0.00, 1.80), ("H",  1.30,  0.60, 2.00), ("H",  1.30, -0.60, 2.00)],
            "OH1":  [("O",  0.60,  0.00, 1.80), ("H",  1.30,  0.60, 2.00)],
            "OH2":  [("O",  0.60,  0.00, 1.80), ("H",  1.30, -0.60, 2.00)],
            "O":    [("O",  0.80,  0.00, 1.60)],
            "OOH1": [("O",  1.03, -0.84, 1.24), ("O",  1.34, -0.14, 2.37), ("H",  2.17,  0.37, 2.07)],
            "OOH2": [("O",  1.03,  0.84, 1.24), ("O",  1.34,  0.14, 2.37), ("H",  2.17, -0.37, 2.07)]
        }

    def load_slab(self, out_content):
        """Extracts slab structure from PW.out content."""
        try:
            f = io.StringIO(out_content)
            self.base_atoms = read(f, format='espresso-out', index='-1')
            
            # Determine fixed indices (bottom 66%)
            z_coords = self.base_atoms.positions[:, 2]
            min_z, max_z = np.min(z_coords), np.max(z_coords)
            cutoff = min_z + (max_z - min_z) * 0.66
            self.slab_fixed_indices = [i for i, z in enumerate(z_coords) if z <= cutoff]
            return True
        except Exception:
            return False

    def find_top_sites(self, target_elements, z_tolerance=1.5):
        if self.base_atoms is None: return []
        
        sites = []
        z_coords = [a.position[2] for a in self.base_atoms if a.symbol in target_elements]
        if not z_coords: return []
        
        max_z = max(z_coords)
        for i, atom in enumerate(self.base_atoms):
            if atom.symbol in target_elements and abs(max_z - atom.position[2]) <= z_tolerance:
                sites.append({
                    "index_ase": i,
                    "index_qe": i + 1,
                    "symbol": atom.symbol,
                    "y_coord": atom.position[1],
                    "z_coord": atom.position[2]
                })
        return sorted(sites, key=lambda x: x["z_coord"], reverse=True)

    def build_adsorbates_zip(self, selected_sites):
        output_buffer = io.BytesIO()
        variants = {
            "1-h2o": ["H2O"],
            "2-oh": ["OH1", "OH2"],
            "3-o": ["O"],
            "4-ooh": ["OOH1", "OOH2"]
        }
        
        lattice_y = self.base_atoms.cell.lengths()[1]
        
        with zipfile.ZipFile(output_buffer, 'w') as zf:
            for site in selected_sites:
                ref_pos = self.base_atoms[site['index_ase']].position
                site_name = f"{site['symbol']}-{site['index_qe']}"
                
                # Select offsets based on Y-coordinate grouping
                active_offsets = self.offsets_A if ref_pos[1] > 0.5 * lattice_y else self.offsets_B
                
                for folder, ads_list in variants.items():
                    for ads_type in ads_list:
                        # Clone base and add adsorbate atoms
                        new_atoms = self.base_atoms.copy()
                        for elem, dx, dy, dz in active_offsets[ads_type]:
                            new_pos = [ref_pos[0] + dx, ref_pos[1] + dy, ref_pos[2] + dz]
                            new_atoms.append(Atom(elem, position=new_pos))
                        
                        # Generate VASP/QE content
                        v_buf = io.StringIO()
                        write(v_buf, new_atoms, format='vasp')
                        
                        path = f"{folder}/{site_name}/{ads_type}" if len(ads_list) > 1 else f"{folder}/{site_name}"
                        zf.writestr(f"{path}/input.vasp", v_buf.getvalue())
                        zf.writestr(f"{path}/PW.in", f"! Adsorbate {ads_type} on {site_name}\n" + v_buf.getvalue())
        
        output_buffer.seek(0)
        return output_buffer.getvalue()
    


class AdsorbateAnalyzer:
    """Logic for Step 2: Analyzing OER Adsorbate Results"""
    def __init__(self):
        self.step_order = {"slab": 0, "1-h2o": 1, "2-oh": 2, "3-o": 3, "4-ooh": 4}
        self.site_pattern = r"([A-Z][a-z]?-\d+)"

    def _parse_path_info(self, path: str):
        lower_path = path.lower()
        parts = path.split('/')
        
        # 1. Determine Step
        step = "unknown"
        for key in self.step_order.keys():
            if key in lower_path:
                step = key
                break
        
        # 2. Determine Termination
        term = "atas" if "atas" in lower_path else "bawah" if "bawah" in lower_path else "unknown"

        # 3. Determine Site (e.g., Ni-1)
        site = None
        for part in reversed(parts):
            match = re.search(self.site_pattern, part)
            if match:
                site = match.group(1)
                break
        
        return step, site, term

    def process_zip(self, zip_bytes):
        adsorbates_data = []
        slabs_map = {}

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            out_files = [f for f in z.namelist() if f.endswith((".out", ".log")) and not "__MACOSX" in f]
            
            for path in out_files:
                content = z.read(path).decode("utf-8", errors='ignore')
                
                # Extract Energy (Ry)
                match = re.search(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content)
                if not match: continue
                
                energy_ry = float(match.group(1))
                step, site, term = self._parse_path_info(path)
                
                # Use ASE to extract final structure strings for download
                f_buf = io.StringIO(content)
                try:
                    atoms = read(f_buf, format='espresso-out', index='-1')
                    v_buf = io.StringIO()
                    write(v_buf, atoms, format='vasp')
                    vasp_str = v_buf.getvalue()
                except:
                    vasp_str = ""

                record = {
                    "Path": path, "Energy (Ry)": energy_ry,
                    "Step": step, "Step_Order": self.step_order.get(step, 99),
                    "Site": site, "Termination": term, "vasp": vasp_str
                }

                if step == "slab": slabs_map[term] = record
                else: adsorbates_data.append(record)

        if not adsorbates_data: return pd.DataFrame()

        # Grouping by Site to make the report readable
        adsorbates_data.sort(key=lambda x: (x['Site'] or "", x['Step_Order']))
        final_rows = []
        
        for site_name, group in groupby(adsorbates_data, key=lambda x: x['Site']):
            group_list = list(group)
            term = group_list[0]['Termination']
            
            # Add the reference slab for this site first
            if term in slabs_map:
                s_rec = slabs_map[term].copy()
                s_rec['Site'] = site_name
                final_rows.append(s_rec)
            
            final_rows.extend(group_list)
            # Add a spacer for Excel readability
            final_rows.append({"Path": "", "Step": "", "Site": "", "Energy (Ry)": None})
            
        return pd.DataFrame(final_rows)

    def generate_excel(self, df):
        output = io.BytesIO()
        cols = ['Step', 'Site', 'Energy (Ry)', 'Path']
        df_exp = df[[c for c in cols if c in df.columns]].fillna("")
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='OER_Energies')
        return output.getvalue()