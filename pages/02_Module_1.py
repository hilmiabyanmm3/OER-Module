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
    struct_file = st.file_uploader("Upload Bulk Structure (.cif / .vasp)", type=["cif", "vasp"])
    template_file = st.file_uploader("Upload Template .in", type=["in"])
    
    st.markdown("K-Points Grid")
    k_col1, k_col2, k_col3 = st.columns(3)
    val_kx = k_col1.number_input("Kx", min_value=1, value=6, step=1)
    val_ky = k_col2.number_input("Ky", min_value=1, value=6, step=1)
    val_kz = k_col3.number_input("Kz", min_value=1, value=3, step=1)

    if struct_file and template_file:
        if st.button("Generate Files"):
            file_extension = struct_file.name.split('.')[-1]
            struct_txt = struct_file.getvalue().decode("utf-8")
            temp_txt = template_file.getvalue().decode("utf-8")
            res_in, res_vasp = Manager.prepare_bulk_input(struct_txt, temp_txt, file_format=file_extension, kx=val_kx, ky=val_ky, kz=val_kz)

            with st.expander("Preview PW.in"):
                st.code(res_in, language='fortran')
    
            c1, c2 = st.columns(2)
            c1.download_button("Download .in", res_in, "bulk.in", use_container_width=True)
            c2.download_button("Download .vasp", res_vasp, "bulk.vasp", use_container_width=True)

with step2:
    st.subheader("Metal Variation Engine")
    st.write("Generate bulk structure variations by permuting atom types and create input files for each variation.")
    
    base_in = st.file_uploader("Upload Base Structure (.in)", type=["in"], key="base_in_step2")
    with st.form("variation_form"):
        comp_str = st.text_input("Composition/ratio", value="Ni:3, Fe:3", help="e.g. For replacing 6 atoms with 3 Ni and 3 Fe")
        st.caption("K-Points Grid")
        kc1, kc2, kc3 = st.columns(3)
        kx = kc1.number_input("Kx", value=6, min_value=1)
        ky = kc2.number_input("Ky", value=6, min_value=1)
        kz = kc3.number_input("Kz", value=3, min_value=1)

        generate_btn = st.form_submit_button("Generate Variations")

    if generate_btn and base_in:
        try:
            labels = []
            for part in comp_str.split(','):
                el, count = part.split(':')
                labels.extend([el.strip()] * int(count))
            
            response = Manager.generate_variations(base_in_content=base_in.getvalue().decode('utf-8'), target_metals=labels, kx=kx, ky=ky, kz=kz)
            
            if "error" in response:
                st.error(response["error"])
            else:
                variations = response["variations"]
                
                # Ekstrak kedua zip dari backend
                in_zip_data = response["in_zip_bytes"]
                vasp_zip_data = response["vasp_zip_bytes"]
                
                st.success(f"Success! Generated {len(variations)} unique variations.")
                
                with st.expander("Preview Variation 1 (PW.in)"):
                    st.code(variations[0]['qe_content'], language='fortran')

                c1, c2 = st.columns(2)
                c1.download_button("Download .in ZIP", in_zip_data, "qe_inputs.zip", use_container_width=True)
                c2.download_button("Download .vasp ZIP", vasp_zip_data, "vasp_structures.zip", use_container_width=True)

        except Exception as e:
            st.error(f"Error processing: {str(e)}")

with step3:
    st.subheader("Results Extraction")
    out_zip = st.file_uploader("Upload .out ZIP", type=["zip"])
    
    if out_zip and st.button("Extract & Sort Energies"):
        df_result, excel_data = Manager.extract_energies(out_zip)
        if df_result is not None and not df_result.empty:
            def highlight_min(s):
                    is_min = s['Relative Energy (eV)'] == 0.0
                    return ['background-color: #d4edda; color: black' if is_min else '' for _ in s]
            
            st.dataframe(df_result.style.format("{:.6f}", subset=["Energy (Ry)", "Energy (eV)", "Relative Energy (eV)"]).apply(highlight_min, axis=1), use_container_width=True)
            st.download_button("Download Excel", excel_data, "bulk_energies.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("No valid energy data found in the uploaded ZIP.")

# --- FOOTER NAVIGATION ---
st.divider()
if st.button("Complete & Move to Module 2 ➡️"):
    st.switch_page("pages/03_Module_2.py")