#!/bin/bash

# Pastikan script berjalan di direktori tempat file ini berada
cd "$(dirname "$0")"

echo "QE Tools"
echo ""

# 1. Cek apakah Python3 terinstall
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python3 tidak ditemukan!"
    echo "Silakan install Python dari python.org atau gunakan Homebrew (brew install python)."
    exit 1
fi

# 2. Cek/Buat Virtual Environment
if [ ! -d "env" ]; then
    echo "[INFO] Setup awal sedang berjalan... (Hanya sekali)"
    echo "[INFO] Membuat virtual environment..."
    python3 -m venv env
    
    echo "[INFO] Mengaktifkan environment..."
    source env/bin/activate
    
    echo "[INFO] Mengupgrade pip..."
    pip install --upgrade pip
    
    echo "[INFO] Menginstall library (perlu internet)..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "[WARNING] File requirements.txt tidak ditemukan!"
    fi
    
    echo "[INFO] Setup selesai!"
else
    echo "[INFO] Environment ditemukan. Mengaktifkan..."
    source env/bin/activate
fi

# 3. Jalankan Aplikasi
echo ""
echo "[INFO] Menjalankan Aplikasi Streamlit..."
echo "[INFO] Tekan Ctrl+C untuk berhenti."
echo ""

streamlit run Main_Menu.py

# Non-aktifkan environment setelah selesai
deactivate
