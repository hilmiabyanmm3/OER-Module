# utils/03_Module_2.py
import io
import zipfile
import tempfile
import numpy as np
import re
import pandas as pd
import os
from ase import Atoms
from ase.build import surface, make_supercell
from ase.io import read, write

class SlabManager:
    """Logic for Step 1: Position Updates with Dynamic Template Mapping"""
    def __init__(self):
        # Your specific OER Slab Template
        self.template = """&control
    calculation = 'relax'
    tprnfor = .true.
    tstress = .true.
    pseudo_dir = '~/PSEUDO'
    outdir = './outdir/'
    nstep = 1000
    tefield = .true.
    dipfield = .true.
/
&SYSTEM
    ibrav = 0
    degauss = 0.01
    ecutrho = 500
    ecutwfc = 50
    nat = 78
    nspin = 2
    ntyp = 4
    occupations = 'smearing'
    smearing = 'gaussian'
    vdw_corr = 'DFT-D'
    starting_magnetization(1) = 1
    starting_magnetization(2) = 1
    starting_magnetization(3) = 1
    starting_magnetization(4) = 1
    edir                      = 3
    eamp                      = 0.0
    emaxpos                   = 0.75
/
&ELECTRONS
    electron_maxstep = 150
    mixing_beta = 0.1
    startingpot = 'atomic'
    startingwfc = 'atomic+random'
    scf_must_converge = .FALSE.
    mixing_mode = 'local-TF'
/
&IONS
    ion_dynamics = 'bfgs'
/

K_POINTS gamma

ATOMIC_SPECIES
  Ni   58.693   Ni.pbe-n-rrkjus_psl.1.0.0.UPF
  Fe   55.845   Fe.pbe-n-rrkjus_psl.1.0.0.UPF
  P    30.974   P.pbe-n-rrkjus_psl.1.0.0.UPF
  O    15.999   O.pbe-n-rrkjus_psl.1.0.0.UPF
"""

    def update_positions_from_out(self, out_content):
        try:
            f = io.StringIO(out_content)
            # Read the last frame from the .out file
            atoms = read(f, format='espresso-out', index='-1')
            num_atoms = len(atoms)
            
            # 1. Dynamically update 'nat' in the template
            # Uses regex to find 'nat = anynumber' and replace it with the actual count
            updated_template = re.sub(r'nat\s*=\s*\d+', f'nat = {num_atoms}', self.template)
            
            # 2. Extract Cell Parameters
            cell = atoms.get_cell()
            cell_str = "CELL_PARAMETERS angstrom\n"
            for vector in cell:
                cell_str += f"  {vector[0]:14.10f}  {vector[1]:14.10f}  {vector[2]:14.10f}\n"
            
            # 3. Extract Atomic Positions (Crystal/Scaled)
            positions = atoms.get_scaled_positions()
            symbols = atoms.get_chemical_symbols()
            pos_str = "ATOMIC_POSITIONS crystal\n"
            for sym, pos in zip(symbols, positions):
                # Using 0 0 0 flags as per your template style
                pos_str += f"  {sym:2}  {pos[0]:14.10f}  {pos[1]:14.10f}  {pos[2]:14.10f}  0 0 0\n"
            
            # Combine
            return f"{updated_template.strip()}\n\n{cell_str}\n{pos_str}"
            
        except Exception as e:
            return f"Error: {str(e)}"

class SurfaceGenerator:
    """Logic for Step 2: Slab/Surface Generation"""
    def __init__(self, bulk_atoms: Atoms):
        self.bulk_atoms = bulk_atoms

    @classmethod
    def from_file(cls, file_name: str, content: bytes):
        suffix = f".{file_name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
            tfile.write(content)
            tmp_name = tfile.name
        
        # ASE's read is smart enough to handle most formats
        bulk_atoms = read(tmp_name)
        return cls(bulk_atoms)

    def generate_surface(self, miller_index, num_layers, vacuum_user, supercell_matrix, fix_fraction=0.66, kpoints=(1, 1, 1)):
        # 1. Cut Surface
        slab = surface(self.bulk_atoms, miller_index, num_layers)
        
        # 2. Add Vacuum
        slab.center(vacuum=vacuum_user/2.0, axis=2)
        
        # 3. Supercell
        P = [[supercell_matrix[0], 0, 0], 
             [0, supercell_matrix[1], 0], 
             [0, 0, supercell_matrix[2]]]
        slab_super = make_supercell(slab, P)
        
        # 4. Generate Output Strings
        results = {}
        # VASP
        v_out = io.StringIO()
        write(v_out, slab_super, format='vasp')
        results['vasp'] = v_out.getvalue()
        
        # CIF
        c_out = io.StringIO()
        write(c_out, slab_super, format='cif')
        results['cif'] = c_out.getvalue()
        
        # QE Input (Simplified)
        results['pw_in'] = f"! QE Input Generated for Miller {miller_index}\n! K-Points: {kpoints}\n" + results['vasp']
        
        return results

    def process_and_zip(self, miller_input, num_layers, vacuum_user, supercell_matrix, fix_fraction, kpoints):
        hkl = tuple(map(int, miller_input.split(',')))
        res = self.generate_surface(hkl, num_layers, vacuum_user, supercell_matrix, fix_fraction, kpoints)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("PW.in", res['pw_in'])
            zf.writestr("input.vasp", res['vasp'])
            zf.writestr("input.cif", res['cif'])
            
        preview_data = {
            'top_pw_in': res['pw_in'],
            'folder': "".join(map(str, hkl))
        }
        return zip_buffer.getvalue(), preview_data
    
class EnergyExtractor:
    """Logic for Step 3: Extracting Energy Data from Slab Results"""
    
    def extract_from_zip(self, zip_bytes):
        data = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                for filename in z.namelist():
                    # Only process output or log files
                    if filename.endswith(('.out', '.log', '.txt')):
                        with z.open(filename) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            
                            # Search for the total energy in Ry (Quantum ESPRESSO standard)
                            # Regex looks for: !    total energy              =     -123.456 Ry
                            match = re.search(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content)
                            
                            if match:
                                energy_ry = float(match.group(1))
                                data.append({
                                    "Filename": filename,
                                    "Total Energy (Ry)": energy_ry,
                                    "Total Energy (eV)": energy_ry * 13.6056980659 # Conversion for convenience
                                })
            
            if not data:
                return None, "No energy data found in the provided files."

            # Create DataFrame and sort from lowest energy (most stable) to highest
            df = pd.DataFrame(data).sort_values(by="Total Energy (Ry)")
            
            # Save to Excel buffer
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Slab_Energies')
            
            return output.getvalue(), None
            
        except Exception as e:
            return None, f"Error processing ZIP: {str(e)}"
        
class SurfaceAnalyzer:
    """Logic for Step 4: Surface Energy Calculation (Gamma)"""
    def __init__(self, bulk_out_content: str):
        # Extract Bulk energy and atom count
        self.e_bulk_ev, self.n_bulk = self._extract_basic_data(bulk_out_content)

    def _extract_basic_data(self, content):
        """Helper to get energy (eV) and atom count from any QE .out content."""
        f = io.StringIO(content)
        atoms = read(f, format='espresso-out', index='-1')
        
        # Energy extraction via regex (looking for total energy in Ry)
        match = re.search(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content)
        if not match:
            raise ValueError("Could not find energy in .out file")
        
        energy_ev = float(match.group(1)) * 13.6056980659
        return energy_ev, len(atoms)

    def _calculate_area(self, cell):
        """Calculates surface area from the first two lattice vectors (a x b)."""
        v1, v2 = cell[0], cell[1]
        # Cross product magnitude
        cross = np.cross(v1, v2)
        return np.linalg.norm(cross)

    def process_slab_zip(self, zip_bytes):
        results = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            # Group files by folder
            folder_map = {}
            for f in z.namelist():
                if f.endswith(('.out', '.log')):
                    dirname = os.path.dirname(f)
                    folder_map[dirname] = z.read(f).decode('utf-8', errors='ignore')

            for folder, content in folder_map.items():
                try:
                    # 1. Extract Slab Data
                    f_buf = io.StringIO(content)
                    atoms = read(f_buf, format='espresso-out', index='-1')
                    e_slab_ev, n_slab = self._extract_basic_data(content)
                    area = self._calculate_area(atoms.get_cell())

                    # 2. Physics Calculation (Gamma)
                    # Formula: (E_slab - (n_slab/n_bulk)*E_bulk) / (2 * Area)
                    numerator = e_slab_ev - (n_slab / self.n_bulk) * self.e_bulk_ev
                    gamma_ev_ang2 = numerator / (2 * area)
                    gamma_j_m2 = gamma_ev_ang2 * 16.02176634 # eV/A^2 to J/m^2

                    results.append({
                        "Folder": folder if folder else "Root",
                        "Gamma (J/m²)": gamma_j_m2,
                        "Gamma (eV/Å²)": gamma_ev_ang2,
                        "Area (Å²)": area,
                        "N_slab": n_slab,
                        "E_Slab (eV)": e_slab_ev
                    })
                except:
                    continue
        return results

    def generate_excel(self, results_list):
        df = pd.DataFrame(results_list)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Surface_Energy')
        return output.getvalue()

