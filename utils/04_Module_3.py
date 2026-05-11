# utils/04_Module_3.py
import io
import zipfile
import re
import numpy as np
import pandas as pd
from itertools import groupby
import ase
from ase import Atom
from ase.constraints import FixAtoms
from ase.io import read, write
from ase.data import atomic_masses, atomic_numbers
# Add at the top of 04_Module_3.py
import os


class AdsorbateGenerator:
    def __init__(self):
        self.base_atoms = None
        self.slab_fixed_indices = []
        self.base_template = ""
        self.base_cell_str = ""
        
        # --- Group A (y > 0.5 * lattice_y) ---
        self.offsets_A = {
            "H2O":  [("O", -0.60,  0.00, 1.80), ("H", -1.30,  0.60, 2.00), ("H", -1.30, -0.60, 2.00)],
            "OH1":  [("O", -0.60,  0.00, 1.80), ("H", -1.30,  0.60, 2.00)],
            "OH2":  [("O", -0.60,  0.00, 1.80), ("H", -1.30, -0.60, 2.00)],
            "O":    [("O", -0.80,  0.00, 1.60)],
            "OOH1": [("O", -1.03, -0.82, 1.25), ("O", -1.31, -0.09, 2.38), ("H", -2.15,  0.40, 2.08)],
            "OOH2": [("O", -1.03,  0.82, 1.25), ("O", -1.31,  0.09, 2.38), ("H", -2.15, -0.40, 2.08)],
            "H":    [("H",  0.00,  0.00, 1.00)]
        }

        # --- Group B (y < 0.5 * lattice_y) ---
        self.offsets_B = {
            "H2O":  [("O",  0.60,  0.00, 1.80), ("H",  1.30,  0.60, 2.00), ("H",  1.30, -0.60, 2.00)],
            "OH1":  [("O",  0.60,  0.00, 1.80), ("H",  1.30,  0.60, 2.00)],
            "OH2":  [("O",  0.60,  0.00, 1.80), ("H",  1.30, -0.60, 2.00)],
            "O":    [("O",  0.80,  0.00, 1.60)],
            "OOH1": [("O",  1.03, -0.84, 1.24), ("O",  1.34, -0.14, 2.37), ("H",  2.17,  0.37, 2.07)],
            "OOH2": [("O",  1.03,  0.84, 1.24), ("O",  1.34,  0.14, 2.37), ("H",  2.17, -0.37, 2.07)],
            "H":    [("H",  0.00,  0.00, 1.00)]
        }

    def load_slab(self, uploaded_zip_bytes):
        self.slabs_data = []
        try:
            with zipfile.ZipFile(io.BytesIO(uploaded_zip_bytes), 'r') as z:
                filenames = z.namelist()
                out_files = [
                    f for f in filenames
                    if (f.endswith('.out') or f.endswith('.log'))
                    and not f.startswith('__MACOSX')
                ]
                if not out_files:
                    return False

                for out_file in out_files:
                    folder_path = os.path.dirname(out_file)  # e.g. "slab-NiFePO-MM"

                    out_content = z.read(out_file).decode('utf-8', errors='ignore')
                    atoms = read(io.StringIO(out_content), format='espresso-out', index='-1')

                    # Find matching .in file in the same folder
                    in_files = [
                        f for f in filenames
                        if os.path.dirname(f) == folder_path and f.endswith('.in')
                    ]

                    base_template = "&CONTROL\n   pseudo_dir = '~/PSEUDO'\n/\n&SYSTEM\n/\n"
                    base_cell_str = "\n"

                    if in_files:
                        in_content = z.read(in_files[0]).decode('utf-8', errors='ignore')

                        # Extract CELL_PARAMETERS block
                        cell_match = re.search(
                            r'(?i)(CELL_PARAMETERS.*?)(?=ATOMIC_SPECIES|K_POINTS|ATOMIC_POSITIONS|$)',
                            in_content, re.DOTALL
                        )
                        if cell_match:
                            base_cell_str = "\n" + cell_match.group(1).strip() + "\n"

                        cards_pattern = re.compile(
                            r'(?i)(ATOMIC_SPECIES|K_POINTS|CELL_PARAMETERS|ATOMIC_POSITIONS)'
                        )
                        base_template = cards_pattern.split(in_content)[0].strip()
                        base_template = re.sub(
                            r"(?i)(pseudo_dir\s*=\s*)['\"].*?['\"]",
                            r"\g<1>'~/PSEUDO'", base_template
                        )

                    # Fixed indices: bottom 66% of z-range
                    z_coords = atoms.positions[:, 2]
                    min_z, max_z = z_coords.min(), z_coords.max()
                    cutoff = min_z + (max_z - min_z) * 0.66
                    fixed_indices = [i for i, z_val in enumerate(z_coords) if z_val <= cutoff]

                    self.slabs_data.append({
                        'atoms': atoms,
                        'template': base_template,
                        'cell_str': base_cell_str,
                        'fixed_indices': fixed_indices,
                        'folder': folder_path,   # "slab-NiFePO-MM"
                    })

            return bool(self.slabs_data)

        except Exception as e:
            print(f"Error loading ZIP: {e}")
            return False

    def find_top_sites(self, atoms, symbols, n_total):
        eligible = []
        for atom in atoms:
            if atom.symbol in symbols:
                eligible.append({
                    'symbol': atom.symbol,
                    'z_coord': atom.position[2],
                    'index_ase': atom.index,
                    'index_qe': atom.index + 1,
                    'position': atom.position,
                })
        sorted_atoms = sorted(eligible, key=lambda x: x['z_coord'], reverse=True)
        return sorted_atoms[:n_total]
    
    def build_adsorbates_zip(self, selected_sites, reaction_package="OER", custom_variants=None):
        output_buffer = io.BytesIO()
        
        pseudo_map = {
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

        # Tentukan variant berdasarkan package yang dipilih
        if reaction_package == "OER":
            variants = {"1-h2o": ["H2O"], "2-oh": ["OH1", "OH2"], "3-o": ["O"], "4-ooh": ["OOH1", "OOH2"]}
        elif reaction_package == "HER":
            variants = {"1-h": ["H"]}
        elif reaction_package == "Custom" and custom_variants is not None:
            variants = custom_variants
        else:
            variants = {"1-ads": ["O"]} 

        # lattice_y = self.base_atoms.cell.lengths()[1]
        metals_list = ['Ni', 'Fe', 'Mn', 'Co', 'Cu', 'Pd', 'Pt', 'Ag', 'Au', 'Ru', 'Rh', 'Ir', 'Os', 'V', 'Cr', 'Ti', 'Sc', 'Zn']
        
        with zipfile.ZipFile(output_buffer, 'w') as zf:
            for slab_idx, slab in enumerate(self.slabs_data):
                atoms       = slab['atoms']
                template    = slab['template']
                cell_str    = slab['cell_str']
                fixed_idx   = slab['fixed_indices']
                folder      = slab['folder']           # root: "slab-NiFePO-MM"
                lattice_y   = atoms.cell.lengths()[1]
                sites       = selected_sites.get(slab_idx, [])

                for site in sites:
                    ref_pos   = atoms[site['index_ase']].position
                    site_name = f"{site['symbol']}-{site['index_qe']}"
                    active_offsets = self.offsets_A if ref_pos[1] > 0.5 * lattice_y else self.offsets_B

                    for step_folder, ads_list in variants.items():
                        for ads_type in ads_list:
                            new_atoms = atoms.copy()
                            if ads_type in active_offsets:
                                for elem, dx, dy, dz in active_offsets[ads_type]:
                                    new_pos = [ref_pos[0]+dx, ref_pos[1]+dy, ref_pos[2]+dz]
                                    new_atoms.append(Atom(elem, position=new_pos))
                            else:
                                print(f"Warning: offset for '{ads_type}' not found, skipping.")
                                continue

                            # --- Build PW.in (same logic as original, using per-slab template) ---
                            unique_elements = list(set(new_atoms.get_chemical_symbols()))
                            ntyp_new = len(unique_elements)
                            cards_pattern = re.compile(r'(?i)(ATOMIC_SPECIES|K_POINTS|CELL_PARAMETERS|ATOMIC_POSITIONS)')
                            template_clean = cards_pattern.split(template)[0].strip()
                            template_clean = re.sub(r'(?i)starting_magnetization\(\d+\)\s*=\s*[\d\.\-]+[\n\r]*', '', template_clean)
                            template_clean = re.sub(r'(?i)(nat\s*=\s*)\d+',  r'\g<1>' + str(len(new_atoms)),  template_clean)
                            template_clean = re.sub(r'(?i)(ntyp\s*=\s*)\d+', r'\g<1>' + str(ntyp_new), template_clean)

                            new_species_str = "\n\nATOMIC_SPECIES\n"
                            mag_str = ""
                            for i, el in enumerate(unique_elements, 1):
                                mass   = atomic_masses[atomic_numbers[el]]
                                pseudo = pseudo_map.get(el, f"{el}.UPF")
                                new_species_str += f"  {el}  {mass:.3f}  {pseudo}\n"
                                mag_val = 1.0 if el in metals_list else 0.0
                                mag_str += f"   starting_magnetization({i}) = {mag_val}\n"

                            system_match = re.search(r'(?i)(&SYSTEM.*?)(/)', template_clean, re.DOTALL)
                            if system_match:
                                new_system = system_match.group(1) + mag_str + system_match.group(2)
                                template_clean = template_clean.replace(system_match.group(0), new_system)

                            if 'dipfield' not in template_clean.lower():
                                template_clean = re.sub(r'(?i)(&CONTROL)', r'\1\n   dipfield = .true.\n   tefield = .true.', template_clean, count=1)
                            if 'edir' not in template_clean.lower():
                                template_clean = re.sub(r'(?i)(&SYSTEM)', r'\1\n   edir = 3\n   emaxpos = 0.75\n   eamp = 0.001', template_clean, count=1)

                            pos_str = "\nATOMIC_POSITIONS angstrom\n"
                            for i, atom in enumerate(new_atoms):
                                fix_flag = "0 0 0" if i in fixed_idx else ""
                                pos_str += f"{atom.symbol}  {atom.position[0]:.10f} {atom.position[1]:.10f} {atom.position[2]:.10f}  {fix_flag}\n"

                            kpoints_str = "\nK_POINTS gamma\n"
                            final_in = template_clean + new_species_str + kpoints_str + cell_str + pos_str

                            # --- Path: folder/site/step[/ads_type if multiple] ---
                            if len(ads_list) > 1:
                                path = f"{folder}/{site_name}/{step_folder}/{ads_type}"
                            else:
                                path = f"{folder}/{site_name}/{step_folder}"

                            v_buf = io.StringIO()
                            write(v_buf, new_atoms, format='vasp')
                            zf.writestr(f"{path}/PW.in", final_in)
                            zf.writestr(f"{path}/input.vasp", v_buf.getvalue())
            
        output_buffer.seek(0)
        return output_buffer.getvalue()
    
class AdsorbateAnalyzer:
    """Logic for Step 2: Analyzing OER Adsorbate Results"""
    def __init__(self):
        # Definisikan urutan agar tabel rapi dari slab -> ooh
        self.step_order = {
            "slab": 0, "surface": 0,
            "1-h2o": 1, "2-oh": 2, "3-o": 3, "4-ooh": 4
        }
        self.site_pattern = r"([A-Z][a-z]?-\d+)"

    def _parse_path_info(self, path: str):
        """
        Extracts Step, Site, and Termination (Atas/Bawah) from file path.
        """
        lower_path = path.lower()
        parts = path.split('/')
        
        # 1. Tentukan Step (Reaksi)
        step = "unknown"
        if "slab" in lower_path or "surface" in lower_path: 
            step = "slab"
        else:
            for key in ["1-h2o", "2-oh", "3-o", "4-ooh"]:
                if key in lower_path: 
                    step = key
                    break
        
        # 2. Tentukan Terminasi (Atas/Bawah)
        termination = "unknown"  # lower_path membuat path menjadi huruf kecil semua. Jadi kita bisa mendeteksi "nim" atau "mm" tanpa khawatir tentang kapitalisasi.
        if "nim" in lower_path: termination = "NiM_termination"
        elif "mm" in lower_path: termination = "MM_termination"

        # 3. Tentukan Site (Contoh: Fe-54)
        site = None
        for part in reversed(parts):
            match = re.search(self.site_pattern, part)
            if match: 
                site = match.group(1)
                break
        
        return step, site, termination

    def process_zip(self, zip_bytes):
        adsorbates_data = []
        slabs_map = {}

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            out_files = [f for f in z.namelist() if f.endswith((".out", ".log")) and not "__MACOSX" in f]
            
            for path in out_files:
                try:
                    content = z.read(path).decode("utf-8", errors='ignore')
                except: continue
                
                # Ekstrak Final energy
                match_final = re.search(r'(?i)Final\s+energy\s*=\s*([-.\d]+)\s*Ry', content)
                
                if match_final:
                    energy_ry = float(match_final.group(1))
                else:
                    matches_total = re.findall(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content, re.IGNORECASE)
                    if matches_total: energy_ry = float(matches_total[-1])
                    else: continue
                
                step, site, term = self._parse_path_info(path)
                
                record = {
                    "Path": path, 
                    "Energy (Ry)": energy_ry,
                    "Step": step, 
                    "Step_Order": self.step_order.get(step, 99),
                    "Site": site, 
                    "Termination": term
                }

                # Simpan slab di dictionary tersendiri berdasarkan terminasi (atas/bawah)
                if step == "slab": slabs_map[term] = record
                else: adsorbates_data.append(record)

        if not adsorbates_data: return pd.DataFrame()

        # --- PENGELOMPOKKAN (GROUPING) ---
        final_rows = []
        adsorbates_data = [x for x in adsorbates_data if x['Site']]
        adsorbates_data.sort(key=lambda x: x['Site'])

        for site_name, group in groupby(adsorbates_data, key=lambda x: x['Site']):
            group_list = list(group)
            term = group_list[0]['Termination']
            
            # 1. Masukkan baris referensi Slab untuk terminasi site ini
            if term in slabs_map:
                s_rec = slabs_map[term].copy()
                s_rec['Site'] = site_name
                final_rows.append(s_rec)
            
            # 2. Masukkan data adsorbat yang sudah diurutkan (H2O -> OOH)
            group_list.sort(key=lambda x: x['Step_Order'])
            final_rows.extend(group_list)
            
            # 3. Baris pemisah (Spacer baris kosong)
            final_rows.append({"Path": None, "Step": None, "Site": None, "Energy (Ry)": None})
            
        return pd.DataFrame(final_rows)

    def generate_excel(self, df):
        output = io.BytesIO()
        
        # Susun urutan kolom agar sesuai dengan adsorbate_energies.xlsx
        target_cols = ['Path', 'Step', 'Site', 'Energy (Ry)']
        cols = [c for c in target_cols if c in df.columns]
        df_exp = df[cols]

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Ubah nama Sheet menjadi 'Final Energies'
            df_exp.to_excel(writer, index=False, sheet_name='Final Energies')
            
            # Formatting lebar kolom
            ws = writer.sheets['Final Energies']
            fmt = writer.book.add_format({'num_format': '0.000000'})
            
            for i, col in enumerate(df_exp.columns):
                # Cari lebar teks maksimum di kolom, atau gunakan panjang header
                lengths = df_exp[col].dropna().astype(str).map(len)
                max_len = lengths.max() if not lengths.empty else len(col)
                max_len = max(max_len, len(col))
                width = min(max_len + 2, 60)
                ws.set_column(i, i, width, fmt if col == 'Energy (Ry)' else None)

        return output.getvalue()
    
    def calculate_adsorption_energies(self, df, isolated_energies_ry):
        RY_TO_EV = 13.605698066
        df_clean = df.dropna(subset=['Step', 'Site', 'Energy (Ry)'])
        
        # [CLEAN CODE] 1. Pandas Idiom: Ekstrak Slab Energies tanpa perlu for-loop iterrows
        slabs = dict(df_clean[df_clean['Step'] == 'slab'].set_index('Site')['Energy (Ry)'])
        
        # [CLEAN CODE] 2. Map Dictionary: Menggantikan if-elif yang memanjang ke bawah
        step_map = {'1-h2o': 'H2O', '2-oh': 'OH', '3-o': 'O', '4-ooh': 'OOH'}
        
        ads_results = []
        for _, row in df_clean[df_clean['Step'] != 'slab'].iterrows():
            step, site, e_sys = row['Step'], row['Site'], row['Energy (Ry)']
            mol_key = step_map.get(step)
            
            # [CLEAN CODE] 3. Guard Clause: Skip data yang cacat secara satu baris
            if not mol_key or mol_key not in isolated_energies_ry or site not in slabs:
                continue 
                
            e_slab, e_iso = slabs[site], isolated_energies_ry[mol_key]
            
            ads_results.append({
                'Site': site, 'Step': step,
                'E_sys (Ry)': e_sys, 'E_slab (Ry)': e_slab, 'E_iso (Ry)': e_iso,
                'E_ads (eV)': (e_sys*RY_TO_EV - e_slab*RY_TO_EV - e_iso*RY_TO_EV)
            })
            
        return pd.DataFrame(ads_results).sort_values(by=['Site', 'Step']) if ads_results else pd.DataFrame()

    def generate_adsorption_excel(self, df_ads, isolated_energies_ry, catalyst_name="Unknown"):
        """
        Mengekspor hasil energi adsorpsi ke Excel ke dalam 2 Sheet terpisah:
        1. Detailed_Data: Energi terisolasi & tabel adsorpsi format vertikal
        2. Summary: Tabel ringkasan pivoted untuk diplot
        """
        output = io.BytesIO()
        RY_TO_EV = 13.605698066
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Buat dua sheet terpisah
            ws_details = workbook.add_worksheet('Detailed_Data')
            ws_sum = workbook.add_worksheet('Summary')
            
            bold = workbook.add_format({'bold': True})
            float_fmt = workbook.add_format({'num_format': '0.000000'})
            header_fmt = workbook.add_format({'bold': True, 'bottom': 1})
            
            # ==============================================================
            # SHEET 1: DETAILED DATA
            # ==============================================================
            
            # --- 1. Tulis info Isolated Molecules ---
            ws_details.write('A1', 'Reference Isolated Molecules', bold)
            ws_details.write('A2', 'Molecule', bold)
            ws_details.write('B2', 'Energy (Ry)', bold)
            ws_details.write('C2', 'Energy (eV)', bold)
            
            row_idx = 2
            for mol, e_ry in isolated_energies_ry.items():
                ws_details.write(row_idx, 0, mol)
                ws_details.write(row_idx, 1, e_ry, float_fmt)
                ws_details.write(row_idx, 2, e_ry * RY_TO_EV, float_fmt)
                row_idx += 1
                
            row_idx += 2 
            
            # --- 2. Tulis Tabel Adsorpsi (Format Vertikal Asli) ---
            if not df_ads.empty:
                columns = list(df_ads.columns)
                for col_num, value in enumerate(columns):
                    ws_details.write(row_idx, col_num, value, header_fmt)
                row_idx += 1
                
                for site_name, group in groupby(df_ads.to_dict('records'), key=lambda x: x['Site']):
                    for record in group:
                        for col_num, col_name in enumerate(columns):
                            val = record[col_name]
                            if isinstance(val, (int, float)):
                                ws_details.write(row_idx, col_num, val, float_fmt)
                            else:
                                ws_details.write(row_idx, col_num, val if val else "")
                        row_idx += 1
                    row_idx += 1 
            
            # Set lebar kolom untuk sheet 1
            ws_details.set_column('A:A', 15)
            ws_details.set_column('B:G', 20)

            # ==============================================================
            # SHEET 2: VOLCANO SUMMARY
            # ==============================================================
            
            if not df_ads.empty:
                # --- 3. [NEW] Tulis Tabel Ringkasan (Pivoted) ---
                sum_row_idx = 0  # Reset index baris untuk sheet baru
                ws_sum.write(sum_row_idx, 0, "Summary", bold)
                sum_row_idx += 2
                
                # Gunakan fungsi pivot bawaan Pandas
                df_pivot = df_ads.pivot(index='Site', columns='Step', values='E_ads (eV)').reset_index()
                
                # Ubah nama kolom langkah (1-h2o dsb) menjadi standar Eads_X
                rename_map = {'1-h2o': 'Eads_H2O', '2-oh': 'Eads_OH', '3-o': 'Eads_O', '4-ooh': 'Eads_OOH'}
                df_pivot.rename(columns=rename_map, inplace=True)
                
                # Pastikan 4 kolom target selalu ada, isi dengan NaN (kosong) jika suatu adsorbat terlewat
                target_cols = ['Eads_H2O', 'Eads_OH', 'Eads_O', 'Eads_OOH']
                for col in target_cols:
                    if col not in df_pivot.columns:
                        df_pivot[col] = np.nan
                        
                # Sisipkan nama katalis ke kolom paling depan
                df_pivot.insert(0, 'Catalyst', catalyst_name)
                
                # Susun ulang urutan kolom
                final_cols = ['Catalyst', 'Site'] + target_cols
                df_pivot = df_pivot[final_cols]
                
                # Cetak Header Tabel Pivot
                for col_num, col_name in enumerate(final_cols):
                    ws_sum.write(sum_row_idx, col_num, col_name, header_fmt)
                sum_row_idx += 1
                
                # Cetak Baris Data Pivot
                for _, record in df_pivot.iterrows():
                    for col_num, col_name in enumerate(final_cols):
                        val = record[col_name]
                        if pd.isna(val):
                            ws_sum.write(sum_row_idx, col_num, "")
                        elif isinstance(val, (int, float)):
                            ws_sum.write(sum_row_idx, col_num, val, float_fmt)
                        else:
                            ws_sum.write(sum_row_idx, col_num, val)
                    sum_row_idx += 1

                # Set lebar kolom untuk sheet 2
                ws_sum.set_column('A:F', 20)

        output.seek(0)
        return output.getvalue()