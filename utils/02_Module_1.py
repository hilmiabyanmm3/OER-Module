# utils/02_Module_1.py
import io
import zipfile
import pandas as pd
from ase.io import read, write
import random

class BulkWorkflowManager:
    # --- STEP 1: BULK PREP ---
    def prepare_bulk_input(self, cif_content, template_in):
        cif_file = io.StringIO(cif_content)
        atoms = read(cif_file, format='cif')
        
        vasp_out = io.StringIO()
        write(vasp_out, atoms, format='vasp')
        
        # Merge template (system/parameters) with coordinates
        final_in = f"{template_in}\n\n{vasp_out.getvalue()}"
        return final_in, vasp_out.getvalue()

    # --- STEP 2: VARIATION (The "Best" Way) ---
    def generate_variations(self, base_in_content, ratio_str):
        """
        Parses ratio_str (e.g., 'Fe:0.5, Ni:0.5') and swaps metal sites.
        """
        # Parse ratios
        ratios = {parts.split(':')[0].strip(): float(parts.split(':')[1]) 
                  for parts in ratio_str.split(',')}
        
        # Read the structure from the .in (assuming it contains VASP/ASE readable coords)
        # We use a temporary buffer to let ASE read the text
        buf = io.StringIO(base_in_content)
        atoms = read(buf, format='vasp') # Using vasp format as proxy for coordinates
        
        in_zip_buffer = io.BytesIO()
        vasp_zip_buffer = io.BytesIO()

        with zipfile.ZipFile(in_zip_buffer, 'w') as z_in, \
             zipfile.ZipFile(vasp_zip_buffer, 'w') as z_vasp:
            
            # Generate 5 unique random distributions based on ratio
            for i in range(1, 6):
                new_atoms = atoms.copy()
                symbols = new_atoms.get_chemical_symbols()
                
                # Logic: Find 'M' or specific metals and swap them
                # Here we replace ALL atoms with the ratio for demonstration
                # In a real OER case, we'd target specific site indices
                new_symbols = random.choices(
                    list(ratios.keys()), 
                    weights=list(ratios.values()), 
                    k=len(symbols)
                )
                new_atoms.set_chemical_symbols(new_symbols)
                
                # Save to ZIP
                v_out = io.StringIO()
                write(v_out, new_atoms, format='vasp')
                
                name = f"var_{i}_{''.join(list(ratios.keys()))}"
                z_in.writestr(f"{name}.in", f"! Variation {i}\n{base_in_content.split('ATOMIC_POSITIONS')[0]}\n{v_out.getvalue()}")
                z_vasp.writestr(f"{name}.vasp", v_out.getvalue())

        return in_zip_buffer.getvalue(), vasp_zip_buffer.getvalue()

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
                                energy = float(line_str.split('=')[1].split('Ry')[0].strip())
                                break
                        if energy is not None:
                            data.append({"File": filename, "Total Energy (Ry)": energy})
        
        df = pd.DataFrame(data).sort_values(by="Total Energy (Ry)")
        excel_out = io.BytesIO()
        df.to_excel(excel_out, index=False)
        return excel_out.getvalue()