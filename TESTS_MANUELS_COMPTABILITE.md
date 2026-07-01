# TESTS MANUELS - MODULE COMPTABILITÉ FINANCIÈRE
## Projet: Easy School 2.0 (Migration Python / PySide6 / PostgreSQL)

Ce document décrit la procédure pas-à-pas pour tester manuellement le nouveau module de Comptabilité, vérifier les états financiers et auditer la base de données.

---

## 1. PROCÉDURE DE TEST ÉTAPE PAR ÉTAPE

### Étape 1 : Accès au module Comptabilité
1. Lancez l'application avec la commande :
   ```bash
   cd easy_school_python
   python main.py
   ```
2. Dans le menu de navigation à gauche, cliquez sur le bouton **Comptabilité**.
3. Vérifiez que l'écran s'ouvre correctement avec le bandeau bleu ciel contenant le titre **COMPTABILITÉ FINANCIÈRE**.
4. Vérifiez la présence des 4 sous-onglets horizontaux :
   - `1. Enregistrements`
   - `2. État des Sorties`
   - `3. Créer un compte`
   - `4. Balance des Comptes`

### Étape 2 : Création des Comptes Comptables (Onglet 3)
1. Allez sur l'onglet **3. Créer un compte**.
2. Remplissez le formulaire de saisie pour créer deux comptes de test :
   - **Compte 1** :
     - N° Compte : `501`
     - Libellé : `Caisse Principale`
     - Cliquez sur **Valider**. Un message de succès apparaît.
   - **Compte 2** :
     - N° Compte : `601`
     - Libellé : `Fournitures Scolaires`
     - Cliquez sur **Valider**.
3. Vérifiez que les deux comptes apparaissent instantanément dans la table du bas.
4. Saisissez `501` dans la barre de recherche et vérifiez que le tableau filtre correctement.
5. Effacez la recherche pour retrouver tous les comptes.

### Étape 3 : Enregistrement de Mouvements Financiers (Onglet 1)
1. Allez sur l'onglet **1. Enregistrements**.
2. Enregistrez un mouvement de type **Crédit** (Entrée d'argent) pour alimenter la caisse :
   - Date : Date du jour
   - Bénéficiaire : `ADMINISTRATION`
   - Tél. : `0102030405`
   - Compte : Sélectionner `501 - Caisse Principale`
   - Mouvement : `Crédit (Entrée d'argent)`
   - Montant : `100 000` (Saisir `100000`)
   - Détail : `Apport initial caisse`
   - Cliquez sur **Valider**.
3. Enregistrez un mouvement de type **Débit** (Sortie d'argent / dépense) :
   - Date : Date du jour
   - Bénéficiaire : `LIBRAIRIE NATIONALE`
   - Tél. : `0708091011`
   - Compte : Sélectionner `601 - Fournitures Scolaires`
   - Mouvement : `Débit (Sortie d'argent)`
   - Montant : `25 000` (Saisir `25000`)
   - Détail : `Achat de registres et cahiers de texte`
   - Cliquez sur **Valider**.
4. Vérifiez que la grille historique affiche les deux mouvements avec leurs codes séquentiels générés de façon unique (Ex: `SF-2026-0001` et `SF-2026-0002`).
5. Vérifiez que la colonne **Sens** affiche `CRÉDIT` en vert et `DÉBIT` en rouge.

### Étape 4 : Consultation de l'État des Sorties (Onglet 2)
1. Allez sur l'onglet **2. État des Sorties**.
2. Laissez les filtres par défaut (Tous les comptes, période de 30 jours) et cliquez sur **Afficher**.
3. Vérifiez qu'uniquement la dépense de `25 000 FCFA` (DÉBIT) faite à `LIBRAIRIE NATIONALE` s'affiche. L'apport initial de `100 000 FCFA` (CRÉDIT) ne doit **pas** apparaître.
4. Vérifiez au bas de la fenêtre que le label affiche : `Total Général des Sorties : 25 000 FCFA`.
5. Sélectionnez le filtre de compte `501 - Caisse Principale` et cliquez sur **Afficher**. La table doit devenir vide (car aucun débit n'a été fait sur ce compte).

### Étape 5 : Consultation de la Balance des Comptes (Onglet 4)
1. Allez sur l'onglet **4. Balance des Comptes**.
2. Réglez la période si nécessaire et cliquez sur **Afficher**.
3. Vérifiez la présence de vos comptes avec leurs débits/crédits et soldes cumulés :
   - Le compte `501 - Caisse Principale` doit afficher :
     - Débit : `0 FCFA`
     - Crédit : `100 000 FCFA`
     - Solde (Crédit - Débit) : `100 000 FCFA` (en vert)
   - Le compte `601 - Fournitures Scolaires` doit afficher :
     - Débit : `25 000 FCFA`
     - Crédit : `0 FCFA`
     - Solde (Crédit - Débit) : `-25 000 FCFA` (en rouge)
4. Vérifiez les totaux cumulatifs en bas :
   - `Total Débit : 25 000 FCFA`
   - `Total Crédit : 100 000 FCFA`
5. Cliquez sur le bouton **Imprimer** et vérifiez qu'une boîte de dialogue apparaît disant `"Impression à venir"`.

---

## 2. REQUÊTES SQL DE CONTRÔLE DE LA BASE DE DONNÉES

Pour valider l'intégrité de la base de données directement dans PostgreSQL, vous pouvez exécuter ces requêtes :

### Requête 1 : Vérification de la création des Comptes
```sql
SELECT "IDCompte", "NumCompte", "LibCompte"
FROM "Compte"
ORDER BY "NumCompte";
```

### Requête 2 : Audit de l'historique des mouvements financiers enregistrés
```sql
SELECT "IDSortieFin", "CodeSortie", "DateSortie", "DebitCredit", "Montant", "Benef", "IDCompte"
FROM "SortieFin"
ORDER BY "DateSortie" DESC, "IDSortieFin" DESC;
```

### Requête 3 : Balance générale brute par compte
```sql
SELECT 
    c."NumCompte",
    c."LibCompte",
    COALESCE(SUM(CASE WHEN s."DebitCredit" = 'Debit' THEN s."Montant" ELSE 0 END), 0) AS debit,
    COALESCE(SUM(CASE WHEN s."DebitCredit" = 'Credit' THEN s."Montant" ELSE 0 END), 0) AS credit,
    COALESCE(SUM(CASE WHEN s."DebitCredit" = 'Credit' THEN s."Montant" ELSE 0 END), 0)
    -
    COALESCE(SUM(CASE WHEN s."DebitCredit" = 'Debit' THEN s."Montant" ELSE 0 END), 0) AS solde
FROM "Compte" c
LEFT JOIN "SortieFin" s ON c."IDCompte" = s."IDCompte"
GROUP BY c."NumCompte", c."LibCompte"
ORDER BY c."NumCompte";
```

---

## 3. RÉSULTATS ATTENDUS ET VALIDATIONS CLÉS

- **Unicité des codes de sortie** : Chaque code `CodeSortie` doit être incrémental et respecter le schéma `SF-AAAA-XXXX` selon l'année scolaire en cours.
- **Validations de sécurité** :
  - Tout montant négatif ou égal à zéro doit être refusé avec un message d'erreur clair.
  - La modification ou suppression d'un mouvement sur une année clôturée est strictement bloquée par l'application.
- **Stabilité de l'Espace Central** : Tous les labels, boutons, tables et entrées du formulaire utilisent de grands contrastes (police sombre sur fond clair) afin de garantir la lisibilité optimale.
