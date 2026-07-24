# Easy School 2.0 — Adaptation CJGA

Application de bureau (Python / PySide6 / PostgreSQL) de gestion scolaire,
adaptee pour le College Catholique Joseph Garnier d'Attingue (CJGA) :
scolarite, familles, inscriptions, versements, autres frais, kiosque/stock,
comptabilite, statistiques, utilisateurs et permissions.

## Demarrer

Voir [README_PYTHON.md](README_PYTHON.md) pour l'installation et le
lancement en local.

En production, configurer `APP_ENV=prod` et appliquer les migrations avant
chaque démarrage/déploiement :

```bash
alembic upgrade head
python main.py
```

L'application vérifie alors la connexion sans créer ni modifier le schéma.

## Documentation du projet

- [MIGRATIONS.md](MIGRATIONS.md) — migrations de schema (Alembic).
- [BACKUP.md](BACKUP.md) — sauvegarde et restauration de la base.
- [SECURITE_ENV.md](SECURITE_ENV.md) — configuration et securite de `.env`.
- [RESET_DEV_DATABASE.md](RESET_DEV_DATABASE.md) — reinitialiser la base de developpement locale.
- [PLAN_STABILISATION.md](PLAN_STABILISATION.md) — suivi du plan de
  stabilisation issu de l'audit du projet.
- `TESTS_MANUELS_*.md` — checklists de recette manuelle par module.

## Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Qualite

```bash
ruff check .
```
