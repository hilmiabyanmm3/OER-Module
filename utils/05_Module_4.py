# utils/05_Module_4.py
import io
import zipfile
import numpy as np
import pandas as pd
import re
import os
from ase import Atoms
from ase.io import read
from ase.units import Ry, Bohr, _hbar, _e, _amu
from itertools import groupby

class ZPEManager:
    def __init__(self):
        self.delta = 0.01
        # Mapping adsorbate types to number of atoms to displace
        self.ads_map = {
            "ooh": 3,
            "h2o": 3,
            "oh": 2,
            "o": 1
        }

    def detect_n_from_path(self, path):
        """Detects how many atoms to displace based on folder/file keywords."""
        lower_path = path.lower()
        # Order matters: check 'ooh' before 'oh' and 'o'
        for key in ["ooh", "h2o", "oh", "o"]:
            if key in lower_path:
                return self.ads_map[key]
        return 0 # Default if no match found

    def generate_finite_displacements(self, out_content, template_content, n_to_displace):
        """Core logic to generate 6 displaced files for the top n atoms."""
        try:
            f_out = io.StringIO(out_content)
            atoms = read(f_out, format='espresso-out', index='-1')
            total_atoms = len(atoms)

            # Update 'nat'
            template_adjusted = re.sub(r'(nat\s*=\s*)\d+', f'\\1{total_atoms}', template_content, flags=re.IGNORECASE)
            template_clean = re.split(r'ATOMIC_POSITIONS', template_adjusted, flags=re.IGNORECASE)[0].strip()

            directions = [
                ('x', 0, 1, 'p'), ('x', 0, -1, 'm'),
                ('y', 1, 1, 'p'), ('y', 1, -1, 'm'),
                ('z', 2, 1, 'p'), ('z', 2, -1, 'm')
            ]

            target_indices = range(total_atoms - n_to_displace, total_atoms)
            file_results = {}

            for idx in target_indices:
                qe_idx = idx + 1
                for axis, axis_idx, sign, suffix in directions:
                    displaced_atoms = atoms.copy()
                    displaced_atoms[idx].position[axis_idx] += self.delta * sign

                    pos_block = "\n\nATOMIC_POSITIONS {angstrom}\n"
                    for atom in displaced_atoms:
                        pos_block += f"{atom.symbol:4} {atom.position[0]:12.8f} {atom.position[1]:12.8f} {atom.position[2]:12.8f}\n"

                    filename = f"PWINPUT_atm{qe_idx}_{axis}{suffix}.in"
                    file_results[filename] = template_clean + pos_block
            return file_results
        except:
            return None

    def process_batch_zip(self, input_zip_bytes, template_content):
        """Handles the batch ZIP-in/ZIP-out logic."""
        output_buffer = io.BytesIO()
        
        with zipfile.ZipFile(io.BytesIO(input_zip_bytes), 'r') as in_zip:
            with zipfile.ZipFile(output_buffer, 'w') as out_zip:
                # Find all .out files
                out_files = [f for f in in_zip.namelist() if f.endswith(('.out', '.log')) and not '__MACOSX' in f]
                
                for path in out_files:
                    n = self.detect_n_from_path(path)
                    if n == 0: continue # Skip files that don't match adsorbate keywords
                    
                    content = in_zip.read(path).decode('utf-8', errors='ignore')
                    # Generate the 6*n files
                    displaced_files = self.generate_finite_displacements(content, template_content, n)
                    
                    if displaced_files:
                        # We use the original path folder name to keep things organized
                        folder_prefix = "/".join(path.split("/")[:-1])
                        for fname, ftext in displaced_files.items():
                            out_zip.writestr(f"{folder_prefix}/{fname}", ftext)
        
        output_buffer.seek(0)
        return output_buffer.getvalue()

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
                # ... (kode parsing step dan perhitungan ZPE tetap sama seperti sebelumnya) ...
                step, site, term = self._parse_path_info(folder)
                if step == "unknown" or step not in self.species_params: 
                    continue

                species_len = len(self.species_params[step]["symbols"])
                n_slab = 0
                geom_path = f"{folder}/GEOM.xyz" if folder else "GEOM.xyz"
                try:
                    content = z.read(geom_path).decode('utf-8')
                    total_atoms = int(content.strip().split('\n')[0].strip())
                    n_slab = total_atoms - species_len
                except Exception:
                    n_slab = 156 
                
                idx_move = [n_slab + i for i in range(1, species_len + 1)]
                
                try:
                    zpe_val = self.compute_zpe(z, folder, step, idx_move)
                    zpe_data.append({"Path": folder, "Step": step, "Step_Order": self.step_order.get(step, 99),"Site": site, "ZPE (eV)": zpe_val})
                except Exception as e:
                    print(f"Failed processing ZPE at {folder}: {e}")
                    continue
                    
        # --- LOGIKA PENGELOMPOKKAN (GROUPING) ---
        if not zpe_data: return pd.DataFrame()
        
        # Buang data yang tidak punya site (None/kosong)
        zpe_data = [x for x in zpe_data if x['Site']]
        
        # Urutkan berdasarkan Site terlebih dahulu, lalu Step_Order agar 1-h2o sampai 4-ooh berurutan
        zpe_data.sort(key=lambda x: (x['Site'], x['Step_Order']))

        final_rows = []
        # Group berdasarkan Site
        for site_name, group in groupby(zpe_data, key=lambda x: x['Site']):
            group_list = list(group)
            
            # Masukkan seluruh data dalam satu site tersebut
            final_rows.extend(group_list)
            
            # Tambahkan baris kosong (spacer) sebagai pemisah di Excel
            final_rows.append({"Path": None, "Step": None, "Site": None, "ZPE (eV)": None})
            
        return pd.DataFrame(final_rows)
    
    def generate_excel(self, df: pd.DataFrame):
        output = io.BytesIO()
        target = ['Path', 'Step', 'Site', 'ZPE (eV)']
        cols = [c for c in target if c in df.columns]
        df_exp = df[cols].fillna("")

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='ZPE Summary')
            ws = writer.sheets['ZPE Summary']
            
            fmt = writer.book.add_format({'num_format': '0.000'})
            
            for i, col in enumerate(df_exp.columns):
                max_len = len(str(col))
                if not df_exp[col].empty:
                    s_len = df_exp[col].astype(str).map(len)
                    if not s_len.empty: max_len = max(max_len, s_len.max())
                width = min(max_len + 2, 60)
                ws.set_column(i, i, width, fmt if col == 'ZPE (eV)' else None)
                
        output.seek(0)
        return output
    