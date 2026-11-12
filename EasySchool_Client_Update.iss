#define MyAppName "Easy School CJGA"
#define MyAppVersion "2.3.2"
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
OutputDir=dist\EasySchool_Update_v2.3.2
OutputBaseFilename=EasySchool_CJGA_Mise_A_Jour_v2.3.2
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
Source: "dist_update_v2.3.2\EasySchool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist_tools_v2.3.2\EasySchoolDbTest.exe"; Flags: dontcopy

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
var
  EnvBackupPath: String;
  ServerPage: TInputQueryWizardPage;
  DatabasePage: TInputQueryWizardPage;
  TestButton: TNewButton;
  TestStatusLabel: TNewStaticText;
  EnvLoaded: Boolean;
  ConnectionValidated: Boolean;
  ValidatedSignature: String;

function DecodeEnvValue(Value: String): String;
var
  I: Integer;
begin
  Result := Value;
  if (Length(Value) < 2) or
     (Value[1] <> Chr(39)) or
     (Value[Length(Value)] <> Chr(39)) then
    exit;

  Result := '';
  I := 2;
  while I < Length(Value) do
  begin
    if (Value[I] = Chr(92)) and (I + 1 < Length(Value)) and
       ((Value[I + 1] = Chr(92)) or (Value[I + 1] = Chr(39))) then
    begin
      Result := Result + Value[I + 1];
      I := I + 2;
    end
    else
    begin
      Result := Result + Value[I];
      I := I + 1;
    end;
  end;
end;

function EncodeEnvValue(Value: String): String;
var
  I: Integer;
begin
  Result := Chr(39);
  for I := 1 to Length(Value) do
  begin
    if (Value[I] = Chr(92)) or (Value[I] = Chr(39)) then
      Result := Result + Chr(92);
    Result := Result + Value[I];
  end;
  Result := Result + Chr(39);
end;

function ReadEnvValue(const FileName, Key: String): String;
var
  Lines: TArrayOfString;
  I: Integer;
  Line: String;
  Prefix: String;
begin
  Result := '';
  Prefix := Key + '=';
  if not LoadStringsFromFile(FileName, Lines) then
    exit;

  for I := 0 to GetArrayLength(Lines) - 1 do
  begin
    Line := Trim(Lines[I]);
    if Pos(Prefix, Line) = 1 then
    begin
      Result := DecodeEnvValue(Copy(Line, Length(Prefix) + 1, MaxInt));
      exit;
    end;
  end;
end;

procedure LoadExistingEnvironment;
var
  EnvPath: String;
  Value: String;
begin
  if EnvLoaded then
    exit;
  EnvLoaded := True;

  ServerPage.Values[0] := '';
  ServerPage.Values[1] := '5432';
  DatabasePage.Values[0] := 'easy_school_cjga_db';
  DatabasePage.Values[1] := 'easy_school_app';
  DatabasePage.Values[2] := '';

  EnvPath := ExpandConstant('{app}\.env');
  if not FileExists(EnvPath) then
    exit;

  Value := ReadEnvValue(EnvPath, 'DB_HOST');
  if Value <> '' then ServerPage.Values[0] := Value;
  Value := ReadEnvValue(EnvPath, 'DB_PORT');
  if Value <> '' then ServerPage.Values[1] := Value;
  Value := ReadEnvValue(EnvPath, 'DB_NAME');
  if Value <> '' then DatabasePage.Values[0] := Value;
  Value := ReadEnvValue(EnvPath, 'DB_USER');
  if Value <> '' then DatabasePage.Values[1] := Value;
  Value := ReadEnvValue(EnvPath, 'DB_PASSWORD');
  if Value <> '' then DatabasePage.Values[2] := Value;
end;

function CurrentConnectionSignature: String;
begin
  Result :=
    Trim(ServerPage.Values[0]) + #1 +
    Trim(ServerPage.Values[1]) + #1 +
    Trim(DatabasePage.Values[0]) + #1 +
    Trim(DatabasePage.Values[1]) + #1 +
    DatabasePage.Values[2];
end;

function IsValidPort(Value: String): Boolean;
var
  CharacterIndex: Integer;
  PortNumber: Integer;
begin
  Result := False;
  Value := Trim(Value);
  if Value = '' then
    exit;

  PortNumber := 0;
  for CharacterIndex := 1 to Length(Value) do
  begin
    if (Value[CharacterIndex] < '0') or (Value[CharacterIndex] > '9') then
      exit;
    PortNumber := (PortNumber * 10) + Ord(Value[CharacterIndex]) - Ord('0');
    if PortNumber > 65535 then
      exit;
  end;
  Result := PortNumber >= 1;
end;

function ValidateServerFields: Boolean;
begin
  Result := False;
  if Trim(ServerPage.Values[0]) = '' then
    MsgBox('Veuillez saisir l''adresse IP ou le nom du serveur PostgreSQL.', mbError, MB_OK)
  else if not IsValidPort(ServerPage.Values[1]) then
    MsgBox('Le port PostgreSQL doit être un nombre compris entre 1 et 65535.', mbError, MB_OK)
  else
    Result := True;
end;

function ValidateConnectionFields: Boolean;
begin
  Result := False;
  if not ValidateServerFields then
    exit;

  if Trim(DatabasePage.Values[0]) = '' then
    MsgBox('Veuillez saisir le nom de la base de données.', mbError, MB_OK)
  else if Trim(DatabasePage.Values[1]) = '' then
    MsgBox('Veuillez saisir l''utilisateur PostgreSQL.', mbError, MB_OK)
  else if DatabasePage.Values[2] = '' then
    MsgBox('Veuillez saisir le mot de passe PostgreSQL.', mbError, MB_OK)
  else
    Result := True;
end;

function TestDatabaseConnection(ShowSuccess: Boolean): Boolean;
var
  ConfigPath: String;
  ResultPath: String;
  ConfigContent: String;
  ResultMessage: AnsiString;
  ResultCode: Integer;
  Executed: Boolean;
begin
  Result := False;
  if not ValidateConnectionFields then
    exit;

  ConfigPath := ExpandConstant('{tmp}\easy_school_db_connection.ini');
  ResultPath := ExpandConstant('{tmp}\easy_school_db_connection_result.txt');
  DeleteFile(ConfigPath);
  DeleteFile(ResultPath);

  ConfigContent :=
    'host=' + Trim(ServerPage.Values[0]) + #13#10 +
    'port=' + Trim(ServerPage.Values[1]) + #13#10 +
    'dbname=' + Trim(DatabasePage.Values[0]) + #13#10 +
    'user=' + Trim(DatabasePage.Values[1]) + #13#10 +
    'password=' + DatabasePage.Values[2] + #13#10;

  if not SaveStringToFile(ConfigPath, ConfigContent, False) then
  begin
    MsgBox('Impossible de préparer le test de connexion.', mbError, MB_OK);
    exit;
  end;

  TestButton.Enabled := False;
  WizardForm.NextButton.Enabled := False;
  TestStatusLabel.Font.Color := clBlue;
  TestStatusLabel.Caption := 'Test de connexion en cours...';
  try
    Executed := Exec(
      ExpandConstant('{tmp}\EasySchoolDbTest.exe'),
      '"' + ConfigPath + '" "' + ResultPath + '"',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    );

    ResultMessage := 'Le test de connexion n''a retourné aucun détail.';
    if FileExists(ResultPath) then
      LoadStringFromFile(ResultPath, ResultMessage);

    if Executed and (ResultCode = 0) then
    begin
      ConnectionValidated := True;
      ValidatedSignature := CurrentConnectionSignature;
      TestStatusLabel.Font.Color := clGreen;
      TestStatusLabel.Caption := ResultMessage;
      if ShowSuccess then
        MsgBox(ResultMessage, mbInformation, MB_OK);
      Result := True;
    end
    else
    begin
      ConnectionValidated := False;
      ValidatedSignature := '';
      TestStatusLabel.Font.Color := clRed;
      TestStatusLabel.Caption := ResultMessage;
      MsgBox(ResultMessage + #13#10 + #13#10 +
        'Corrigez les informations ou la configuration réseau avant de continuer.', mbError, MB_OK);
    end;
  finally
    DeleteFile(ConfigPath);
    DeleteFile(ResultPath);
    TestButton.Enabled := True;
    WizardForm.NextButton.Enabled := True;
  end;
end;

procedure TestButtonClick(Sender: TObject);
begin
  TestDatabaseConnection(True);
end;

procedure InitializeWizard;
begin
  ExtractTemporaryFile('EasySchoolDbTest.exe');

  ServerPage := CreateInputQueryPage(
    wpSelectDir,
    'Connexion au serveur Easy School',
    'Indiquez le serveur PostgreSQL utilisé par ce poste.',
    'Les valeurs actuelles du fichier .env sont préremplies lorsqu''elles existent.'
  );
  ServerPage.Add('Adresse IP ou nom du serveur :', False);
  ServerPage.Add('Port PostgreSQL :', False);

  DatabasePage := CreateInputQueryPage(
    ServerPage.ID,
    'Base de données Easy School',
    'Saisissez les identifiants puis testez la connexion.',
    'La mise à jour ne pourra pas continuer tant que le test PostgreSQL n''aura pas réussi.'
  );
  DatabasePage.Add('Nom de la base :', False);
  DatabasePage.Add('Utilisateur :', False);
  DatabasePage.Add('Mot de passe :', True);

  TestButton := TNewButton.Create(DatabasePage);
  TestButton.Parent := DatabasePage.Surface;
  TestButton.Left := 0;
  TestButton.Top := DatabasePage.Edits[2].Top + DatabasePage.Edits[2].Height + ScaleY(14);
  TestButton.Width := ScaleX(210);
  TestButton.Height := ScaleY(28);
  TestButton.Caption := 'Tester la connexion PostgreSQL';
  TestButton.OnClick := @TestButtonClick;

  TestStatusLabel := TNewStaticText.Create(DatabasePage);
  TestStatusLabel.Parent := DatabasePage.Surface;
  TestStatusLabel.Left := 0;
  TestStatusLabel.Top := TestButton.Top + TestButton.Height + ScaleY(10);
  TestStatusLabel.Width := DatabasePage.SurfaceWidth;
  TestStatusLabel.Height := ScaleY(44);
  TestStatusLabel.AutoSize := False;
  TestStatusLabel.WordWrap := True;
  TestStatusLabel.Caption := 'Connexion non testée.';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectDir then
  begin
    EnvLoaded := False;
    ConnectionValidated := False;
  end;
  if CurPageID = ServerPage.ID then
    LoadExistingEnvironment;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ServerPage.ID then
  begin
    if not ValidateServerFields then
      Result := False;
  end
  else if CurPageID = DatabasePage.ID then
  begin
    if CurrentConnectionSignature <> ValidatedSignature then
    begin
      ConnectionValidated := False;
      TestStatusLabel.Font.Color := clBlue;
      TestStatusLabel.Caption := 'Les informations ont changé : un nouveau test est requis.';
    end;
    if not ConnectionValidated then
      Result := TestDatabaseConnection(False);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  EnvPath: String;
begin
  Result := '';
  if (not ConnectionValidated) or (CurrentConnectionSignature <> ValidatedSignature) then
  begin
    Result := 'La connexion PostgreSQL doit être testée avec succès avant l''installation.';
    exit;
  end;

  EnvPath := ExpandConstant('{app}\.env');
  EnvBackupPath := ExpandConstant('{app}\.env.avant-mise-a-jour-v2.3.2');
  if FileExists(EnvPath) and (not CopyFile(EnvPath, EnvBackupPath, False)) then
    Result := 'Impossible de sauvegarder le fichier de configuration .env.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvContent: String;
  ResultCode: Integer;
  LogPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    EnvContent :=
      'DB_HOST=' + EncodeEnvValue(Trim(ServerPage.Values[0])) + #13#10 +
      'DB_PORT=' + EncodeEnvValue(Trim(ServerPage.Values[1])) + #13#10 +
      'DB_NAME=' + EncodeEnvValue(Trim(DatabasePage.Values[0])) + #13#10 +
      'DB_USER=' + EncodeEnvValue(Trim(DatabasePage.Values[1])) + #13#10 +
      'DB_PASSWORD=' + EncodeEnvValue(DatabasePage.Values[2]) + #13#10 +
      'APP_ENV=prod' + #13#10;

    if not SaveStringToFile(ExpandConstant('{app}\.env'), EnvContent, False) then
      RaiseException('Impossible d''enregistrer le fichier de configuration .env.');

    LogPath := ExpandConstant('{localappdata}\EasySchool\logs\easy_school.log');
    if not Exec(
      ExpandConstant('{app}\{#MyAppExeName}'),
      '--migrate',
      ExpandConstant('{app}'),
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    ) or (ResultCode <> 0) then
    begin
      if ResultCode = 2 then
        RaiseException(
          'La connexion PostgreSQL a été perdue pendant la migration.' + #13#10 +
          'Vérifiez le serveur puis relancez la mise à jour.' + #13#10 +
          'Journal : ' + LogPath
        )
      else
        RaiseException(
          'La mise à jour des fichiers est terminée, mais la migration de la base a échoué.' + #13#10 +
          'Journal : ' + LogPath
        );
    end;
  end;
end;
