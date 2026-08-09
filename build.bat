@echo off
REM ============================================================
REM  4R022 SAAT - Windows Yerel Derleme (Build) Betigi
REM ============================================================
REM  Bu betik, bilgisayarinizda Python kuruluysa 4R022_Saat.py
REM  dosyasini tek parca, konsolsuz bir .exe dosyasina donusturur.
REM  Sonuc dosya "dist\4R022_Saat.exe" olarak olusur.
REM
REM  Kullanim: Bu dosyaya cift tiklayin veya bir komut satirindan
REM            "build.bat" yazip calistirin.
REM ============================================================

echo.
echo === 4R022 SAAT - Derleme baslatiliyor ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi. Lutfen once Python 3.10+ kurun:
    echo        https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Gerekli paketler yukleniyor...
python -m pip install --upgrade pip >nul
pip install pyinstaller >nul
if exist requirements.txt (
    pip install -r requirements.txt >nul
)

echo [2/3] PyInstaller ile .exe olusturuluyor...
pyinstaller 4R022_Saat.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [HATA] Derleme basarisiz oldu. Yukaridaki mesajlari kontrol edin.
    pause
    exit /b 1
)

echo [3/3] Tamamlandi!
echo.
echo ==============================================
echo   4R022_Saat.exe dosyaniz hazir:
echo   dist\4R022_Saat.exe
echo ==============================================
echo.
pause
