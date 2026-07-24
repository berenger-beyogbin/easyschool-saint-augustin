# Guide de démarrage d'Easy School 2.0 (Python / PySide6)

Ce guide résume les commandes indispensables pour lancer l'application de bureau Python sur votre machine locale Windows.

## Version de Python

Le projet cible et recommande explicitement **Python 3.12**. Cette version est
également utilisée par Ruff et par l'intégration continue GitHub Actions. Avant
de créer l'environnement virtuel, vérifiez que Python 3.12 est installé :

```powershell
py -3.12 --version
```

## Étapes d'installation et de lancement

Ouvrez un terminal (PowerShell ou Invite de commandes) et exécutez les instructions suivantes :

```powershell
# 1. Se déplacer dans le dossier du projet Python
cd "easy_school_python cjga"

# 2. Créer l'environnement virtuel avec Python 3.12
py -3.12 -m venv venv

# 3. Activer l'environnement virtuel (Windows)
venv\Scripts\activate

# 4. Installer les dépendances du projet
python -m pip install -r requirements.txt

# 5. Préparer le fichier de configuration de l'environnement (.env)
copy .env.example .env

# 6. Vérifier APP_ENV=dev dans .env, puis exécuter l'application de bureau
python main.py
```

En développement, `APP_ENV=dev` conserve la création automatique d'une base
locale pour simplifier le premier lancement. En production, utiliser
`APP_ENV=prod`, installer les dépendances de migration, puis préparer le
schéma explicitement avant de lancer l'application :

```bash
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
python main.py
```

Le processus applicatif en production vérifie uniquement la connexion. Il
n'exécute ni `create_all()` ni les anciens `ALTER TABLE` de compatibilité.

## Stack Technique Utilise de l'application
* **Interface Graphique (GUI) :** PySide6 (Qt pour Python)
* **Base de données :** PostgreSQL
* **ORM :** SQLAlchemy ; migrations de production gérées par Alembic
* **Configuration :** python-dotenv
