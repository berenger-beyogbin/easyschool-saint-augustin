# Procédures de Tests Manuels - Module PARAMÈTRES (Easy School 2.0)

Ce guide décrit pas à pas la procédure de validation manuelle pour s'assurer que toutes les corrections, validations métiers et améliorations demandées sur le module **PARAMÈTRES** de l'application de bureau Python (PySide6 + PostgreSQL) sont fonctionnelles et stables.

---

## 1. Démarrage de l'application & Connexion PostgreSQL

### Objectif
Vérifier que l'application détecte correctement l'absence de base de données PostgreSQL, s'arrête proprement et affiche un message explicite sans ouvrir la fenêtre principale.

### Étapes de test
1. Éteignez ou arrêtez temporairement votre service PostgreSQL ou renommez la variable `DB_NAME` / modifiez le mot de passe dans le fichier `.env` pour simuler une indisponibilité.
2. Lancez l'application avec la commande :
   ```bash
   python main.py
   ```
3. **Résultat attendu :** Une boîte de dialogue `QMessageBox` s'ouvre avec le message :
   > "Impossible de se connecter à PostgreSQL. Vérifiez le fichier .env, le mot de passe, le nom de la base et que le service PostgreSQL est démarré."
4. Cliquez sur **OK**.
5. **Résultat attendu :** L'application s'arrête proprement de suite sans charger aucune interface ni jeter d'erreurs/crashs de thread.
6. Rétablissez la configuration correcte de PostgreSQL dans le fichier `.env` ou relancez le service PostgreSQL.
7. Relancez à nouveau `python main.py`.
8. **Résultat attendu :** L'application se connecte avec succès et ouvre la fenêtre principale d'Easy School 2.0.

---

## 2. Sélecteur d'Année Académique & Session de Démarrage

### Objectif
Valider que la session est initialisée proprement et qu'au moins une année académique existe par défaut au lancement.

### Étapes de test
1. Assurez-vous que la base de données est vide de toute année scolaire (pour un premier lancement complet).
2. Lancez l'application : `python main.py`.
3. **Résultat attendu :** 
   - L'année scolaire **2026-2027** est automatiquement créée en base de données.
   - Le sélecteur d'année scolaire en haut à droite affiche bien **2026-2027** sélectionné par défaut.
   - Les listes et vues de l'application sont prêtes sans aucun message d'erreur.
4. Allez dans l'onglet **Généraux > Année Scolaire**.
5. **Résultat attendu :** La table récapitulative liste l'année **2026-2027** avec le statut **Active**.

---

## 3. Formulaires & Bouton "Nouveau"

### Objectif
Vérifier le rôle du bouton "Nouveau" sur tous les écrans concernés : Année scolaire, Niveau, Classe, Nationalité et Religion.

### Étapes de test
1. Dans n'importe lequel de ces 5 onglets de formulaire :
   - Renseignez quelques caractères ou sélectionnez des éléments dans les champs.
   - Cliquez sur le bouton **Nouveau**.
2. **Résultat attendu :** 
   - Tous les champs de saisie de l'écran courant sont vidés / réinitialisés à leurs valeurs par défaut.
   - Le focus du curseur est automatiquement repositionné sur le tout premier champ de saisie du formulaire.

---

## 4. Boutons "Fermer" Sécurisés

### Objectif
S'assurer qu'aucun clic sur le bouton "Fermer" ne ferme la fenêtre parente ou ne détruit l'interface du conteneur de manière dangereuse.

### Étapes de test
1. Sur chacun des écrans (Établissement, Année scolaire, Cycle, Niveau, Classe, Nationalité, Religion) :
   - Remplissez partiellement des valeurs dans les champs du formulaire.
   - Cliquez sur le bouton **Fermer**.
2. **Résultats attendus :**
   - **Écrans de paramétrage (Année, Cycle, Niveau, Classe, Nationalité, Religion) :** Le bouton réinitialise/vide les champs en toute sécurité sans fermer l'onglet ni la fenêtre.
   - **Écran Établissement :** Le bouton recharge les informations enregistrées depuis la base de données (restauration d'état d'origine) et avertit l'utilisateur par une notification.

---

## 5. Validations Métier Strictes (Prévention des Doublons & Formatage)

### Objectif
Valider le moteur d'intégrité de données en empêchant les saisies incorrectes dans les services.

### Étapes de test

#### A. Année Scolaire (Format & Séquence)
1. Allez sur **Généraux > Année Scolaire**.
2. Saisissez dans le champ : `2026/2027` ou `abcd-efgh`. Cliquez sur **Valider**.
   - **Résultat attendu :** Message d'erreur bloquant de format.
3. Saisissez maintenant : `2026-2028`. Cliquez sur **Valider**.
   - **Résultat attendu :** Message d'erreur bloquant stipulant que la deuxième année (2028) doit être égale à la première année (2026) + 1.
4. Saisissez `2026-2027` (déjà existant par défaut). Cliquez sur **Valider**.
   - **Résultat attendu :** Message d'erreur bloquant spécifiant que l'année existe déjà.

#### B. Cycles & Niveaux (Doublons & Cascade)
1. Allez sur **Classes > Cycle**. Ajoutez un cycle `COLLEGE`.
2. Essayez de ré-ajouter `COLLEGE` pour la même année scolaire active.
   - **Résultat attendu :** Doublon refusé par le service.
3. Allez sur **Classes > Niveau**. 
   - **Résultat attendu :** Si aucun cycle n'a été créé, le combo reste vide et un avertissement "Veuillez d'abord créer un cycle." est affiché de façon claire.
4. Sélectionnez le cycle `COLLEGE` et ajoutez le niveau `6EME`.
5. Essayez de ré-ajouter le niveau `6EME` sous le même cycle `COLLEGE` pour cette année scolaire active.
   - **Résultat attendu :** Doublon refusé.

#### C. Classes (Doublons & Capacité [1-200])
1: Allez sur **Classes > Classe**.
2: Testez les limites de saisie de capacité :
   - Saisissez `1` : la valeur est acceptée.
   - Saisissez `200` : la valeur est acceptée.
   - Essayez de saisir `0` ou `201` via l'interface (SpinBox) : notez que la SpinBox bloque et ne permet pas d'aller en dessous de `1` ni au-dessus de `200`.
   - Si vous testez via le service ou de force, vérifiez que le validateur du service renvoie une erreur bloquante ("La capacité de la classe doit être comprise entre 1 et 200").
3: Saisissez une capacité valide (ex : `35`) et ajoutez une classe `6EME A` sous le niveau `6EME`.
4: Ré-ajoutez la même classe `6EME A` sous le même niveau `6EME` et la même session en cours.
   - **Résultat attendu :** Doublon refusé par le validateur et par la contrainte d'unicité SQL.

#### D. Autres réglages : Nationalités & Religions (Unicité)
1. Allez sur **Autres réglages > Nationalités**.
2. Ajoutez la nationalité `IVOIRIENNE`.
3. Essayez d'ajouter `ivoirienne` (minuscule), ou `  IVOIRIENNE  ` (avec des espaces).
   - **Résultat attendu :** Doublon détecté et bloqué.
4. Effectuez le même test d'unicité avec les religions dans **Autres réglages > Religions** (ex : ajoutez `ISLAM` puis testez `islam`).
   - **Résultat attendu :** Doublon refusé avec succès.

---

## 6. Rafraîchissement des Données lors du Changement d'Onglet

### Objectif
Prendre en compte automatiquement les changements d'année scolaire active ou d'ajouts dans d'autres formulaires quand on navigue entre les sections des paramètres.

### Étapes de test
1. Ajoutez une nationalité depuis l'onglet dédié.
2. Allez sur l'onglet **Religions** puis revenez sur l'onglet **Nationalités**.
3. **Résultat attendu :** La liste des nationalités est automatiquement rechargée et à jour.
4. Modifiez l'année scolaire de session dans le sélecteur en haut à droite (par exemple, passez de `2026-2027` à une autre année récemment créée).
5. **Résultat attendu :** Toutes les listes de cycles, niveaux et classes se mettent à jour instantanément pour afficher uniquement les données liées à l'année nouvellement sélectionnée.

---

## 7. Validations de Stabilisation Finale du Module PARAMÈTRES

### Objectif
Assurer un comportement robuste au niveau de la gestion dynamique des sessions, de la création des années scolaires futures, des suppressions sécurisées en cascade, et de l'ergonomie de l'interface utilisateur.

### Étapes de test

#### A. Persistance de l'Année Scolaire Sélectionnée
1. Créez deux années scolaires non clôturées (ex : `2026-2027` et `2027-2028`).
2. Dans le sélecteur en haut à droite, sélectionnez manuellement l'année `2027-2028`.
3. Naviguez entre différents onglets (ex: passez de **Classes > Niveau** à **Généraux > Année Scolaire** puis à d'autres modules développés).
4. **Résultat attendu :** L'année sélectionnée reste fidèlement `2027-2028`. Elle n'est pas réinitialisée silencieusement à l'année précédente `2026-2027`.

#### B. Clôture d'Année et Création Automatique de l'Année Suivante
1. Mettez-vous sur l'année active `2026-2027`.
2. Allez dans l'onglet **Généraux > Année Scolaire**.
3. Cliquez sur le bouton **Clôturer** face à l'année `2026-2027` :
   - Confirmez la clôture.
4. **Résultats attendus :**
   - L'année scolaire `2026-2027` passe au statut "Clôturée".
   - L'application crée automatiquement l'année suivante `2027-2028` (puisque toutes les années précédentes sont désormais clôturées).
   - L'année `2027-2028` devient la nouvelle session active sélectionnée en haut à droite dans le sélecteur d'année.

#### C. Validation de la Liste du Sélecteur (Filtrage des Années Clôturées)
1. Ouvrez le menu déroulant du sélecteur d'année scolaire en haut à droite.
2. **Résultat attendu :** L'année clôturée `2026-2027` n'apparaît **jamais** dans le combo du haut. Seules les années scolaires actives (non clôturées) y figurent. Il est donc impossible pour l'utilisateur de resélectionner une année clôturée comme session active.

#### D. Sécurité de Suppression des Cycles
1. Créez un cycle (ex: `LYCEE`), puis associez-y un niveau (ex: `SECONDE`).
2. Allez dans l'onglet **Classes > Cycle**.
3. Essayez de cliquer sur le bouton **Supprimer** face au cycle `LYCEE`.
4. **Résultat attendu :** L'application refuse la suppression et affiche un message clair : 
   > "Impossible de supprimer ce cycle car il contient déjà des niveaux ou des classes."
   La base de données n'est pas sollicitée pour lever une erreur brutale, le blocage est géré sainement au niveau applicatif.

#### E. Sécurité de Suppression des Niveaux
1. Créez un niveau (ex: `SECONDE`), puis créez une classe rattachée (ex: `2nde A`).
2. Allez dans l'onglet **Classes > Niveau**.
3. Essayez de supprimer le niveau `SECONDE`.
4. **Résultat attendu :** L'application refuse la suppression et affiche un message clair :
   > "Impossible de supprimer ce niveau car il contient déjà des classes."

#### F. Ergonomie et Absence de Pop-up Répétitives
1. Supprimez (ou assurez-vous de n'avoir) aucun cycle en base dans votre année active.
2. Cliquez sur l'onglet **Classes > Niveau** ou **Classes > Classe**.
3. Naviguez entre les onglets et observez le rafraîchissement d'interface.
4. **Résultats attendus :**
   - **Aucune boîte de dialogue intrusive (pop-up) ne s'affiche à chaque clic d'onglet ou refresh de données.**
   - Un bandeau ou label d'avertissement rouge discret s'affiche au sommet de l'onglet : 
     > "Veuillez d'abord créer un cycle dans l'onglet Cycle." (ou "Veuillez d'abord créer un niveau pour ce cycle dans l'onglet Niveau.").
   - Le bouton **Valider** (ou **Valider la Classe**) est **automatiquement grisé et désactivé** tant que le prérequis n'est pas rempli.
   - Dès que vous créez un cycle (et un niveau respectif), le bandeau disparaît et le bouton s'active à nouveau de façon transparente au prochain affichage.

