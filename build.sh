#!/usr/bin/env bash
# ============================================================
#  4R022 SAAT - Linux / macOS Yerel Derleme (Build) Betigi
# ============================================================
#  Bu betik, 4R022_Saat.py dosyasini tek parca bir calistirilabilir
#  dosyaya donusturur. Sonuc dosya "dist/4R022_Saat" olarak olusur.
#
#  Kullanim:
#    chmod +x build.sh
#    ./build.sh
# ============================================================

set -e

echo ""
echo "=== 4R022 SAAT - Derleme baslatiliyor ==="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[HATA] python3 bulunamadi. Lutfen once Python 3.10+ kurun."
    exit 1
fi

echo "[1/3] Gerekli paketler yukleniyor..."
python3 -m pip install --upgrade pip --quiet
pip install pyinstaller --quiet
if [ -f requirements.txt ]; then
    pip install -r requirements.txt --quiet
fi

echo "[2/3] PyInstaller ile calistirilabilir dosya olusturuluyor..."
pyinstaller 4R022_Saat.spec --noconfirm

echo "[3/3] Tamamlandi!"
echo ""
echo "=============================================="
echo "  Calistirilabilir dosyaniz hazir: dist/4R022_Saat"
echo "=============================================="
echo ""
