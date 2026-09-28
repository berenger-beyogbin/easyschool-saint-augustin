#define MyAppName "Easy School CJGA"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "CJGA"
#define MyAppExeName "EasySchool.exe"

[Setup]
AppId={{D1B33C50-2D19-4D13-8D59-9BE54B7E934A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\EasySchool
DisableDirPage=auto
DisableProgramGroupPage=yes
OutputDir=dist\EasySchool_Update_v2.2.0
OutputBaseFilename=EasySchool_CJGA_Mise_A_Jour_v2.2.0
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "dist_update_latest\EasySchool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
var
  EnvBackupPath: String;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  EnvPath: String;
begin
  Result := '';
  EnvPath := ExpandConstant('{app}\.env');
  EnvBackupPath := ExpandConstant('{app}\.env.avant-mise-a-jour-v2.2.0');
  if not FileExists(EnvPath) then
  begin
    Result := 'Configuration .env introuvable dans ' + ExpandConstant('{app}') +
      '. Installez d''abord Easy School ou sélectionnez son dossier actuel.';
    exit;
  end;
  if not CopyFile(EnvPath, EnvBackupPath, False) then
    Result := 'Impossible de sauvegarder le fichier de configuration .env.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if not Exec(
      ExpandConstant('{app}\{#MyAppExeName}'),
      '--migrate',
      ExpandConstant('{app}'),
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    ) or (ResultCode <> 0) then
      RaiseException(
        'La mise à jour des fichiers est terminée, mais la migration de la base a échoué.' + #13#10 +
        'Consultez le journal dans %LOCALAPPDATA%\EasySchool\logs\easy_school.log.'
      );
  end;
end;
