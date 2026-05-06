# utils/05_Module_4.py
import io, zipfile, re, os
import numpy as np
import pandas as pd
from ase import Atoms
from ase.io import read
from ase.data import atomic_masses, atomic_numbers
from ase.units import Ry, Bohr, _hbar, _e, _amu
from itertools import groupby

class ZPEManager:
    def __init__(self):
        self.delta = 0.01
        self.ads_map = {"ooh": 3, "h2o": 3, "oh": 2, "o": 1}
        self.metals = {'Ni', 'Fe', 'Mn', 'Co', 'Cu', 'Pd', 'Pt', 'Ag', 'Au', 'Ru', 'Rh', 'Ir', 'Os', 'V', 'Cr', 'Ti', 'Sc', 'Zn'}

    def detect_n_from_path(self, path):
        # Gunakan generator untuk mencari n dengan cepat dalam 1 baris
        return next((self.ads_map[k] for k in ["ooh", "h2o", "oh", "o"] if k in path.lower()), 0)

    def generate_finite_displacements(self, out_content, in_content, n_displace):
        try:
            atoms = read(io.StringIO(out_content), format='espresso-out', index='-1')
            elements = list(set(atoms.get_chemical_symbols()))

            # 1. Ekstrak K_POINTS & CELL_PARAMETERS pakai Regex Lookahead (berhenti di blok huruf kapital berikutnya)
            cell = re.search(r'(?i)(CELL_PARAMETERS.*?)(?=\n[A-Z_]+|$)', in_content, re.S)
            kp = re.search(r'(?i)(K_POINTS.*?)(?=\n[A-Z_]+|$)', in_content, re.S)
            cell_str = f"\n{cell.group(1).strip()}\n" if cell else "\n"
            kp_str = f"\n{kp.group(1).strip()}\n" if kp else "\nK_POINTS gamma\n"

            # 2. Bersihkan template dasar & update Control/System params
            base = re.split(r'(?i)ATOMIC_SPECIES|K_POINTS|CELL_PARAMETERS|ATOMIC_POSITIONS', in_content)[0].strip()
            updates = [
                (r"(?i)(pseudo_dir\s*=\s*)['\"].*?['\"]", r"\g<1>'~/PSEUDO'"),
                (r'(?i)(nat\s*=\s*)\d+', rf'\g<1>{len(atoms)}'),
                (r'(?i)(ntyp\s*=\s*)\d+', rf'\g<1>{len(elements)}'),
                (r'(?i)starting_magnetization\(\d+\)\s*=\s*[\d\.\-]+[\n\r]*', '')
            ]
            for p, r in updates: 
                base = re.sub(p, r, base)

            # 3. Bangun ATOMIC_SPECIES & Magnetization via loop 1 baris (List Comprehension)
            p_map = {
                'Ni': 'Ni.pbe-n-rrkjus_psl.1.0.0.UPF',
                'Mn': 'Mn.pbe-spn-rrkjus_psl.1.0.0.UPF',
                'Fe': 'Fe.pbe-n-rrkjus_psl.1.0.0.UPF',
                'Co': 'Co.pbe-n-rrkjus_psl.1.0.0.UPF',
                'Cu': 'Cu.pbe-dn-rrkjus_psl.1.0.0.UPF',
                'P':  'P.pbe-n-rrkjus_psl.1.0.0.UPF',
                'O':  'O.pbe-n-rrkjus_psl.1.0.0.UPF',
                'H':  'H.pbe-rrkjus_psl.1.0.0.UPF',
                'S':  'S.pbe-n-rrkjus_psl.1.0.0.UPF'
            }

            species_str = "\n\nATOMIC_SPECIES\n" + "".join(
                f"  {el:2}  {atomic_masses[atomic_numbers[el]]:.3f}  {p_map.get(el, f'{el}.pbe-n-rrkjus_psl.1.0.0.UPF')}\n" 
                for el in elements
            )
            mag_str = "".join(f"   starting_magnetization({i}) = {1.0 if el in self.metals else 0.0}\n" 
                              for i, el in enumerate(elements, 1))
            
            # Sisipkan magnetisasi ke blok &SYSTEM
            base = re.sub(r'(?i)(&SYSTEM.*?)(/)', rf'\1{mag_str}\2', base, flags=re.S)
            header = base + species_str + kp_str + cell_str

            # 4. Generate Output Posisi Displaced
            dirs = [('x', 0, 1, 'p'), ('x', 0, -1, 'm'), ('y', 1, 1, 'p'), ('y', 1, -1, 'm'), ('z', 2, 1, 'p'), ('z', 2, -1, 'm')]
            res = {}
            for idx in range(len(atoms) - n_displace, len(atoms)):
                for ax, ax_idx, sign, suf in dirs:
                    datoms = atoms.copy()
                    datoms[idx].position[ax_idx] += self.delta * sign
                    pos = "\nATOMIC_POSITIONS angstrom\n" + "".join(
                        f"{a.symbol:4}  {a.position[0]:12.10f}  {a.position[1]:12.10f}  {a.position[2]:12.10f}\n" for a in datoms
                    )
                    res[f"PWINPUT_atm{idx+1}_{ax}{suf}"] = header + pos
            return res
        except Exception as e:
            print(f"Gen error: {e}"); return None

    def process_batch_zip(self, in_zip_bytes, tmpl_content=None):
        out_buf = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(in_zip_bytes), 'r') as zin, zipfile.ZipFile(out_buf, 'w') as zout:
            for path in [f for f in zin.namelist() if f.endswith(('.out', '.log')) and '__MACOSX' not in f]:
                if not (n := self.detect_n_from_path(path)): 
                    continue
                
                folder = os.path.dirname(path)
                out_c = zin.read(path).decode('utf-8', 'ignore')
                in_path = f"{folder}/PW.in"
                in_c = zin.read(in_path).decode('utf-8', 'ignore') if in_path in zin.namelist() else tmpl_content
                
                # Gunakan Walrus Operator (:=) untuk eksekusi dan cek hasil sekaligus
                if in_c and (dfiles := self.generate_finite_displacements(out_c, in_c, n)):
                    for fname, ftext in dfiles.items(): 
                        zout.writestr(f"{folder}/{fname}", ftext)
        return out_buf.getvalue()

class ZPEAnalyzer:
    """Logic for Step 2: Extracting Forces and Computing ZPE"""
    def __init__(self):
        # Define chemical species and their masses for OER intermediates
        raw_species = {"1-h2o": {"symbols": "OHH"}, "2-oh": {"symbols": "OH"}, "3-o": {"symbols": "O"}, "4-ooh": {"symbols": "OOH"}, "h": {"symbols": "H"}}
        self.species_params = {k: {"symbols": v["symbols"], "masses": Atoms(v["symbols"]).get_masses().tolist()} for k, v in raw_species.items()}
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
        
        zpe_data = [x for x in zpe_data if x['Site']] # Buang data yang tidak punya site (None/kosong)
        
        # Urutkan berdasarkan Site terlebih dahulu, lalu Step_Order agar 1-h2o sampai 4-ooh berurutan
        zpe_data.sort(key=lambda x: (x['Site'], x['Step_Order']))

        final_rows = []
        for site_name, group in groupby(zpe_data, key=lambda x: x['Site']):
            group_list = list(group)
            final_rows.extend(group_list)
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
    