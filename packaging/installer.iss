; Installateur Windows pour Easy School 2.0
;
; Prerequis avant de compiler ce script avec Inno Setup (ISCC.exe) :
;   1. Build PyInstaller a jour :
;        venv\Scripts\pyinstaller.exe packaging\easy_school.spec --noconfirm
;      -> doit produire dist\EasySchool\EasySchool.exe
;   2. Installeur officiel PostgreSQL copie dans packaging\vendor\ :
;        packaging\vendor\postgresql-18.4-2-windows-x64.exe
;      (non versionne dans git, cf. .gitignore)
;
; Compilation :
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
; -> produit packaging\Output\EasySchool-Setup.exe
;
; Mode client-serveur :
;   Cet installateur propose un choix "Serveur" / "Client" pendant l'installation.
;   - Serveur : installe PostgreSQL en local, configure l'acces reseau (listen_addresses,
;     pg_hba.conf, pare-feu Windows) pour que les postes clients du reseau local puissent
;     s'y connecter, puis affiche le mot de passe genere a noter pour les clients.
;   - Client : n'installe pas PostgreSQL, demande l'adresse du serveur et les identifiants
;     (fournis par l'administrateur qui a installe le serveur), puis ecrit le .env en
;     consequence.

#define MyAppName "Easy School"
#define MyAppVersion "2.0"
#define MyAppPublisher "Easy School"
#define MyAppExeName "EasySchool.exe"
#define PgInstallerName "postgresql-18.4-2-windows-x64.exe"
#define PgBinDir "C:\Program Files\PostgreSQL\18\bin"
#define PgDataDir "C:\Program Files\PostgreSQL\18\data"
#define PgServiceName "postgresql-x64-18"
#define PgDbName "easy_school_db"

[Setup]
AppId={{8F3B6E3E-6B7E-4C7B-9C6B-9C6B9C6B9C6B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\EasySchool
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=EasySchool-Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; GroupDescription: "Icônes supplémentaires :"

[Files]
Source: "..\dist\EasySchool\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "vendor\{#PgInstallerName}"; DestDir: "{tmp}"; Flags: dontcopy

[Dirs]
Name: "{app}\assets\photos_eleves"; Permissions: users-modify
Name: "{app}\assets\logos"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer Easy School"; Flags: nowait postinstall skipifsilent

[Code]
const
  PasswordCharset = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';

var
  PgAlreadyPresent: Boolean;
  GeneratedPassword: String;
  ModePage: TInputOptionWizardPage;
  ClientPage: TInputQueryWizardPage;

function IsServerMode(): Boolean;
begin
  Result := ModePage.SelectedValueIndex = 0;
end;

procedure InitializeWizard();
begin
  ModePage := CreateInputOptionPage(wpSelectTasks,
    'Type d''installation',
    'Ce poste va-t-il héberger la base de données ou se connecter à un serveur existant ?',
    'Choisissez le rôle de ce poste sur le réseau, puis cliquez sur Suivant :',
    True, False);
  ModePage.Add('Serveur : ce poste héberge la base de données (PostgreSQL sera installé)');
  ModePage.Add('Client : ce poste se connecte à un serveur Easy School déjà installé sur le réseau');
  ModePage.SelectedValueIndex := 0;

  ClientPage := CreateInputQueryPage(ModePage.ID,
    'Connexion au serveur',
    'Renseignez les informations de connexion au serveur Easy School',
    'Ces informations sont fournies par la personne qui a installé le serveur.');
  ClientPage.Add('Adresse IP ou nom du serveur :', False);
  ClientPage.Add('Port PostgreSQL :', False);
  ClientPage.Add('Utilisateur PostgreSQL :', False);
  ClientPage.Add('Mot de passe PostgreSQL :', True);

  ClientPage.Values[1] := '5432';
  ClientPage.Values[2] := 'postgres';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = ClientPage.ID then
    Result := IsServerMode();
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = ClientPage.ID) and not IsServerMode() then
  begin
    if ClientPage.Values[0] = '' then
    begin
      MsgBox('Merci de renseigner l''adresse du serveur.', mbError, MB_OK);
      Result := False;
    end
    else if ClientPage.Values[3] = '' then
    begin
      MsgBox('Merci de renseigner le mot de passe PostgreSQL du serveur.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function IsPostgreSQLInstalled(): Boolean;
var
  Names: TArrayOfString;
  I: Integer;
  DisplayName: String;
begin
  Result := False;
  if RegGetSubkeyNames(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', Names) then
  begin
    for I := 0 to GetArrayLength(Names) - 1 do
    begin
      if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\' + Names[I], 'DisplayName', DisplayName) then
      begin
        if Pos('PostgreSQL', DisplayName) > 0 then
        begin
          Result := True;
          Exit;
        end;
      end;
    end;
  end;
end;

function GenerateRandomPassword(PwdLength: Integer): String;
var
  I: Integer;
begin
  Result := '';
  for I := 1 to PwdLength do
    Result := Result + PasswordCharset[Random(Length(PasswordCharset)) + 1];
end;

procedure WriteEnvFile(const Password: String; const Placeholder: Boolean);
var
  Lines: TArrayOfString;
  EnvPath: String;
begin
  SetArrayLength(Lines, 7);
  Lines[0] := '# Genere automatiquement par l''installateur Easy School 2.0 (serveur)';
  Lines[1] := 'DB_HOST=localhost';
  Lines[2] := 'DB_PORT=5432';
  Lines[3] := 'DB_USER=postgres';
  Lines[4] := 'DB_PASSWORD=' + Password;
  Lines[5] := 'DB_NAME=' + '{#PgDbName}';
  Lines[6] := 'APP_ENV=prod';

  EnvPath := ExpandConstant('{app}\.env');
  SaveStringsToFile(EnvPath, Lines, False);

  if Placeholder then
  begin
    MsgBox('PostgreSQL est déjà installé sur ce poste : l''installateur n''a pas pu configurer automatiquement ' +
           'le mot de passe de connexion.' + #13#10#13#10 +
           'Veuillez modifier le fichier :' + #13#10 + EnvPath + #13#10#13#10 +
           'avec les identifiants PostgreSQL réels de ce poste (DB_USER / DB_PASSWORD) avant de lancer Easy School.' + #13#10#13#10 +
           'Si d''autres postes doivent se connecter à ce serveur, pensez aussi à configurer manuellement ' +
           'l''accès réseau (listen_addresses dans postgresql.conf, une règle dans pg_hba.conf, et le pare-feu).',
           mbInformation, MB_OK);
  end;
end;

procedure WriteClientEnvFile();
var
  Lines: TArrayOfString;
  EnvPath: String;
begin
  SetArrayLength(Lines, 7);
  Lines[0] := '# Genere automatiquement par l''installateur Easy School 2.0 (poste client)';
  Lines[1] := 'DB_HOST=' + ClientPage.Values[0];
  Lines[2] := 'DB_PORT=' + ClientPage.Values[1];
  Lines[3] := 'DB_USER=' + ClientPage.Values[2];
  Lines[4] := 'DB_PASSWORD=' + ClientPage.Values[3];
  Lines[5] := 'DB_NAME=' + '{#PgDbName}';
  Lines[6] := 'APP_ENV=prod';

  EnvPath := ExpandConstant('{app}\.env');
  SaveStringsToFile(EnvPath, Lines, False);
end;

procedure ConfigureNetworkAccess();
var
  ConfLines, HbaLines: TArrayOfString;
  I: Integer;
  ResultCode: Integer;
begin
  // Autoriser PostgreSQL a ecouter sur toutes les interfaces reseau, pas seulement localhost.
  if LoadStringsFromFile(ExpandConstant('{#PgDataDir}\postgresql.conf'), ConfLines) then
  begin
    for I := 0 to GetArrayLength(ConfLines) - 1 do
    begin
      if Pos('listen_addresses', ConfLines[I]) > 0 then
        ConfLines[I] := 'listen_addresses = ''*''';
    end;
    SaveStringsToFile(ExpandConstant('{#PgDataDir}\postgresql.conf'), ConfLines, False);
  end;

  // Autoriser les connexions authentifiees depuis les plages d'adresses privees usuelles (reseau local).
  SetArrayLength(HbaLines, 3);
  HbaLines[0] := 'host    all             all             192.168.0.0/16          scram-sha-256';
  HbaLines[1] := 'host    all             all             10.0.0.0/8              scram-sha-256';
  HbaLines[2] := 'host    all             all             172.16.0.0/12           scram-sha-256';
  SaveStringsToFile(ExpandConstant('{#PgDataDir}\pg_hba.conf'), HbaLines, True);

  // Ouvrir le port PostgreSQL dans le pare-feu Windows pour les autres postes du reseau.
  Exec('netsh.exe',
      'advfirewall firewall add rule name="Easy School PostgreSQL" dir=in action=allow protocol=TCP localport=5432',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

  // Redemarrer le service pour appliquer les changements de configuration.
  Exec('net.exe', 'stop "{#PgServiceName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('net.exe', 'start "{#PgServiceName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(2000);
end;

procedure InstallBundledPostgreSQL(const Password: String);
var
  ResultCode: Integer;
  PgExePath: String;
begin
  ExtractTemporaryFile('{#PgInstallerName}');
  PgExePath := ExpandConstant('{tmp}\{#PgInstallerName}');

  if not Exec(PgExePath,
      '--mode unattended --unattendedmodeui minimal --superpassword "' + Password + '" ' +
      '--serverport 5432 --disable-components pgAdmin,stackbuilder',
      '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('L''installation de PostgreSQL a échoué (code ' + IntToStr(ResultCode) + '). ' +
           'Vous pouvez l''installer manuellement puis configurer {app}\.env.', mbError, MB_OK);
    Exit;
  end;

  // Laisse au service PostgreSQL le temps de finir de demarrer avant createdb.
  Sleep(3000);

  Exec('cmd.exe',
      '/C set PGPASSWORD=' + Password + '&& "{#PgBinDir}\createdb.exe" -U postgres -h localhost -p 5432 {#PgDbName}',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // Code non nul si la base existe deja : sans consequence, on l'ignore.
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if IsServerMode() then
    begin
      PgAlreadyPresent := IsPostgreSQLInstalled();

      if PgAlreadyPresent then
      begin
        WriteEnvFile('CHANGE_ME', True);
      end
      else
      begin
        GeneratedPassword := GenerateRandomPassword(24);
        InstallBundledPostgreSQL(GeneratedPassword);
        ConfigureNetworkAccess();
        WriteEnvFile(GeneratedPassword, False);

        MsgBox('Ce poste est configuré comme serveur Easy School.' + #13#10#13#10 +
               'Mot de passe PostgreSQL généré : ' + GeneratedPassword + #13#10#13#10 +
               'Notez ce mot de passe : il sera nécessaire pour installer les postes clients ' +
               '(avec l''adresse IP de ce poste sur le réseau).',
               mbInformation, MB_OK);
      end;
    end
    else
    begin
      WriteClientEnvFile();
    end;
  end;
end;
