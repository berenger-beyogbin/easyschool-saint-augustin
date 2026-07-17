<#
.SYNOPSIS
    Sauvegarde la base PostgreSQL d'Easy School (format custom pg_dump, compresse),
    avec rotation et journal. Voir BACKUP.md pour la procedure complete
    (planification, test de restauration, chiffrement).

.PARAMETER BackupDir
    Dossier de destination des sauvegardes. Par defaut : backups/ a la racine du projet.
    Doit etre un support DIFFERENT du disque de la base (cle USB, partage reseau, cloud)
    pour survivre a une panne du poste.

.PARAMETER KeepLast
    Nombre de sauvegardes a conserver (les plus anciennes au-dela sont supprimees).

.PARAMETER EncryptionPassword
    Optionnel. Si fourni et que 7z.exe est disponible sur le PATH, chiffre la sauvegarde
    en AES-256 (7-Zip) et supprime le dump non chiffre.

.EXAMPLE
    .\scripts\backup_db.ps1
    .\scripts\backup_db.ps1 -BackupDir "D:\Sauvegardes\EasySchool" -KeepLast 30
#>
param(
    [string]$BackupDir = (Join-Path $PSScriptRoot "..\backups"),
    [int]$KeepLast = 14,
    [string]$EncryptionPassword = ""
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

$envFile = Join-Path $PSScriptRoot "..\.env"
$envVars = Read-DotEnv $envFile

$DbHost = if ($envVars["DB_HOST"]) { $envVars["DB_HOST"] } else { "127.0.0.1" }
$DbPort = if ($envVars["DB_PORT"]) { $envVars["DB_PORT"] } else { "5432" }
$DbUser = if ($envVars["DB_USER"]) { $envVars["DB_USER"] } else { "postgres" }
$DbName = if ($envVars["DB_NAME"]) { $envVars["DB_NAME"] } else { "easy_school_cjga_db" }
$DbPassword = if ($envVars["DB_PASSWORD"]) { $envVars["DB_PASSWORD"] } else { "" }

if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    Write-Error "pg_dump introuvable sur le PATH. Installez les outils client PostgreSQL ou ajoutez leur dossier bin au PATH."
    exit 1
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$dumpFile = Join-Path $BackupDir "easy_school_${DbName}_${timestamp}.dump"
$logFile = Join-Path $BackupDir "backup_log.csv"

Write-Host "Sauvegarde de la base '$DbName' ($DbHost`:$DbPort) vers $dumpFile ..."

$env:PGPASSWORD = $DbPassword
$success = $true
$errorMsg = ""
try {
    & pg_dump -h $DbHost -p $DbPort -U $DbUser -d $DbName -Fc -f $dumpFile
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump a retourne le code $LASTEXITCODE"
    }
} catch {
    $success = $false
    $errorMsg = $_.Exception.Message
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

$finalFile = $dumpFile
if ($success -and $EncryptionPassword -and (Get-Command 7z -ErrorAction SilentlyContinue)) {
    $encFile = "$dumpFile.7z"
    & 7z a -p"$EncryptionPassword" -mhe=on "$encFile" "$dumpFile" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Remove-Item $dumpFile -Force
        $finalFile = $encFile
        Write-Host "Sauvegarde chiffree (AES-256) : $encFile"
    } else {
        Write-Warning "Echec du chiffrement 7z ; le dump non chiffre est conserve : $dumpFile"
    }
} elseif ($success -and $EncryptionPassword) {
    Write-Warning "7z introuvable sur le PATH : sauvegarde non chiffree, malgre -EncryptionPassword."
}

$sizeMb = if ($success -and (Test-Path $finalFile)) { [math]::Round((Get-Item $finalFile).Length / 1MB, 2) } else { 0 }
$logLine = "$timestamp,$DbName,$finalFile,$sizeMb Mo,$(if ($success) {'OK'} else {'ECHEC: ' + $errorMsg})"
Add-Content -Path $logFile -Value $logLine

if (-not $success) {
    Write-Error "Echec de la sauvegarde : $errorMsg"
    exit 1
}

Write-Host "Sauvegarde terminee avec succes : $finalFile ($sizeMb Mo)"

# Rotation : ne garde que les KeepLast sauvegardes les plus recentes
$allBackups = Get-ChildItem -Path $BackupDir -Filter "easy_school_*" | Where-Object { -not $_.PSIsContainer } | Sort-Object LastWriteTime -Descending
if ($allBackups.Count -gt $KeepLast) {
    $toDelete = $allBackups | Select-Object -Skip $KeepLast
    foreach ($old in $toDelete) {
        Write-Host "Rotation : suppression de l'ancienne sauvegarde $($old.Name)"
        Remove-Item $old.FullName -Force
    }
}
