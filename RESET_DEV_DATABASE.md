# Réinitialisation de la Base de Données PostgreSQL de Développement

Puisque le projet **Easy School 2.0** est en phase active de développement et de migration d'architecture, certaines modifications structurelles critiques (comme l'ajout de contraintes d'unicités et d'intégrité ou l'adaptation des schémas de données du rendu 3) nécessitent une réinitialisation complète de votre base de données PostgreSQL locale.

> ⚠️ **ATTENTION :** Cette opération supprimera définitivement toutes les données de test existantes dans votre base de données de développement.

---

## Procédure pas à pas

### 1. Recréer la Base de Données

Connectez-vous à votre serveur PostgreSQL (via un terminal `psql`, pgAdmin ou DBeaver) et exécutez les requêtes SQL suivantes :

```sql
-- Déconnexion forcée des autres sessions ouvertes sur la base (si nécessaire)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'easy_school_db'
  AND pid <> pg_backend_pid();

-- Suppression de la base existante
DROP DATABASE IF EXISTS easy_school_db;

-- Recréation propre
CREATE DATABASE easy_school_db;
```

---

### 2. Relancer l'Application

Une fois la base de données propre et vide recréée, retournez dans votre terminal de projet et lancez simplement la commande de démarrage :

```bash
python main.py
```

---

## Ce qu'il se passe au démarrage :
1. L'application teste la connexion avec la nouvelle base de données SQL.
2. SQLAlchemy génère automatiquement toutes les tables requises avec les nouvelles contraintes d'unicité et de clé primaire.
3. Le système initialise la session de démarrage avec un établissement générique d'exemple.
4. L'année scolaire par défaut **2026-2027** (non clôturée) est automatiquement créée en base et déjà sélectionnée comme session active dans le sélecteur graphique en haut à droite !
