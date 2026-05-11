import streamlit as st
import importlib
import io
from utils.ui_components import (
    module_header, 
    main_content_text, 
    sub_section_header, 
    highlight_box,
    inject_global_css,   
    style_sidebar,      
    render_sidebar_progress 
)

# --- 1. GLOBAL STYLING & CONFIG ---
st.set_page_config(
    page_title="Module 3: Adsorbate Modeling | CMD-ITB", 
    layout="wide"
)
inject_global_css()
style_sidebar()

# --- 2. LOGIC IMPORTS ---
try:
    module_logic = importlib.import_module("utils.04_Module_3")
except ImportError:
    st.error("Could not find the utility module: utils.04_Module_3")
    st.stop()

# Initialize AdsorbateGenerator in session state
if 'ads_gen' not in st.session_state:
    st.session_state.ads_gen = module_logic.AdsorbateGenerator()

# --- 3. NAVIGATION HEADER ---
module_header("03", "Adsorbate Modeling", "From clean slabs to intermediate reaction structures")


# --- 4. TABBED INTERFACE ---
tab1, tab2 = st.tabs(["Step 1: Site Selection", "Step 2: Energy Analysis"])

with tab1:
    st.subheader("Structure Setup")
    st.write("* Upload a zip file containing your relaxed slab (PW.in and PW.out). \n"
             "* Select elements for prospective active sites. \n"
             "* Specify how many top atoms to include. \n"
             "* Click 'Find Top Sites' to identify potential active sites based on Z-coordinates. \n"
             "* Select the site to which you want to add the adsorbate. \n"
             "* Choose a reaction package or define custom reactions. \n"
             "* Click 'Generate Adsorbate Structures'. \n")

    uploaded_slab_zip = st.file_uploader("Upload Relaxed Slab ZIP", type=["zip"], key="slab_uploader")

    if uploaded_slab_zip:
        zip_bytes = uploaded_slab_zip.getvalue()
        
        if st.session_state.ads_gen.load_slab(zip_bytes):
            st.success(f"Slab Loaded: {st.session_state.ads_gen.base_atoms.get_chemical_formula()}")
            
            # --- SITE FINDING FORM ---
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
                        "Total Top Atoms:", 
                        min_value=1, 
                        value=4, 
                        help="Select the top 'n' atoms based on highest Z-coordinates."
                    )

                if st.form_submit_button("Find Top Sites", type="primary"):
                    st.session_state.found_sites = st.session_state.ads_gen.find_top_sites(metals, n_total)

    # Render Site Selection results
    if st.session_state.get('found_sites'):
        st.divider()
        sub_section_header("Select Active Sites", icon_class="fa-solid fa-location-dot")
        selected_sites = []
        
        for site in st.session_state.found_sites:
            label = f"Site {site['index_qe']} ({site['symbol']}) at Z={site['z_coord']:.2f}"
            if st.checkbox(label, value=True, key=f"site_{site['index_qe']}"):
                selected_sites.append(site)
        
        st.write("### Reaction Configuration")
        package_choice = st.selectbox("Select Reaction Package:", ["OER (*H2O, *OH, *O, *OOH)", "HER (*H)", "Custom"])
        
        custom_dict = None
        if package_choice == "Custom":
            st.info("Define custom variants. Format: `FolderName: Adsorbate1, Adsorbate2`")
            custom_input = st.text_area("Custom Variants Mapping:")
            if custom_input:
                try:
                    custom_dict = {}
                    lines = custom_input.strip().split('\n')
                    for line in lines:
                        if ':' in line:
                            folder, ads_str = line.split(':')
                            custom_dict[folder.strip()] = [x.strip() for x in ads_str.split(',')]
                except Exception:
                    st.error("Invalid custom format. Please follow the required example.")
        
        if st.button("Generate Adsorbate Structures", type="primary", use_container_width=True):
            if selected_sites:
                pkg_name = package_choice.split(" ")[0] 
                
                with st.spinner("Generating intermediate coordinates..."):
                    zip_data = st.session_state.ads_gen.build_adsorbates_zip(
                        selected_sites, 
                        reaction_package=pkg_name, 
                        custom_variants=custom_dict
                    )
                    # Updated: Professional download style
                    st.download_button(
                        label=f"Download {pkg_name} Package (ZIP) ↓",
                        data=zip_data,
                        file_name=f"{pkg_name}_Adsorbates.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            else:
                st.warning("Please select at least one site to proceed.")

with tab2:
    st.subheader("Results Analysis")
    st.write("* Upload the zip file containing your optimized reaction intermediate results (.out files). \n"
             "* Specify the reference energies for isolated molecules (H2O, OH, O, OOH) in Rydberg (Ry). \n"
             "* Click 'Extract & Calculate Energies' to display the final energies and adsorption energies in tables. \n")

    if 'ads_analyzer' not in st.session_state:
        st.session_state.ads_analyzer = module_logic.AdsorbateAnalyzer()

    st.write("##### Reference Isolated Molecules")
    mol_configs = [("H2O", -34.2722502241), ("OH", -32.8706489556), ("O", -31.519078765), ("OOH", -64.6811961464)]
    cols = st.columns(len(mol_configs))
    
    isolated_energies = {
        mol: col.number_input(f"{mol} Energy (Ry)", value=val, format="%.10f") 
        for col, (mol, val) in zip(cols, mol_configs)
    }

    st.divider()
    st.write("##### System Information & Data Upload")
    col_cat, col_upload = st.columns([1, 2]) # Rasio lebar 1 : 2
    
    with col_cat:
        catalyst_name = st.text_input("Catalyst Name", value="NiFePO", help="This will be used as identifier.")
        
    with col_upload:
        uploaded_results = st.file_uploader("Upload Results ZIP (.out files)", type="zip", key="results_uploader")

    if uploaded_results and st.button("Extract & Calculate Energies", type="primary", use_container_width=True):
        with st.spinner("Analyzing structural paths and calculating energies..."):
            df_results = st.session_state.ads_analyzer.process_zip(uploaded_results.getvalue())
            
            # [CLEAN CODE] 3. Guard Clause: Tangani kegagalan di awal lalu stop (st.stop)
            if df_results.empty:
                st.warning("No valid OER data found. Check folder naming conventions.")
                st.stop()
                
            st.success("Successfully processed structures.")
            df_ads = st.session_state.ads_analyzer.calculate_adsorption_energies(df_results, isolated_energies)
            
            # --- TAMPILAN TABEL ---
            c1, c2 = st.columns(2)
            c1.write("**Final Energies (Ry)**")
            c1.dataframe(df_results.dropna(subset=['Path'])[['Step', 'Site', 'Energy (Ry)']].style.format({"Energy (Ry)": "{:.6f}"}), use_container_width=True)
            
            c2.write("**Adsorption Energies (eV)**")
            if not df_ads.empty:
                c2.dataframe(df_ads[['Step', 'Site', 'E_ads (eV)']].style.format({"E_ads (eV)": "{:.3f}"}), use_container_width=True)
            else:
                c2.warning("No adsorption data generated. Ensure 'slab' folder exists.")
            
            # --- DOWNLOAD BUTTONS ---
            dl1, dl2 = st.columns(2)
            dl1.download_button("Download Final Energies ↓", st.session_state.ads_analyzer.generate_excel(df_results), "Final_Energies.xlsx", use_container_width=True)
            dl2.download_button("Download Adsorption Energies ↓", st.session_state.ads_analyzer.generate_adsorption_excel(df_ads, isolated_energies, catalyst_name), "Adsorption_Energies.xlsx", use_container_width=True)

# --- 5. FOOTER NAVIGATION ---
st.divider()
col_b, col_n = st.columns([1, 4])

with col_b:
    # Standard Typographic Back Arrow
    if st.button("← Back"):
        st.switch_page("pages/03_Module_2.py")

with col_n:
    # Standard Typographic Forward Arrow with Primary Styling
    if st.button("Complete Module 3 →", type="primary", use_container_width=True):
        st.switch_page("pages/05_Module_4.py")

# --- 6. SIDEBAR PROGRESS ---
render_sidebar_progress(st.session_state.get('progress', 45))