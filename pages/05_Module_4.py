import streamlit as st
import importlib
import io
import zipfile
import pandas as pd

# 1. DYNAMIC IMPORT
module_logic = importlib.import_module("utils.05_Module_4")
ZPE = module_logic.ZPEManager()

st.set_page_config(page_title="Module 4: ZPE & Vibrations", layout="wide")

# --- NAVIGATION HEADER ---
st.title("05 | Module 4: Vibrational Analysis")
col_nav, _ = st.columns([1, 5])
with col_nav:
    if st.button("⬅️ Back to Module 3"):
        st.switch_page("pages/04_Module_3.py")
st.divider()

# --- TABBED INTERFACE ---
tab1, tab2, tab3 = st.tabs(["Step 1: Displacement & Jobs", "Step 2: Frequency Extraction", "Step 3: ZPE/Entropy Calc"])

with tab1:
    st.subheader("Finite Displacement Generator")
    st.info("Generate inputs for vibrational frequency calculations using the finite displacement method.")

    # Displacement Section
    with st.container(border=True):
        st.write("#### 1. Generate Displaced .in Files")
        uploaded_template = st.file_uploader("Upload Template QE Input (.in)", type=["in"], key="zpe_template")
        n_to_displace = st.number_input("Number of atoms to displace (from bottom)", min_value=1, value=1)

        if uploaded_template:
            content = uploaded_template.getvalue().decode("utf-8").splitlines(keepends=True)
            if st.button(f"Generate {n_to_displace * 6} Files", type="primary"):
                results = ZPE.generate_finite_displacements(content, n_to_displace)
                if results:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as z:
                        for name, text in results.items():
                            z.writestr(name, text)
                    
                    st.success("Displacements generated!")
                    st.download_button("Download .in ZIP", data=zip_buffer.getvalue(), file_name="displaced_inputs.zip")

    # Script Generation Section
    with st.container(border=True):
        st.write("#### 2. Generate Job Submission Scripts")
        st.info("Upload the ZIP from Part 1 to create corresponding .sh scripts.")
        
        col_header, col_zip = st.columns([2, 1])
        with col_header:
            bash_header = st.text_area("Slurm/Bash Header", 
                                     value="#!/bin/bash\n#SBATCH --nodes=1\n#SBATCH --ntasks-per-node=24", 
                                     height=150)
        with col_zip:
            zip_to_sh = st.file_uploader("Upload .in ZIP", type=["zip"], key="zip_for_sh")

        if zip_to_sh and bash_header:
            if st.button("Generate .sh Scripts"):
                with zipfile.ZipFile(zip_to_sh, 'r') as z:
                    input_filenames = [f for f in z.namelist() if f.endswith('.in')]
                
                if input_filenames:
                    sh_results = ZPE.generate_job_scripts(input_filenames, bash_header)
                    sh_zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(sh_zip_buffer, "w") as sz:
                        for sh_name, sh_text in sh_results.items():
                            sz.writestr(sh_name, sh_text)
                    
                    st.success(f"Generated {len(sh_results)} scripts.")
                    st.download_button("Download .sh ZIP", data=sh_zip_buffer.getvalue(), file_name="submission_scripts.zip")

with tab2:
    st.subheader("Step 2: ZPE Data Extractor")
    st.info("Extract forces from your displacement calculations to solve the vibrational Hessian.")

    uploaded_zpe_zip = st.file_uploader("Upload Completed ZPE ZIP", type="zip", key="zpe_results")
    
    if uploaded_zpe_zip:
        if st.button("Generate ZPE Summary", type="primary"):
            with st.spinner("Calculating vibrational frequencies..."):
                df_zpe = st.session_state.zpe_analyzer.process_zip(uploaded_zpe_zip.getvalue())
                
                if not df_zpe.empty:
                    st.success(f"Successfully calculated ZPE for {len(df_zpe)} structures.")
                    
                    # Display Data
                    st.dataframe(df_zpe[['Step', 'Site', 'ZPE (eV)']].style.format({"ZPE (eV)": "{:.4f}"}), 
                                 use_container_width=True)
                    
                    # Export
                    excel_data = st.session_state.zpe_analyzer.generate_excel(df_zpe)
                    st.download_button("📊 Download ZPE Excel", excel_data, "ZPE_Results.xlsx")
                else:
                    st.error("No valid displacement logs found. Ensure filenames match 'atom1_x_plus.out', etc.")
with tab3:
    st.subheader("Step 3: Gibbs Free Energy Profile")
    st.info("Combine Energy (Module 3) and ZPE (Module 4) to calculate reaction thermodynamics.")

    c1, c2 = st.columns(2)
    file_e = c1.file_uploader("Upload Energy Summary (from Module 3)", type=['xlsx', 'csv'])
    file_z = c2.file_uploader("Upload ZPE Summary (from Step 2)", type=['xlsx', 'csv'])

    if file_e and file_z:
        st.divider()
        st.write("#### Thermodynamics Parameters")
        p1, p2, p3 = st.columns(3)
        g_h2o = p1.number_input("G_H2O (eV)", value=-466.4078885915, format="%.10f")
        g_h2 = p2.number_input("G_H2 (eV)", value=-31.8575183992, format="%.10f")
        title = p3.text_input("Material Name", value="OER Catalyst")

        if st.button("Calculate Free Energy"):
            df_e = pd.read_excel(file_e) if file_e.name.endswith('xlsx') else pd.read_csv(file_e)
            df_z = pd.read_excel(file_z) if file_z.name.endswith('xlsx') else pd.read_csv(file_z)
            
            st.session_state.m4_plot_data = st.session_state.gibbs.calculate_deltas(df_e, df_z, g_h2o, g_h2, U=0.0)
            st.success("Calculations complete!")

    # Interactive Plotting Area
    if 'm4_plot_data' in st.session_state:
        st.divider()
        u_slider = st.slider("Adjust Applied Potential (U vs RHE)", 0.0, 2.5, 1.23, step=0.01)
        
        fig = st.session_state.gibbs.create_plot(st.session_state.m4_plot_data, title, U_shift=u_slider)
        st.pyplot(fig)

        # Summary Table
        st.write("#### Results Table")
        res_table = []
        for d in st.session_state.m4_plot_data:
            res_table.append({"Site": d['label'], "Overpotential (V)": d['overpotential']})
        st.table(pd.DataFrame(res_table))

# --- FOOTER ---
st.divider()
if st.button("Complete Module 4 🚀"):
    st.switch_page("pages/06_Module_5.py")