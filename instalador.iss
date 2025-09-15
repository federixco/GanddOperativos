; Script de instalación Inno Setup para GanddOperativos
; Este archivo crea un instalador profesional con wizard

#define MyAppName "TimeSlice"
#define MyAppVersion "1.0"
#define MyAppPublisher "Federico Gabriel Arena"
#define MyAppURL "https://github.com/Federixco/GanddOperativos"
#define MyAppExeName "TimeSlice.exe"

[Setup]
; Información básica de la aplicación
AppId={{F47AC10B-58CC-4CA2-9496-6B2F24472422}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Configuración del instalador
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
InfoBeforeFile=INFO.txt
InfoAfterFile=AFTER_INSTALL.txt
OutputDir=Instalador_Final
OutputBaseFilename=TimeSlice_Instalador
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Requisitos del sistema
MinVersion=6.1sp1
PrivilegesRequired=admin

; Configuración visual
; WizardImageFile=wizard.bmp
; WizardSmallImageFile=wizard_small.bmp
DisableProgramGroupPage=yes
DisableReadyPage=no
DisableFinishedPage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Archivo principal del programa
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Archivos de documentación
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

; Archivos de datos del programa
Source: "utils\input_historial.json"; DestDir: "{app}\utils"; Flags: ignoreversion
Source: "sistema_completo.txt"; DestDir: "{app}"; Flags: ignoreversion

; NOTA: No use "Flags: ignoreversion" en ningún archivo compartido del sistema

[Icons]
; Icono en el menú inicio
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Icono en el escritorio (opcional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

; Icono en la barra de tareas (solo Windows XP)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Opción para ejecutar el programa después de la instalación
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Código personalizado para el instalador

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Crear carpeta de datos del usuario si no existe
    ForceDirectories(ExpandConstant('{userdocs}\GanddOperativos\Datos'));
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Limpiar archivos temporales del usuario (opcional)
    DelTree(ExpandConstant('{userdocs}\GanddOperativos\Temp'), True, True, True);
  end;
end;
