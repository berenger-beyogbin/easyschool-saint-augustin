# TESTS MANUELS DES ETATS DU MODULE STATISTIQUES

Ce document décrit la procédure de test manuel, les requêtes SQL de vérification et les résultats attendus pour le module **Statistiques** d'Easy School 2.0.

---

## 📅 PROCÉDURE DE TEST MANUEL DU MODULE

1. **Lancement de l'application** :
   ```bash
   cd easy_school_python
   python main.py
   ```
2. **Accès au module** :
   * Dans le menu latéral gauche, cliquer sur le bouton **Statistiques**.
   * Confirmer l'ouverture de l'écran avec le bandeau bleu clair caractéristique contenant l'état sélectionné.
3. **Vérification de l'état "Inscrits"** :
   * Cliquer sur le sous-onglet **Inscrits**.
   * Vérifier que la liste affiche les élèves inscrits dans l'année active courante.
   * Sélectionner un **Niveau** dans le sélecteur d'en-tête, puis vérifier que le sélecteur de **Classe** se met à jour pour n'afficher que les classes de ce niveau.
   * Cliquer sur **Afficher** et confirmer le filtre correct.
   * Cliquer sur **Imprimer** et vérifier l'affichage de la boîte d'information indiquant *"Impression à venir"*.
4. **Vérification de l'état "Nouveaux"** :
   * Cliquer sur le sous-onglet **Nouveaux**.
   * Confirmer l'affichage exclusif des élèves identifiés comme **Nouveaux (Nouveau = True)** dans la base de données.
   * Tester le filtre par **Utilisateur** (login ayant saisi l'inscription), **Niveau** et **Classe**.
5. **Vérification de l'état "Scolarité" (Financier)** :
   * Cliquer sur le sous-onglet **Scolarité**.
   * Observer le tableau financier avec lignes alternées **jaune clair et blanc** et texte noir parfaitement lisible.
   * Cliquer sur **Afficher** : vérifier les montants dus, versés, réductions appliquées et restes à payer.
   * Confirmer la mise à jour des totaux de pied de page : **Total dû, Solde Ant., Total versé, Réd., Reste**.
6. **Vérification de l'état "Cantine" (Financier)** :
   * Cliquer sur le sous-onglet **Cantine**.
   * Confirmer que seuls les élèves inscrits avec l'option **Cantine = True** sont répertoriés.
   * Confirmer la cohérence des montants dus provenant du tarif Cantine paramétré pour le niveau de l'élève.
   * Valider la sommation des totaux en bas de page.
7. **Vérification de l'état "Transport" (Financier)** :
   * Cliquer sur l'onglet **Transport**.
   * Confirmer l'inclusion exclusive des élèves abonnés au transport (**Transport = True**).
   * Confirmer l'exactitude des calculs (Montant dû, Montant versé, Reste).
8. **Vérification des ventes Kiosque "Vente" (Financier)** :
   * Ouvrir l'onglet **Vente**.
   * Sélectionner une plage de dates via les deux calendriers (**Date du** / **Date au**).
   * Cliquer sur **Afficher** et vérifier l'affichage du journal des ventes avec le total général calculé en bas.
9. **Vérification de l'inventaire "Stock" (Kiosque)** :
   * Sélectionner l'onglet **Stock**.
   * Tapez un libellé d'article dans le champ de recherche dynamique pour vérifier le filtre interactif.
   * Valider l'affichage de la colonne **État** colorée selon le stock courant par rapport au seuil définis (Vert : **OK**, Orange : **Alerte**, Rouge en Gras : **Rupture**).
   * Confirmer la sommation de la valorisation du stock en pied de page (Stock courant * Prix de Vente).

---

## 🗄️ REQUÊTES SQL DE VÉRIFICATION POSTGRESQL

Vous pouvez exécuter ces requêtes directement dans votre gestionnaire de base de données PostgreSQL pour croiser les calculs affichés dans les tableaux :

### 1. Liste complète des inscrits de l'année scolaire active

```sql
SELECT 
    i."DateInscription",
    e."Matricule",
    e."Nom",
    e."Prenoms",
    e."DateNaissance",
    c."LibClasse",
    n."Libelle" AS niveau
FROM "TInscription" i
LEFT JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
LEFT JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
LEFT JOIN "TNiveau" n ON i."IDNiveau" = n."IDT_Niveau"
WHERE i."IDTAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = false ORDER BY "Libelle" DESC LIMIT 1)
ORDER BY c."LibClasse", e."Nom";
```

### 2. Liste des nouveaux élèves de l'année scolaire active

```sql
SELECT 
    i."DateInscription",
    e."Matricule",
    e."Nom",
    e."Prenoms",
    c."LibClasse",
    i."Nouveau"
FROM "TInscription" i
LEFT JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
LEFT JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
WHERE i."Nouveau" = true
  AND i."IDTAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = false ORDER BY "Libelle" DESC LIMIT 1)
ORDER BY i."DateInscription" DESC;
```

### 3. État des versements de scolarité par élève

```sql
SELECT 
    e."Matricule",
    e."Nom",
    e."Prenoms",
    c."LibClasse",
    COALESCE(SUM(v."MontantVersSco"), 0) AS total_scolarite
FROM "TInscription" i
LEFT JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
LEFT JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
LEFT JOIN "VersementScol" v ON v."IDEleve" = e."IDEleve" AND v."IDTAnneeScolaire" = i."IDTAnneeScolaire"
WHERE i."IDTAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = false ORDER BY "Libelle" DESC LIMIT 1)
GROUP BY e."Matricule", e."Nom", e."Prenoms", c."LibClasse"
ORDER BY c."LibClasse", e."Nom";
```

### 4. État des versements de cantine

```sql
SELECT 
    e."Matricule",
    e."Nom",
    e."Prenoms",
    c."LibClasse",
    COALESCE(SUM(v."MontantCantine"), 0) AS total_cantine
FROM "TInscription" i
LEFT JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
LEFT JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
LEFT JOIN "VersementScol" v ON v."IDEleve" = e."IDEleve" AND v."IDTAnneeScolaire" = i."IDTAnneeScolaire"
WHERE i."Cantine" = true
  AND i."IDTAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = false ORDER BY "Libelle" DESC LIMIT 1)
GROUP BY e."Matricule", e."Nom", e."Prenoms", c."LibClasse"
ORDER BY c."LibClasse", e."Nom";
```

### 5. État des versements de transport

```sql
SELECT 
    e."Matricule",
    e."Nom",
    e."Prenoms",
    c."LibClasse",
    COALESCE(SUM(v."MontantVersTrans"), 0) AS total_transport
FROM "TInscription" i
LEFT JOIN "Eleve" e ON i."IDEleve" = e."IDEleve"
LEFT JOIN "TClasse" c ON i."IDClasse" = c."IDTClasse"
LEFT JOIN "VersementScol" v ON v."IDEleve" = e."IDEleve" AND v."IDTAnneeScolaire" = i."IDTAnneeScolaire"
WHERE i."Transport" = true
  AND i."IDTAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = false ORDER BY "Libelle" DESC LIMIT 1)
GROUP BY e."Matricule", e."Nom", e."Prenoms", c."LibClasse"
ORDER BY c."LibClasse", e."Nom";
```

### 6. État des ventes de Kiosque

```sql
SELECT 
    s."DateSort",
    s."HeureSortie",
    a."Libelle",
    s."QuantiteSort",
    s."Prix_vente",
    s."QuantiteSort" * s."Prix_vente" AS total
FROM "StockSortie" s
LEFT JOIN "TArticle" a ON s."IDTArticle" = a."IDTArticle"
WHERE s."IDTAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = false ORDER BY "Libelle" DESC LIMIT 1)
ORDER BY s."DateSort" DESC, s."HeureSortie" DESC;
```

### 7. État des stocks d'articles et kits du Kiosque

```sql
SELECT 
    a."Libelle",
    a."PU",
    a."QTESeuil",
    a."KIT",
    s."QuantiteCour",
    s."QuantiteCour" * a."PU" AS valeur_stock
FROM "TArticle" a
LEFT JOIN "StockCour" s ON a."IDTArticle" = s."IDTArticle"
ORDER BY a."Libelle";
```
