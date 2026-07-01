# DIAGNOSTIC COMPLET — EASY SCHOOL 2.0
**Date de diagnostic :** 2026-07-01 (mise à jour du diagnostic du 2026-06-20)
**Analysé par :** Claude Code (Sonnet 5)
**Périmètre :** `easy_school_python/` — Python 3.14 / PySide6 / SQLAlchemy 2.0 / PostgreSQL

---

## 1. SYNTHÈSE EXÉCUTIVE

### État global du projet

Depuis le diagnostic du 20/06, le projet a nettement progressé : module **Utilisateurs/Authentification** livré (22/06), **impression des statistiques** implémentée pour tous les rapports sauf la balance des comptes (24/06), **ventilation analytique des prestations** ajoutée (29/06–01/07), une **suite de tests automatisés pytest** est apparue (23 tests, tous verts), et une **migration SQLAlchemy 2.0** (`session.query(Model).get(id)` → `session.get(Model, id)`) est en cours sur l'arbre de travail (24 fichiers modifiés, non commités).

La quasi-totalité des risques CRITIQUE et ÉLEVÉ du diagnostic précédent sont résolus. Le projet est **utilisable en production limitée**, avec deux zones encore non développées (Bibliothèque, SMS) et un point d'attention immédiat : **du travail non commité dans l'arbre Git**.

### Niveau de maturité
- **Compilation Python :** ✅ PASS (`py_compile` sur tous les fichiers suivis par Git, aucune erreur)
- **Tests automatisés :** ✅ 23/23 passent (`pytest tests/`) — nouveau depuis le dernier diagnostic
- **Architecture générale :** Solide, inchangée (M/S/V)
- **Modules fonctionnels :** Paramètres, Scolarité/Inscriptions, Versements, Kiosque, Comptabilité, Statistiques, Utilisateurs/Droits, Tableau de bord
- **Modules non développés :** Bibliothèque (placeholder), SMS (menu seul)
- **Impression :** Fonctionnelle pour 8/9 rapports ; seule la Balance des comptes reste "à venir"

### ⚠️ Point d'attention immédiat : arbre de travail non commité

```
24 fichiers modifiés (migration session.get(), nettoyage list_printer.py/statistiques_service.py)
3 fichiers non suivis : requirements-dev.txt, tests/, utils/datetime_utils.py
```
Ce travail est terminé et validé (compilation OK, 23 tests passent), mais n'est pas encore commité. À committer avant de continuer, pour éviter de le perdre ou de le mélanger avec de nouvelles modifications.

### Risques résolus depuis le 20/06

| # | Risque (diagnostic 20/06) | Statut au 01/07 |
|---|---|---|
| 1 | `Login="Directeur"` hardcodé dans `inscription_service.py` | ✅ Résolu — plus aucune occurrence, passe par `AppSession` |
| 2 | `login="ADMIN"` hardcodé dans `caisse_view.py` | ✅ Résolu — idem |
| 3 | `get_logged_in_username()` retournait "KANGA JULIEN" en dur | ✅ Résolu — vraie authentification (module Utilisateurs), session pilotée par `AppSession.set_current_user()` |
| 4 | CASCADE dangereux Famille→Élève / Famille→Inscription | ✅ Résolu — `cascade="save-update, merge"` (delete-orphan retiré, commentaire explicite) |
| 5 | Suppression élève sans vérifier les versements | ✅ Résolu — `EleveService.delete_eleve()` bloque si inscriptions OU versements existent |
| 6 | `echo=True` en dur dans `database.py` | ✅ Résolu — conditionné sur `APP_ENV=dev_debug` |
| 7 | Boutons Imprimer = "Impression à venir" (8 vues) | ✅ Résolu pour 7/8 (Inscrits, Nouveaux, Scolarité, Cantine, Transport, Vente, Stock + Prestataires) |
| 8 | `session.query(Model).get(id)` déprécié | ✅ Résolu — migré vers `session.get(Model, id)` (en attente de commit) |
| 9 | `SoldeAnt`/`Impaye` hardcodés à 0.0 dans stats scolarité | ✅ Nettoyé — champs retirés du rapport (colonnes mortes supprimées proprement, pas de faux 0.0 affiché) |
| 10 | Aucun test automatisé | ✅ Résolu — `tests/` avec conftest.py, factories.py, 23 tests (utilisateurs, versements, ventilation) |
| 11 | Tableau de bord = QLabel statique | ✅ Résolu — `DashboardView` + `DashboardService` (Phase 5, 20/06) |

### Notes globales sur 100

| Axe | Note (20/06) | Note (01/07) | Commentaire |
|-----|------|------|-------------|
| Architecture | 82 | 84 | Inchangée, un peu plus mûre (module utilisateurs bien intégré) |
| Base de données | 85 | 90 | CASCADE dangereux corrigés, protection suppression élève |
| Stabilité | 78 | 88 | Tests automatisés + migration SQLAlchemy 2.0 propre |
| Interface | 72 | 83 | Impression fonctionnelle (7/8), alignement droite sur 17 vues |
| Cohérence métier | 80 | 90 | Login réel partout, ventilation analytique cohérente |
| Maintenabilité | 78 | 82 | `datetime_utils.utcnow()` centralisé ; encore ~100 `print()` au lieu de `logging` |
| **GLOBAL** | **79** | **86** | Progression nette, reste Bibliothèque/SMS/logging/commit en attente |

---

## 2. CE QUI A CHANGÉ DEPUIS LE 20/06 (voir mémoire de session)

- **22/06** — Module Gestion des Utilisateurs : login, profils, droits par profil (9 fichiers créés, 4 modifiés)
- **24/06** — Impression Statistiques Scolarité : `ScolariteStatPrinter` A4 paysage, interface épurée (9 colonnes, 4 totaux) — étendu depuis à Cantine/Transport/Vente/Stock/Inscrits/Nouveaux/Prestataires
- **29/06 → 01/07** — Ventilation analytique des prestations : couverture des prestations annexes par ordre de création (règle changée en cascade le 01/07), à visée informative pour les stats
- **Non daté (travail en cours, non commité)** — Migration SQLAlchemy 2.0 (`session.get`), ajout de `tests/` (pytest), `utils/datetime_utils.py` (remplace `datetime.utcnow()` déprécié), nettoyage des colonnes mortes `SoldeAnt`/`Impaye`/`sum_ant` dans `list_printer.py` et `statistiques_service.py`

---

## 3. DIAGNOSTIC TECHNIQUE

### Tests automatisés (nouveau)

```
tests/
├── conftest.py       — base de test dédiée (DB_NAME=easy_school_test_db), nettoyage des tables entre tests
├── factories.py       — factories de données de test
├── test_utilisateur_service.py   (7 tests)
├── test_ventilation_service.py   (6 tests)
└── test_versement_service.py     (10 tests)

Résultat : 23 passed in 1.19s
```
Bonne pratique : base de test isolée (`easy_school_test_db`), fixtures `autouse` pour vider les tables entre tests. Aucun test pour Inscription/Eleve/Famille/Comptabilité/Kiosque/Statistiques — couverture encore partielle mais un socle solide est posé.

### Migration SQLAlchemy 2.0
- ✅ Terminée : plus aucune occurrence de `session.query(Model).get(id)` dans le code suivi par Git
- Fichiers concernés : `app/session.py`, `services/inscription_service.py`, `services/prestation_service.py`, et 8 autres services
- `utils/datetime_utils.py` ajouté pour remplacer `datetime.utcnow()` (déprécié en Python 3.12+) par `datetime.now(timezone.utc).replace(tzinfo=None)` — utilisé dans les modèles `prestataire.py`, `prestation_annexe.py`, `ventilation_prestation.py` et `ventilation_service.py`
- ⚠️ Restant : `datetime.now()` encore utilisé directement (sans le helper) dans `services/utilisateur_service.py:80` (`DernierAcces`), `services/stock_service.py:93`, `views/stat_prestataire_view.py:460` — non problématique (pas de `.utcnow()` déprécié) mais incohérent avec le nouveau helper centralisé

### CASCADE et intégrité des données
- ✅ `models/famille.py` : cascade limité à `save-update, merge` sur `eleves` et `inscriptions` (delete-orphan retiré intentionnellement, commenté)
- ✅ `models/eleve.py` : idem sur `inscriptions`
- ✅ `EleveService.delete_eleve()` : bloque si inscriptions OU versements existants
- ✅ `FamilleService.delete_famille()` (`services/famille_service.py:173-192`) : bloque déjà si des élèves sont rattachés à la famille — cohérent avec la protection ajoutée côté élève

### Impression
| Rapport | Statut |
|---------|--------|
| Inscrits | ✅ `imprimer_clic` branché |
| Nouveaux inscrits | ✅ |
| Scolarité | ✅ `ScolariteStatPrinter` |
| Cantine | ✅ `CantineStatPrinter` |
| Transport | ✅ `TransportStatPrinter` |
| Vente kiosque | ✅ `VenteStatPrinter` |
| Stock | ✅ `StockStatPrinter` |
| Prestataires (synthèse + détail) | ✅ `PrestationSyntheseStatPrinter` / `PrestationDetailStatPrinter` |
| Balance des comptes | ❌ `"Impression à venir"` — dernier bouton non implémenté |

### Logging
- Toujours ~100 occurrences de `print()` dans le code applicatif (hors tests) — aucune migration vers `logging` depuis le dernier diagnostic. Faible priorité mais dette qui grossit avec chaque nouveau module.

### Sécurité / secrets
- ✅ `.env` n'a jamais été commité (vérifié via `git log --all -- .env`)
- ✅ `.gitignore` couvre `.env`, `.env.*`, `venv/`
- ✅ `.env.example` ne contient aucune donnée réelle (`CHANGE_ME`)

---

## 4. MODULES NON DÉVELOPPÉS (inchangé depuis le 20/06)

### Bibliothèque
- Toujours un simple `EmptyState` dans `KiosqueView` ("Module Bibliothèque à venir")
- Aucun modèle, service ou vue dédiée

### SMS
- Toujours un commentaire `# index 6: SMS placeholder` dans `main_window.py`, aucune intégration

---

## 5. RISQUES RESTANTS

### ÉLEVÉ
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 1 | 24 fichiers modifiés + 3 non trackés, non commités | racine du projet | Perte de travail possible, risque de conflit avec du travail futur |

### MOYEN
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 2 | Impression Balance des comptes non implémentée | `views/balance_comptes_view.py:170` | Fonctionnalité manquante |
| 3 | N+1 queries dans `StatistiquesService` (pas de `joinedload`) | `services/statistiques_service.py` | Performance sur gros volumes |
| 4 | `TypeSortie` toujours non branché en UI comptabilité | `views/enregistrement_mouvement_view.py` | Catégorisation absente |
| 5 | ~100 `print()` au lieu de `logging` | multiple | Pas de niveaux de log, pas de rotation |

### FAIBLE
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 6 | Bibliothèque = placeholder | `views/kiosque_view.py` | Module absent |
| 7 | SMS = placeholder | `views/main_window.py` | Module absent |
| 8 | `datetime.now()` utilisé hors helper centralisé à 3 endroits | `utilisateur_service.py`, `stock_service.py`, `stat_prestataire_view.py` | Incohérence mineure |
| 9 | Couverture de tests partielle (Inscription/Famille/Éleve/Comptabilité/Kiosque non testés) | `tests/` | Risque de régression non détectée |

---

## 6. PLAN D'ACTION RECOMMANDÉ

1. **Committer le travail en cours** (migration SQLAlchemy 2.0 + tests + datetime_utils + nettoyage list_printer) — c'est terminé et validé, il ne devrait pas rester dans l'arbre de travail
2. **Implémenter l'impression de la Balance des comptes** (dernier bouton "à venir" sur 9 rapports)
3. **Étendre la couverture de tests** aux services Inscription, Famille, Éleve (les plus critiques côté intégrité de données)
4. Priorité basse : Bibliothèque, SMS, migration `print()` → `logging`, `joinedload` dans StatistiquesService

---

*Rapport généré par Claude Code (Sonnet 5) — Diagnostic de suivi Easy School 2.0, 2026-07-01*
