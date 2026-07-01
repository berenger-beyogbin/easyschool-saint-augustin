# Protocole des Tests Manuels - Module Scolarité / Inscriptions - Easy School 2.0

Ce document répertorie les scénarios de validation manuelle du module **Scolarité > Inscriptions** de l'application Easy School 2.0, ainsi que les requêtes d'analyse PostgreSQL correspondantes afin de certifier la robustesse fonctionnelle de l'application.

---

## 1. Cas de Test Fonctionnels

### Cas de Test 1 : Formulaire d'Enregistrement de Parents / Famille
* **Objectif** : Valider la création, la recopie automatique et la modification des fiches familles.
* **Procédure** :
  1. Naviguer vers **Scolarité**, sous-onglet **Liste des Parents**, puis cliquer sur **Nouveau**.
  2. Saisir les informations du Père : *Nom & Prénoms : COULIBALY GÉRALD*, *Téléphone : 0707070707*.
  3. Sélectionner la qualité du responsable légal : **Père**.
  4. **Attendu** : Les champs de la section *Responsable Légal* (Nom, Portable, Profession) sont recopiés automatiquement depuis les données du père.
  5. Saisir l'habitation du parent : *ABOBO SOGEFIHA*.
  6. Décocher ou cocher "Le Responsable lui-même" dans la section urgence.
  7. **Attendu** : Si coché, les valeurs d'urgence se verrouillent et copient l'identité du responsable. Sinon, elles redeviennent éditables individuellement.
  8. Cliquer sur **Valider**.
  9. **Vérification** : Une ligne apparaît dans le tableau avec "COULIBALY GÉRALD".

### Cas de Test 2 : Formulaire de Création d'Élève
* **Objectif** : Valider la génération du matricule séquentiel unique, le calcul d'âge en temps réel et la photo d'un élève.
* **Procédure** :
  1. Aller dans l'onglet **Scolarité** > sous-onglet **Élèves** et cliquer sur **Nouveau**.
  2. **Attendu** : Le champ *Matricule* propose un matricule automatique cohérent structuré comme `26-001` (où 26 représente l'année active 2026).
  3. Saisir *Nom : COULIBALY*, *Prénoms : KADER*.
  4. Définir une date de naissance il y a exactement 8 ans de cela.
  5. **Attendu** : Le champ d'âge calculé affiche instantanément **8 ans**.
  6. Associer la Famille Responsable créée précédemment (*COULIBALY GÉRALD*).
  7. Cliquer sur **Parcourir** et choisir une image sur le disque.
  8. **Attendu** : L'aperçu de la photo de l'élève s'affiche de manière harmonieuse dans le cadre d'aperçu.
  9. Cliquer sur **Valider**.

### Cas de Test 3 : Saisie d'une Inscription d'Élève (Cascades et Options)
* **Objectif** : Effectuer l'inscription d'un élève à une classe de destination sous la session en cours.
* **Procédure** :
  1. Aller dans l'onglet **Scolarité** > sous-onglet **Inscription**.
  2. Saisir "Coulibaly" dans le champ de recherche de gauche.
  3. Sélectionner le parent *COULIBALY GÉRALD* dans le tableau des familles.
  4. **Attendu** : Le tableau inférieur des élèves filtre instantanément pour n'afficher que l'élève non-inscrit *COULIBALY KADER*.
  5. Sélectionner l'élève *COULIBALY KADER*.
  6. Dans le volet d'affectation de droite, sélectionner un niveau scolaire (ex: **CP1**).
  7. **Attendu** : Le selecteur *Classe de destination* se peuple automatiquement des classes du niveau CP1 (ex: *CP1-A*, *CP1-B*).
  8. Choisir la classe *CP1-A*.
  9. **Attendu** : L'indicateur d'effectif affiche la situation actuelle par exemple `Effectif actuel : 0 / 45`.
  10. Choisir les options (cocher Scolarité, Nouveau).
  11. Cliquer sur **Inscrire l'Élève**.
  12. **Attendu** : Message de succès "Élève inscrit avec succès". L'élève quitte automatiquement le tableau des élèves non inscrits de gauche pour le parent courant. L'effectif de la classe CP1-A passe à `1 / 45` en bleu.

### Cas de Test 4 : Contrôle de Capacité de Classe
* **Objectif** : Certifier que l'application refuse d'exécuter une inscription si la classe cible est à saturation.
* **Procédure de simulation** :
  1. Choisir une classe dont l'effectif actuel atteint sa capacité `Capacite` de paramétrage (ex: effectif = 45, capacité = 45).
  2. Tenter d'inscrire un élève additionnel.
  3. **Attendu** : L'application bloque l'accès et affiche une boîte d'alerte critique claire : `"Impossible d'inscrire l'élève : La classe choisie a atteint sa capacité maximale (.../45)."`

### Cas de Test 5 : Sécurité et Interdictions de Suppression
* **Objectif** : Valider que les règles de gestion d'intégrité référentielle sont respectées :
  - Suppression d'un élève inscrit bloquée.
  - Suppression d'une famille liée à un ou plusieurs élèves bloquée.
* **Procédure** :
  1. Tenter de supprimer l'élève *COULIBALY KADER* depuis le sous-onglet **Élèves**.
  2. **Attendu** : Bloqué avec le message : `"Impossible de supprimer cet élève car il possède déjà une inscription active."`
  3. Tenter de supprimer le parent *COULIBALY GÉRALD* depuis le sous-onglet **Liste des Parents**.
  4. **Attendu** : Bloqué avec le message : `"Impossible de supprimer cette famille : Un ou plusieurs élèves y sont rattachés."`

---

## 2. Requêtes d'Analyse SQL (PostgreSQL)

Ces scripts peuvent être exécutés directement dans la base de données PostgreSQL pour vérifier l'exactitude des écritures :

### Requête 1 : Liste détaillée des inscriptions de l'année scolaire active
```sql
SELECT 
    ins."IDTInscription" AS id_inscription,
    el."Matricule" AS matricule,
    el."Nom" AS nom_eleve,
    el."Prenoms" AS prenom_eleve,
    fam."NomResponsable" AS parent,
    niv."Libelle" AS niveau,
    cla."LibClasse" AS classe,
    ann."Libelle" AS annee_scolaire,
    ins."Scolarite" AS scolarite,
    ins."Cantine" AS cantine,
    ins."Transport" AS transport
FROM "TInscription" ins
JOIN "Eleve" el ON ins."IDEleve" = el."IDEleve"
JOIN "TFamille" fam ON ins."IDFamille" = fam."IdTFamille"
JOIN "TNiveau" niv ON ins."IDNiveau" = niv."IDT_Niveau"
JOIN "TClasse" cla ON ins."IDClasse" = cla."IDTClasse"
JOIN "TAnneeScolaire" ann ON ins."IDTAnneeScolaire" = ann."IDTAnneeScolaire"
WHERE ann."Cloturer" = FALSE;
```

### Requête 2 : Recensement des effectifs par classe de l'année scolaire en cours
```sql
SELECT 
    cla."IDTClasse" AS id_classe,
    cla."LibClasse" AS nom_classe,
    cla."Capacite" AS capacite_max,
    COUNT(ins."IDTInscription") AS effectif_reel,
    cla."Capacite" - COUNT(ins."IDTInscription") AS places_disponibles
FROM "TClasse" cla
LEFT JOIN "TInscription" ins ON cla."IDTClasse" = ins."IDClasse"
LEFT JOIN "TAnneeScolaire" ann ON ins."IDTAnneeScolaire" = ann."IDTAnneeScolaire"
WHERE cla."IDAnneeScolaire" = (SELECT "IDTAnneeScolaire" FROM "TAnneeScolaire" WHERE "Cloturer" = FALSE LIMIT 1)
GROUP BY cla."IDTClasse", cla."LibClasse", cla."Capacite"
ORDER BY cla."LibClasse" ASC;
```

### Requête 3 : Détection des élèves créés sans aucune famille associée (Anomalie logicielle)
```sql
SELECT "IDEleve", "Matricule", "Nom", "Prenoms"
FROM "Eleve"
WHERE "IDFamille" IS NULL;
```

### Requête 4 : Liste des familles sans aucun élève rattaché (Opportunités de nettoyage)
```sql
SELECT fam."IdTFamille", fam."NomResponsable", fam."CellulaireResponsable"
FROM "TFamille" fam
LEFT JOIN "Eleve" el ON fam."IdTFamille" = el."IDFamille"
WHERE el."IDEleve" IS NULL;
```
