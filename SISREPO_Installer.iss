#define MyAppName "SISREPO"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "JVRaiol"
#define MyAppURL "https://github.com/JVRaiol/SISREPO"
#define MyAppExeName "SISREPO.exe"

[Setup]
AppId={{8C7C1A2E-6A6B-4BC1-9F4D-2F6C8E3B91A7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
OutputDir=installer
OutputBaseFilename=SISREPO_Setup
SetupIconFile=templates\logobpav.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Dirs]
Name: "{userappdata}\SISREPO"

[Files]
; Copia toda a distribuição produzida pelo PyInstaller.
; Não incluir .env, registroUser.json ou dados do usuário neste pacote.
Source: "dist\SISREPO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar o SISREPO"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
