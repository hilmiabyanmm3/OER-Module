# pages/09_File_Converter.py
import streamlit as st
import os
from pathlib import Path
from utils.file_converter import StructureConverter
from utils.ui_components import (
    module_header, 
    inject_global_css, 
    style_sidebar, 
    render_sidebar_progress
)

# Page Setup & Styling
st.set_page_config(
    page_title="Format Converter | CMD-ITB", 
    page_icon="https://img.icons8.com/?size=100&id=vtLGHdmfoSt8&format=png&color=000000",
    layout="wide"
)
inject_global_css()
style_sidebar()

module_header(
    "Tool", 
    "File Format Converter", 
    "Convert structure geometries across Quantum ESPRESSO, VASP, CIF, and XYZ"
)

# --- TRIGGER / CONFIGURATION ---
with st.container(border=True):
    col_in, col_out = st.columns(2)
    with col_in:
        input_ext = st.selectbox(
            "Input Extension",
            options=[".in", ".out", ".cif", ".vasp", ".xyz"],
            help="Select the format of the source structure file."
        )

    with col_out:
        available_outputs = [ext for ext in [".vasp", ".cif", ".xyz", ".in"] if ext != input_ext]
        output_ext = st.selectbox(
            "Target Extension",
            options=available_outputs,
            help="Select the converted target format."
        )

    input_mode = st.radio(
        "Upload Type",
        options=["Single File (Step 2a)", "Batch Archive (.zip) (Step 2b)"],
        horizontal=True
    )

st.divider()

# --- STEP 1: File Upload Filtered by Extension ---
st.subheader("Step 1: Upload Source File")

clean_in_ext = input_ext.lstrip('.')
uploaded_single = None
uploaded_zip = None

if "Single File" in input_mode:
    uploaded_single = st.file_uploader(
        f"Insert your *{input_ext} file",
        type=[clean_in_ext],
        key="single_converter_uploader"
    )
else:
    uploaded_zip = st.file_uploader(
        f"Insert a .ZIP archive containing *{input_ext} files",
        type=["zip"],
        key="zip_converter_uploader"
    )

# --- STEP 2: Processing & Output Destination ---
if uploaded_single or uploaded_zip:
    st.subheader("Step 2: Processing & Destination")

    output_dir_input = st.text_input(
        "Local Output Folder (Optional for direct server save)",
        value="converted_output",
        help="Creates this folder and saves the outputs on disk alongside the browser download."
    )

    clean_out_ext = output_ext.lstrip('.')

    # --- STEP 2a: Single File Conversion ---
    if "Single File" in input_mode and uploaded_single is not None:
        if st.button("Convert File", type="primary", use_container_width=True):
            try:
                converted_bytes = StructureConverter.convert_stream(
                    uploaded_single.getvalue(),
                    input_ext,
                    output_ext
                )

                orig_stem = Path(uploaded_single.name).stem
                new_filename = f"view_converted_{orig_stem}.{clean_out_ext}"

                if output_dir_input.strip():
                    os.makedirs(output_dir_input, exist_ok=True)
                    local_save_path = os.path.join(output_dir_input, new_filename)
                    with open(local_save_path, "wb") as f:
                        f.write(converted_bytes)
                    st.info(f"Local copy written to: `{local_save_path}`")

                # Step 3: Confirmation
                st.success("Step 3: Conversion successfully completed!")
                st.download_button(
                    label=f"Download Converted File ({new_filename}) ↓",
                    data=converted_bytes,
                    file_name=new_filename,
                    mime="application/octet-stream",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Conversion failed: {e}")

    # --- STEP 2b: Recursive ZIP Batch Processing ---
    elif "Batch Archive" in input_mode and uploaded_zip is not None:
        if st.button("Convert Batch Archive", type="primary", use_container_width=True):
            with st.spinner(f"Scanning archive recursively for *{input_ext} and converting to *{output_ext}..."):
                try:
                    result_zip_bytes = StructureConverter.process_zip_batch(
                        uploaded_zip.getvalue(),
                        input_ext,
                        output_ext
                    )

                    out_zip_name = f"view_converted_batch_{clean_out_ext}.zip"

                    if output_dir_input.strip():
                        os.makedirs(output_dir_input, exist_ok=True)
                        local_save_path = os.path.join(output_dir_input, out_zip_name)
                        with open(local_save_path, "wb") as f:
                            f.write(result_zip_bytes)
                        st.info(f"Local archive saved to: `{local_save_path}`")

                    # Step 3: Confirmation
                    st.success("Step 3: Batch archive converted successfully!")
                    st.download_button(
                        label=f"Download Processed Archive ({out_zip_name}) ↓",
                        data=result_zip_bytes,
                        file_name=out_zip_name,
                        mime="application/zip",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Batch conversion failed: {e}")

# Sidebar Progress (Synced to current state)
render_sidebar_progress(st.session_state.get('progress', 0))