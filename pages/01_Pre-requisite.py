import streamlit as st
from utils.ui_components import (
    module_header, 
    main_content_text, 
    sub_section_header, 
    highlight_box,
    inject_global_css,   
    style_sidebar,      
    render_sidebar_progress 
)

# --- 1. GLOBAL STYLING ---
# Ensure the modern font and Font Awesome are loaded
inject_global_css()
style_sidebar()

# --- 2. LAYOUT SETUP ---
left, mid, right = st.columns([1, 4, 1])

with mid:
    # --- 3. HEADER ---
    module_header("PRE", "Pre-requisite", "Essential tools and resources for OER modeling")

    main_content_text("""
        To ensure a smooth transition from theory to computation, please verify that your 
        local workstation is equipped with the following software and data access. 
        These tools will be used throughout the 7 modules.
    """)

    # --- 4. DATA SOURCE (Materials Project) ---
    # Updated: Database icon
    sub_section_header("1. Bulk Data Source", icon_class="fa-solid fa-database")
    main_content_text("""
        We will use the <b>Materials Project</b> database to obtain the initial 
        crystal structures for our Nickel Phosphate models.
    """)
    st.link_button("Access Materials Project", "https://next-gen.materialsproject.org/materials")
    
    highlight_box("""
        <b>Tip:</b> Always record the unique <b>Material ID (mp-id)</b> of your bulk structure. 
        This 'fingerprint' ensures your research is reproducible.
    """, type="info")

    # --- 5. VISUALIZATION (VESTA) ---
    # Updated: 3D Cube icon
    sub_section_header("2. Model Visualization", icon_class="fa-solid fa-cube")
    main_content_text("""
        <b>VESTA</b> (Visualization for Electronic and Structural Analysis) is required 
        for inspecting our 3D crystal structures, verifying slab cuts, and 
        visualizing electron density.
    """)
    st.link_button("Download VESTA", "https://www.jp-minerals.org/vesta/en/download.html")

    # --- 6. PYTHON ENVIRONMENT ---
    # Updated: Code icon
    sub_section_header("3. Python Environment", icon_class="fa-solid fa-code")
    main_content_text("""Required for executing simulation scripts and backend dependencies.""")
    
    col_py1, col_py2, col_py3 = st.columns(3)
    with col_py1:
        st.link_button("Python for Windows", "https://www.python.org/downloads/windows/")
    with col_py2:
        st.link_button("Python for macOS", "https://www.python.org/downloads/macos/")
    with col_py3:
        st.link_button("Python for Linux", "https://www.python.org/downloads/source/")

    # --- 7. DOWNLOAD INPUT FILES ---
    # Updated: Download icon
    sub_section_header("4. Download Input Files", icon_class="fa-solid fa-download")
    main_content_text("""
        Download the specific input templates, pseudo-potentials, and reference data 
        required for the <b>NiFePO</b> OER simulation modules.
    """)
    
    st.link_button("Download Input Files", "https://drive.google.com/drive/folders/1YgqMfzjpEIW3pUAWATGuSstM95r9pO8r?usp=sharing")

    # --- 8. READINESS CHECK ---
    st.divider()
    # Updated: Clipboard Check icon
    sub_section_header("Readiness Check", icon_class="fa-solid fa-clipboard-check")
    
    ready = st.checkbox("I have setup my Pre-requisite and downloaded the necessary files.")
    
    if ready:
        # We can update session state progress here
        st.session_state['progress'] = 5 
        st.success("Pre-requisite setup complete! You are ready to begin.")
        if st.button("Proceed to Module 1: Bulk Setup →", use_container_width=True):
            st.switch_page("pages/02_Module_1.py")
    else:
        st.warning("Please finalize your pre-requisite before proceeding.")

# --- 9. RENDER SIDEBAR PROGRESS ---
# Optional: Keeps the progress bar in sync even on sub-pages
render_sidebar_progress(st.session_state.get('progress', 0))