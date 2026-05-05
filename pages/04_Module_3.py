import streamlit as st
import importlib
import io

# 1. LOGIC IMPORTS
module_logic = importlib.import_module("utils.04_Module_3")

# Initialize AdsorbateGenerator in session state
if 'ads_gen' not in st.session_state:
    st.session_state.ads_gen = module_logic.AdsorbateGenerator()

st.set_page_config(page_title="Module 3: Adsorbates", layout="wide")

# --- NAVIGATION HEADER ---
st.title("04 | Module 3: Adsorbate Generator")
col_nav, _ = st.columns([1, 5])
with col_nav:
    if st.button("⬅️ Back to Module 2"):
        st.switch_page("pages/03_Module_2.py")
st.divider()

# --- TABBED INTERFACE ---
tab1, tab2 = st.tabs(["Step 1: Slab Loading & Site Selection", "Step 2: Adsorbate Data Analysis"])

with tab1:
    st.subheader("Structure Setup")
    st.info("Upload a ZIP file containing your relaxed slab files (PW.in and PW.out)")

    uploaded_slab_zip = st.file_uploader("Upload Relaxed Slab ZIP (.zip)", type=["zip"], key="slab_uploader")

    if uploaded_slab_zip:
        # Teruskan raw bytes (tidak di-decode utf-8) ke backend
        zip_bytes = uploaded_slab_zip.getvalue()
        
        # Panggil fungsi load_slab dengan zip_bytes
        if st.session_state.ads_gen.load_slab(zip_bytes):
            st.success(f"Slab Loaded: {st.session_state.ads_gen.base_atoms.get_chemical_formula()}")
            
            # --- UPDATED SITE FINDING FORM ---
            with st.form("site_finder"):
                st.write("#### Global Site Detection")
                col_m, col_n = st.columns([2, 1])
                
                with col_m:
                    metals = st.multiselect(
                        "Active Elements to Include:", 
                        ["Ni", "Fe", "Co", "Mn", "Cu", "O"], 
                        default=["Ni", "Fe"]
                    )
                
                with col_n:
                    n_total = st.number_input(
                        "Total Top Atoms (Sum):", 
                        min_value=1, 
                        value=4, 
                        help="Select the top 'n' atoms total from all selected elements combined, based on highest Z-coordinates."
                    )

                if st.form_submit_button("Find Top Sites", type="primary"):
                    st.session_state.found_sites = st.session_state.ads_gen.find_top_sites(metals, n_total)

    # Render Site Selection results
    if st.session_state.get('found_sites'):
        st.divider()
        st.write(f"### Select Active Sites")
        selected_sites = []
        
        for site in st.session_state.found_sites:
            label = f"Site {site['index_qe']} ({site['symbol']}) at Z={site['z_coord']:.2f}"
            if st.checkbox(label, value=True, key=f"site_{site['index_qe']}"):
                selected_sites.append(site)
        
        st.write("### Reaction Package Configuration")
        package_choice = st.selectbox("Select Reaction:", ["OER (*H2O, *OH, *O, *OOH)", "HER (*H)", "Custom"])
        
        custom_dict = None
        if package_choice == "Custom":
            st.info("Define your custom variants. Format: FolderName: Adsorbate1, Adsorbate2. \nExample: `CO2RR: CO2, CO, HCOOH`")
            custom_input = st.text_area("Custom Variants Mapping:")
            if custom_input:
                try:
                    custom_dict = {}
                    lines = custom_input.strip().split('\n')
                    for line in lines:
                        if ':' in line:
                            folder, ads_str = line.split(':')
                            custom_dict[folder.strip()] = [x.strip() for x in ads_str.split(',')]
                except Exception as e:
                    st.error("Invalid custom format. Please follow the example.")
        
        if st.button("Generate Adsorbate Structures", type="primary"):
            if selected_sites:
                # Ambil nama package asli (OER, HER, atau Custom) tanpa teks dalam kurung
                pkg_name = package_choice.split(" ")[0] 
                
                with st.spinner("Generating intermediate coordinates..."):
                    # Panggil fungsi backend yang telah di-update
                    zip_data = st.session_state.ads_gen.build_adsorbates_zip(
                        selected_sites, 
                        reaction_package=pkg_name, 
                        custom_variants=custom_dict
                    )
                    st.download_button(
                        label=f"⬇️ Download {pkg_name}_Adsorbates.zip",
                        data=zip_data,
                        file_name=f"{pkg_name}_Adsorbates.zip",
                        mime="application/zip"
                    )
            else:
                st.warning("Please select at least one site to proceed.")

with tab2:
    st.subheader("Results Analysis")
    st.info("Upload the ZIP file containing all your optimized OER intermediate results.")

    if 'ads_analyzer' not in st.session_state:
        st.session_state.ads_analyzer = module_logic.AdsorbateAnalyzer()

    uploaded_results = st.file_uploader("Upload Results ZIP", type="zip", key="results_uploader")

    if uploaded_results:
        if st.button("Extract Energies & Group by Site", type="primary"):
            with st.spinner("Analyzing structural paths..."):
                df_results = st.session_state.ads_analyzer.process_zip(uploaded_results.getvalue())
                
                if not df_results.empty:
                    st.success(f"Successfully processed structures.")
                    df_display = df_results[df_results['Path'].notna()]
                    st.dataframe(
                        df_display[['Step', 'Site', 'Energy (Ry)']].style.format({"Energy (Ry)": "{:.6f}"}), 
                        use_container_width=True
                    )
                    
                    excel_data = st.session_state.ads_analyzer.generate_excel(df_results)
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_data,
                        file_name="oer_energy_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.warning("No valid OER data found. Check folder naming conventions.")

# --- FOOTER ---
st.divider()
if st.button("Complete Module 3 🚀"):
    st.switch_page("pages/05_Module_4.py")