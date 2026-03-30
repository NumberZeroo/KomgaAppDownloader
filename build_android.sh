#!/bin/bash
# build_android.sh — Sincronizza, Builda, Installa e Avvia automaticamente

# CONFIGURAZIONE PERCORSI
WINDOWS_DIR="/mnt/c/Users/mluke/KomgaAppDownloader"
LINUX_DIR="$HOME/KomgaAppDownloader"
# Percorso ADB (usando quello scaricato da Buildozer)
ADB="$HOME/.buildozer/android/platform/android-sdk/platform-tools/adb"
PACKAGE_NAME="org.komga.komgadownloader"

echo "==> Pulizia e Sincronizzazione file..."

mkdir -p "$LINUX_DIR"
rm -rf "$LINUX_DIR/src"
rm -rf "$LINUX_DIR/ui"

mkdir -p "$LINUX_DIR/src"
mkdir -p "$LINUX_DIR/ui"
mkdir -p "$LINUX_DIR/bin"

cp "$WINDOWS_DIR/main.py"             "$LINUX_DIR/"
cp "$WINDOWS_DIR/buildozer.spec"      "$LINUX_DIR/"
cp "$WINDOWS_DIR/src/client.py"       "$LINUX_DIR/src/"
cp "$WINDOWS_DIR/src/models.py"       "$LINUX_DIR/src/"
cp "$WINDOWS_DIR/src/credentials.py"  "$LINUX_DIR/src/"
cp "$WINDOWS_DIR/ui/screens.py"       "$LINUX_DIR/ui/"
cp "$WINDOWS_DIR/ui/login.kv"         "$LINUX_DIR/ui/"
cp "$WINDOWS_DIR/ui/search.kv"        "$LINUX_DIR/ui/"
cp "$WINDOWS_DIR/ui/reader.kv"        "$LINUX_DIR/ui/"
cp "$WINDOWS_DIR/ui/series_books.kv"  "$LINUX_DIR/ui/"
cp "$WINDOWS_DIR/ui/downloads.kv"     "$LINUX_DIR/ui/"

echo "    ✅ Sincronizzazione completata."

echo "==> Avvio build APK con Buildozer..."
cd "$LINUX_DIR"
buildozer android debug

# Controllo esito build
if [ $? -eq 0 ]; then
    APK=$(ls -t "$LINUX_DIR/bin/"*.apk 2>/dev/null | head -1)
    if [ -n "$APK" ]; then
        # 1. Copia backup su Windows
        mkdir -p "$WINDOWS_DIR/bin"
        cp "$APK" "$WINDOWS_DIR/bin/"
        echo "✅ APK copiato in Windows: $WINDOWS_DIR/bin/$(basename "$APK")"

        # 2. Installazione sul telefono (sovrascrive la precedente)
        echo "==> 📲 Installazione sul telefono via WiFi..."
        $ADB install -r "$APK"

        if [ $? -eq 0 ]; then
             echo "✅ Installazione completata."
             # 3. Avvio automatico dell'app sul telefono
             echo "==> 🚀 Avvio app..."
             $ADB shell monkey -p $PACKAGE_NAME -c android.intent.category.LAUNCHER 1
        else
             echo "❌ Errore installazione. Verifica che il telefono sia connesso (adb connect)."
        fi
    fi
else
    echo ""
    echo "❌ Build fallita. Controlla i log sopra."
fi