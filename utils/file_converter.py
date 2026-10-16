# utils/file_converter.py
import io
import os
import zipfile
from pathlib import Path
from ase.io import read, write

ASE_FORMAT_MAP = {
    '.in': 'espresso-in',
    '.out': 'espresso-out',
    '.cif': 'cif',
    '.vasp': 'vasp',
    '.xyz': 'xyz'
}

class StructureConverter:
    @staticmethod
    def get_ase_format(ext: str) -> str:
        return ASE_FORMAT_MAP.get(ext.lower(), None)

    @classmethod
    def convert_stream(cls, file_bytes: bytes, input_ext: str, output_ext: str) -> bytes:
        in_fmt = cls.get_ase_format(input_ext)
        out_fmt = cls.get_ase_format(output_ext)

        if not in_fmt or not out_fmt:
            raise ValueError(f"Unsupported format pair: {input_ext} -> {output_ext}")

        in_stream = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        # index='-1' retrieves the final relaxed frame from .out / trajectories
        atoms = read(in_stream, format=in_fmt, index='-1')

        out_stream = io.StringIO()
        write(out_stream, atoms, format=out_fmt)
        return out_stream.getvalue().encode('utf-8')

    @classmethod
    def process_zip_batch(cls, zip_bytes: bytes, input_ext: str, output_ext: str) -> bytes:
        out_buffer = io.BytesIO()

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as in_zip:
            with zipfile.ZipFile(out_buffer, 'w', zipfile.ZIP_DEFLATED) as out_zip:
                for file_path in in_zip.namelist():
                    if file_path.endswith('/') or '__MACOSX' in file_path:
                        continue

                    if file_path.lower().endswith(input_ext.lower()):
                        raw_data = in_zip.read(file_path)
                        try:
                            converted_data = cls.convert_stream(raw_data, input_ext, output_ext)

                            parent_dir = os.path.dirname(file_path)
                            orig_stem = Path(file_path).stem
                            clean_out_ext = output_ext.lstrip('.')
                            new_filename = f"view_converted_{orig_stem}.{clean_out_ext}"

                            dest_path = f"{parent_dir}/{new_filename}" if parent_dir else new_filename
                            out_zip.writestr(dest_path, converted_data)
                        except Exception:
                            continue

        out_buffer.seek(0)
        return out_buffer.getvalue()

    