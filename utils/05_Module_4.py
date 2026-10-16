# utils/05_Module_4.py
import io
import os
import re
import zipfile
from datetime import datetime
import numpy as np
import pandas as pd
from ase.io import read, write
from ase.units import Ry, Bohr, _hbar, _e, _amu

# Folder-to-Reaction mapping
REACTION_MAP = {
    "FeN4G_2": "* + CH2OHCHOHCH2OH → CH2OHCHOHCH2OH* (GLY*, 1)",
    "FeN4G_2A": "CH2OHCHOHCH2OH* (GLY*, 1) → CH2OHCHOCH2OH* (2A) + (H+ + e-)",
    "FeN4G_3A": "CH2OHCHOCH2OH* (2A) → CH2OHCOCH2OH* (DHA*, 3A) + (H+ + e-)",
    "FeN4G_4A": "CH2OHCOCH2OH* (DHA*, 3A) → CH2OCOCH2OH* (4A) + (H+ + e-)",
    "FeN4G_5A": "CH2OCOCH2OH* (4A) → CHOCOCH2OH* (HPAD*, 5A) + (H+ + e-)",
    "FeN4G_6A": "CHOCOCH2OH* (HPAD*, 5A) + H2O → COCH2OH* (6A) + HCOOH + (H+ + e-)",
    "FeN4G_7A": "COCH2OH* (6A) + H2O → COOHCH2OH* (GCA*, 7A) + (H+ + e-)",
    "FeN4G_8B": "COOHCH2OH* (GCA*, 7A) → COOHCHOH* (8B) + (H+ + e-)",
    "FeN4G_9B": "COOHCHOH* (8B) + H2O → 2HCOOH* (2FA*, 9B) + (H+ + e-)",
    "FeN4G_9A": "COOHCHOH* (8B) → COOHCHO* (GOA*, 9A) + (H+ + e-)",
    "FeN4G_8A": "COOHCH2OH* (GCA*, 7A) → COOHCH2O* (8A) + (H+ + e-)",
    "FeN4G_10B": "2HCOOH* (2FA*, 9B) → HCOO* (10B) + HCOOH + (H+ + e-)",
    "FeN4G_13A": "HCOO* (10B) → CO2* (13A) + (H+ + e-)",
    "FeN4G_10A": "COOHCHO* (GOA*, 9A) + H2O → COOHCHOOH* (10A) + (H+ + e-)",
    "FeN4G_11A": "COOHCHOOH* (10A) → COOHCOOH* (OA*, 11A) + (H+ + e-)",
    "FeN4G_12A": "COOHCOOH* (OA*, 11A) → COOH* (12A) + CO2 + (H+ + e-)",
    "FeN4G_2B": "CH2OHCHOHCH2OH* (1) → CH2OCHOHCH2OH* (2B) + (H+ + e-)",
    "FeN4G_3B": "CH2OCHOHCH2OH* (2B) → CHOCHOHCH2OH* (GAD*, 3B) + (H+ + e-)",
    "FeN4G_4BS1": "CHOCHOHCH2OH* (GAD*, 3B) → COCHOHCH2OH* (4B) + (H+ + e-)",
    "FeN4G_4BS2": "CHOCHOHCH2OH* (3B) + H2O → CHOOHCHOHCH2OH* (4B) + (H+ + e-)",
    "FeN4G_5B": "CHOOHCHOHCH2OH* (4B) → COOHCHOHCH2OH* (GLA*, 5B) + (H+ + e-)",
    "FeN4G_6B": "COOHCHOHCH2OH* (GLA*, 5B) + H2O → CHOOHCH2OH* (6B) + HCOOH + (H+ + e-)",
    "FeN4G_6E": "COOHCHOHCH2OH* (GLA*, 5B) → COOHCHOCH2OH* (6E) + (H+ + e-)",
    "FeN4G_6F": "COOHCHOHCH2OH* (GLA*, 5B) → COOHCHOH-CH2O* (6F) + (H+ + e-)",
    "FeN4G_3CS0": "CH2OHCHOCH2OH* (2A) → CHOCH2OH* + HCHO* (GCAD* + FAD*, 3C) + (H+ + e-)",
    "FeN4G_4C": "CHOCH2OH* + HCHO* (GCAD* + FAD*, 3C) → CHOCH2OH* + CH2OOH* (4C) + (H+ + e-)",
    "FeN4G_5Cv2": "CHOCH2OH* + CH2OOH* (4C) → CHOCH2OH* (GCAD*, 5C) + HCOOH + (H+ + e-)",
    "FeN4G_6H": "CHOCH2OH* (5C) → CH2OH* (6H) + HCOOH + (H+ + e-)",
    "FeN4G_7H": "CH2OH* (6H) → HCHO* (FAD*, 7H) + (H+ + e-)",
    "FeN4G_10K": "HCHO* (FAD*, 7H) + H2O → CH2OOH* (10K) + (H+ + e-)",
    "FeN4G_6DS2": "CHOCOCH2OH* (HPAD*, 5A) + H2O → CHOOHCOCH2OH* (6D) + (H+ + e-)",
    "FeN4G_6DS1": "CHOCOCH2OH* (HPAD*, 5A) → COCOCH2OH* (6D) + (H+ + e-)",
    "FeN4G_6C": "CHOCOCH2OH* (HPAD*, 5A) + H2O → CHO* + COOHCH2OH* (6C) + (H+ + e-)",
    "FeN4G_7E": "CHOOHCOCH2OH* (6D) → COOHCOCH2OH* (HPA*, 7E) + (H+ + e-)",
    "FeN4G_4D": "CHOCHOHCH2OH* (GAD*, 3B) + H2O → CHOHCH2OH* (4D) + HCOOH + (H+ + e-)",
    "FeN4G_5C": "CHOHCH2OH* (4D) → CHOCH2OH* (GCAD*, 5C) + (H+ + e-)",
    "FeN4G_7G": "COOHCHOCH2OH* (6E) → COOHCHO* + HCHO* (GOA* + FAD*, 7G) + (H+ + e-)",
    "FeN4G_7F": "COOHCHOHCH2O* (6F) → COOHCHOHCHO* (HPPA*, 7F) + (H+ + e-)",
    "FeN4G_8FS1": "COOHCHOHCHO* (7F) → COOHCHOHCO* (8F) + (H+ + e-)",
    "FeN4G_8FS2": "COOHCHOHCHO* (HPPA*, 7F) + H2O → COOHCHOHCHOOH* (8F) + (H+ + e-)",
    "FeN4G_9F": "COOHCHOHCO* (8F) + H2O → COOHCHOHCOOH* (TTA*, 9F) + (H+ + e-)",
    "FeN4G_10F": "COOHCHOHCOOH* (TTA*, 9F) → COOHCHOCOOH* (10F) + (H+ + e-)",
    "FeN4G_11F": "COOHCHOCOOH* (10F) → COOHCOCOOH* (MA*, 11F) + (H+ + e-)",
    "FeN4G_10E": "COOHCOCOOH* (MA*, 11F) → COCOOH* (10E) + CO2 + (H+ + e-)",
    "FeN4G_8G": "COOHCHO* + HCHO* (GOA* + FAD*, 7G) → COOHCHO* + CH2OOH* (8G) + (H+ + e-)",
    "FeN4G_8E": "COOHCOCH2OH* (HPA*, 7E) → COOHCOCH2O* (8E) + (H+ + e-)",
    "FeN4G_9E": "COOHCOCH2O* (8E) → COOHCOCHO* (DOPA*, 9E) + (H+ + e-)",
    "FeN4G_10J": "COOHCOCHO* (DOPA*, 9E) → COOHCOCO* (10J) + (H+ + e-)",
    "FeN4G_10H": "COOHCOCHO* (DOPA*, 9E) + H2O → COOCHO* (10H) + HCOOH + (H+ + e-)",
    "FeN4G_8H": "COOHCOCH2OH* (HPA*, 7E) + H2O → COOCH2OH* (8H) + HCOOH + (H+ + e-)",
    "FeN4G_9H": "COOCH2OH* (8H) → COOCH2O* (9H) + (H+ + e-)",
    "FeN4G_9K": "COOCH2OH* (8H) + H2O → CH2OHOH* (9K) + CO2 + (H+ + e-)",
    "FeN4G_11K": "CH2OOH* (10K) → HCOOH* (FA*, 11K) + (H+ + e-)",
    "FeN4G_8I": "COOHCOCH2OH* (HPA*, 7E) + H2O → COOH* (8I) + COOHCH2OH* + (H+ + e-)"
}

class ExcelLogManager:
    """Safely updates the tracking Excel file and appends audit backups to a .txt log."""
    
    EXCEL_COLUMNS = ["Path Name", "Reaction Name", "Energy", "ZPE", "Vibration Mode"]

    @classmethod
    def load_or_create_excel(cls, excel_bytes: bytes = None) -> pd.DataFrame:
        if excel_bytes and len(excel_bytes) > 0:
            try:
                return pd.read_excel(io.BytesIO(excel_bytes))
            except Exception:
                pass
        return pd.DataFrame(columns=cls.EXCEL_COLUMNS)

    @classmethod
    def backup_to_log(cls, existing_df: pd.DataFrame, log_content: str = "", overwrite_count: int = 1) -> str:
        """Appends the prior state of the DataFrame to a persistent text log."""
        if existing_df.empty:
            return log_content
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"\n{'='*70}\n"
        record += f"OVERWRITE #{overwrite_count} | DATE: {timestamp}\n"
        record += f"{'='*70}\n"
        record += existing_df.to_string(index=False)
        record += "\n\n"
        return log_content + record

    @classmethod
    def export_excel(cls, df: pd.DataFrame) -> bytes:
        out_buf = io.BytesIO()
        with pd.ExcelWriter(out_buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Vibrational_Summary')
        return out_buf.getvalue()


class ZPEManager:
    def __init__(self, delta: float = 0.01):
        self.delta = delta

    @staticmethod
    def extract_final_energy(out_content: str) -> float:
        """Extracts the final total energy from a QE output file in Ry."""
        matches = re.findall(r'!\s+total energy\s+=\s+([-+]?\d*\.\d+|\d+)\s+Ry', out_content)
        if matches:
            return float(matches[-1])
        return np.nan

    @staticmethod
    def identify_reaction(folder_name: str) -> str:
        clean_name = os.path.basename(folder_name.strip('/'))
        if clean_name in REACTION_MAP:
            return REACTION_MAP[clean_name]
        for k, v in REACTION_MAP.items():
            if k.lower() in clean_name.lower():
                return v
        return f"Surface Intermediate ({clean_name})"

    def process_batch_zip(self, input_zip_bytes: bytes, boundary_idx: int, existing_excel_bytes: bytes = None, log_text: str = "", overwrite_count: int = 0):
        """
        Scans each folder in the input zip, looks for PW.in and PW.out,
        displaces atoms with 1-based index > boundary_idx, creates GEOM.xyz,
        and initializes/appends to Vibration_Analysis.xlsx with backup logging.
        """
        output_buffer = io.BytesIO()
        df_excel = ExcelLogManager.load_or_create_excel(existing_excel_bytes)
        
        # Audit log backup if overwriting populated records
        if not df_excel.empty:
            overwrite_count += 1
            log_text = ExcelLogManager.backup_to_log(df_excel, log_text, overwrite_count)

        with zipfile.ZipFile(io.BytesIO(input_zip_bytes), 'r') as in_zip:
            # Map files to directories
            folder_groups = {}
            for name in in_zip.namelist():
                if name.endswith('/') or '__MACOSX' in name or '.DS_Store' in name:
                    continue
                parent = os.path.dirname(name)
                folder_groups.setdefault(parent, []).append(name)

            with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as out_zip:
                for folder, file_list in folder_groups.items():
                    # Identify PW.in and PW.out in this folder
                    pw_in_file = next((f for f in file_list if os.path.basename(f).lower() == 'pw.in' or f.lower().endswith('.in')), None)
                    pw_out_file = next((f for f in file_list if os.path.basename(f).lower() == 'pw.out' or f.lower().endswith('.out')), None)

                    if not pw_out_file or not pw_in_file:
                        continue

                    in_content = in_zip.read(pw_in_file).decode('utf-8', errors='ignore')
                    out_content = in_zip.read(pw_out_file).decode('utf-8', errors='ignore')

                    # Parse relaxed structure
                    try:
                        atoms = read(io.StringIO(out_content), format='espresso-out', index='-1')
                    except Exception:
                        continue

                    total_atoms = len(atoms)
                    # All atoms > boundary_idx (1-based) will be displaced
                    displace_indices = [i for i in range(total_atoms) if (i + 1) > boundary_idx]
                    if not displace_indices:
                        continue

                    # Copy original files
                    out_zip.writestr(f"{folder}/PW.in", in_content)
                    out_zip.writestr(f"{folder}/PW.out", out_content)

                    # Export GEOM.xyz
                    xyz_io = io.StringIO()
                    write(xyz_io, atoms, format='xyz')
                    out_zip.writestr(f"{folder}/GEOM.xyz", xyz_io.getvalue())

                    # Prepare QE template header
                    template_adjusted = re.sub(r'(nat\s*=\s*)\d+', rf'\g<1>{total_atoms}', in_content, flags=re.IGNORECASE)
                    template_clean = re.split(r'ATOMIC_POSITIONS', template_adjusted, flags=re.IGNORECASE)[0].strip()

                    directions = [
                        ('x', 0, 1, 'p'), ('x', 0, -1, 'm'),
                        ('y', 1, 1, 'p'), ('y', 1, -1, 'm'),
                        ('z', 2, 1, 'p'), ('z', 2, -1, 'm')
                    ]

                    # Generate 6 displacement files per vibrated atom
                    for idx in displace_indices:
                        qe_idx = idx + 1
                        for axis, axis_idx, sign, suffix in directions:
                            displaced_atoms = atoms.copy()
                            displaced_atoms[idx].position[axis_idx] += self.delta * sign

                            pos_block = "\n\nATOMIC_POSITIONS {angstrom}\n"
                            for atom in displaced_atoms:
                                pos_block += f"{atom.symbol:4} {atom.position[0]:12.8f} {atom.position[1]:12.8f} {atom.position[2]:12.8f}\n"

                            # Pattern: PWINPUT_atm157_xm
                            filename = f"PWINPUT_atm{qe_idx}_{axis}{suffix}"
                            out_zip.writestr(f"{folder}/{filename}", template_clean + pos_block)

                    # Extract final energy and update Excel
                    final_e = self.extract_final_energy(out_content)
                    rxn_name = self.identify_reaction(folder)
                    
                    # Update row or append
                    if folder in df_excel['Path Name'].values:
                        r_idx = df_excel[df_excel['Path Name'] == folder].index[0]
                        df_excel.at[r_idx, 'Reaction Name'] = rxn_name
                        df_excel.at[r_idx, 'Energy'] = final_e
                    else:
                        new_row = {
                            "Path Name": folder,
                            "Reaction Name": rxn_name,
                            "Energy": final_e,
                            "ZPE": np.nan,
                            "Vibration Mode": ""
                        }
                        df_excel = pd.concat([df_excel, pd.DataFrame([new_row])], ignore_index=True)

        output_buffer.seek(0)
        excel_bytes = ExcelLogManager.export_excel(df_excel)
        return output_buffer.getvalue(), excel_bytes, log_text, overwrite_count


class ZPEAnalyzer:
    def __init__(self, delta: float = 0.01):
        self.delta = delta

    @staticmethod
    def _read_forces(zf: zipfile.ZipFile, filepath: str, idx_move: list) -> np.ndarray:
        """Parses QE forces for requested 1-based atom indices."""
        forces = np.zeros((len(idx_move), 3))
        try:
            with zf.open(filepath) as f:
                lines = f.read().decode('utf-8', errors='ignore').splitlines()
        except Exception:
            return forces

        it = iter(lines)
        for line in it:
            if 'Forces acting' in line:
                while 'type' not in line:
                    try: line = next(it)
                    except StopIteration: break
                ia = 0
                while True:
                    try: line = next(it)
                    except StopIteration: break
                    parts = line.split()
                    if len(parts) >= 9 and parts[0] == 'atom':
                        if int(parts[1]) in idx_move:
                            forces[ia] = [
                                float(parts[6]) * Ry / Bohr,
                                float(parts[7]) * Ry / Bohr,
                                float(parts[8]) * Ry / Bohr
                            ]
                            ia += 1
                    else:
                        break
        return forces

    def compute_zpe_and_modes(self, zf: zipfile.ZipFile, folder_path: str, idx_move: list, atomic_masses: list):
        """Constructs Hessian using finite differences and computes frequencies."""
        m = np.array(atomic_masses)
        n = 3 * len(idx_move)
        H = np.zeros((n, n))
        r = 0

        for a in idx_move:
            for axis in 'xyz':
                # Accept both LOG_atm157_xm or atom1_x_minus.out
                fm_candidates = [
                    f"{folder_path}/LOG_atm{a}_{axis}m",
                    f"{folder_path}/PWINPUT_atm{a}_{axis}m.out",
                    f"{folder_path}/atom{a}_{axis}_minus.out"
                ]
                fp_candidates = [
                    f"{folder_path}/LOG_atm{a}_{axis}p",
                    f"{folder_path}/PWINPUT_atm{a}_{axis}p.out",
                    f"{folder_path}/atom{a}_{axis}_plus.out"
                ]

                f_m = next((c for c in fm_candidates if c in zf.namelist()), fm_candidates[0])
                f_p = next((c for c in fp_candidates if c in zf.namelist()), fp_candidates[0])

                fm_forces = self._read_forces(zf, f_m, idx_move)
                fp_forces = self._read_forces(zf, f_p, idx_move)

                H[r] = 0.5 * (fm_forces - fp_forces).ravel() / (2.0 * self.delta)
                r += 1

        H = 0.5 * (H + H.T)
        im = np.repeat(m**-0.5, 3)
        omega2, _ = np.linalg.eigh(im[:, None] * H * im)
        
        # Unit conversion to eV
        s = _hbar * 1e10 / np.sqrt(_e * _amu)
        hnu = s * omega2.astype(complex)**0.5
        
        # Mode frequencies in cm^-1 (1 eV = 8065.544 cm^-1)
        modes_cm = [f"{(freq * 8065.544):.1f}" for freq in hnu.real if freq > 0]
        modes_str = ", ".join(modes_cm)
        zpe_val = float(0.5 * hnu.real.sum())

        return zpe_val, modes_str

    def process_extraction_zip(self, zip_bytes: bytes, boundary_idx: int, existing_excel_bytes: bytes, log_text: str = "", overwrite_count: int = 0):
        """Extracts forces from completed calculations, computes ZPE, and populates the Excel sheet."""
        df_excel = ExcelLogManager.load_or_create_excel(existing_excel_bytes)
        
        if not df_excel.empty and df_excel['ZPE'].notna().any():
            overwrite_count += 1
            log_text = ExcelLogManager.backup_to_log(df_excel, log_text, overwrite_count)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            # Find folders with output logs
            all_files = zf.namelist()
            log_folders = {
                os.path.dirname(f) for f in all_files 
                if ("LOG_atm" in f or "PWINPUT_atm" in f) and not f.endswith('/')
            }

            for folder in log_folders:
                # Find base PW.out in this folder or higher-order folder to get atomic masses
                pw_out = next((f for f in all_files if f.startswith(folder) and f.endswith(('PW.out', '.out')) and 'LOG' not in f and 'PWINPUT' not in f), None)
                if not pw_out:
                    continue

                try:
                    atoms = read(io.StringIO(zf.read(pw_out).decode('utf-8', errors='ignore')), format='espresso-out', index='-1')
                except Exception:
                    continue

                total_atoms = len(atoms)
                displace_indices = [i for i in range(total_atoms) if (i + 1) > boundary_idx]
                if not displace_indices:
                    continue

                idx_move = [i + 1 for i in displace_indices]
                masses = [atoms[i].mass for i in displace_indices]

                try:
                    zpe_val, modes_str = self.compute_zpe_and_modes(zf, folder, idx_move, masses)
                    matched_path = next((p for p in df_excel['Path Name'] if p in folder or folder in p), folder)

                    if matched_path in df_excel['Path Name'].values:
                        r_idx = df_excel[df_excel['Path Name'] == matched_path].index[0]
                        df_excel.at[r_idx, 'ZPE'] = zpe_val
                        df_excel.at[r_idx, 'Vibration Mode'] = modes_str
                    else:
                        new_row = {
                            "Path Name": matched_path,
                            "Reaction Name": ZPEManager.identify_reaction(folder),
                            "Energy": ZPEManager.extract_final_energy(zf.read(pw_out).decode('utf-8', errors='ignore')),
                            "ZPE": zpe_val,
                            "Vibration Mode": modes_str
                        }
                        df_excel = pd.concat([df_excel, pd.DataFrame([new_row])], ignore_index=True)
                except Exception:
                    continue

        excel_bytes = ExcelLogManager.export_excel(df_excel)
        return df_excel, excel_bytes, log_text, overwrite_count