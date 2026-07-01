# SÉCURITÉ — GESTION DES SECRETS ET DU FICHIER .ENV

## 1. Pourquoi .env ne doit JAMAIS être versionné

Le fichier `.env` contient des données **sensibles et confidentielles** :
- Le **mot de passe PostgreSQL** de la base de données de production
- Le nom de l'hôte de base de données
- Le nom de la base de données

Si ce fichier est publié sur GitHub ou partagé par email :
- N'importe qui peut se connecter à la base de données PostgreSQL
- Toutes les données des élèves, parents et paiements sont exposées
- La conformité RGPD/protection des données personnelles est compromise

**Le fichier `.env` est exclu du versioning par le `.gitignore`.** Ne pas le modifier.

---

## 2. Comment créer le fichier .env pour un nouveau développeur

```bash
# 1. Copier le fichier modèle
copy .env.example .env

# 2. Ouvrir .env avec un éditeur de texte
# 3. Remplacer CHANGE_ME par le vrai mot de passe PostgreSQL
# 4. Sauvegarder — NE PAS committer ce fichier
```

Contenu du fichier `.env` à remplir :

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=easy_school_db
DB_USER=postgres
DB_PASSWORD=<mot_de_passe_reel>
APP_ENV=dev
```

---

## 3. Si un mot de passe a été exposé, que faire ?

Si le fichier `.env` a été commité accidentellement sur Git ou partagé :

### Étape 1 — Changer le mot de passe PostgreSQL immédiatement
```sql
-- Se connecter à PostgreSQL et changer le mot de passe
ALTER USER postgres WITH PASSWORD 'nouveau_mot_de_passe_fort';
```

### Étape 2 — Mettre à jour le fichier .env local
```ini
DB_PASSWORD=nouveau_mot_de_passe_fort
```

### Étape 3 — Si commité sur GitHub
```bash
# Supprimer l'historique contenant le secret (ATTENTION : opération destructive)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Pousser en force (nécessite les droits admin sur le dépôt)
git push origin --force --all
```
Ou utiliser l'outil `git-filter-repo` (recommandé).

### Étape 4 — Contacter l'administrateur du dépôt
Si le dépôt est partagé avec d'autres personnes, les prévenir immédiatement.

---

## 4. Règles à respecter — Récapitulatif

| Règle | Obligatoire |
|-------|-------------|
| Ne jamais committer `.env` | ✅ OUI |
| Toujours utiliser `.env.example` comme modèle | ✅ OUI |
| Ne pas partager `.env` par email ou Slack | ✅ OUI |
| Utiliser un mot de passe fort (12+ caractères, maj/min/chiffres/symboles) | ✅ OUI |
| Changer le mot de passe dès qu'il est exposé | ✅ OUI |
| Créer un utilisateur PostgreSQL dédié (pas `postgres` superuser) | Recommandé |
| Stocker les secrets dans un gestionnaire de secrets en prod | Recommandé |

---

## 5. Configuration APP_ENV

Le fichier `.env` contient aussi la variable `APP_ENV` qui contrôle le comportement de l'application :

| Valeur | Comportement |
|--------|-------------|
| `dev` | Développement normal — logs minimaux, echo SQL désactivé |
| `dev_debug` | Debug — echo SQL activé (toutes les requêtes dans la console) |
| `prod` | Production — logs minimaux, echo SQL désactivé |

**En production, toujours utiliser `APP_ENV=prod`.**

---

*Document généré lors de la Phase 1 — Stabilisation Critique — Easy School 2.0*
