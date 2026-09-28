#define MyAppName "Easy School CJGA"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "CJGA"
#define MyAppExeName "EasySchool.exe"

[Setup]
AppId={{D1B33C50-2D19-4D13-8D59-9BE54B7E934A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\EasySchool
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist\EasySchool_Installation_v2.1.0\2_Client
OutputBaseFilename=EasySchool_CJGA_Client_Setup_v2.1.0
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

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Files]
Source: "dist_client_latest\EasySchool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
var
  ServerPage: TInputQueryWizardPage;
  DatabasePage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ServerPage := CreateInputQueryPage(
    wpSelectDir,
    'Connexion au serveur Easy School',
    'Indiquez le serveur PostgreSQL déjà configuré.',
    'Ces informations seront enregistrées uniquement sur ce poste client.'
  );
  ServerPage.Add('Adresse IP ou nom du serveur :', False);
  ServerPage.Add('Port PostgreSQL :', False);
  ServerPage.Values[1] := '5432';

  DatabasePage := CreateInputQueryPage(
    ServerPage.ID,
    'Base de données Easy School',
    'Indiquez les identifiants de connexion de l''application.',
    'Utilisez les mêmes paramètres que ceux configurés sur le serveur.'
  );
  DatabasePage.Add('Nom de la base :', False);
  DatabasePage.Add('Utilisateur :', False);
  DatabasePage.Add('Mot de passe :', True);
  DatabasePage.Values[0] := 'easy_school_cjga_db';
  DatabasePage.Values[1] := 'easy_school_app';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ServerPage.ID then
  begin
    if Trim(ServerPage.Values[0]) = '' then
    begin
      MsgBox('Veuillez saisir l''adresse IP ou le nom du serveur.', mbError, MB_OK);
      Result := False;
    end
    else if Trim(ServerPage.Values[1]) = '' then
    begin
      MsgBox('Veuillez saisir le port PostgreSQL.', mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = DatabasePage.ID then
  begin
    if Trim(DatabasePage.Values[0]) = '' then
    begin
      MsgBox('Veuillez saisir le nom de la base de données.', mbError, MB_OK);
      Result := False;
    end
    else if Trim(DatabasePage.Values[1]) = '' then
    begin
      MsgBox('Veuillez saisir l''utilisateur PostgreSQL.', mbError, MB_OK);
      Result := False;
    end
    else if DatabasePage.Values[2] = '' then
    begin
      MsgBox('Veuillez saisir le mot de passe PostgreSQL.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvContent: String;
begin
  if CurStep = ssPostInstall then
  begin
    EnvContent :=
      'DB_HOST=' + Trim(ServerPage.Values[0]) + #13#10 +
      'DB_PORT=' + Trim(ServerPage.Values[1]) + #13#10 +
      'DB_NAME=' + Trim(DatabasePage.Values[0]) + #13#10 +
      'DB_USER=' + Trim(DatabasePage.Values[1]) + #13#10 +
      'DB_PASSWORD=' + DatabasePage.Values[2] + #13#10 +
      'APP_ENV=prod' + #13#10;

    if not SaveStringToFile(ExpandConstant('{app}\.env'), EnvContent, False) then
      RaiseException('Impossible de créer le fichier de configuration .env.');
  end;
end;
