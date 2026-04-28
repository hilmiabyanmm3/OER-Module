#pages/03_Module_2.py

import importlib
import streamlit as st
import pandas as pd

# Dynamic import
module_logic = importlib.import_module("utils.03_Module_2")
Manager = module_logic.SlabManager()
SlabManager = module_logic.SlabManager
SurfaceGenerator = module_logic.SurfaceGenerator
Extractor = module_logic.EnergyExtractor() # New Instance for Step 3

st.set_page_config(page_title="Module 2: Slab Opt", layout="wide")

# Navigation Header
st.title("03 | Module 2")
col_nav, _ = st.columns([1, 5])
with col_nav:
    if st.button("⬅️ Back"):
        st.switch_page("pages/02_Module_1.py")
st.divider()

# TABBED STEPS
tab1, tab2, tab3, tab4 = st.tabs(["Step 1: Position Update", "Step 2: Surface Builder", "Step 3: Surface Energy Data Extraction", "Step 4: Surface Energy Analyzer"])

# --- STEP 1: POSITION UPDATE ---
with tab1:
    st.subheader("Step 1: Update Atomic Positions")
    st.write("Upload a QE `.out` file to extract final coordinates and inject them into the standard template.")

    uploaded_out = st.file_uploader("Upload .out file", type=["out", "log"])

    if uploaded_out:
        content = uploaded_out.getvalue().decode("utf-8")
        
        if st.button("Generate Updated .in File", type="primary"):
            with st.spinner("Extracting coordinates..."):
                new_in_content = Manager.update_positions_from_out(content)
                
                if "Error" in new_in_content:
                    st.error(new_in_content)
                else:
                    st.success("Positions successfully updated!")
                    st.text_area("Preview Updated Input:", new_in_content, height=400)
                    st.download_button(
                        label="Download New .in File",
                        data=new_in_content,
                        file_name=f"relaxed_{uploaded_out.name.replace('.out', '.in')}",
                        mime="text/plain"
                    )

    # --- FOOTER NAVIGATION ---
    st.divider()
    if st.button("Complete & Move to Step 2 ➡️"):
        # Note: This technically goes to the same file for now as we build it
        # but we can add a session state tracker later for the 4 internal steps
        st.info("Step 2 logic will be added here next.")

# --- STEP 2: SURFACE BUILDER ---
with tab2:
    st.subheader("Slab Supercell Generation")
    st.info("Build your surface from the relaxed bulk structure.")

    uploaded_bulk = st.file_uploader("Upload Bulk (CIF/VASP)", type=["cif", "vasp"], key="step2_bulk")
    
    if uploaded_bulk:
        try:
            generator = SurfaceGenerator.from_file(uploaded_bulk.name, uploaded_bulk.getvalue())
            st.success(f"Loaded: {generator.bulk_atoms.get_chemical_formula()}")

            with st.form("surface_params"):
                c1, c2, c3 = st.columns(3)
                miller = c1.text_input("Miller Index (h,k,l)", "1,0,0")
                layers = c2.number_input("Layers", 1, 10, 3)
                vacuum = c3.number_input("Vacuum (Å)", 0.0, 50.0, 15.0)
                
                sc_x = c1.number_input("X Repeat", 1, 5, 2)
                sc_y = c2.number_input("Y Repeat", 1, 5, 1)
                sc_z = c3.number_input("Z Repeat", 1, 5, 1)
                
                k_x = c1.number_input("Kx", 1, 10, 1)
                k_y = c2.number_input("Ky", 1, 10, 1)
                k_z = c3.number_input("Kz", 1, 10, 1)

                if st.form_submit_button("Generate Surface"):
                    zip_bytes, preview = generator.process_and_zip(
                        miller, layers, vacuum, [sc_x, sc_y, sc_z], 0.66, (k_x, k_y, k_z)
                    )
                    
                    st.code(preview['top_pw_in'], language='text')
                    st.download_button("⬇️ Download Slab Package", zip_bytes, f"surface_{preview['folder']}.zip")
        except Exception as e:
            st.error(f"Error: {e}")

# ---- STEP 3 ----
with tab3:
    st.subheader("Step 3: Surface Energy Data Extraction")
    st.info("Upload a ZIP file containing the `.out` results from your slab optimizations.")

    uploaded_zip = st.file_uploader("Upload Results ZIP", type=["zip"], key="step3_zip")

    if uploaded_zip:
        if st.button("Extract & Export to Excel", type="primary"):
            with st.spinner("Parsing output files..."):
                excel_data, error = Extractor.extract_from_zip(uploaded_zip.getvalue())
                
                if error:
                    st.error(error)
                else:
                    st.success("Data successfully extracted and sorted!")
                    st.download_button(
                        label="Excel Result 📥",
                        data=excel_data,
                        file_name=f"slab_energies_{uploaded_zip.name.replace('.zip', '')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

with tab4:
    st.subheader("Step 4: Surface Energy Analyzer")
    st.write("Calculate the thermodynamic stability ($\gamma$) of your surfaces.")

    c1, c2 = st.columns(2)
    with c1:
        bulk_file = st.file_uploader("Upload Bulk Relaxed (.out)", type=["out", "log"], key="step4_bulk")
    with c2:
        slabs_zip = st.file_uploader("Upload Slabs ZIP (.out files)", type=["zip"], key="step4_slabs")

    if bulk_file and slabs_zip:
        if st.button("Calculate Gamma", type="primary"):
            try:
                # Initialize Analyzer
                bulk_content = bulk_file.getvalue().decode("utf-8")
                analyzer = module_logic.SurfaceAnalyzer(bulk_content)
                
                st.success(f"Bulk Loaded: {analyzer.n_bulk} atoms | Energy: {analyzer.e_bulk_ev:.3f} eV")

                # Process Slabs
                results = analyzer.process_slab_zip(slabs_zip.getvalue())
                
                if results:
                    df = pd.DataFrame(results)
                    st.dataframe(df.style.format("{:.4f}", subset=["Gamma (J/m²)", "Gamma (eV/Å²)", "Area (Å²)"]))
                    
                    # Download Report
                    excel_data = analyzer.generate_excel(results)
                    st.download_button("⬇️ Download Excel Report", excel_data, "surface_energy_results.xlsx")
                else:
                    st.warning("No valid energy data found in the ZIP.")
                    
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    # Navigation Footer
    st.divider()
    if st.button("Complete & Move to Module 3 ➡️"):
        st.switch_page("pages/04_Module_3.py")

