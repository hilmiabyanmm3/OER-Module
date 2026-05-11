# pages/03_Module_2.py
import importlib
import streamlit as st
import pandas as pd
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
    page_title="Module 2: Slab Optimization | CMD-ITB", 
    layout="wide"
)
inject_global_css()
style_sidebar()

# --- 2. DYNAMIC IMPORT ---
try:
    module_logic = importlib.import_module("utils.03_Module_2")
    SurfaceGenerator = module_logic.SurfaceGenerator
    SurfaceAnalyzer = module_logic.SurfaceAnalyzer
except ImportError:
    st.error("Could not find the utility module: utils.03_Module_2")
    st.stop()

# --- 3. HEADER ---
module_header("02", "Slab Design & Analysis", "Conversion of bulk structures to slabs and surface stability analysis")

# --- 4. TOP NAVIGATION ---

# --- 5. WORKFLOW TABS ---
tab1, tab2 = st.tabs(["Step 1: Surface Builder", "Step 2: Surface Energy Analyzer"])

# --- STEP 1: SURFACE BUILDER ---
with tab1:
    st.subheader("Slab Generation")
    st.write("Generate slab structures from relaxed bulk structures. \n"
             "* Upload bulk relaxation results (.out) \n" 
             "* Upload template file (.in) containing the desired settings for QE calculations. \n"
             "* Specify Miller index, number of layers, vacuum thickness, and supercell dimensions. \n"
             "* Choose the portion of the top layer to remain free (not fixed) during relaxation. \n"
             "* Click 'Generate Slab' to create the slab structure. \n"
    )
    
    # 1. Coordinate and Template Uploaders
    c1, c2 = st.columns(2)
    with c1:
        uploaded_bulk = st.file_uploader("Upload Bulk .out", type=["out", "log"], key="b_out")
    with c2:
        template_in = st.file_uploader("Upload Template .in", type=["in"], key="t_in")

    # 2. Results Session State Initialization
    if 'slab_results' not in st.session_state:
        st.session_state.slab_results = None

    if uploaded_bulk and template_in:
        try:
            # Initialize the generator from the utility file
            generator = SurfaceGenerator.from_out_and_template(
                uploaded_bulk.getvalue().decode(), 
                template_in.getvalue().decode()
            )
            st.success(f"Bulk Loaded: {generator.bulk_atoms.get_chemical_formula()}")

            # 3. The Parameters Form
            with st.form("slab_form"):
                col1, col2, col3 = st.columns(3)
                miller = col1.text_input("Miller Index (h,k,l)", "1,0,0")
                layers = col2.number_input("Layers", 1, 10, 3)
                vacuum = col3.number_input("Vacuum (Å)", 0.0, 50.0, 15.0)
                
                sc_x = col1.number_input("X Repeat", 1, 5, 2)
                sc_y = col2.number_input("Y Repeat", 1, 5, 1)
                sc_z = col3.number_input("Z Repeat", 1, 5, 1)

                k_col1, k_col2, k_col3 = st.columns(3)
                k_x = k_col1.number_input("Kx", 1, 20, 4)
                k_y = k_col2.number_input("Ky", 1, 20, 4)
                k_z = k_col3.number_input("Kz", 1, 20, 1) # Usually 1 for slabs

                # Fraction of the top layer to remain mobile
                free_choice = st.selectbox(
                    "Portion of top atoms to remain FREE (not fixed)",
                    options=[0.25, 0.33, 0.50, 1.0],
                    format_func=lambda x: "All atoms (100%)" if x == 1.0 else f"Top {int(x*100)}% (≈ 1/{int(1/x)})"
                )

                submit_clicked = st.form_submit_button("Generate Slab")
                
                if submit_clicked:
                    with st.spinner("Cutting slab and applying constraints..."):
                        # Calculate results and store in session state
                        zip_bytes, preview = generator.process_and_zip(
                            miller, layers, vacuum, [sc_x, sc_y, sc_z], kpts=[k_x, k_y, k_z], free_fraction=free_choice
                        )
                        st.session_state.slab_results = (zip_bytes, preview)
        
        except Exception as e:
            st.error(f"Error initializing structure: {e}")

    # 4. Output Display
    if st.session_state.slab_results:
        zip_bytes, preview = st.session_state.slab_results
        
        st.success(f"Slab Generated Successfully! {preview['fixed_info']}")
        
        # Display the QE input header and coordinate preview
        with st.expander("Preview PW.in"):
                st.code(preview['top_pw_in'], language='fortran')
        
        # Updated: Professional download style
        st.download_button(
            label="Download Slab Package (ZIP) ↓", 
            data=zip_bytes, 
            file_name=f"slab_{preview['folder']}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

# --- STEP 2: ANALYZER ---
with tab2:
    st.subheader("Surface Energy")
    st.write("Calculate surface energy using relaxed bulk and slab outputs. \n"
             "* Upload the relaxed bulk output file (.out) \n"
             "* Upload a zip file containing the input and output files for the relaxed slab. \n"
             "* Click 'Calculate Surface Energy' to display the results in a table. \n")

    c1, c2 = st.columns(2)
    with c1:
        bulk_file = st.file_uploader("Relaxed Bulk (.out)", type=["out", "log"], key="ana_bulk")
    with c2:
        slabs_zip = st.file_uploader("Relaxed Slabs (.zip)", type=["zip"], key="ana_zip")

    if bulk_file and slabs_zip:
        if st.button("Calculate Surface Energies", type="primary", use_container_width=True):
            try:
                analyzer = SurfaceAnalyzer(bulk_file.getvalue().decode())
                results = analyzer.process_slab_zip(slabs_zip.getvalue())
                if results:
                    df = pd.DataFrame(results)
                    st.dataframe(df.style.format("{:.4f}", subset=["Surface Energy (J/m²)", "Surface Energy (eV/Å²)"]), use_container_width=True)
                    # Updated: Professional download style
                    st.download_button("Download Excel Report ↓", analyzer.generate_excel(results), "surface_energies.xlsx", use_container_width=True)
                else:
                    st.warning("No valid energy data found.")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

# --- 6. FOOTER NAVIGATION ---
st.divider()
col_b, col_n = st.columns([1, 4])

with col_b:
    # Standard Typographic Back Arrow
    if st.button("← Back"):
        st.switch_page("pages/02_Module_1.py")

with col_n:
    # Standard Typographic Forward Arrow with Primary Styling
    if st.button("Complete Module 2 →", type="primary", use_container_width=True):
        st.switch_page("pages/04_Module_3.py")

# --- 7. SIDEBAR PROGRESS ---
render_sidebar_progress(st.session_state.get('progress', 30))