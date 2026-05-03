@echo off
TITLE QE Tools
CLS

:: 1. Cek apakah Python terinstall
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python tidak terdeteksi di komputer ini!
    echo Silakan install Python dari python.org dan pastikan centang "Add to PATH".
    PAUSE
    EXIT /B
)

:: 2. Cek apakah Virtual Environment sudah ada
IF NOT EXIST "env" (
    echo [INFO] Setup awal sedang berjalan... (Hanya sekali)
    echo [INFO] Membuat virtual environment...
    python -m venv env
    
    echo [INFO] Mengaktifkan environment...
    call env\Scripts\activate
    
    echo [INFO] Mengupgrade pip...
    python -m pip install --upgrade pip
    
    echo [INFO] Menginstall library yang dibutuhkan (perlu internet)...
    pip install -r requirements.txt
    
    echo [INFO] Setup selesai!
) ELSE (
    echo [INFO] Environment ditemukan. Mengaktifkan...
    call env\Scripts\activate
)

:: 3. Jalankan Aplikasi Streamlit
echo.
echo [INFO] Menjalankan Aplikasi Streamlit...
echo [INFO] Tekan Ctrl+C di jendela ini untuk berhenti.
echo.

:: Menjalankan streamlit & membuka browser otomatis
streamlit run Main_Menu.py

PAUSE