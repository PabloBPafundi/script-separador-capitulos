#!/usr/bin/env bash
# Instala PDF Chapter Splitter para el usuario actual, sin sudo.
# Uso: ejecutar este script desde la carpeta descomprimida del release
# (junto a bin/, pdf-chapter-splitter.desktop.template, icon.png).

set -eu

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/opt/pdf-chapter-splitter"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "Instalando PDF Chapter Splitter en $INSTALL_DIR ..."

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$APPS_DIR" "$ICONS_DIR"

cp "$SCRIPT_DIR/bin/pdf-chapter-splitter-gui" "$INSTALL_DIR/pdf-chapter-splitter-gui"
cp "$SCRIPT_DIR/bin/pdf-chapter-splitter" "$INSTALL_DIR/pdf-chapter-splitter"
chmod +x "$INSTALL_DIR/pdf-chapter-splitter-gui" "$INSTALL_DIR/pdf-chapter-splitter"

cp "$SCRIPT_DIR/icon.png" "$ICONS_DIR/pdf-chapter-splitter.png"

ln -sf "$INSTALL_DIR/pdf-chapter-splitter" "$BIN_DIR/pdf-chapter-splitter"

sed \
    -e "s#__EXEC__#$INSTALL_DIR/pdf-chapter-splitter-gui#g" \
    -e "s#__ICON__#pdf-chapter-splitter#g" \
    "$SCRIPT_DIR/pdf-chapter-splitter.desktop.template" > "$APPS_DIR/pdf-chapter-splitter.desktop"

cat > "$INSTALL_DIR/uninstall.sh" <<EOF
#!/usr/bin/env bash
set -eu
rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/pdf-chapter-splitter"
rm -f "$ICONS_DIR/pdf-chapter-splitter.png"
rm -f "$APPS_DIR/pdf-chapter-splitter.desktop"
rm -f "$APPS_DIR/pdf-chapter-splitter-uninstall.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true
echo "PDF Chapter Splitter desinstalado."
EOF
chmod +x "$INSTALL_DIR/uninstall.sh"

sed \
    -e "s#__EXEC__#$INSTALL_DIR/uninstall.sh#g" \
    -e "s#__ICON__#pdf-chapter-splitter#g" \
    "$SCRIPT_DIR/pdf-chapter-splitter-uninstall.desktop.template" > "$APPS_DIR/pdf-chapter-splitter-uninstall.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" || true
fi

echo "Listo. Buscá 'PDF Chapter Splitter' en el menú de aplicaciones."
echo "La CLI queda disponible como: pdf-chapter-splitter"
echo "Para desinstalar: $INSTALL_DIR/uninstall.sh"
