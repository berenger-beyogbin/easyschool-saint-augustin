# Guide de démarrage d'Easy School 2.0 (Python / PySide6)

Ce guide résume les commandes indispensables pour lancer l'application de bureau Python sur votre machine locale Windows.

## Étapes d'installation et de lancement

Ouvrez un terminal (PowerShell ou Invite de commandes) et exécutez les instructions suivantes :

```bash
# 1. Se déplacer dans le dossier du projet Python
cd easy_school_python

# 2. Créer l'environnement virtuel Python
python -m venv venv

# 3. Activer l'environnement virtuel (Windows)
venv\Scripts\activate

# 4. Installer les dépendances du projet
pip install -r requirements.txt

# 5. Préparer le fichier de configuration de l'environnement (.env)
copy .env.example .env

# 6. Exécuter l'application de bureau
python main.py
```

## Stack Technique Utilise de l'application
* **Interface Graphique (GUI) :** PySide6 (Qt pour Python)
* **Base de données :** PostgreSQL
* **ORM :** SQLAlchemy (avec détection automatique du schéma)
* **Configuration :** python-dotenv
