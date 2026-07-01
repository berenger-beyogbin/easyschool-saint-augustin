# TESTS MANUELS - MODULE KIOSQUE (Easy School 2.0)

Ce guide décrit la procédure de test manuel pas-à-pas pour valider le bon fonctionnement du module Kiosque, ainsi que les requêtes d'audit SQL correspondantes.

## 1. Procédure de test manuel dans l'interface

1. **Lancer l'application**
   ```bash
   cd easy_school_python
   python main.py
   ```
2. **Aller dans Kiosque** (dans le menu latéral gauche).
3. **Aller dans Article** (sous-onglet *3. Articles & KITS*).
4. **Créer un article** en cliquant sur *Nouvel Article* :
   - **Libellé** : `Cahier 100 pages`
   - **PU** (Prix unitaire) : `500`
   - **Seuil** (Seuil minimum) : `5`
5. **Vérifier que l'article apparaît sans crash** dans la liste globale.
6. **Vérifier que le stock courant est 0** pour cet article.
7. **Aller dans Approvisionnement** (sous-onglet *2. Approvisionnement*).
8. **Sélectionner l'article** `Cahier 100 pages` dans la liste déroulante.
9. **Entrer Quantité** : `20`.
10. **Choisir une date d'approvisionnement** spécifique (via le calendrier proposé).
11. **Valider** l'approvisionnement.
12. **Vérifier que le stock courant devient 20** (dans le sous-onglet *3. Articles & KITS*).
13. **Vérifier que la date enregistrée correspond à la date choisie** dans le tableau d'historique des entrées à droite.
14. **Aller dans Vente** (sous-onglet *1. Vendre*).
15. **Sélectionner l'article** `Cahier 100 pages` à gauche.
16. **Prix de vente** : `500`.
17. **Quantité** : `2`.
18. **Valider la vente** en ajoutant au panier puis en pressant *Valider la Vente*.
19. **Vérifier que le stock courant devient 18** (20 initial - 2 vendus).
20. **Essayer de vendre 100 unités** (saisir 100 unités et tenter de l'ajouter au panier).
21. **Vérifier que l'application refuse la vente** avec un message d'alerte explicite signalant le stock insuffisant.
22. **Créer un kit simple** (*Nouveau KIT*) en nommant le kit et en y incorporant un ou plusieurs articles (comme le `Cahier 100 pages`).
23. **Tenter de supprimer un article utilisé dans ce kit** (sélectionner `Cahier 100 pages` et cliquer sur *Supprimer la sélection*).
24. **Vérifier que la suppression est refusée** avec le message d'interdiction attendu : *"Impossible de supprimer cet article car il est utilisé dans la composition d’un kit."*

---

## 2. Requêtes d'audit SQL de contrôle PostgreSQL

### 2.1. Requêtes de contrôle de table directes
```sql
SELECT * FROM "TArticle";
SELECT * FROM "StockCour";
SELECT * FROM "StockEnt";
SELECT * FROM "StockSortie";
```

### 2.2. Requête stock
Cette requête permet d'auditer l'état de l'inventaire en direct dans la base.
```sql
SELECT 
    a."IDTArticle",
    a."Libelle",
    a."PU",
    a."QTESeuil",
    a."KIT",
    s."QuantiteCour"
FROM "TArticle" a
LEFT JOIN "StockCour" s ON a."IDTArticle" = s."IDTArticle"
ORDER BY a."Libelle";
```

### 2.3. Requête approvisionnements
Affiche l'historique complet des entrées de stock enregistrées au kiosque.
```sql
SELECT 
    e."DateEnt",
    a."Libelle",
    e."QuantiteEnt",
    e."Login"
FROM "StockEnt" e
LEFT JOIN "TArticle" a ON e."IDTArticle" = a."IDTArticle"
ORDER BY e."DateEnt" DESC, e."IDStockEnt" DESC;
```

### 2.4. Requête ventes
Affiche l'historique de l'ensemble des ventes réalisées au kiosque.
```sql
SELECT 
    so."DateSort",
    so."HeureSortie",
    a."Libelle",
    so."QuantiteSort",
    so."Prix_vente",
    so."Login"
FROM "StockSortie" so
LEFT JOIN "TArticle" a ON so."IDTArticle" = a."IDTArticle"
ORDER BY so."DateSort" DESC, so."HeureSortie" DESC;
```
