# Tests Manuels IHM — Easy School 2.0
Date : 2026-06-20

Checklist de validation manuelle après amélioration IHM.

## Démarrage

- [ ] **1. Lancer l'application**
  - Commande : `python main.py` (depuis le venv)
  - Vérifier : fenêtre 1280×800 s'ouvre sans erreur
  - Vérifier : aucune exception dans le terminal

## Sidebar & Navigation

- [ ] **2. Vérifier la sidebar**
  - Fond bleu nuit visible (#071B33)
  - Avatar "KJ" circulaire bleu affiché
  - Nom "KANGA JULIEN" et rôle "Administrateur" visibles
  - Indicateur "● En ligne" en vert
  - Menu lisible : 7 items bien espacés
  - Item sélectionné mis en surbrillance bleue (#2563EB)
  - Hover légèrement visible
  - Version en bas discrète

## Topbar

- [ ] **3. Vérifier la topbar**
  - Hauteur fixe stable (~56px)
  - Titre module visible et lisible
  - Sélecteur année académique visible à droite
  - Fond blanc, bordure basse discrète

## Tableau de bord

- [ ] **4. Vérifier le tableau de bord**
  - En-tête blanc avec titre "Tableau de bord" bleu foncé
  - Date et utilisateur affichés en haut à droite
  - Bouton "Actualiser" visible et fonctionnel
  - 10 cartes KPI affichées en 2 lignes de 5
  - Chaque carte a une bande de couleur à gauche
  - Chaque carte affiche une icône, un titre et une valeur
  - Panneau "Alertes" visible : message vert si aucune alerte
  - Tableau "Dernières inscriptions" affiché dans un panneau carte
  - Tableau "Derniers versements" affiché dans un panneau carte
  - Tableau "Dernières ventes" affiché dans un panneau carte
  - Section "Accès rapide" avec 6 boutons secondaires
  - Aucun texte blanc hors sidebar

## Paramètres

- [ ] **5. Ouvrir Paramètres (menu Paramètres)**
  - 4 onglets : Généraux, Classes, Versements, Autres réglages
  - Sous-onglets fonctionnels (Établissement, Cycle, Niveau, Classe…)
  - Aucune erreur à l'ouverture

## Scolarité / Inscriptions

- [ ] **6. Ouvrir Scolarité / Inscriptions**
  - Liste des élèves visible dans un tableau
  - Boutons Ajouter, Modifier, Supprimer présents
  - Tableau avec en-tête gris clair et lignes alternées

## Modale Parents

- [ ] **7. Ouvrir la modale Parents**
  - Cliquer "Enregistrer Parents" dans la liste des familles
  - Fenêtre 780×620 s'ouvre
  - En-tête sombre bleu foncé avec titre blanc
  - 4 sections cards : Père, Mère, Responsable légal, Urgence
  - Champs compacts (hauteur ~32px)
  - Labels alignés à droite avec largeur fixe
  - Boutons "Fermer" et "Valider" en bas à droite
  - Scroll fonctionnel si la fenêtre est petite
  - Aucun champ géant

## Versements / Caisse

- [ ] **8. Ouvrir Versements / Caisse**
  - Panneau gauche : recherche + tableau élèves + formulaire versement + historique
  - Panneau droit : "Situation financière" avec header bleu foncé
  - Header affiche "Situation financière" en blanc sur fond bleu
  - 4 sections colorées : Scolarité (bleu), Transport (bleu ciel), Cantine (orange), Autres (violet)
  - Chaque section affiche Dû / Versé / Reste
  - "Reste" en rouge si > 0, vert si = 0
  - Total général visible avec fond gris clair
  - Sélectionner un élève : données financières se mettent à jour
  - Saisir un versement et valider : succès ou message d'erreur clair

## Kiosque

- [ ] **9. Ouvrir Kiosque**
  - Onglets : Vendre, Approvisionnement, Articles & KITS
  - Tableaux visibles sans erreur
  - Aucun plantage à l'ouverture

## Comptabilité

- [ ] **10. Ouvrir Comptabilité**
  - Onglets : Enregistrements, État des Sorties, Créer un compte, Balance
  - Chaque onglet s'ouvre sans erreur
  - Les tableaux sont lisibles

## Statistiques

- [ ] **11. Ouvrir Statistiques**
  - 7 onglets : Inscrits, Nouveaux, Scolarité, Cantine, Transport, Vente, Stock
  - Les filtres de date sont disponibles
  - Aucun tableau entièrement vide sans message

## SMS Placeholder

- [ ] **12. Ouvrir SMS**
  - Carte centrale visible
  - Titre "Module SMS" affiché
  - Badge "BIENTÔT" en orange
  - Description explicative visible
  - Aucun bouton qui plante

## Vérifications générales

- [ ] **13. Tableaux vides**
  - Si aucune donnée, le tableau affiche "Aucune donnée disponible" centré
  - Pas de tableau complètement vide sans indication

- [ ] **14. Boutons**
  - Bouton principal : fond bleu, texte blanc
  - Bouton succès : fond vert, texte blanc
  - Bouton danger : fond rouge, texte blanc
  - Bouton secondaire : fond gris clair, texte foncé, bordure légère
  - Hauteur cohérente (~34px) sur tous les écrans
  - Arrondi (~6px) visible

- [ ] **15. Lisibilité du texte**
  - Texte blanc uniquement dans la sidebar, les headers de modales, les boutons colorés
  - Texte foncé sur tous les fonds clairs
  - Labels de formulaire bien lisibles (~12px)
  - Titres de sections visibles et hiérarchisés

- [ ] **16. Stabilité**
  - Naviguer entre tous les modules sans plantage
  - Revenir au tableau de bord depuis chaque module
  - Changer l'année académique dans la topbar : les données se rechargent
  - Fermer l'application proprement
