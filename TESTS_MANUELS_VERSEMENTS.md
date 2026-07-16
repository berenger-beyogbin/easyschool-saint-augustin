# PROCÉDURE DE TESTS MANUELS - MODULE VERSEMENTS (SCOLARITÉ)

Ce document décrit pas à pas la procédure de test technique et fonctionnel pour valider le module **Scolarité > Versements** de l'application **Easy School 2.0**.

---

## 1. VÉRIFICATION DU PARAMÉTRAGE DES TARIFS (ADMINISTRATEUR)

### Étape 1.1 : Tarification Scolarité
1. Allez dans l'onglet **Scolarité > Versements > Scolarité**.
2. Dans le bloc de gauche **APPLICATION COMMUNE À TOUS LES NIVEAUX** :
   - Saisissez `130000` pour Non affecté et `150000` pour Affecté.
   - Cliquez sur **Appliquer à tous les niveaux** et validez le message de succès.
3. Vérifiez dans la grille de droite que tous les niveaux se voient attribuer ces montants (colonnes Non affecté / Affecté).
4. Sélectionnez le niveau **CP1** dans la grille :
   - Dans le bloc **MODIFIER LE NIVEAU SÉLECTIONNÉ**, modifiez le tarif Affecté à `160000`.
   - Cliquez sur **Enregistrer ce niveau**.
   - Vérifiez que la valeur Affecté du CP1 dans le tableau s'est mise à jour à `160 000 F`.

### Étape 1.2 : Tarification Transport
1. Allez dans l'onglet **Scolarité > Versements > Transport**.
2. Dans le bloc commun, saisissez `30000` (coût annuel ou mensuel transport) et cliquez sur **Appliquer à tous les niveaux**.
3. Vérifiez que la grille de droite est actualisée.

### Étape 1.3 : Tarification Cantine
1. Allez dans l'onglet **Scolarité > Versements > Cantine**.
2. Dans le bloc de gauche, saisissez `40000` (tarif cantine commun) et cliquez sur **Appliquer à tous les niveaux**.
3. Vérifiez la propagation correcte.

### Étape 1.4 : Gestion des Autres Frais (Frais Annexes)
1. Allez dans l'onglet **Scolarité > Versements > Autres Frais**.
2. Saisissez dans **1. ENREGISTRER UN TYPE DE FRAIS ANNEXE** :
   - Code Frais : `TENUE`
   - Libellé : `Tenue de sport et uniforme`
   - Cliquez sur **Créer le type de frais**.
3. Procédez de même pour :
   - Code Frais : `ASSUR` | Libellé : `Assurance scolaire`
4. Allez dans le bloc **2. ATTRIBUER UN TARIF PAR NIVEAU** :
   - Sélectionnez `TENUE - Tenue de sport et uniforme` dans la liste déroulante des types.
   - Sélectionnez `CP1` dans la liste déroulante du niveau.
   - Entrez le montant : `15000`.
   - Cliquez sur **Enregistrer ce tarif**.
5. Vérifiez que la grille de droite affiche la nouvelle ligne.

---

## 2. ENREGISTREMENT ET CALCUL DES PAIEMENTS EN CAISSE

### Étape 2.1 : Activation de Fiche et Application des Options d'Inscription
Avant de tester, assurez-vous de sélectionner des élèves inscrits ayant des profils ou des options d'inscriptions variés.

1. Sélectionnez un élève **CP1** qui possède l'option **Cantine** cochée mais **pas de Transport** :
   - Vérifiez sur son profil que le champ de versement **Transport** est grisé ou marqué **[Désactivé]** avec la valeur `0`.
   - Vérifiez que les champs **Scolarité** et **Cantine** sont pleinement éditables.
2. Saisissez son versement :
   - Scolarité : `80000` (sur un total dû de `160000`).
   - Cantine : `40000` (sur un total dû de `40000`).
   - Cliquez sur **Valider et Enregistrer**.
3. **Observation attendue** :
   - Le tableau de bord à droite met à jour instantanément la situation :
     - Scolarité : Dû `160 000 F` | Versé `80 000 F` | Reste `80 000 F`.
     - Cantine : Dû `40 000 F` | Versé `40 000 F` | Reste `0 F`.
     - Transport : Dû `0 F` | Versé `0 F` | Reste `0 F` (Désactivé).
   - L'historique des paiements en bas de l'écran affiche une nouvelle ligne de transaction avec la date du jour et les montants respectifs.

### Étape 2.2 : Application du Plafond de Versement (Règles Métier)
1. Essayez d'enregistrer sur ce même élève un second versement de Scolarité supérieur au reste à payer :
   - Entrez `95000` (alors que le reste est de `80000`).
   - Cliquez sur **Valider et Enregistrer**.
2. **Observation attendue** : Un popup rouge de rejet bloque la transaction en indiquant que le montant versé (`95 000 F`) dépasse le maximum dû (`80 000 F`).

### Étape 2.3 : Forçage via l'option "Restitution" (Trop-perçu)
1. Cochez l'option **Restitution (Plafonds désactivés)**.
2. Saisissez à nouveau `95000` en scolarité.
3. Cliquez sur **Valider et Enregistrer**.
4. **Observation attendue** : Transaction acceptée. Le solde versé comptabilise ce trop-perçu temporaire pour des besoins d'ajustements comptables.

### Étape 2.4 : Annulation d'un Versement
1. Sélectionnez une transaction dans la grille d'historique en bas.
2. Le bouton **Annuler Versement** devient actif. Cliquez dessus.
3. Confirmez le dialogue de validation.
4. **Observation attendue** : Le paiement est supprimé, et la situation financière à droite réinterroge la base de données pour recalculer les soldes d'origine.

---

## 3. REQUÊTES SQL DE VÉRIFICATION DE LA BASE DE DONNÉES

Pour s'assurer que l'écriture en base est propre et respecte les contraintes relationnelles, vous pouvez exécuter ces requêtes directement sur votre outil d'administration PostgreSQL :

### 3.1. Vérification des Types de Frais Annexes créés
```sql
SELECT "IDAutres_Frais", "CodeFrais", "LibelleFrais"
FROM "Autres_Frais"
ORDER BY "CodeFrais" ASC;
```

### 3.2. Vérification des Tarifs affectés aux Niveaux (Autres Frais)
```sql
-- NOTE : MontantAutresFrais utilise "IDT_Niveau" (et non "IDNiveau")
-- car ce modèle suit une convention de nommage différente des autres tables de tarifs.
SELECT m."IDMontantAutres" AS id_tarif, f."CodeFrais", n."Libelle" AS niveau, m."MontantFrais" AS tarif
FROM "MontantAutresFrais" m
JOIN "Autres_Frais" f ON m."IDAutres_Frais" = f."IDAutres_Frais"
JOIN "TNiveau" n ON m."IDT_Niveau" = n."IDT_Niveau"
ORDER BY f."CodeFrais", n."Libelle";
```

### 3.3. Vérification des Paramétrages de Scolarité Standard par Niveau
```sql
SELECT s."IDMontantScol" AS id, n."Libelle" AS niveau, s."MontantNonAffecte" AS non_affecte, s."MontantAffecte" AS affecte
FROM "MontantScol" s
JOIN "TNiveau" n ON s."IDNiveau" = n."IDT_Niveau"
ORDER BY n."Libelle";
```

### 3.4. Vérification des Tarifs Transport et Cantine par Niveau
```sql
-- Transport
SELECT t."IDMontantTrans" AS id, n."Libelle" AS niveau, t."Montant" AS tarif_transport
FROM "MontantTrans" t
JOIN "TNiveau" n ON t."IDNiveau" = n."IDT_Niveau";

-- Cantine
SELECT c."IDMontantCant" AS id, n."Libelle" AS niveau, c."Montant" AS tarif_cantine
FROM "MontantCant" c
JOIN "TNiveau" n ON c."IDNiveau" = n."IDT_Niveau";
```

### 3.5. Audit Complet des Versements Réalisés par Élève (Exemple d'historique comptable)
```sql
SELECT 
    v."IDVersementScol" AS id_recu,
    v."DateVers" AS date_versement,
    e."Matricule",
    e."Nom" || ' ' || e."Prenoms" AS eleve,
    v."MontantVersSco" AS scol_verse,
    v."MontantVersTrans" AS trans_verse,
    v."MontantCantine" AS cantine_verse,
    v."MontantVersAutres" AS autres_verse,
    v."Reduction" AS a_reduction,
    v."Impaye" AS est_impaye,
    v."Restitution" AS est_restitue,
    v."Login" AS caissier
FROM "VersementScol" v
JOIN "Eleve" e ON v."IDEleve" = e."IDEleve"
ORDER BY v."DateVers" DESC, v."IDVersementScol" DESC;
```
