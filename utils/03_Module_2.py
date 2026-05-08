# utils/03_Module_2_util.py
import io
import zipfile
import re
import numpy as np
import pandas as pd
import os
from ase.build import surface, make_supercell
from ase.io import read, write
from ase.constraints import FixAtoms

class SurfaceGenerator:
    """Consolidated logic: Extracts bulk from .out and applies it to a template[cite: 4]."""
    def __init__(self, bulk_atoms):
        self.bulk_atoms = bulk_atoms
        self.template_content = ""

    @classmethod
    def from_out_and_template(cls, out_content, template_content):
        """Reads relaxed bulk atoms and stores the template[cite: 4]."""
        f = io.StringIO(out_content)
        bulk_atoms = read(f, format='espresso-out', index='-1')
        instance = cls(bulk_atoms)
        instance.template_content = template_content
        return instance

    def generate_surface(self, miller_index, num_layers, vacuum_user, supercell_matrix, free_fraction):
        """
        Cuts the slab, shifts atoms to Z=0, and exports in Angstrom units.
        """
        # 1. Build the initial Slab
        slab = surface(self.bulk_atoms, miller_index, num_layers)
        
        # Geser dulu atomnya ke titik 0 secara Cartesian
        # Supaya nempel di "lantai" cell
        slab.translate([0, 0, 0.01-np.min(slab.positions[:, 2])])
        
        # Sekarang baru set vacuum di atasnya
        # Kita hitung tinggi slab sekarang + vacuum dari user
        z_max_atoms = np.max(slab.positions[:, 2])
        new_cell_height = z_max_atoms + vacuum_user
        
        current_cell = slab.get_cell()
        current_cell[2, 2] = new_cell_height
        slab.set_cell(current_cell)
        
        # Buat Supercell
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
        fixed_indices = [atom.index for atom in slab_super if atom.position[2] < threshold]
        
        # 3. Merge Slab Coords with User Template (FORMAT: ANGSTROM)
        num_atoms = len(slab_super)
        updated_temp = re.sub(r'nat\s*=\s*\d+', f'nat = {num_atoms}', self.template_content)
        
        cell = slab_super.get_cell()
        cell_str = "\nCELL_PARAMETERS angstrom\n" + "\n".join([f"  {v[0]:14.10f} {v[1]:14.10f} {v[2]:14.10f}" for v in cell])
        
        # Ambil posisi dalam Angstrom (Cartesian), bukan scaled/crystal
        pos_angstrom = slab_super.get_positions()
        syms = slab_super.get_chemical_symbols()
        
        pos_str = "\nATOMIC_POSITIONS angstrom\n"
        for i, (s, p) in enumerate(zip(syms, pos_angstrom)):
            # Pakai '0 0 0' untuk atom yang di-freeze di QE
            freeze = "0 0 0" if i in fixed_indices else "1 1 1"
            pos_str += f"  {s:2} {p[0]:14.10f} {p[1]:14.10f} {p[2]:14.10f} {freeze}\n"
        
        return {
            'pw_in': f"{updated_temp.strip()}\n{cell_str}\n{pos_str}",
            'vasp': self._get_vasp_string(slab_super),
            'fixed_count': len(fixed_indices)
        }

    def _get_vasp_string(self, atoms):
        v_out = io.StringIO()
        write(v_out, atoms, format='vasp')
        return v_out.getvalue()

    def process_and_zip(self, miller_input, num_layers, vacuum_user, supercell_matrix, free_fraction):
        hkl = tuple(map(int, miller_input.split(',')))
        res = self.generate_surface(hkl, num_layers, vacuum_user, supercell_matrix, free_fraction)
        
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
        self.e_bulk_ev, self.n_bulk = self._extract_basic_data(bulk_out_content)

    def _extract_basic_data(self, content):
        f = io.StringIO(content)
        atoms = read(f, format='espresso-out', index='-1')
        match = re.search(r'!\s+total energy\s+=\s+([-.\d]+)\s+Ry', content)
        if not match:
            raise ValueError("Could not find energy in .out file")
        energy_ev = float(match.group(1)) * 13.6056980659
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
                    e_slab_ev, n_slab = self._extract_basic_data(content)
                    area = self._calculate_area(atoms.get_cell())
                    numerator = e_slab_ev - (n_slab / self.n_bulk) * self.e_bulk_ev
                    gamma_ev_ang2 = numerator / (2 * area)
                    results.append({
                        "Folder": folder if folder else "Root",
                        "Gamma (J/m²)": gamma_ev_ang2 * 16.02176634,
                        "Gamma (eV/Å²)": gamma_ev_ang2,
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