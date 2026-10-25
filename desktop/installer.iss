; AselCam Studio - Windows Installer Script (Inno Setup 6)
; Automatic installation of application, DirectShow Virtual Camera & Virtual Audio Drivers

#define MyAppName "AselCam Studio"
#define MyAppVersion "1.4.9"
#define MyAppPublisher "Aselens Technologies"
#define MyAppURL "https://aselcam.aselens.com"
#define MyAppExeName "AselCam.exe"

[Setup]
AppId={{E68A8D2A-0A74-4C3D-9477-7678D5B48001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\AselCam
DefaultGroupName=AselCam Studio
DisableProgramGroupPage=yes
OutputDir=..\releases\windows
OutputBaseFilename=AselCam-v1.4.9-Windows-Setup
SetupIconFile=aselcam\assets\aselcam_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copy all dist files into {app}
Source: "dist\AselCam\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\aselcam\assets\aselcam_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\aselcam\assets\aselcam_icon.ico"; Tasks: desktopicon

[Registry]
; 64-bit DirectShow FriendlyName
Root: HKLM64; Subkey: "SOFTWARE\Classes\CLSID\{{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{{5C2CD55C-92AD-4999-8666-912BD3E70010}"; ValueType: string; ValueName: "FriendlyName"; ValueData: "AselCam Virtual Camera"; Flags: createvalueifdoesntexist uninsdeletekey; Check: IsWin64
; 32-bit DirectShow FriendlyName (For 32-bit Discord, Chrome, etc. in WOW6432Node)
Root: HKLM32; Subkey: "SOFTWARE\Classes\CLSID\{{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{{5C2CD55C-92AD-4999-8666-912BD3E70010}"; ValueType: string; ValueName: "FriendlyName"; ValueData: "AselCam Virtual Camera"; Flags: createvalueifdoesntexist uninsdeletekey; Check: IsWin64
; HKCR DirectShow FriendlyName
Root: HKCR; Subkey: "CLSID\{{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{{5C2CD55C-92AD-4999-8666-912BD3E70010}"; ValueType: string; ValueName: "FriendlyName"; ValueData: "AselCam Virtual Camera"; Flags: createvalueifdoesntexist uninsdeletekey

[Run]
; 1. Register 64-bit DirectShow Virtual Camera Filter
Filename: "{sys}\regsvr32.exe"; Parameters: "/s ""{app}\_internal\aselcam\drivers\windows\UnityCaptureFilter64.dll"""; StatusMsg: "AselCam Sanal Kamera (64-bit) kaydediliyor..."; Flags: runhidden
; 2. Register 32-bit DirectShow Virtual Camera Filter (for Discord, Zoom, Chrome)
Filename: "{syswow64}\regsvr32.exe"; Parameters: "/s ""{app}\_internal\aselcam\drivers\windows\UnityCaptureFilter32.dll"""; StatusMsg: "AselCam Sanal Kamera (32-bit Discord/Tarayıcı) kaydediliyor..."; Flags: runhidden; Check: IsWin64
; 3. Install Virtual Audio Driver via PnPUtil
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\_internal\aselcam\drivers\windows\VirtualAudioDriver.inf"" /install"; StatusMsg: "AselCam Sanal Mikrofon sürücüsü kuruluyor..."; Flags: runhidden
; 4. Optional Launch After Install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Unregister DirectShow Filters cleanly on uninstall
Filename: "{sys}\regsvr32.exe"; Parameters: "/u /s ""{app}\_internal\aselcam\drivers\windows\UnityCaptureFilter64.dll"""; Flags: runhidden
Filename: "{syswow64}\regsvr32.exe"; Parameters: "/u /s ""{app}\_internal\aselcam\drivers\windows\UnityCaptureFilter32.dll"""; Flags: runhidden; Check: IsWin64
