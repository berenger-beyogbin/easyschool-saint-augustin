<#
.SYNOPSIS
    Restaure une sauvegarde Easy School (produite par backup_db.ps1) dans une base
    PostgreSQL. Voir BACKUP.md pour la procedure de test mensuel.

.PARAMETER BackupFile
    Chemin du fichier .dump (ou .dump.7z chiffre) a restaurer.

.PARAMETER TargetDb
    Base de destination. Par defaut, une base de verification separee
    (jamais la base de production) pour eviter tout ecrasement accidentel.

.PARAMETER Confirm
    Doit etre passe explicitement pour restaurer sur une base DIFFERENTE de la base
    de verification par defaut (protection contre un ecrasement accidentel de prod).

.EXAMPLE
    # Test de restauration standard, dans une base jetable dediee :
    .\scripts\restore_db.ps1 -BackupFile "backups\easy_school_easy_school_cjga_db_2026-07-16_120000.dump"

.EXAMPLE
    # Restauration reelle sur la base de production (apres sinistre), en connaissance de cause :
    .\scripts\restore_db.ps1 -BackupFile "backups\....dump" -TargetDb "easy_school_cjga_db" -Confirm
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$TargetDb = "easy_school_restore_test_db",
    [switch]$Confirm,
    [string]$DecryptionPassword = ""
)

$ErrorActionPreference = "Stop"

function Read-DotEnv([string]$path) {
    $vars = @{}
    if (Test-Path $path) {
        Get-Content $path | ForEach-Object {
            if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$' -and $_ -notmatch '^\s*#') {
                $vars[$matches[1]] = $matches[2].Trim('"').Trim("'")
            }
        }
    }
    return $vars
}

if ($TargetDb -ne "easy_school_restore_test_db" -and -not $Confirm) {
    Write-Error "Restauration vers '$TargetDb' (different de la base de test par defaut) : relancez avec -Confirm pour confirmer que c'est intentionnel. Une restauration ECRASE la base cible."
    exit 1
}

if (-not (Test-Path $BackupFile)) {
    Write-Error "Fichier de sauvegarde introuvable : $BackupFile"
    exit 1
}

$envFile = Join-Path $PSScriptRoot "..\.env"
$envVars = Read-DotEnv $envFile
$DbHost = if ($envVars["DB_HOST"]) { $envVars["DB_HOST"] } else { "127.0.0.1" }
$DbPort = if ($envVars["DB_PORT"]) { $envVars["DB_PORT"] } else { "5432" }
$DbUser = if ($envVars["DB_USER"]) { $envVars["DB_USER"] } else { "postgres" }
$DbPassword = if ($envVars["DB_PASSWORD"]) { $envVars["DB_PASSWORD"] } else { "" }

$dumpToRestore = $BackupFile
if ($BackupFile -like "*.7z") {
    if (-not $DecryptionPassword) {
        Write-Error "Ce fichier est chiffre (.7z) : fournissez -DecryptionPassword."
        exit 1
    }
    if (-not (Get-Command 7z -ErrorAction SilentlyContinue)) {
        Write-Error "7z introuvable sur le PATH, impossible de dechiffrer."
        exit 1
    }
    $tempDir = Join-Path $env:TEMP "easy_school_restore_$(Get-Random)"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    & 7z x "-p$DecryptionPassword" -o"$tempDir" "$BackupFile" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Echec du dechiffrement (mot de passe incorrect ?)."
        exit 1
    }
    $dumpToRestore = Get-ChildItem $tempDir -Filter "*.dump" | Select-Object -First 1 -ExpandProperty FullName
}

Write-Host "Recreation de la base '$TargetDb' ($DbHost`:$DbPort)..."
$env:PGPASSWORD = $DbPassword
try {
    & psql -h $DbHost -p $DbPort -U $DbUser -d postgres -c "DROP DATABASE IF EXISTS `"$TargetDb`";"
    & psql -h $DbHost -p $DbPort -U $DbUser -d postgres -c "CREATE DATABASE `"$TargetDb`";"

    Write-Host "Restauration de $dumpToRestore vers '$TargetDb'..."
    & pg_restore -h $DbHost -p $DbPort -U $DbUser -d $TargetDb --no-owner --no-privileges $dumpToRestore
    if ($LASTEXITCODE -ne 0) {
        throw "pg_restore a retourne le code $LASTEXITCODE"
    }
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    if ($tempDir -and (Test-Path $tempDir)) {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Restauration terminee dans '$TargetDb'."
Write-Host "Verifiez maintenant les totaux de controle (nombre d'eleves, somme des versements, etc.) contre l'etat attendu - voir BACKUP.md."
