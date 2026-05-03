# utils/02_Module_1.py
import io
import re
import zipfile
import pandas as pd
from ase.io import read, write
from ase.data import atomic_masses, atomic_numbers
import itertools

class BulkWorkflowManager:
    def __init__(self):
        # Kembalikan pseudo_map di dalam kelas
        self.pseudo_map = {
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

    # --- STEP 1: BULK PREP ---
    def prepare_bulk_input(self, structure_content, template_in, file_format='cif',kx=6, ky=6, kz=3):
        structure_file = io.StringIO(structure_content)
        ase_format = 'vasp' if file_format.lower() in ['vasp', 'poscar'] else 'cif'
        atoms = read(structure_file, format=ase_format)

        unique_elements = list(set(atoms.get_chemical_symbols()))
        ntyp = len(unique_elements)
        
        # 1. BERSIHKAN TEMPLATE DARI CARDS LAMA
        cards_pattern = re.compile(r'(?i)(ATOMIC_SPECIES|K_POINTS|CELL_PARAMETERS|ATOMIC_POSITIONS)')
        template_clean = cards_pattern.split(template_in)[0].strip()

        if re.search(r'ntyp\s*=', template_clean, re.IGNORECASE):
            template_clean = re.sub(r'(?i)(ntyp\s*=\s*)\d+', r'\g<1>' + str(ntyp), template_clean)
        else:
            template_clean = re.sub(r'(?i)(/[\s\n]*)$', f'   ntyp = {ntyp}\n/', template_clean, count=1)
        template_clean = re.sub(r'(?i)starting_magnetization\(\d+\)\s*=\s*[\d\.\-]+[\n\r]*', '', template_clean)
        
        # 2. BANGUN ATOMIC_SPECIES & MAGNETIZATION BARU SESUAI CIF
        new_species_str = "\n\nATOMIC_SPECIES\n"
        mag_str = ""
        metals = ['Ni', 'Fe', 'Mn', 'Co', 'Cu', 'Pd', 'Pt', 'Ag', 'Au', 'Ru', 'Rh', 'Ir', 'Os', 'V', 'Cr', 'Ti', 'Sc', 'Zn']

        for i, el in enumerate(unique_elements, 1):
            # Ambil massa otomatis dari library ASE
            mass = atomic_masses[atomic_numbers[el]]
            pseudo = self.pseudo_map.get(el, f"{el}.UPF")
            
            new_species_str += f"  {el}  {mass:.3f}  {pseudo}\n"
            
            mag_val = 1.0 if el in metals else 0.0
            mag_str += f"   starting_magnetization({i}) = {mag_val}\n"

        system_match = re.search(r'(?i)(&SYSTEM.*?)(/)', template_clean, flags=re.DOTALL)
        if system_match:
            new_system = system_match.group(1) + mag_str + system_match.group(2)
            template_clean = template_clean.replace(system_match.group(0), new_system)

        # 3. BANGUN BLOK K_POINTS, CELL_PARAMETERS, ATOMIC_POSITIONS
        kpoints_str = f"\nK_POINTS automatic\n{kx} {ky} {kz} 0 0 0\n"

        cell = atoms.get_cell()
        cell_str = "\nCELL_PARAMETERS angstrom\n"
        for row in cell:
            cell_str += f"{row[0]:.10f} {row[1]:.10f} {row[2]:.10f}\n"

        pos_str = "\nATOMIC_POSITIONS angstrom\n"
        for atom in atoms:
            pos_str += f"{atom.symbol}  {atom.position[0]:.10f} {atom.position[1]:.10f} {atom.position[2]:.10f}\n"

        # 4. GABUNGKAN SEMUA
        final_in = template_clean + new_species_str + kpoints_str + cell_str + pos_str

        # Generate output VASP juga untuk kebutuhan Variation Step 2
        vasp_out = io.StringIO()
        write(vasp_out, atoms, format='vasp')

        return final_in, vasp_out.getvalue()

    # --- STEP 2: VARIATION (Permutasi Logam + Generate ZIP di Backend) ---
    def generate_variations(self, base_in_content, target_metals, kx=6, ky=6, kz=3):
        
        buf = io.StringIO(base_in_content)
        atoms = read(buf, format='espresso-in') 
        
        symbols = atoms.get_chemical_symbols()
        # Ambil indeks yang merupakan logam transisi
        target_indices = [i for i, sym in enumerate(symbols) if sym in ['Ni', 'Fe', 'Mn', 'Co', 'Cu', 'Pd', 'Pt']]
        
        if len(target_indices) != len(target_metals):
            return {"error": f"Atom mismatch: Target metals in input ({len(target_metals)}) != metal sites found in structure ({len(target_indices)})."}
            
        unique_labelings = sorted(list(set(itertools.permutations(target_metals))))
        
        cards_pattern = re.compile(r'(?i)(ATOMIC_POSITIONS)')
        base_template_only = cards_pattern.split(base_in_content)[0].strip()
        base_template_only = re.sub(r'(?i)K_POINTS.*?\n[\d\s\.]+\n', '', base_template_only, flags=re.DOTALL)
        kpoints_str = f"\nK_POINTS automatic\n{kx} {ky} {kz} 0 0 0\n"

        results = []
        for idx, labels in enumerate(unique_labelings, 1):
            new_atoms = atoms.copy()
            new_symbols = new_atoms.get_chemical_symbols()
            
            for i, label in zip(target_indices, labels):
                new_symbols[i] = label
                
            new_atoms.set_chemical_symbols(new_symbols)
            
            v_out = io.StringIO()
            write(v_out, new_atoms, format='vasp')
            vasp_content = v_out.getvalue()
            
            pos_str = "\nATOMIC_POSITIONS angstrom\n"
            for atom in new_atoms:
                pos_str += f"{atom.symbol}  {atom.position[0]:.10f} {atom.position[1]:.10f} {atom.position[2]:.10f}\n"
            
            final_in = base_template_only + kpoints_str + pos_str
            
            results.append({
                "name": f"var_{idx}",
                "labels": labels,
                "qe_content": final_in,
                "vasp_content": vasp_content
            })

        # --- PEMBUATAN 2 ZIP TERPISAH DI BACKEND ---
        in_zip_buffer = io.BytesIO()
        vasp_zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(in_zip_buffer, "w", zipfile.ZIP_DEFLATED) as z_in, \
             zipfile.ZipFile(vasp_zip_buffer, "w", zipfile.ZIP_DEFLATED) as z_vasp:
            for var in results:
                name = var['name']
                # Masukkan ke zip masing-masing (tanpa sub-folder agar rapi)
                z_in.writestr(f"{name}.in", var['qe_content'].encode('utf-8'))
                z_vasp.writestr(f"{name}.vasp", var['vasp_content'].encode('utf-8'))

        # Kembalikan dictionary berisi kedua file ZIP dan list hasil untuk preview
        return {
            "in_zip_bytes": in_zip_buffer.getvalue(),
            "vasp_zip_bytes": vasp_zip_buffer.getvalue(),
            "variations": results
        }

    # --- STEP 3: DATA EXTRACTION ---
    def extract_energies(self, uploaded_zip):
        data = []
        with zipfile.ZipFile(uploaded_zip) as z:
            for filename in z.namelist():
                if filename.endswith('.out') or filename.endswith('.log'):
                    with z.open(filename) as f:
                        lines = f.readlines()
                        energy = None
                        for line in reversed(lines):
                            line_str = line.decode('utf-8')
                            # Standard QE energy line
                            if '!    total energy' in line_str:
                                try:
                                    energy_ry = float(line_str.split('=')[1].split('Ry')[0].strip())
                                    break
                                except (IndexError, ValueError):
                                    continue
                        
                        if energy_ry is not None:
                            energy_ev = energy_ry * 13.605698066
                            data.append({
                                "Filename": filename, 
                                "Energy (Ry)": energy_ry,
                                "Energy (eV)": energy_ev
                            })
        
        # --- JARING PENGAMAN ---
        # Jika tidak ada satu pun file yang mengandung data energi (kalkulasi gagal/belum selesai)
        if len(data) == 0:
            return None, b""

        df = pd.DataFrame(data)
        min_ev = df["Energy (eV)"].min()
        df["Relative Energy (eV)"] = df["Energy (eV)"] - min_ev
        df = df.sort_values(by="Energy (eV)").reset_index(drop=True)
        excel_out = io.BytesIO()
        df.to_excel(excel_out, index=False)
        return df, excel_out.getvalue()