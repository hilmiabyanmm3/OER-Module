import streamlit as st
import importlib

# Logic Import
module_logic = importlib.import_module("utils.02_Module_1")
Manager = module_logic.BulkWorkflowManager()

st.set_page_config(page_title="Module 1: Workflow", layout="wide")

st.title("02 | Module 1: Bulk & Variations")

# --- TOP NAVIGATION ---
col1, _ = st.columns([1, 5])
with col1:
    if st.button("⬅️ Back"):
        st.switch_page("pages/01_Pre-requisite.py")

st.divider()

# --- WORKFLOW TABS ---
step1, step2, step3 = st.tabs(["Step 1: Bulk Prep", "Step 2: Variation", "Step 3: Energy Analysis"])

with step1:
    st.subheader("Structure & Template Setup")
    cif_file = st.file_uploader("Upload Bulk .cif", type=["cif"])
    template_file = st.file_uploader("Upload Template .in", type=["in"])
    
    if cif_file and template_file:
        if st.button("Generate Files"):
            cif_txt = cif_file.getvalue().decode("utf-8")
            temp_txt = template_file.getvalue().decode("utf-8")
            res_in, res_vasp = Manager.prepare_bulk_input(cif_txt, temp_txt)
            
            st.download_button("Download .in", res_in, "bulk.in")
            st.download_button("Download .vasp", res_vasp, "bulk.vasp")

# (Keep the navigation code from the previous response)
# ... inside Step 2 Tab ...
with step2:
    st.subheader("Metal Variation Engine")
    st.write("This tool will create 5 random distributions based on your target ratio.")
    
    base_in = st.file_uploader("Upload Base .in / .vasp", type=["in", "vasp"])
    ratio_input = st.text_input("Metal Ratios", value="Fe:0.5, Ni:0.5", help="Format: Metal:Ratio, Metal:Ratio")
    
    if base_in and st.button("Generate Variations"):
        with st.spinner("Calculating permutations..."):
            in_zip, vasp_zip = Manager.generate_variations(base_in.getvalue().decode(), ratio_input)
            
            c1, c2 = st.columns(2)
            c1.download_button("🎁 Download .in ZIP", in_zip, "qe_inputs.zip", use_container_width=True)
            c2.download_button("💎 Download VASP ZIP", vasp_zip, "vasp_structures.zip", use_container_width=True)

with step3:
    st.subheader("Results Extraction")
    out_zip = st.file_uploader("Upload .out ZIP", type=["zip"])
    
    if out_zip and st.button("Extract & Sort Energies"):
        excel_data = Manager.extract_energies(out_zip)
        st.download_button("Download Energy Excel", excel_data, "oer_energies.xlsx")

# --- FOOTER NAVIGATION ---
st.divider()
if st.button("Complete & Move to Module 2 ➡️"):
    st.switch_page("pages/03_Module_2.py")