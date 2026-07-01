# TESTS MANUELS — Template UI Moderne — Easy School 2.0

## Prérequis

- PostgreSQL démarré et accessible
- Venv activé : `.\venv\Scripts\activate`
- Lancer : `python main.py`

---

## 1. Lancer l'application

- [ ] `python main.py` démarre sans erreur
- [ ] La fenêtre s'ouvre à 1280×800 minimum
- [ ] Le titre de fenêtre est : "Easy School 2.0 — Gestion d'École Professionnelle"

---

## 2. Vérifier la sidebar

- [ ] Fond bleu nuit profond (#071B33) visible
- [ ] "Easy School" en blanc + "2.0" en bleu vif en haut
- [ ] Avatar circulaire bleu avec initiales "KJ"
- [ ] Nom "KANGA JULIEN" en blanc
- [ ] Rôle "Administrateur" en gris clair
- [ ] Statut "● En ligne" en vert
- [ ] Label "NAVIGATION" en majuscules discret
- [ ] 7 menus listés avec icônes Unicode
- [ ] Menu actif (Tableau de bord) en fond bleu vif arrondi
- [ ] Hover sur autres menus : fond blanc très léger
- [ ] "Version 2.0 · Migration Python" en bas discret

---

## 3. Vérifier la topbar

- [ ] Fond blanc avec bordure inférieure grise
- [ ] Texte "MODULE EN COURS :" en gris foncé + nom du module en bleu coloré
- [ ] Sélecteur "Année Académique :" à droite avec QComboBox moderne
- [ ] Le sélecteur d'année affiche les années non clôturées

---

## 4. Vérifier l'écran Tableau de bord

- [ ] Fond gris clair (#F5F7FB) de la zone centrale
- [ ] Cartes KPI blanches avec titres gris et valeurs colorées
- [ ] 10 cartes KPI réparties sur 2 lignes
- [ ] Section ALERTES en rouge avec contenu lisible
- [ ] 3 tableaux "Dernières inscriptions / versements / ventes" avec alternance bleue
- [ ] Section "ACCÈS RAPIDE AUX MODULES" avec boutons gris
- [ ] Aucun texte blanc sur fond blanc

---

## 5. Ouvrir Paramètres

- [ ] Clic sur "⚙  Paramètres" dans la sidebar → menu actif change
- [ ] Topbar affiche "MODULE EN COURS : PARAMÈTRES" en bleu
- [ ] 4 onglets modernes : Généraux / Classes / Versements / Autres réglages
- [ ] Onglet actif : fond blanc, texte bleu foncé, barre bleue en bas
- [ ] Onglets inactifs : fond gris clair, texte gris
- [ ] Sous-onglets (position West) fonctionnent : Établissement, Année Scolaire, etc.
- [ ] Onglet "Versements" affiche "Fonctionnalité à venir." proprement

---

## 6. Ouvrir Scolarité

- [ ] Clic sur "✎  Scolarité" → module actif
- [ ] Topbar affiche "SCOLARITÉ / INSCRIPTIONS"
- [ ] 2 onglets principaux : Inscriptions / Versements
- [ ] Onglet Inscriptions : 3 sous-onglets (Élèves / Inscription / Liste des Parents)
- [ ] Liste élèves s'affiche avec tableau alterné bleu
- [ ] Formulaire inscription lisible (labels noirs, champs blancs)

---

## 7. Ouvrir Versements (sous-onglet de Scolarité)

- [ ] Clic onglet "Versements" dans Scolarité
- [ ] 5 sous-onglets : Caisse / Scolarité / Transport / Cantine / Autres Frais
- [ ] Caisse : tableau élèves visible, champs blancs lisibles
- [ ] Panneau "Situation Financière" à droite visible (si présent)
- [ ] Montants Dû / Versé / Reste à payer lisibles en noir/vert/rouge
- [ ] Aucun texte blanc sur fond blanc

---

## 8. Ouvrir Kiosque

- [ ] Clic "⊛  Kiosque"
- [ ] En-tête "GESTION DU KIOSQUE" avec sous-titre gris
- [ ] Aucun bandeau bleu ciel (#bae6fd) — VÉRIFIÉ : supprimé
- [ ] 2 onglets : KIOSQUE / BIBLIOTHÈQUE
- [ ] Sous-onglets Kiosque : Vendre / Approvisionnement / Articles & KITS
- [ ] Onglet BIBLIOTHÈQUE affiche placeholder centré avec icône 📚

---

## 9. Ouvrir Comptabilité

- [ ] Clic "◈  Comptabilité"
- [ ] En-tête "COMPTABILITÉ FINANCIÈRE" avec sous-titre
- [ ] Aucun bandeau bleu ciel — VÉRIFIÉ : supprimé
- [ ] 4 onglets : Enregistrements / État des Sorties / Créer un compte / Balance
- [ ] Tableaux lisibles avec alternance bleu
- [ ] Totaux débit/crédit visibles et lisibles

---

## 10. Ouvrir Statistiques

- [ ] Clic "⊜  Statistiques"
- [ ] En-tête "STATISTIQUES ET RAPPORTS" avec sous-titre
- [ ] 7 onglets : Inscrits / Nouveaux / Scolarité / Cantine / Transport / Vente / Stock
- [ ] Chaque onglet affiche un tableau avec données
- [ ] Boutons "Afficher" / "Imprimer" présents et lisibles

---

## 11. Ouvrir SMS

- [ ] Clic "✉  SMS · Bientôt"
- [ ] Page SMS placeholder propre s'affiche (pas de redirection vers dashboard)
- [ ] Icône ✉ en bleu en haut de la carte
- [ ] Titre "Module SMS" en bleu foncé
- [ ] Badge orange "BIENTÔT"
- [ ] Texte descriptif en gris centré
- [ ] Aucun bouton qui plante

---

## 12. Vérifier les modales

- [ ] Ouvrir formulaire Nouvel Élève → fenêtre modale s'ouvre
- [ ] Fond blanc, titre visible, champs avec bordure grise
- [ ] Labels noirs lisibles
- [ ] Boutons colorés lisibles (vert Enregistrer, rouge Annuler)
- [ ] Aucun texte blanc invisible sur fond blanc dans la modale

---

## 13. Vérifier les tableaux

- [ ] Alternance bleue/blanche sur les tableaux principaux
- [ ] Header gris clair avec texte noir gras
- [ ] Sélection d'une ligne : fond bleu clair (#DBEAFE) lisible
- [ ] Montants alignés à droite dans les colonnes financières
- [ ] Aucune cellule avec texte blanc sur fond blanc

---

## 14. Vérifier les boutons

- [ ] Bouton principal bleu : fond #2563EB / texte blanc
- [ ] Bouton succès vert : fond #16A34A / texte blanc
- [ ] Bouton danger rouge : fond #DC2626 / texte blanc
- [ ] Bouton secondaire gris : fond #6B7280 / texte blanc
- [ ] Hover sur boutons : changement de teinte visible
- [ ] Bouton désactivé : fond gris clair / texte gris (pas blanc)

---

## 15. Vérifier la lisibilité globale

- [ ] Aucun texte blanc sur fond blanc (zones de contenu central)
- [ ] Tous les labels de formulaire sont noirs / gris foncé
- [ ] Les titres de section sont bleu foncé (#1E3A8A)
- [ ] Les valeurs importantes sont en couleur (bleu/vert/rouge)
- [ ] Police lisible, taille correcte (min 12px)

---

## 16. Vérifier les boutons Imprimer

- [ ] Si bouton "Imprimer" existe : clic affiche "Impression à venir." ou similaire
- [ ] Aucun bouton "Imprimer" ne plante avec traceback visible
- [ ] Si un QMessageBox s'affiche : il est lisible et fermable

---

## 17. Vérifier la compilation finale

```bash
cd easy_school_python
python -m compileall app views -q
```

- [ ] Sortie vide = 0 erreur

---

## Résultats attendus

| Test | Résultat attendu |
|------|-----------------|
| Compilation | 0 erreur |
| Import MainWindow | OK |
| Import styles | OK |
| Sidebar couleur | #071B33 visible |
| Bandeau bleu ciel | ABSENT dans Kiosque et Comptabilité |
| SMS placeholder | Affiché proprement |
| Texte blanc hors sidebar | ABSENT |
