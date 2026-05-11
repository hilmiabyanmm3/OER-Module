# utils/03_Module_2_util.py
import io
import zipfile
import re
from ase import atoms
import numpy as np
import pandas as pd
import os
from ase.build import surface, make_supercell
from ase.io import read, write
from ase.constraints import FixAtoms
from ase.data import atomic_masses, atomic_numbers

class SurfaceGenerator:
    """Consolidated logic: Extracts bulk from .out and applies it to a template[cite: 4]."""
    def __init__(self, bulk_atoms, template_content):
        self.bulk_atoms = bulk_atoms
        self.template_content = template_content
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

    @classmethod
    def from_out_and_template(cls, out_content, template_content):
        """Reads relaxed bulk atoms and stores the template[cite: 4]."""
        f = io.StringIO(out_content)
        bulk_atoms = read(f, format='espresso-out', index='-1')
        return cls(bulk_atoms=bulk_atoms, template_content=template_content)

    def generate_surface(self, miller_index, num_layers, vacuum_user, supercell_matrix, kpts, free_fraction):
        """
        Cuts the slab, shifts atoms to Z=0, and exports in Angstrom units.
        """
        # 1. Build the initial Slab
        slab = surface(self.bulk_atoms, miller_index, num_layers)
        slab.translate([0, 0, 0.01-np.min(slab.positions[:, 2])])
        
        z_max_atoms = np.max(slab.positions[:, 2])
        new_cell_height = z_max_atoms + vacuum_user
        current_cell = slab.get_cell()
        current_cell[2, 2] = new_cell_height
        slab.set_cell(current_cell)
        
        P = [[supercell_matrix[0], 0, 0], 
             [0, supercell_matrix[1], 0], 
             [0, 0, supercell_matrix[2]]]
        slab_super = make_supercell(slab, P)

        # 2. Apply Constraints (Fix the bottom atoms)
        z_coords = slab_super.positions[:, 2]
        z_min = np.min(z_coords)
        z_max = np.max(z_coords)
        z_range = z_max - z_min
        
        threshold = z_min + (z_range * (1.0 - free_fraction))

        unique_elements = sorted(list(set(slab_super.get_chemical_symbols())))
        ntyp = len(unique_elements)
        nat = len(slab_super)

        # We strip everything after the namelists (starting at ATOMIC_SPECIES, K_POINTS, etc.)
        cards_pattern = re.compile(r'(?i)(ATOMIC_SPECIES|K_POINTS|CELL_PARAMETERS|ATOMIC_POSITIONS)')
        template_clean = cards_pattern.split(self.template_content)[0].strip()
        
        # Update ntyp and nat in the clean template
        template_clean = re.sub(r'(?i)(ntyp\s*=\s*)\d+', r'\g<1>' + str(ntyp), template_clean)
        template_clean = re.sub(r'(?i)(nat\s*=\s*)\d+', r'\g<1>' + str(nat), template_clean)

        # Remove old magnetizations to prevent duplicates
        template_clean = re.sub(r'(?i)[ \t]*starting_magnetization\(\d+\)\s*=\s*[\d\.\-]+[\n\r]*', '', template_clean)

        new_species_str = "\n\nATOMIC_SPECIES\n"
        mag_str = ""
        metals = ['Ni', 'Fe', 'Mn', 'Co', 'Cu', 'Pd', 'Pt', 'Ag', 'Au', 'Ru', 'Rh', 'Ir', 'Os', 'V', 'Cr', 'Ti', 'Sc', 'Zn']

        for i, el in enumerate(unique_elements, 1):
            mass = atomic_masses[atomic_numbers[el]]
            pseudo = self.pseudo_map.get(el, f"{el}.UPF")
            new_species_str += f"  {el:2}  {mass:7.3f}  {pseudo}\n"
            
            mag_val = 1.0 if el in metals else 0.0
            mag_str += f"    starting_magnetization({i}) = {mag_val}\n"

        # Inject mag_str into &SYSTEM
        system_match = re.search(r'(?i)(&SYSTEM.*?)(/)', template_clean, flags=re.DOTALL)
        if system_match:
            group1 = system_match.group(1).rstrip()
            new_system = f"{group1}\n{mag_str}{system_match.group(2)}"
            template_clean = template_clean.replace(system_match.group(0), new_system)

        # 5. Build Geometry Cards
        z_coords = slab_super.positions[:, 2]
        threshold = np.min(z_coords) + ((np.max(z_coords) - np.min(z_coords)) * (1.0 - free_fraction))
        
        pos_str = "\n\nATOMIC_POSITIONS angstrom\n"
        for atom in slab_super:
            freeze = "0 0 0" if atom.position[2] < threshold else "1 1 1"
            pos_str += f"  {atom.symbol:2} {atom.position[0]:14.10f} {atom.position[1]:14.10f} {atom.position[2]:14.10f} {freeze}\n"

        cell = slab_super.get_cell()
        cell_str = "\nCELL_PARAMETERS angstrom\n" + "\n".join([f"  {v[0]:14.10f} {v[1]:14.10f} {v[2]:14.10f}" for v in cell])
        
        kpoints_str = f"\nK_POINTS automatic\n{kpts[0]} {kpts[1]} {kpts[2]} 0 0 0\n"

        return {
            'pw_in': f"{template_clean}\n{new_species_str}{kpoints_str}{cell_str}{pos_str}",
            'vasp': self._get_vasp_string(slab_super),
            'fixed_count': sum(1 for a in slab_super if a.position[2] < threshold)
        }

    def _get_vasp_string(self, atoms):
        v_out = io.StringIO()
        write(v_out, atoms, format='vasp')
        return v_out.getvalue()

    def process_and_zip(self, miller_input, num_layers, vacuum_user, supercell_matrix, kpts, free_fraction):
        hkl = tuple(map(int, miller_input.split(',')))
        res = self.generate_surface(hkl, num_layers, vacuum_user, supercell_matrix, kpts=kpts, free_fraction=free_fraction)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("slab.in", res['pw_in'])
            zf.writestr("slab.vasp", res['vasp'])
            
        return zip_buffer.getvalue(), {
            'top_pw_in': res['pw_in'], 
            'folder': "".join(map(str, hkl)),
            'fixed_info': f"Fixed {res['fixed_count']} atoms (Bottom {int((1-free_fraction)*100)}%)"
        }

class SurfaceAnalyzer:
    """Logic for Step 2: Surface Energy Calculation (Gamma)[cite: 4]."""
    def __init__(self, bulk_out_content: str):
        self.e_bulk_ev, self.n_bulk = self._extract_basic_data(bulk_out_content, is_bulk=True)

    def _extract_basic_data(self, content, is_bulk=True):
        f = io.StringIO(content)
        atoms = read(f, format='espresso-out', index='-1')

        if is_bulk:
            matches = re.findall(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content)
            if not matches:
                raise ValueError("Could not find '! total energy' in bulk .out file")
            energy_ry = float(matches[-1])

        else:
            matches = re.findall(r'(?i)Final energy\s+=\s+([-.\d]+)\s+Ry', content)
            if matches:
                energy_ry = float(matches[-1])
            else:
                # Fallback aman jika ternyata file slab yang di-upload adalah SCF (bukan relax)
                fallback = re.findall(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content)
                if not fallback:
                    raise ValueError("Could not find energy in slab .out file")
                energy_ry = float(fallback[-1])

        energy_ev = energy_ry * 13.605698066
        return energy_ev, len(atoms)

    def _calculate_area(self, cell):
        v1, v2 = cell[0], cell[1]
        cross = np.cross(v1, v2)
        return np.linalg.norm(cross)

    def process_slab_zip(self, zip_bytes):
        results = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            folder_map = {os.path.dirname(f): z.read(f).decode('utf-8', errors='ignore') 
                         for f in z.namelist() if f.endswith(('.out', '.log'))}

            for folder, content in folder_map.items():
                try:
                    f_buf = io.StringIO(content)
                    atoms = read(f_buf, format='espresso-out', index='-1')
                    e_slab_ev, n_slab = self._extract_basic_data(content, is_bulk=False)
                    area = self._calculate_area(atoms.get_cell())
                    numerator = e_slab_ev - (n_slab / self.n_bulk) * self.e_bulk_ev
                    gamma_ev_ang2 = numerator / (2 * area)
                    results.append({
                        "Folder": folder if folder else "Root",
                        "Surface Energy (J/m²)": gamma_ev_ang2 * 16.02176634,
                        "Surface Energy (eV/Å²)": gamma_ev_ang2,
                        "Area (Å²)": area,
                        "N_slab": n_slab,
                        "E_Slab (eV)": e_slab_ev
                    })
                except: continue
        return results

    def generate_excel(self, results_list):
        df = pd.DataFrame(results_list)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Surface_Energy')
        return output.getvalue()