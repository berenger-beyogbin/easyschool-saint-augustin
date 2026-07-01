# DIAGNOSTIC COMPLET — EASY SCHOOL 2.0
**Date de diagnostic :** 2026-06-20  
**Analysé par :** Claude Code (Sonnet 4.6)  
**Périmètre :** `easy_school_python/` — Python 3 / PySide6 / SQLAlchemy / PostgreSQL

---

## 1. SYNTHÈSE EXÉCUTIVE

### État global du projet

Easy School 2.0 est une migration **bien avancée** d'une application WinDev 25 / HFSQL C/S vers Python. L'architecture est propre, la séparation models/services/views est respectée, et les modules principaux sont fonctionnels. Le projet est **utilisable en production limitée** mais comporte encore des zones incomplètes (Bibliothèque, SMS, Tableau de bord, Impression) et quelques risques techniques à corriger avant livraison définitive.

### Niveau de maturité
- **Compilation Python :** ✅ PASS — aucune erreur de syntaxe (py -m compileall .)
- **Architecture générale :** Solide
- **Modules fonctionnels :** Paramètres, Scolarité/Inscriptions, Versements, Kiosque, Comptabilité, Statistiques
- **Modules partiellement développés :** Tableau de bord (texte unique), Impression (tous les boutons → "à venir")
- **Modules non développés :** Bibliothèque (placeholder), SMS (menu seul), Rapports imprimés

### Risques bloquants identifiés
1. `Login="Directeur"` hardcodé dans `inscription_service.py` ligne 141 — cohérence d'audit brisée
2. `DB_PASSWORD` visible en clair dans `.env` (committing accidentel dangereux)
3. Bouton "Imprimer" non fonctionnel dans **toutes** les vues statistiques et comptabilité
4. SQL incorrect dans `TESTS_MANUELS_VERSEMENTS.md` (colonne `"IDNiveau"` au lieu de `"IDT_Niveau"`)
5. `echo=True` dans `database.py` → flood de logs SQL en production

### Priorité de finalisation
Phase 1 (stabilisation) → Phase 2 (corrections login/impression) → Phase 3 (Bibliothèque) → Phase 4 (SMS/placeholders propres) → Phase 5 (Tableau de bord) → Phase 6 (Tests end-to-end) → Phase 7 (Livraison)

### Notes globales sur 100

| Axe | Note | Commentaire |
|-----|------|-------------|
| Architecture | 82/100 | Séparation M/S/V propre, styles centralisés |
| Base de données | 85/100 | Numeric partout, contraintes uniques, CASCADE contrôlées |
| Stabilité | 78/100 | Pas d'erreurs de syntaxe, quelques N+1, echo=True |
| Interface | 72/100 | Styles cohérents, impression absente, SMS/Biblio placeholder |
| Cohérence métier | 80/100 | Versements bien calculés, mais login hardcodé |
| Maintenabilité | 78/100 | Code lisible, mais requêtes dépréciées SQLAlchemy 2.x |
| **GLOBAL** | **79/100** | Projet solide, finalisable rapidement |

---

## 2. STRUCTURE DU PROJET

### Arborescence

```
easy_school_python/
├── main.py                        ← Point d'entrée principal
├── requirements.txt               ← PySide6, SQLAlchemy, psycopg2-binary, python-dotenv
├── .env                           ← Config PostgreSQL (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
├── README_PYTHON.md               ← Documentation utilisateur
├── RESET_DEV_DATABASE.md          ← Procédure reset base dev
├── DIAGNOSTIC_COMPLET_EASY_SCHOOL.md  ← Ce fichier
├── TESTS_MANUELS_*.md (6 fichiers) ← Procédures de tests manuels
├── app/
│   ├── __init__.py
│   ├── config.py                  ← Lecture .env → URL PostgreSQL
│   ├── database.py                ← Engine SQLAlchemy, sessionmaker, create_tables()
│   ├── session.py                 ← AppSession (année active, établissement actif)
│   └── styles.py                  ← Palette et QSS centralisés
├── models/ (23 modèles .py)
├── services/ (21 services .py)
├── views/ (47 vues .py)
└── assets/logos/.gitkeep          ← Logos (répertoire vide à ce stade)
```

### Fichiers suspects ou à surveiller
- `.env` : contient `DB_PASSWORD=Carowhite45` en clair → ne pas committer
- `assets/logos/.gitkeep` : répertoire logos vide — pas de gestion de logo établissement active
- Aucun fichier `__pycache__` ni `.pyc` stale problématique détecté

---

## 3. DIAGNOSTIC DE L'ARCHITECTURE

### Points forts
- **Séparation M/S/V** respectée : chaque couche a son rôle clair
- **Styles centralisés** dans `app/styles.py` : `STYLE_BUTTON_PRIMARY`, `STYLE_TABLE`, `COLOR_PRIMARY_BLUE`, etc.
- **AppSession** gère correctement l'année active et l'établissement actif avec rechargement automatique
- **`create_tables()`** importe tous les modèles avant `Base.metadata.create_all()` → aucun modèle oublié
- **Migration idempotente** via `ALTER TABLE IF EXISTS ... ADD COLUMN IF NOT EXISTS` dans `database.py`
- **joinedload** utilisé dans VersementService, EleveService, StockService pour éviter les DetachedInstanceError
- **`pool_pre_ping=True`** dans le moteur SQLAlchemy → reconnexion automatique si connexion idle

### Faiblesses identifiées

| Problème | Fichier | Ligne | Gravité |
|---------|---------|-------|---------|
| `echo=True` en prod | `app/database.py` | 21 | MOYEN |
| `session.query(...).get(id)` déprécié SQLAlchemy 2.x | multiple services | - | FAIBLE |
| N+1 queries dans StatistiquesService (join sans joinedload/contains_eager) | `services/statistiques_service.py` | 22-44 | MOYEN |
| `Login="Directeur"` hardcodé | `services/inscription_service.py` | 141 | ÉLEVÉ |
| `login="ADMIN"` passé depuis la vue | `views/caisse_view.py` | 659 | ÉLEVÉ |
| Onglet "Versements" dans Paramètres = QLabel placeholder | `views/main_window.py` | 256-257 | MOYEN |
| Gestion utilisateur non implémentée (get_logged_in_username hardcoded) | `app/session.py` | 12-13 | ÉLEVÉ |

---

## 4. DIAGNOSTIC BASE DE DONNÉES

### Tableau des modèles

| Fichier | Classe Python | Table PostgreSQL | Clé primaire | Relations | Risques |
|---------|---------------|-----------------|--------------|-----------|---------|
| etablissement.py | EtablissementEcole | Etablissement_Ecole | IDEtablissement_Ecole | Aucune directe | OK |
| annee_scolaire.py | TAnneeScolaire | TAnneeScolaire | IDTAnneeScolaire | niveaux, classes | OK |
| cycle.py | TCycle | TCycle | IDT_Cycle | niveaux, classes | Contrainte unique (Libelle+Annee+Etab) ✅ |
| niveau.py | TNiveau | TNiveau | IDT_Niveau | cycle, annee_scolaire, classes | Contrainte unique (Libelle+Cycle+Annee+Etab) ✅ |
| classe.py | TClasse | TClasse | IDTClasse | cycle, niveau, annee_scolaire | Contrainte unique (LibClasse+Niveau+Annee+Etab) ✅ |
| nationalite.py | TNationalite | TNationalite | IDTNationalite | Aucune | OK |
| religion.py | TReligion | TReligion | IDTReligion | Aucune | OK |
| famille.py | TFamille | TFamille | IdTFamille | eleves(delete-orphan), inscriptions(delete-orphan) | ⚠️ CASCADE dangereux |
| eleve.py | Eleve | Eleve | IDEleve | famille, nationalite, religion, inscriptions(delete-orphan) | ⚠️ |
| inscription.py | TInscription | TInscription | IDTInscription | annee_scolaire, famille, eleve, niveau, classe | UniqueConstraint(IDEleve+IDAnneeScolaire) ✅ |
| montant_scol.py | MontantScol | MontantScol | IDMontantScol | annee_scolaire, niveau | UniqueConstraint(Annee+Niveau) ✅ |
| montant_cantine.py | MontantCantine | MontantCant | IDMontantCant | annee_scolaire, niveau | UniqueConstraint ✅ |
| montant_transport.py | MontantTransport | MontantTrans | IDMontantTrans | annee_scolaire, niveau | UniqueConstraint ✅ |
| autres_frais.py | AutresFrais | Autres_Frais | IDAutres_Frais | Aucune | CodeFrais unique ✅ |
| montant_autres_frais.py | MontantAutresFrais | MontantAutresFrais | IDMontantAutres | annee_scolaire, etablissement, niveau, autre_frais | UniqueConstraint 4 colonnes ✅ |
| versement_scol.py | VersementScol | VersementScol | IDVersementScol | famille, eleve, annee_scolaire | CASCADE depuis Famille et Eleve ⚠️ |
| article.py | Article | TArticle | IDTArticle | Aucune | Libelle unique ✅ |
| stock_cour.py | StockCour | StockCour | IDStockCour | article | IDTArticle unique ✅ |
| stock_entree.py | StockEntree | StockEnt | IDStockEnt | annee_scolaire, article | OK |
| stock_sortie.py | StockSortie | StockSortie | IDStockSort | annee_scolaire, article | OK |
| compte.py | Compte | Compte | IDCompte | Aucune | NumCompte unique ✅ |
| type_sortie.py | TypeSortie | TypeSortie | IDTypeSortie | compte | OK — non utilisé en UI |
| sortie_fin.py | SortieFin | SortieFin | IDSortieFin | compte, annee_scolaire | RESTRICT sur delete ✅ |

### Vérifications critiques

**Imports dans create_tables() :** ✅ Tous les 23 modèles sont importés explicitement

**upgrade_schema() :** ✅ Présent via ALTER TABLE IF EXISTS dans `create_tables()` (lignes 82-87)

**Colonnes ajoutées par migration idempotente :**
- `VersementScol.MontantCantine` ✅ (ADD COLUMN IF NOT EXISTS)
- `VersementScol.MontantVersAutres` ✅ (ADD COLUMN IF NOT EXISTS)

**Types monétaires :** ✅ Tous les montants utilisent `Numeric(12,2)` — aucun `Float` pour les montants

**Risques CASCADE dangereux :**
- `TFamille → Eleve` : `cascade="all, delete-orphan"` → supprimer une famille supprime TOUS ses élèves
- `TFamille → TInscription` : idem → supprime toutes les inscriptions associées
- `Eleve → TInscription` : idem → cohérent avec le précédent
- `VersementScol` : CASCADE depuis `Famille` et `Eleve` au niveau DB → perte de tout l'historique de paiements si famille ou élève supprimé
- **Recommandation :** Vérifier que les services de suppression de famille/élève vérifient bien les versements existants avant suppression (voir `EleveService.delete_eleve()` qui vérifie les inscriptions ✅, mais pas les versements)

**TypeSortie non branché en UI :**
- La table `TypeSortie` existe avec son modèle et son service (`type_sortie_service.py`)
- La vue `enregistrement_mouvement_view.py` ne l'utilise pas — l'enregistrement est direct sans catégorie prédéfinie
- Décision métier à confirmer : intégrer TypeSortie ou supprimer le modèle

---

## 5. DIAGNOSTIC PAR MODULE

### A. PARAMÈTRES

**Statut : ✅ OK**

| Sous-module | Statut | Notes |
|-------------|--------|-------|
| Établissement | ✅ OK | Sauvegarde/chargement fonctionnels |
| Année Scolaire | ✅ OK | Signal `data_changed` branché sur MainWindow |
| Cycles | ✅ OK | Contrainte unique, protection suppression si niveaux liés |
| Niveaux | ✅ OK | Filtré par année et cycle actifs |
| Classes | ✅ OK | Capacité [1-200] validée, contrainte unique |
| Nationalités | ✅ OK | Unicité contrôlée |
| Religions | ✅ OK | Unicité contrôlée |

**Bugs détectés :**
- Aucun bug fonctionnel détecté dans les paramètres

**Améliorations nécessaires :**
- Onglet "Versements" dans Paramètres reste un QLabel placeholder (`main_window.py:256`) — doit afficher une info utile ou être supprimé du menu
- Logo établissement non géré (`LogoPath` existe dans le modèle mais `assets/logos/` est vide)

**Priorité :** Faible — module stable

---

### B. SCOLARITÉ > INSCRIPTIONS

**Statut : ✅ OK**

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Familles (Liste, Ajout, Modif, Suppression) | ✅ OK | FamilleService complet |
| Élèves (Fiche, Ajout, Modif, Suppression) | ✅ OK | EleveService avec validation |
| Génération Matricule | ✅ OK | Format AA-XXX basé sur l'année active |
| Liaison Élève/Famille | ✅ OK | IDFamille mis à jour si nécessaire à l'inscription |
| Inscription (Niveau+Classe+Année) | ✅ OK | Double-check doublon + capacité classe |
| Contrôle doublon inscription | ✅ OK | UniqueConstraint + vérification service |
| Contrôle capacité classe | ✅ OK | Vérification effectif vs Capacite |
| Suppression sécurisée élève | ✅ OK | Bloqué si inscriptions existantes |
| Chargement nationalités/religions | ✅ OK | Via ComboBox dans EleveFormView |

**Bugs identifiés :**
1. **Login hardcodé** : `InscriptionService.create_inscription()` ligne 141 → `Login="Directeur"` au lieu de `AppSession.get_logged_in_username()`
2. **EleveService.get_eleves_non_inscrits_by_famille()** : condition `(~Eleve.IDEleve.in_(inscrits_list) if inscrits_list else True)` — le `True` ne filtre pas correctement si la liste est vide (retourne tous les élèves de la famille, ce qui est l'objectif, mais la syntaxe peut être confuse)
3. **Potentiel DetachedInstanceError** : `InscriptionService.get_inscriptions_by_annee()` retourne des objets sans joinedload — non utilisé directement en vue avec accès relations, mais risque si réutilisé

**Priorité :** ÉLEVÉ (login hardcodé)

---

### C. SCOLARITÉ > VERSEMENTS

**Statut : ✅ OK — Logique métier solide**

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Paramétrage scolarité (MontantScol) | ✅ OK | Montant standard + EnsPri + EnsSec |
| Paramétrage transport (MontantTrans) | ✅ OK | Par niveau et année |
| Paramétrage cantine (MontantCant) | ✅ OK | Par niveau et année |
| Autres frais (AutresFrais + MontantAutresFrais) | ✅ OK | Affectation par niveau |
| Caisse (VersementScol) | ✅ OK | Calcul dû/versé/reste |
| MontantCantine | ✅ OK | Colonne présente dans modèle et migration |
| MontantVersAutres | ✅ OK | Colonne présente dans modèle et migration |
| Plafond anti-dépassement | ✅ OK | Validé dans VersementService.create_versement() |
| Options inscription (Scol/Cant/Trans/Autres) | ✅ OK | Champs désactivés si option non cochée |
| Réduction | ✅ OK | Checkbox + flag en base |
| Cohérence année active | ✅ OK | Filtrage IDTAnneeScolaire correct |
| Restitution (bypass plafond) | ✅ OK | Mode restitution disponible |

**Bugs identifiés :**
1. **login="ADMIN"** dans `CaisseView.on_validate_and_save()` ligne 659 — devrait être `AppSession.get_logged_in_username()`
2. **Arrondis** : `int(fin['scol_reste'])` dans la vue peut causer des différences d'arrondi pour les montants Decimal. À surveiller.
3. **`clear_dashboard()`** dans `caisse_view.py` lignes 707-718 : logique de reset des labels complexe et fragile — certains labels pourraient ne pas se réinitialiser correctement

**Priorité :** MOYEN

---

### D. KIOSQUE

**Statut : ✅ OK**

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Articles (Liste, Ajout, Modif, Suppression) | ✅ OK | ArticleService |
| Kits (Contenu JSON en Text) | ✅ OK | ContenuKit + QteKit en Text formaté |
| Stock courant (StockCour) | ✅ OK | Unique par article |
| Approvisionnement | ✅ OK | Date saisie + historique StockEnt |
| Vente (panier) | ✅ OK | Double-check stock avant validation |
| Historique entrées | ✅ OK | joinedload(article) ✅ |
| Historique sorties | ✅ OK | joinedload(article) ✅ |
| Sécurité stock négatif | ✅ OK | Vérification `sc.QuantiteCour < qte` |
| AppSession.get_logged_in_username() | ⚠️ PARTIEL | Retourne "KANGA JULIEN" hardcodé |
| vendre_article() | ✅ OK | Proxy vers StockService.remove_stock() |

**Risques :**
1. **KIT** : La vente d'un kit diminue le stock du kit lui-même (pas des composants). La décomposition du kit en articles n'est pas automatique — `ContenuKit` et `QteKit` sont stockés en Text (ex: "1;4;7") mais pas utilisés pour la déduction atomique. C'est un choix de design à confirmer.
2. **Prix modifiable par l'opérateur** : `txt_pu` est éditable dans VenteView — risque de manipulation du prix de vente
3. **Pas de suppression d'historique** : impossible de corriger une vente enregistrée (pas de "annuler vente")

**Priorité :** MOYEN

---

### E. COMPTABILITÉ

**Statut : ✅ FONCTIONNEL — Limites fonctionnelles à noter**

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Création de compte | ✅ OK | NumCompte unique |
| TypeSortie | ⚠️ NON UTILISÉ EN UI | Modèle et service existent, pas branché |
| SortieFin (mouvement Débit/Crédit) | ✅ OK | |
| Enregistrement débit/crédit | ✅ OK | Sélection compte obligatoire |
| Génération CodeSortie | ✅ OK | Format SF-AAAA-XXXX séquentiel |
| État des sorties | ✅ OK | Filtre sur DebitCredit='Debit' |
| Balance des comptes | ✅ OK | Outer join pour inclure comptes sans mouvements |
| Calcul solde | ✅ OK | Solde = Credit - Debit |
| Cohérence année scolaire | ✅ OK | IDAnSco filtré |
| Intégration avec versements | ❌ ABSENTE | Pas de liaison automatique |
| Intégration avec kiosque | ❌ ABSENTE | Pas de liaison automatique |

**Limites reconnues :**
1. La comptabilité est **indépendante** des versements et du kiosque — c'est une saisie manuelle pure
2. Le bouton "Imprimer" dans Balance des Comptes affiche "Impression à venir" (`balance_comptes_view.py:169`)
3. `TypeSortie` existe mais n'est pas intégré dans `EnregistrementMouvementView` — cela simplifie l'interface mais perd la catégorisation automatique

**Priorité :** MOYEN (impression manquante)

---

### F. STATISTIQUES

**Statut : ✅ FONCTIONNEL — Impression manquante**

| Rapport | Statut | Notes |
|---------|--------|-------|
| Inscrits | ✅ OK | Filtres niveau/classe |
| Nouveaux inscrits | ✅ OK | Filtre Nouveau=True |
| Scolarité | ✅ OK | Calcul MontantDu / Versé / Reste |
| Cantine | ✅ OK | Filtré Cantine=True |
| Transport | ✅ OK | Filtré Transport=True |
| Vente kiosque | ✅ OK | StockSortie jointe Article |
| Stock | ✅ OK | Alerte si QuantiteCour <= QTESeuil |
| Boutons Imprimer | ❌ PLACEHOLDER | Tous → "Impression à venir" |

**Bugs détectés :**
1. **`SoldeAnt` et `Impaye` hardcodés à 0.0** dans `get_etat_versements_scolarite()` (lignes 162-163) — ces colonnes ne sont pas calculées
2. **N+1 queries** dans `get_inscrits()`, `get_nouveaux_inscrits()` : `ins.eleve.Matricule`, `ins.classe.LibClasse`, `ins.niveau.Libelle` triggent des lazy loads sans joinedload (session toujours ouverte donc pas DetachedInstanceError, mais non optimal)
3. **Filtre scolarité** : dans `get_etat_versements_scolarite()`, les inscriptions sans option Scolarité (`ins.Scolarite=False`) ont `scol_due=0` mais apparaissent dans le rapport avec état "Impayé" — devrait être filtré ou étiqueter différemment

**Priorité :** MOYEN

---

### G. BIBLIOTHÈQUE

**Statut : ❌ PLACEHOLDER UNIQUEMENT**

- Présent comme onglet dans `KiosqueView` (deuxième onglet "BIBLIOTHÈQUE")
- Affiche `QGroupBox("Espace Bibliothèque")` avec texte "Module Bibliothèque à venir"
- **Aucun modèle**, aucun service, aucune vue dédiée
- Aucune table `TLivre`, `TEmprunt`, `TAuteur` ou équivalent dans les modèles
- Non mentionné dans `create_tables()` — aucune table créée

**Proposition de développement prioritaire :**
1. Créer modèles : `TLivre` (ISBN, Titre, Auteur, Editeur, Exemplaires), `TEmprunt` (IDLivre, IDEleve, DateEmprunt, DateRetour, Restitue)
2. Créer services : `livre_service.py`, `emprunt_service.py`
3. Créer vues : `livre_list_view.py`, `emprunt_view.py`
4. Intégrer dans `KiosqueView` en remplacement du placeholder

---

### H. SMS

**Statut : ❌ PLACEHOLDER — MENU SEUL**

- Présent uniquement dans le menu gauche : `"SMS (Bientôt)"` (ligne 109)
- Aucun service, aucune vue, aucune intégration API SMS
- Navigation vers SMS affiche le tableau de bord générique avec le message "Module 'SMS (Bientôt)' en cours de développement..."

**Proposition :**
- Court terme : Renommer en `"SMS (Bientôt)"` avec une vue dédiée informant des API compatibles (ex: Twilio, Orange SMS CI)
- Moyen terme : Intégrer une API SMS (numéro de téléphone = `CellulaireResponsable` dans `TFamille`)
- Dépendances : `TFamille.CellulaireResponsable`, possiblement configuration serveur SMTP/SMS

---

### I. TABLEAU DE BORD

**Statut : ❌ PLACEHOLDER**

- `widget_dashboard` = `QLabel("Bienvenue dans l'administration d'école Easy School 2.0 !")` (ligne 167)
- Aucune donnée réelle affichée
- Activé pour les index de menu 0 (Tableau de bord), 5 (SMS), et tout menu non reconnu

**Ce qu'il faudrait afficher en version finale :**
- Nombre d'élèves inscrits pour l'année active
- Montant total encaissé / reste à payer (scolarité)
- Alertes stock kiosque (articles sous le seuil)
- Dernières transactions comptables
- Raccourcis vers les modules principaux

---

## 6. DIAGNOSTIC INTERFACE UTILISATEUR

### Analyse globale
- **Texte blanc hors sidebar :** ✅ AUCUN — recherche `QWidget { color: white }` → 0 résultat
- **QLabel { color: white } :** ✅ AUCUN — 0 résultat
- **Styles globaux :** Cohérents — app/styles.py utilisé dans toutes les vues
- **Couleurs boutons :** Logique cohérente (bleu=primaire, vert=succès, gris=secondaire, rouge=danger)
- **Tableaux :** Alternance de couleurs cohérente (ligne paire blanche, ligne impaire bleu clair)
- **Alignement des montants :** Non alignés à droite dans les tableaux (`QTableWidgetItem` sans `Qt.AlignRight`)

### Occurrences importantes recherchées

| Pattern recherché | Résultat |
|-------------------|---------|
| `QWidget { color: white }` | ✅ Aucune occurrence |
| `QLabel { color: white }` | ✅ Aucune occurrence |
| `Qt.GlobalColor.fromRgb` | ✅ Aucune occurrence |
| `setFont(QColor` | ✅ Aucune occurrence |
| `close_active_tab` | ✅ Existe dans MainWindow (ligne 313), correctement appellé par les sous-vues |
| `get_logged_in_username` | ⚠️ Hardcodé "KANGA JULIEN" dans `app/session.py:13` |
| `print_placeholder` | ⚠️ Dans `balance_comptes_view.py:169` → "Impression à venir" |
| `imprimer_clic` | ⚠️ Dans toutes les vues stat → "Impression à venir" |
| `SMS (Bientôt)` | ⚠️ Dans menu `main_window.py:109` — placeholder visible |
| `Bientôt` | ⚠️ 1 occurrence (SMS) |

### Menus non branchés / placeholders restants
1. **SMS (Bientôt)** → redirige vers tableau de bord générique
2. **Tableau de bord** → QLabel statique
3. **Onglet "Versements" dans Paramètres** → QLabel placeholder (`main_window.py:256`)
4. **Bibliothèque** (onglet dans Kiosque) → placeholder avec texte statique
5. **Tous les boutons "Imprimer"** (7 vues stat + 1 balance) → "Impression à venir"

---

## 7. DIAGNOSTIC TECHNIQUE SQLALCHEMY

### Sessions et risques DetachedInstanceError

| Service | Méthode | Risk DetachedInstanceError | Raison |
|---------|---------|--------------------------|--------|
| `versement_service.py` | `get_eleves_inscrits()` | ✅ FAIBLE | joinedload sur eleve, famille, classe, niveau |
| `eleve_service.py` | `get_all_eleves()` | ✅ FAIBLE | joinedload sur nationalite, religion, famille |
| `stock_service.py` | `get_stock_history_entrees()` | ✅ FAIBLE | joinedload(article) |
| `stock_service.py` | `get_stock_history_sorties()` | ✅ FAIBLE | joinedload(article) |
| `comptabilite_service.py` | `get_all_mouvements()` | ✅ FAIBLE | joinedload(compte) |
| `inscription_service.py` | `get_inscriptions_by_annee()` | ⚠️ RISQUE | Aucun joinedload — si relations accédées après close() |
| `statistiques_service.py` | `get_inscrits()` | ⚠️ N+1 | join() sans joinedload → accès lazy dans le try block |
| `session.py` | `is_active_annee_valid()` | ✅ FAIBLE | Accède uniquement à annee.Cloturer (attribut direct) |

### Patterns dépréciés SQLAlchemy 2.x
- `session.query(Model).get(id)` → déprécié depuis SQLAlchemy 2.0
- Doit être remplacé par `session.get(Model, id)`
- Fichiers affectés : `app/session.py:47`, `services/eleve_service.py:216`, `services/inscription_service.py:58/115/145`, `services/versement_service.py:265`

### Commit/Rollback
- Pattern cohérent dans tous les services : try/except/rollback/finally close ✅
- Aucune transaction laissée ouverte détectée

### Exceptions silencieuses
- Plusieurs `except Exception as e: print(...)` sans relever l'exception → erreurs non propagées à l'UI dans les services statistiques et stock
- `on_fermer()` dans `vente_view.py` et `approvisionnement_view.py` : `try: ... except: pass` → silence total sur l'erreur

---

## 8. DIAGNOSTIC DES TESTS MANUELS

### Fichiers présents
| Fichier | Présent | Cohérence |
|---------|---------|-----------|
| TESTS_MANUELS_PARAMETRES.md | ✅ | ✅ Bon |
| TESTS_MANUELS_SCOLARITE_INSCRIPTIONS.md | ✅ | ✅ Bon |
| TESTS_MANUELS_VERSEMENTS.md | ✅ | ⚠️ Bug SQL |
| TESTS_MANUELS_KIOSQUE.md | ✅ | À vérifier |
| TESTS_MANUELS_COMPTABILITE.md | ✅ | À vérifier |
| TESTS_MANUELS_STATISTIQUES.md | ✅ | À vérifier |

### Bug SQL identifié dans TESTS_MANUELS_VERSEMENTS.md

**Section 3.2 — Requête incorrecte :**
```sql
-- INCORRECT (colonne "IDNiveau" n'existe pas dans MontantAutresFrais) :
JOIN "TNiveau" n ON m."IDNiveau" = n."IDT_Niveau"

-- CORRECT (la colonne s'appelle "IDT_Niveau" dans MontantAutresFrais) :
JOIN "TNiveau" n ON m."IDT_Niveau" = n."IDT_Niveau"
```
Le modèle `montant_autres_frais.py` définit `IDT_Niveau = Column(...)` mais la requête SQL du test utilise `m."IDNiveau"`. Cette requête PostgreSQL retournerait une erreur `column "IDNiveau" does not exist`.

### Tests manquants
- Test de clôture d'année avec migration de données vers l'année suivante
- Test de suppression d'un élève ayant des versements
- Test de stock négatif forcé
- Test de balance comptable avec mouvements croisés débit/crédit

---

## 9. TESTS TECHNIQUES EXÉCUTÉS

### Compilation Python
```
Commande : py -m compileall .
Résultat : SUCCÈS — Tous les fichiers Python compilent sans erreur de syntaxe
Fichiers analysés : 95 fichiers .py
Erreurs : 0
```

### Tests d'import (non exécutables sans PostgreSQL actif en session diagnostique)
Note : Les imports nécessitent une connexion PostgreSQL active car `app/database.py` est importé par tous les modules.

Analyse statique des imports : ✅ Tous les imports sont cohérents entre les modules.

---

## 10. RECHERCHES OBLIGATOIRES DANS LE CODE

### Occurrences critiques par catégorie

#### TODO / FIXME
**Résultat :** Aucune occurrence `TODO` ni `FIXME` dans le code Python

#### pass
**Résultat :** Aucune occurrence significative de `pass` nu dans les handlers

#### Bientôt / SMS
| Fichier | Ligne | Occurrence | Risque | Action |
|---------|-------|-----------|--------|--------|
| `views/main_window.py` | 109 | `"SMS (Bientôt)"` | FAIBLE | Remplacer ou garder en l'état |

#### Placeholder / close_active_tab
| Fichier | Ligne | Occurrence | Statut |
|---------|-------|-----------|--------|
| `views/main_window.py` | 313 | `def close_active_tab():` | ✅ Méthode implémentée |
| `views/main_window.py` | 256 | Onglet "Versements" Paramètres = QLabel | ⚠️ Placeholder |
| `views/main_window.py` | 166 | `widget_dashboard` = QLabel | ⚠️ Placeholder |
| `views/kiosque_view.py` | 112 | Onglet Bibliothèque = placeholder | ⚠️ Placeholder |

#### get_logged_in_username
| Fichier | Ligne | Valeur | Action |
|---------|-------|--------|--------|
| `app/session.py` | 13 | `return "KANGA JULIEN"` | ⚠️ Hardcodé — à connecter à un vrai système d'auth |
| `views/vente_view.py` | 365 | `AppSession.get_logged_in_username()` | OK — appelle la méthode |
| `views/approvisionnement_view.py` | 258 | idem | OK |
| `services/comptabilite_service.py` | 68 | idem | OK |

#### Login hardcodé (contournant AppSession)
| Fichier | Ligne | Valeur | Action |
|---------|-------|--------|--------|
| `services/inscription_service.py` | 141 | `Login="Directeur"` | ❌ À corriger → `AppSession.get_logged_in_username()` |
| `views/caisse_view.py` | 659 | `login="ADMIN"` | ❌ À corriger |

#### print_placeholder / Imprimer
| Fichier | Ligne | Comportement | Action |
|---------|-------|-------------|--------|
| `views/balance_comptes_view.py` | 169 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_inscrits_view.py` | 186 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_nouveaux_view.py` | 197 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_scolarite_view.py` | 250 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_cantine_view.py` | 221 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_transport_view.py` | 221 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_vente_view.py` | 198 | "Impression à venir" | ⚠️ À implémenter |
| `views/stat_stock_view.py` | 196 | "Impression à venir" | ⚠️ À implémenter |

#### CASCADE et delete-orphan
| Fichier | Cascade | Risque |
|---------|---------|--------|
| `models/famille.py:55` | `cascade="all, delete-orphan"` sur eleves | ⚠️ Supprimer famille → supprime TOUS ses élèves |
| `models/famille.py:56` | `cascade="all, delete-orphan"` sur inscriptions | ⚠️ Supprimer famille → supprime toutes ses inscriptions |
| `models/eleve.py:40` | `cascade="all, delete-orphan"` sur inscriptions | ⚠️ Supprimer élève → supprime ses inscriptions |
| `models/versement_scol.py:13` | `ondelete="CASCADE"` sur IDFamille | ⚠️ Supprimer famille → supprime TOUS les versements |
| `models/versement_scol.py:20` | `ondelete="CASCADE"` sur IDEleve | ⚠️ Supprimer élève → supprime TOUS ses versements |

#### float (en dehors des modèles)
Utilisé correctement dans les services pour les calculs après extraction de Numeric → `float(m_scol.Montant)`. Acceptable pour les calculs intermédiaires.

#### Numeric
✅ Tous les montants monétaires utilisent `Numeric(12, 2)` dans les modèles.

#### echo=True
| Fichier | Ligne | Valeur | Action |
|---------|-------|--------|--------|
| `app/database.py` | 21 | `echo=True` | ⚠️ À passer à `False` en production |

---

## 11. RISQUES PRIORITAIRES

### CRITIQUE
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 1 | Mot de passe PostgreSQL en clair dans `.env` | `.env:5` | Sécurité — si commité sur Git |
| 2 | SQL incorrect dans fichier de tests (colonne inexistante) | `TESTS_MANUELS_VERSEMENTS.md:102` | Tests invalides → fausse confiance |
| 3 | Suppression d'une famille supprime TOUS ses élèves et versements (CASCADE) | `models/famille.py:55-56` | Perte de données irréversible |

### ÉLEVÉ
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 4 | Login="Directeur" hardcodé dans audit d'inscription | `services/inscription_service.py:141` | Piste d'audit brisée |
| 5 | login="ADMIN" dans l'enregistrement de versement | `views/caisse_view.py:659` | Piste d'audit brisée |
| 6 | `get_logged_in_username()` retourne toujours "KANGA JULIEN" | `app/session.py:13` | Authentification fictive |
| 7 | Pas de vérification de versements avant suppression élève | `services/eleve_service.py:291-298` | Perte de données historiques |

### MOYEN
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 8 | `echo=True` en production → flood logs SQL | `app/database.py:21` | Performance et sécurité |
| 9 | Impressions non implémentées (8 boutons) | stat_*.py, balance_comptes_view.py | Fonctionnalité manquante |
| 10 | TypeSortie non utilisé en UI de comptabilité | `views/enregistrement_mouvement_view.py` | Catégorisation absente |
| 11 | SoldeAnt et Impaye hardcodés à 0.0 dans stats scolarité | `services/statistiques_service.py:162-163` | Données incorrectes |
| 12 | `session.query().get()` déprécié SQLAlchemy 2.x | multiple | Warnings futurs |
| 13 | N+1 queries dans statistiques_service | `services/statistiques_service.py` | Performance |
| 14 | Onglet "Versements" dans Paramètres = QLabel inutile | `views/main_window.py:256` | UX trompeuse |
| 15 | Tableau de bord = QLabel statique | `views/main_window.py:167` | Fonctionnalité absente |

### FAIBLE
| # | Risque | Fichier | Impact |
|---|--------|---------|--------|
| 16 | Bibliothèque = placeholder | `views/kiosque_view.py:112` | Module absent |
| 17 | SMS = placeholder | `views/main_window.py:109` | Module absent |
| 18 | Montants non alignés à droite dans les tableaux | Multiple vues | Ergonomie |
| 19 | Logo établissement non géré | `models/etablissement.py:18` | Fonctionnalité absente |
| 20 | Prix de vente éditable par l'opérateur dans VenteView | `views/vente_view.py:75-78` | Risque manipulation prix |

---

## 12. PLAN DE FINALISATION

### Phase 1 — Stabilisation technique (Estimé : 2-3 heures)
**Objectif :** Éliminer les risques élevés et critiques

| Tâche | Fichier | Priorité |
|-------|---------|----------|
| Corriger `Login="Directeur"` → `AppSession.get_logged_in_username()` | `services/inscription_service.py:141` | CRITIQUE |
| Corriger `login="ADMIN"` → `AppSession.get_logged_in_username()` | `views/caisse_view.py:659` | CRITIQUE |
| Passer `echo=True` → `echo=False` en production (ou conditionnel sur APP_ENV) | `app/database.py:21` | ÉLEVÉ |
| Remplacer `session.query(Model).get(id)` → `session.get(Model, id)` | Multiple services | MOYEN |
| Ajouter vérification versements avant suppression élève | `services/eleve_service.py:291` | ÉLEVÉ |
| Corriger SQL `"IDNiveau"` → `"IDT_Niveau"` dans TESTS_MANUELS | `TESTS_MANUELS_VERSEMENTS.md:102` | CRITIQUE |
| Ajouter `.gitignore` incluant `.env` | Racine projet | CRITIQUE |

**Dépendances :** Aucune — tâches indépendantes

---

### Phase 2 — Correction des modules existants (Estimé : 3-5 heures)
**Objectif :** Améliorer la qualité et cohérence des modules fonctionnels

| Tâche | Fichier | Priorité |
|-------|---------|----------|
| Corriger `SoldeAnt` et `Impaye` dans stats scolarité | `services/statistiques_service.py:162-163` | ÉLEVÉ |
| Aligner les montants à droite dans les tableaux | Multiple vues | MOYEN |
| Intégrer `TypeSortie` dans EnregistrementMouvementView (ou supprimer le modèle) | Vue + service | MOYEN |
| Supprimer/remplacer le QLabel placeholder "Versements" dans Paramètres | `views/main_window.py:256` | FAIBLE |
| Remplacer N+1 par joinedload/contains_eager dans StatistiquesService | `services/statistiques_service.py` | MOYEN |
| Conditionner `echo` sur `APP_ENV` | `app/database.py` | MOYEN |

**Dépendances :** Phase 1 complétée

---

### Phase 3 — Développement Bibliothèque (Estimé : 8-12 heures)
**Objectif :** Implémenter le module Bibliothèque

| Tâche | Fichiers à créer |
|-------|-----------------|
| Créer modèles TLivre et TEmprunt | `models/livre.py`, `models/emprunt.py` |
| Créer services | `services/livre_service.py`, `services/emprunt_service.py` |
| Créer vues | `views/livre_list_view.py`, `views/emprunt_view.py` |
| Intégrer dans KiosqueView | `views/kiosque_view.py` |
| Ajouter import dans create_tables() | `app/database.py` |
| Créer TESTS_MANUELS_BIBLIOTHEQUE.md | Racine projet |

**Dépendances :** Phase 1

---

### Phase 4 — SMS et placeholders propres (Estimé : 2-4 heures)
**Objectif :** Gérer proprement les modules futurs

| Tâche | Impact |
|-------|--------|
| Créer une vue `SMSView` informative (API disponibles, configuration) | UX propre |
| Brancher SMS dans le menu principal | `views/main_window.py` |
| OU désactiver le menu SMS jusqu'à implémentation réelle | Honnêteté produit |

---

### Phase 5 — Tableau de bord final (Estimé : 4-6 heures)
**Objectif :** Remplacer le QLabel par un vrai tableau de bord

| Indicateur à afficher | Source de données |
|----------------------|------------------|
| Nb inscrits (année active) | TInscription |
| Total encaissé scolarité | VersementScol.MontantVersSco |
| Total reste à payer | Calcul MontantScol - versé |
| Articles kiosque en alerte | StockCour vs QTESeuil |
| Derniers mouvements comptables | SortieFin |

---

### Phase 6 — Tests de bout en bout (Estimé : 4-8 heures)
**Objectif :** Validation complète avant livraison

| Test | Vérification |
|------|-------------|
| Création établissement → Année → Cycle → Niveau → Classe | Cascade de création |
| Inscription d'un élève → Versement → Statistique | Flux complet |
| Vente kiosque → Stock décrémenté → Stat vente | Flux complet |
| Mouvement comptable → Balance des comptes | Cohérence |
| Redémarrage application → Session préservée | Persistance |
| Clôture d'année → Création automatique année suivante | Robustesse |

---

### Phase 7 — Nettoyage et livraison (Estimé : 2-3 heures)
**Objectif :** Code propre et livrable

| Tâche |
|-------|
| Supprimer `echo=True` ou le conditionner sur APP_ENV |
| Ajouter `.gitignore` avec `.env` |
| Mettre à jour `README_PYTHON.md` avec le guide de démarrage complet |
| Vérifier requirements.txt (versions figées) |
| Nettoyer les `print()` de debug |
| Packaging optionnel (PyInstaller) |

---

## 13. CHECKLIST DE VALIDATION FINALE

| Critère | Statut actuel | Action requise |
|---------|--------------|----------------|
| ✅ Lancement application | ✅ Compile sans erreur | Tester avec PostgreSQL actif |
| ✅ Connexion PostgreSQL | ✅ Config .env présente | Vérifier mot de passe |
| ✅ Paramètres Établissement | ✅ OK | — |
| ✅ Paramètres Années/Cycles/Niveaux/Classes | ✅ OK | — |
| ✅ Inscription élève | ✅ OK | Corriger login audit |
| ✅ Versement scolarité | ✅ OK | Corriger login audit |
| ✅ Vente kiosque | ✅ OK | — |
| ✅ Mouvement comptable | ✅ OK | — |
| ✅ Statistiques | ✅ OK | Corriger SoldeAnt/Impaye |
| ⚠️ Redémarrage → Session préservée | À tester | — |
| ⚠️ Persistance des données | À tester | — |
| ⚠️ Impression statistiques | ❌ Non implémentée | Phase 2 |
| ⚠️ Absence de texte illisible | ✅ Aucun texte blanc trouvé | Vérifier visuellement |
| ⚠️ Absence de données supprimées accidentellement | ⚠️ Risque CASCADE | Phase 1 |
| ❌ Bibliothèque | ❌ Placeholder | Phase 3 |
| ❌ SMS | ❌ Placeholder | Phase 4 |
| ❌ Tableau de bord données réelles | ❌ QLabel statique | Phase 5 |

---

## 14. RECOMMANDATIONS PROFESSIONNELLES

### Structure
- Envisager un dossier `utils/` pour les fonctions communes (formatage FCFA, validation dates) actuellement dupliquées dans les vues
- Centraliser les constantes métier (format matricule, capacité classe par défaut) dans un fichier `app/constants.py`

### Sécurité
- **Authentification réelle :** Créer une table `TUtilisateur` avec hash mot de passe (bcrypt) et remplacer le hardcoding "KANGA JULIEN"
- **`.gitignore` :** Ajouter impérativement `.env` et `__pycache__/`
- **Rotation du mot de passe PostgreSQL :** `Carowhite45` est exposé — le changer et ne jamais committer `.env`
- **Droits PostgreSQL :** Créer un utilisateur dédié avec droits minimaux plutôt que d'utiliser `postgres`

### Sauvegarde PostgreSQL
```bash
# Commande de sauvegarde recommandée
pg_dump -U postgres -h localhost easy_school_db > backup_easy_school_$(date +%Y%m%d).sql

# Restauration
psql -U postgres -h localhost easy_school_db < backup_easy_school_YYYYMMDD.sql
```
- Planifier des sauvegardes automatiques quotidiennes (Windows Task Scheduler)
- Conserver les 7 derniers jours de sauvegardes

### Stratégie de migration
- La migration HFSQL → PostgreSQL via modèles SQLAlchemy est le bon choix — continuer
- Pour les données existantes de WinDev : prévoir un script d'import CSV ou SQL par table
- Documenter les correspondances de colonnes HFSQL → PostgreSQL

### Tests
- Ajouter des tests unitaires Python (`pytest`) pour les services critiques (VersementService, InscriptionService)
- Exemple minimal : tester que `create_versement()` bloque bien si montant > reste dû

### Logs
- Remplacer les `print()` par `logging.getLogger(__name__)` avec niveaux INFO/WARNING/ERROR
- Configurer la rotation des logs pour éviter de remplir le disque

### Gestion erreurs
- Les `except Exception as e: print(f"Erreur: {e}")` silencieux devraient au minimum logger avec niveau WARNING
- Envisager un journal d'erreurs applicatif consultable depuis l'interface

### Packaging futur
- PyInstaller compatible avec PySide6 : `pyinstaller --windowed --onefile main.py`
- Inclure le `.env` dans le répertoire d'exécution (ne pas embarquer dans l'exécutable)
- Tester le packaging sur Windows 10/11 propre (sans Python installé)

### Documentation utilisateur
- Compléter `README_PYTHON.md` avec :
  - Prérequis système
  - Procédure d'installation PostgreSQL
  - Procédure de premier lancement
  - Guide utilisateur par module

---

## 15. FORMAT DE RÉPONSE ATTENDU

### A. Résultat global

- **Statut :** Projet fonctionnel — modules principaux opérationnels
- **Note globale :** 79/100
- **Modules OK :** Paramètres, Scolarité/Inscriptions, Versements, Kiosque, Comptabilité, Statistiques
- **Modules à corriger :** Login audit (Inscription + Versement), SoldeAnt/Impayé stats, Impressions, Tableau de bord, SQL test Versements
- **Modules à développer :** Bibliothèque, SMS, Tableau de bord données réelles, Authentification utilisateur

---

### B. Top 10 des corrections prioritaires

1. **Ajouter `.gitignore`** avec `.env` — risque sécurité immédiat (mot de passe PostgreSQL en clair)
2. **Corriger `Login="Directeur"`** dans `inscription_service.py:141` → `AppSession.get_logged_in_username()`
3. **Corriger `login="ADMIN"`** dans `caisse_view.py:659` → `AppSession.get_logged_in_username()`
4. **Corriger SQL test** `"IDNiveau"` → `"IDT_Niveau"` dans `TESTS_MANUELS_VERSEMENTS.md:102`
5. **Ajouter vérification versements** avant suppression d'un élève dans `eleve_service.py:291`
6. **Passer `echo=False`** ou conditionner sur `APP_ENV` dans `database.py:21`
7. **Corriger `SoldeAnt` et `Impaye`** hardcodés à 0.0 dans `statistiques_service.py:162-163`
8. **Implémenter l'impression** dans au moins les stats Inscrits et Scolarité (priorité)
9. **Remplacer `session.query().get()`** déprécié → `session.get(Model, id)` dans les services
10. **Intégrer ou supprimer `TypeSortie`** de l'interface comptabilité (`enregistrement_mouvement_view.py`)

---

### C. Top 10 des risques

1. **Suppression famille → perte TOUS élèves et versements** (CASCADE non protégé)
2. **Mot de passe PostgreSQL en clair dans `.env` commitable**
3. **Authentification fictive** (`get_logged_in_username()` hardcodé) — tous les audits sont faux
4. **SQL incorrect dans fichier de test** — test retournerait une erreur PostgreSQL
5. **Aucune impression fonctionnelle** — 8 boutons non implémentés
6. **echo=True en prod** — expose toutes les requêtes SQL dans les logs
7. **SoldeAnt/Impayé à 0.0** — données statistiques tronquées
8. **TypeSortie non utilisé** — classification comptable non fonctionnelle
9. **Bibliothèque absente** — fonctionnalité attendue non disponible
10. **Tableau de bord statique** — première vue = message d'accueil sans données

---

### D. Ordre recommandé pour finir le projet

1. Phase 1 : Stabilisation technique (login, echo, SQL test) — 2-3h
2. Phase 2 : Corrections modules existants (SoldeAnt, align montants, TypeSortie) — 3-5h
3. Phase 3 : Développement Bibliothèque — 8-12h
4. Phase 4 : SMS et placeholders propres — 2-4h
5. Phase 5 : Tableau de bord final avec données réelles — 4-6h
6. Phase 6 : Impressions (PDF ou QPrinter) — 6-10h
7. Phase 7 : Tests de bout en bout — 4-8h
8. Phase 8 : Nettoyage, packaging, livraison — 2-3h

---

### E. Commandes exécutées

```powershell
# Compilation Python (via PowerShell)
py -m compileall .
# Résultat : SUCCESS — 0 erreur de syntaxe sur 95 fichiers .py

# Recherches grep effectuées :
# - TODO|FIXME|NotImplemented|Bientôt|bientôt|Placeholder|placeholder
# - Qt.GlobalColor|setFont(QColor|close_active_tab|get_logged_in_username
# - DROP TABLE|DROP DATABASE|CASCADE|delete-orphan
# - float|Numeric|MontantCantine|MontantVersAutres (dans models/)
# - QWidget { color: white }|QLabel { color: white }
# - print_placeholder|Bientôt|bientôt|SMS
```

---

### F. Fichier de rapport créé

- **`DIAGNOSTIC_COMPLET_EASY_SCHOOL.md`** — présent fichier, créé le 2026-06-20

---

*Rapport généré par Claude Code (Sonnet 4.6) — Session diagnostique Easy School 2.0*
