import streamlit as st
import importlib
import io
import zipfile
import pandas as pd

# 1. DYNAMIC IMPORT
module_logic = importlib.import_module("utils.05_Module_4")
# We assume ZPEManager handles structural extraction from .out 
# and formatting using template.in
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
tab1, tab2, tab3 = st.tabs(["Step 1: Displacement Generator", "Step 2: Frequency Extraction", "Step 3: Gibbs Analysis"])

with tab1:
    st.subheader("Finite Displacement Generator")
    
    with st.container(border=True):
        st.write("#### 1. Input Files")
        c1, c2 = st.columns(2)
        
        with c1:
            uploaded_out = st.file_uploader("Upload Relaxed Structure (.out)", type=["out", "log"], key="zpe_out")
        with c2:
            uploaded_template = st.file_uploader("Upload QE Template (.in)", type=["in"], key="zpe_template")
        
        n_to_displace = st.number_input("Number of atoms to displace", min_value=1, value=3)

        if uploaded_out and uploaded_template:
            # We wrap the generation in a state check to prevent Streamlit from refreshing 
            # and losing the data before the download button is clicked.
            if st.button(f"Generate {n_to_displace * 6} Displaced Files", type="primary", use_container_width=True):
                out_content = uploaded_out.getvalue().decode("utf-8")
                template_content = uploaded_template.getvalue().decode("utf-8")
                
                with st.spinner("Processing displacements..."):
                    results = ZPE.generate_finite_displacements(out_content, template_content, n_to_displace)
                    
                    if results:
                        # Create ZIP in memory
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as z:
                            for name, text in results.items():
                                z.writestr(name, text)
                        
                        st.success(f"Generated {len(results)} files.")
                        st.download_button(
                            label="⬇️ Download Displaced .in ZIP", 
                            data=zip_buffer.getvalue(), 
                            file_name="zpe_displaced_inputs.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    else:
                        st.error("Failed to generate files. Check if the .out file is a valid QE output.")

with tab2:
    st.subheader("Step 2: ZPE Data Extractor")
    st.info("Extract forces from your displacement calculations to solve the vibrational Hessian.")

    uploaded_zpe_zip = st.file_uploader("Upload Completed ZPE ZIP (containing .out logs)", type="zip", key="zpe_results")
    
    if uploaded_zpe_zip:
        # Initialize analyzer if stored in module_logic or session_state
        if 'zpe_analyzer' not in st.session_state:
             st.session_state.zpe_analyzer = module_logic.ZPEAnalyzer()

        if st.button("Calculate ZPE & Frequencies", type="primary"):
            with st.spinner("Solving Hessian and extracting Zero-Point Energies..."):
                df_zpe = st.session_state.zpe_analyzer.process_zip(uploaded_zpe_zip.getvalue())
                
                if not df_zpe.empty:
                    st.success(f"Calculated ZPE for {len(df_zpe)} structures.")
                    st.dataframe(df_zpe[['Step', 'Site', 'ZPE (eV)']].style.format({"ZPE (eV)": "{:.4f}"}), 
                                 use_container_width=True)
                    
                    excel_data = st.session_state.zpe_analyzer.generate_excel(df_zpe)
                    st.download_button("📊 Download ZPE Results (Excel)", excel_data, "ZPE_Results.xlsx")
                else:
                    st.error("Extraction failed. Ensure folder structure/filenames are correct.")

with tab3:
    st.subheader("Step 3: Gibbs Free Energy Profile")
    st.info("Combine DFT Energies and ZPE to visualize the OER reaction coordinate.")

    # Initialize Gibbs engine
    if 'gibbs' not in st.session_state:
        st.session_state.gibbs = module_logic.GibbsAnalyzer()

    c1, c2 = st.columns(2)
    file_e = c1.file_uploader("Upload Energy Summary (Module 3)", type=['xlsx', 'csv'])
    file_z = c2.file_uploader("Upload ZPE Summary (Step 2)", type=['xlsx', 'csv'])

    if file_e and file_z:
        st.divider()
        st.write("#### Thermodynamics Parameters")
        p1, p2, p3 = st.columns(3)
        g_h2o = p1.number_input("G_H2O (eV)", value=-466.4078885915, format="%.10f")
        g_h2 = p2.number_input("G_H2 (eV)", value=-31.8575183992, format="%.10f")
        title = p3.text_input("Material Name", value="OER Catalyst")

        if st.button("Generate Gibbs Profile"):
            df_e = pd.read_excel(file_e) if file_e.name.endswith('xlsx') else pd.read_csv(file_e)
            df_z = pd.read_excel(file_z) if file_z.name.endswith('xlsx') else pd.read_csv(file_z)
            
            st.session_state.m4_plot_data = st.session_state.gibbs.calculate_deltas(df_e, df_z, g_h2o, g_h2, U=0.0)
            st.success("Thermodynamic data ready!")

    if 'm4_plot_data' in st.session_state:
        st.divider()
        u_slider = st.slider("Applied Potential (U vs RHE)", 0.0, 2.5, 1.23, step=0.01)
        fig = st.session_state.gibbs.create_plot(st.session_state.m4_plot_data, title, U_shift=u_slider)
        st.pyplot(fig)

# --- FOOTER ---
st.divider()
if st.button("Complete Module 4 🚀"):
    st.switch_page("pages/06_Module_5.py")