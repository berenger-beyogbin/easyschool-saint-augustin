# TESTS MANUELS — TABLEAU DE BORD
**Fichier :** `TESTS_MANUELS_TABLEAU_DE_BORD.md`  
**Date :** 2026-06-20  
**Module :** Tableau de bord (`views/dashboard_view.py`)  
**Service :** `services/dashboard_service.py`

---

## 1. PRÉREQUIS

- PostgreSQL démarré et accessible
- `.env` correctement configuré (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
- Au moins une année scolaire active en base
- Au moins un établissement configuré

---

## 2. TESTS DE DÉMARRAGE

### 2.1 Lancement de l'application
```
cd easy_school_python
python main.py
```
**Résultat attendu :** L'application démarre sans erreur.

### 2.2 Accès au Tableau de bord
- Cliquer sur **Tableau de bord** dans le menu latéral gauche
- **Résultat attendu :** L'écran Tableau de bord s'affiche avec :
  - Bandeau supérieur (établissement, année scolaire, date, utilisateur)
  - 10 cartes de statistiques sur 2 rangées
  - Zone Alertes
  - 3 tableaux de résumés rapides
  - Boutons d'accès rapide en bas

---

## 3. TESTS DU BANDEAU SUPÉRIEUR

### 3.1 Année scolaire active
- **Vérifier :** Le champ "Année scolaire active" affiche l'année active réelle.
- **Requête de vérification :**
  ```sql
  SELECT "Libelle", "Cloturer"
  FROM "TAnneeScolaire"
  WHERE "Cloturer" = false
  ORDER BY "Libelle" DESC
  LIMIT 1;
  ```

### 3.2 Nom de l'établissement
- **Vérifier :** Le nom de l'établissement s'affiche correctement.
- **Requête de vérification :**
  ```sql
  SELECT "RaisonSociale", "Localite"
  FROM "Etablissement_Ecole"
  LIMIT 1;
  ```

### 3.3 Date du jour
- **Vérifier :** La date affichée correspond à la date du jour (format JJ/MM/AAAA).

### 3.4 Utilisateur connecté
- **Vérifier :** Le champ "Utilisateur" affiche le nom de l'utilisateur actif.

---

## 4. TESTS DES CARTES PRINCIPALES

### 4.1 Élèves inscrits
- **Vérifier :** Le nombre total d'inscrits pour l'année active.
- **Requête SQL :**
  ```sql
  SELECT COUNT(*)
  FROM "TInscription" i
  JOIN "TAnneeScolaire" a ON i."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false;
  ```

### 4.2 Nouveaux élèves
- **Vérifier :** Le nombre d'inscriptions avec `Nouveau = true`.
- **Requête SQL :**
  ```sql
  SELECT COUNT(*)
  FROM "TInscription" i
  JOIN "TAnneeScolaire" a ON i."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false AND i."Nouveau" = true;
  ```

### 4.3 Classes actives
- **Vérifier :** Le nombre de classes de l'année active.
- **Requête SQL :**
  ```sql
  SELECT COUNT(*)
  FROM "TClasse" c
  JOIN "TAnneeScolaire" a ON c."IDAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false;
  ```

### 4.4 Familles
- **Vérifier :** Le nombre total de familles enregistrées.
- **Requête SQL :**
  ```sql
  SELECT COUNT(*) FROM "TFamille";
  ```

### 4.5 Versements Scolarité
- **Vérifier :** La somme des montants versés en scolarité pour l'année active.
- **Requête SQL :**
  ```sql
  SELECT COALESCE(SUM("MontantVersSco"), 0) AS total_scolarite
  FROM "VersementScol" v
  JOIN "TAnneeScolaire" a ON v."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false;
  ```

### 4.6 Versements Cantine
- **Requête SQL :**
  ```sql
  SELECT COALESCE(SUM("MontantCantine"), 0) AS total_cantine
  FROM "VersementScol" v
  JOIN "TAnneeScolaire" a ON v."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false;
  ```

### 4.7 Versements Transport
- **Requête SQL :**
  ```sql
  SELECT COALESCE(SUM("MontantVersTrans"), 0) AS total_transport
  FROM "VersementScol" v
  JOIN "TAnneeScolaire" a ON v."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false;
  ```

### 4.8 Ventes Kiosque
- **Requête SQL :**
  ```sql
  SELECT COALESCE(SUM("QuantiteSort" * "Prix_vente"), 0) AS total_ventes
  FROM "StockSortie" s
  JOIN "TAnneeScolaire" a ON s."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false;
  ```

### 4.9 Dépenses Comptabilité
- **Requête SQL :**
  ```sql
  SELECT COALESCE(SUM("Montant"), 0) AS total_depenses
  FROM "SortieFin" sf
  JOIN "TAnneeScolaire" a ON sf."IDAnSco" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false AND sf."DebitCredit" = 'Debit';
  ```

### 4.10 Recettes Comptabilité
- **Requête SQL :**
  ```sql
  SELECT COALESCE(SUM("Montant"), 0) AS total_recettes
  FROM "SortieFin" sf
  JOIN "TAnneeScolaire" a ON sf."IDAnSco" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false AND sf."DebitCredit" = 'Credit';
  ```

---

## 5. TESTS DES TABLEAUX RAPIDES

### 5.1 Dernières inscriptions
- **Vérifier :** Le tableau affiche les 5 dernières inscriptions.
- **Colonnes attendues :** Date, Matricule, Élève, Classe
- **Requête SQL :**
  ```sql
  SELECT
      i."DateInscription",
      e."Matricule",
      e."Nom" || ' ' || e."Prenoms" AS eleve,
      c."LibClasse"
  FROM "TInscription" i
  JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
  JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
  JOIN "TAnneeScolaire" a ON i."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false
  ORDER BY i."DateInscription" DESC, i."IDTInscription" DESC
  LIMIT 5;
  ```

### 5.2 Derniers versements
- **Vérifier :** Le tableau affiche les 5 derniers versements.
- **Colonnes attendues :** Date, Élève, Scolarité, Cantine, Transport
- **Requête SQL :**
  ```sql
  SELECT
      v."DateVers",
      e."Nom" || ' ' || e."Prenoms" AS eleve,
      v."MontantVersSco",
      v."MontantCantine",
      v."MontantVersTrans"
  FROM "VersementScol" v
  JOIN "Eleve" e ON v."IDEleve" = e."IDEleve"
  JOIN "TAnneeScolaire" a ON v."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false
  ORDER BY v."DateVers" DESC, v."IDVersementScol" DESC
  LIMIT 5;
  ```

### 5.3 Dernières ventes kiosque
- **Vérifier :** Le tableau affiche les 5 dernières ventes.
- **Colonnes attendues :** Date, Article, Qté, Montant
- **Requête SQL :**
  ```sql
  SELECT
      s."DateSort",
      a."Libelle",
      s."QuantiteSort",
      s."QuantiteSort" * s."Prix_vente" AS montant
  FROM "StockSortie" s
  JOIN "TArticle" a ON s."IDTArticle" = a."IDTArticle"
  JOIN "TAnneeScolaire" an ON s."IDTAnneeScolaire" = an."IDTAnneeScolaire"
  WHERE an."Cloturer" = false
  ORDER BY s."DateSort" DESC, s."HeureSortie" DESC
  LIMIT 5;
  ```

---

## 6. TESTS DE LA ZONE ALERTES

### 6.1 Alertes stock faible
- **Vérifier :** Si des articles ont un stock <= seuil, ils apparaissent dans les alertes.
- **Requête SQL :**
  ```sql
  SELECT
      a."Libelle",
      a."QTESeuil",
      s."QuantiteCour"
  FROM "TArticle" a
  LEFT JOIN "StockCour" s ON a."IDTArticle" = s."IDTArticle"
  WHERE s."QuantiteCour" <= a."QTESeuil";
  ```

### 6.2 Alertes capacité classe
- **Vérifier :** Les classes à 90%+ de capacité apparaissent dans les alertes.
- **Requête SQL :**
  ```sql
  SELECT
      c."LibClasse",
      c."Capacite",
      COUNT(i."IDTInscription") AS effectif,
      ROUND(COUNT(i."IDTInscription")::numeric / NULLIF(c."Capacite", 0) * 100, 0) AS pct
  FROM "TClasse" c
  LEFT JOIN "TInscription" i ON c."IDTClasse" = i."IDClasse"
  JOIN "TAnneeScolaire" a ON c."IDAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false
  GROUP BY c."LibClasse", c."Capacite"
  HAVING COUNT(i."IDTInscription") >= (c."Capacite" * 0.9)
  ORDER BY pct DESC;
  ```

### 6.3 Alertes impayés scolarité
- **Vérifier :** Les élèves avec un reste à payer en scolarité apparaissent.
- **Requête SQL :**
  ```sql
  SELECT
      e."Nom" || ' ' || e."Prenoms" AS eleve,
      c."LibClasse",
      CASE WHEN i."StatutAffectation" = 'NON_AFFECTE_ETAT' THEN m."MontantNonAffecte" ELSE m."MontantAffecte" END AS montant_du,
      COALESCE(SUM(v."MontantVersSco"), 0) AS total_verse,
      CASE WHEN i."StatutAffectation" = 'NON_AFFECTE_ETAT' THEN m."MontantNonAffecte" ELSE m."MontantAffecte" END - COALESCE(SUM(v."MontantVersSco"), 0) AS reste
  FROM "TInscription" i
  JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
  JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
  JOIN "MontantScol" m ON m."IDNiveau" = i."IDNiveau"
      AND m."IDTAnneeScolaire" = i."IDTAnneeScolaire"
  LEFT JOIN "VersementScol" v ON v."IDEleve" = i."IDEleve"
      AND v."IDTAnneeScolaire" = i."IDTAnneeScolaire"
  JOIN "TAnneeScolaire" a ON i."IDTAnneeScolaire" = a."IDTAnneeScolaire"
  WHERE a."Cloturer" = false AND i."Scolarite" = true
  GROUP BY e."Nom", e."Prenoms", c."LibClasse", i."StatutAffectation", m."MontantNonAffecte", m."MontantAffecte"
  HAVING CASE WHEN i."StatutAffectation" = 'NON_AFFECTE_ETAT' THEN m."MontantNonAffecte" ELSE m."MontantAffecte" END - COALESCE(SUM(v."MontantVersSco"), 0) > 0
  ORDER BY reste DESC
  LIMIT 10;
  ```

### 6.4 Aucune alerte
- **Si toutes les conditions sont bonnes :**
- **Résultat attendu :** Message "Aucune alerte — Tout est en ordre." en vert.

---

## 7. TEST DU BOUTON ACTUALISER

- Cliquer sur le bouton **Actualiser** dans le bandeau supérieur.
- **Résultat attendu :** Toutes les cartes, alertes et tableaux se rechargent depuis la base.

---

## 8. TESTS DES BOUTONS D'ACCÈS RAPIDE

| Bouton        | Action attendue                                    |
|---------------|---------------------------------------------------|
| Paramètres    | Navigue vers le module Paramètres (menu index 6)  |
| Scolarité     | Navigue vers le module Scolarité (menu index 1)   |
| Versements    | Navigue vers le module Scolarité (menu index 1)   |
| Kiosque       | Navigue vers le module Kiosque (menu index 2)     |
| Comptabilité  | Navigue vers Comptabilité (menu index 3)          |
| Statistiques  | Navigue vers Statistiques (menu index 4)          |

---

## 9. TESTS AVEC BASE DE DONNÉES VIDE OU PRESQUE VIDE

### 9.1 Aucun versement
- **Résultat attendu :** Cartes Scolarité, Cantine, Transport affichent "0 F"

### 9.2 Aucune vente kiosque
- **Résultat attendu :** Carte Ventes Kiosque affiche "0 F"

### 9.3 Aucun mouvement comptable
- **Résultat attendu :** Cartes Dépenses et Recettes affichent "0 F"

### 9.4 Aucun élève inscrit
- **Résultat attendu :** Carte Élèves inscrits affiche "0"
- Tableaux affichent "Aucune donnée disponible"

### 9.5 Aucune alerte
- **Résultat attendu :** Zone Alertes affiche "Aucune alerte — Tout est en ordre."

### 9.6 Stabilité
- L'application NE doit PAS planter, même si toutes les tables sont vides.

---

## 10. TESTS DE RÉGRESSION

### 10.1 Modules existants non impactés
Vérifier que les modules suivants fonctionnent normalement après l'intégration du tableau de bord :
- [ ] Paramètres → Établissement
- [ ] Paramètres → Année Scolaire
- [ ] Paramètres → Cycles, Niveaux, Classes
- [ ] Scolarité → Inscriptions
- [ ] Scolarité → Versements (Caisse)
- [ ] Kiosque → Articles, Ventes, Approvisionnement
- [ ] Comptabilité → Enregistrement, Balance
- [ ] Statistiques → Inscrits, Scolarité, Ventes, Stock

### 10.2 Navigation menu ↔ modules
- [ ] Cliquer sur Tableau de bord → tableau de bord s'affiche
- [ ] Cliquer sur Scolarité → module Scolarité s'affiche
- [ ] Cliquer sur Paramètres → module Paramètres s'affiche
- [ ] Revenir au Tableau de bord → données actualisées

---

## 11. VÉRIFICATIONS TECHNIQUES FINALES

```powershell
cd easy_school_python

# Compilation
python -m compileall .

# Imports
python -c "from services.dashboard_service import DashboardService; print('DashboardService OK')"
python -c "from views.dashboard_view import DashboardView; print('DashboardView OK')"
python -c "from views.main_window import MainWindow; print('MainWindow OK')"
```

**Résultats attendus :**
- `compileall` : 0 erreur de syntaxe
- Import DashboardService : OK
- Import DashboardView : OK
- Import MainWindow : OK

---

## 12. CHECKS INTERDITS

```powershell
# Aucune occurrence de ces patterns ne doit exister dans les nouveaux fichiers :
Select-String -Path "views\dashboard_view.py" -Pattern "Qt\.GlobalColor\.fromRgb"
Select-String -Path "views\dashboard_view.py" -Pattern "setFont\(QColor"
Select-String -Path "views\dashboard_view.py" -Pattern "color:\s*white" | Where-Object { $_ -notmatch "sidebar" }
Select-String -Path "services\dashboard_service.py" -Pattern "DROP TABLE|DROP DATABASE|DELETE FROM"
```

**Résultats attendus :** Aucune occurrence pour tous ces patterns.
