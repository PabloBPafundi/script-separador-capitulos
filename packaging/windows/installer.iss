; Instalador de PDF Chapter Splitter para Windows (Inno Setup).
; Se compila desde la raíz del repo: iscc packaging\windows\installer.iss
; Requiere que dist\pdf-chapter-splitter-gui.exe y dist\pdf-chapter-splitter.exe
; ya estén compilados (ver .github/workflows/release.yml).

#define MyAppName "PDF Chapter Splitter"
; MyAppVersion se pasa desde la línea de comandos: iscc /DMyAppVersion=1.2.3 ...
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{B7B6C6C0-6E9B-4B5E-9C7D-9D9F1B2E9A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
; Instalación por usuario: sin UAC, sin necesidad de admin/sudo, y compatible
; con la auto-actualización de un clic (el proceso puede reemplazarse a sí
; mismo porque el directorio queda bajo el propio usuario).
PrivilegesRequired=lowest
DefaultDirName={localappdata}\PDFChapterSplitter
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=pdf-chapter-splitter-gui-setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\pdf-chapter-splitter-gui.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\pdf-chapter-splitter-gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\pdf-chapter-splitter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\pdf-chapter-splitter-gui.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\pdf-chapter-splitter-gui.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos adicionales:"

[Run]
Filename: "{app}\pdf-chapter-splitter-gui.exe"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
