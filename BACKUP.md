# Sauvegarde et restauration — Easy School CJGA

Suite à l'audit (P0-08) : aucune procédure automatisée de sauvegarde n'existait.
Cette page documente `scripts/backup_db.ps1` et `scripts/restore_db.ps1`.

## Sauvegarde manuelle (test immédiat)

```powershell
.\scripts\backup_db.ps1
```

Produit un fichier `backups\easy_school_<base>_<horodatage>.backup` (format
`pg_dump -Fc`, déjà compressé). Lit les identifiants de connexion depuis le
`.env` du projet — pas besoin de les ressaisir.

- `-BackupDir` : dossier de destination. **Mettre un dossier sur un support
  différent du disque du poste** (clé USB, partage réseau, OneDrive/cloud) —
  une sauvegarde sur le même disque que la base ne survit pas à une panne
  de ce disque.
- `-KeepLast N` : rotation, ne garde que les N sauvegardes les plus
  récentes (défaut 14).
- `-EncryptionPassword "..."` : chiffre la sauvegarde en AES-256 si
  [7-Zip](https://www.7-zip.org/) (`7z.exe`) est installé et sur le PATH.
  Les données financières et personnelles des familles justifient de
  chiffrer toute sauvegarde qui quitte le poste.

Chaque exécution ajoute une ligne à `backups\backup_log.csv` (date, base,
fichier, taille, statut) — c'est le journal des sauvegardes demandé par
l'audit.

## Sauvegarde quotidienne automatique

### Depuis l'application (méthode recommandée)

Ouvrir **Paramètres > Généraux > Sauvegardes**, puis :

1. choisir le dossier de destination ;
2. choisir l'heure et le nombre de copies à conserver ;
3. cocher **Activer la sauvegarde automatique quotidienne** ;
4. cliquer sur **Enregistrer la planification**.

Le bouton **Sauvegarder maintenant** permet de vérifier immédiatement le
fonctionnement. La tâche Windows appelle `EasySchool.exe --backup-now` et
fonctionne même si l'interface Easy School est fermée. Le compte Windows qui
a créé la tâche doit toutefois être connecté.

### Depuis PowerShell

Planifier via le Planificateur de tâches Windows :

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\chemin\vers\scripts\backup_db.ps1`" -BackupDir `"D:\Sauvegardes\EasySchool`" -EncryptionPassword `"<mot de passe>`""
$trigger = New-ScheduledTaskTrigger -Daily -At 20:00
Register-ScheduledTask -TaskName "EasySchool - Sauvegarde quotidienne" -Action $action -Trigger $trigger -RunLevel Highest
```

Adapter l'heure et le `-BackupDir` (support externe) à l'environnement
réel du poste CJGA. Vérifier périodiquement `backup_log.csv` pour repérer
d'éventuels échecs silencieux.

## Sauvegarde avant toute migration

**Obligatoire avant d'appliquer une migration Alembic sur une base
contenant des données réelles** (voir [MIGRATIONS.md](MIGRATIONS.md)) :

```powershell
.\scripts\backup_db.ps1 -BackupDir "D:\Sauvegardes\EasySchool\avant_migration"
```

## Test de restauration (mensuel, obligatoire)

Une sauvegarde jamais restaurée n'est pas une sauvegarde fiable. Chaque
mois :

```powershell
.\scripts\restore_db.ps1 -BackupFile "backups\easy_school_..._<date>.backup"
```

Par défaut, restaure dans `easy_school_restore_test_db` (jamais la base de
production — protection contre un écrasement accidentel). Vérifier ensuite
manuellement quelques totaux de contrôle contre l'état attendu au moment de
la sauvegarde : nombre d'élèves inscrits, somme des versements de l'année,
nombre de mouvements comptables. Si les totaux ne concordent pas, la
sauvegarde ou la procédure de restauration a un problème — creuser avant
d'en avoir besoin en urgence réelle.

Pour restaurer réellement sur la base de production (après un sinistre
confirmé) :

```powershell
.\scripts\restore_db.ps1 -BackupFile "backups\....backup" -TargetDb "easy_school_cjga_db" -Confirm
```

Le flag `-Confirm` est requis dès que la cible n'est pas la base de test
par défaut — protection volontaire contre un écrasement accidentel.

## Prérequis

- L'application installée embarque `pg_dump`. En mode développement, il doit
  être sur le `PATH` ou installé dans le dossier habituel de PostgreSQL
  (`...\PostgreSQL\<version>\bin`). `PG_DUMP_PATH` permet d'indiquer un autre
  emplacement.
- Pour la restauration en PowerShell, `pg_restore` et `psql` doivent être sur
  le `PATH` (ils ne sont pas nécessaires à la sauvegarde depuis l'interface).
- `7z.exe` optionnel, uniquement nécessaire pour le chiffrement/déchiffrement.

## Hors scope de ces scripts

- L'automatisation complète (création de la tâche planifiée) n'est pas
  faite par ces scripts eux-mêmes — à enregistrer une fois sur le poste
  réel avec la commande ci-dessus, adaptée au chemin et au support de
  sauvegarde effectivement disponibles au CJGA.
- La copie vers un stockage cloud/off-site n'est pas automatisée ici —
  `-BackupDir` peut pointer directement vers un dossier synchronisé
  (OneDrive, etc.) si disponible.
