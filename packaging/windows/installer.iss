#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName "Anatomia Viva 3D"
#define AppExeName "AnatomiaViva3D.exe"
#define ProjectRoot "..\.."

[Setup]
AppId={{5D11CA91-E738-4F77-8778-341353B54F47}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Luiz Paulo Antunes
AppPublisherURL=https://github.com/luizpaulo-antunes/anatomia-viva-3d
AppSupportURL=https://github.com/luizpaulo-antunes/anatomia-viva-3d/issues
DefaultDirName={localappdata}\Programs\Anatomia Viva 3D
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile={#ProjectRoot}\LICENSE
OutputDir={#ProjectRoot}\release
OutputBaseFilename=AnatomiaViva3D-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "{#ProjectRoot}\dist\AnatomiaViva3D\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent
