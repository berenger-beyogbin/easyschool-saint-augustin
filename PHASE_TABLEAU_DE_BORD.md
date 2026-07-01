# PHASE TABLEAU DE BORD — EASY SCHOOL 2.0
**Date :** 2026-06-20  
**Réalisé par :** Claude Code (Sonnet 4.6)  
**Périmètre :** `easy_school_python/` — Python 3 / PySide6 / SQLAlchemy / PostgreSQL

---

## 1. OBJECTIF DE LA PHASE

Concevoir et intégrer une fenêtre Tableau de bord complète et fonctionnelle comme page d'accueil de l'application Easy School 2.0, en remplacement du QLabel statique existant (`main_window.py` ligne 167).

Le tableau de bord doit afficher une synthèse globale de l'école pour l'année scolaire active, avec indicateurs clés, alertes, résumés rapides et accès rapide aux modules.

---

## 2. FICHIERS CRÉÉS

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `services/dashboard_service.py` | Service centralisant toutes les requêtes du tableau de bord | ~270 |
| `views/dashboard_view.py` | Vue PySide6 du tableau de bord (QScrollArea + cartes + alertes + tables) | ~340 |
| `TESTS_MANUELS_TABLEAU_DE_BORD.md` | Procédures de tests manuels avec requêtes SQL de vérification | ~250 |
| `PHASE_TABLEAU_DE_BORD.md` | Ce fichier de rapport de phase | — |

---

## 3. FICHIERS MODIFIÉS

| Fichier | Modification |
|---------|-------------|
| `views/main_window.py` | Import de `DashboardView`, remplacement du QLabel par `DashboardView(self)`, ajout du case `index == 0` dans `navigation_menu_changed`, correction du `else` (suppression du `.setText()` fragile) |

---

## 4. INDICATEURS INTÉGRÉS

### 4.1 Cartes statistiques (10 cartes sur 2 rangées)

| # | Indicateur | Source SQL | Couleur |
|---|-----------|------------|---------|
| 1 | Élèves inscrits | COUNT(TInscription) filtré par année active | Bleu |
| 2 | Nouveaux élèves | COUNT(TInscription WHERE Nouveau=True) | Vert |
| 3 | Classes actives | COUNT(TClasse) filtré par année active | Bleu |
| 4 | Familles | COUNT(TFamille) — total global | Gris foncé |
| 5 | Versements Scolarité | SUM(VersementScol.MontantVersSco) | Vert |
| 6 | Versements Cantine | SUM(VersementScol.MontantCantine) | Orange |
| 7 | Versements Transport | SUM(VersementScol.MontantVersTrans) | Orange |
| 8 | Ventes Kiosque | SUM(StockSortie.QuantiteSort × Prix_vente) | Bleu |
| 9 | Dépenses Comptabilité | SUM(SortieFin.Montant WHERE DebitCredit='Debit') | Rouge |
| 10 | Recettes Comptabilité | SUM(SortieFin.Montant WHERE DebitCredit='Credit') | Vert |

### 4.2 Tableaux résumés rapides

| Tableau | Colonnes | Source |
|---------|----------|--------|
| Dernières inscriptions (5) | Date, Matricule, Élève, Classe | TInscription + Eleve + TClasse |
| Derniers versements (5) | Date, Élève, Scolarité, Cantine, Transport | VersementScol + Eleve |
| Dernières ventes kiosque (5) | Date, Article, Qté, Montant | StockSortie + TArticle |

### 4.3 Bandeau supérieur

- Nom de l'établissement (depuis Etablissement_Ecole)
- Localité
- Année scolaire active (depuis AppSession)
- Date du jour (datetime.date.today())
- Utilisateur connecté (depuis AppSession.get_logged_in_username())
- Bouton Actualiser

---

## 5. ALERTES INTÉGRÉES

| Alerte | Condition | Couleur |
|--------|-----------|---------|
| Stock faible | StockCour.QuantiteCour <= TArticle.QTESeuil | Orange |
| Classe pleine | Effectif >= 90% de TClasse.Capacite | Orange |
| Impayés scolarité | Montant dû (MontantScol) − Total versé > 0, seulement si montant paramétré | Rouge |
| Aucune alerte | Toutes conditions normales | Vert |

**Règle anti-fausse alerte :** Si aucun MontantScol n'est paramétré pour un niveau, aucune alerte impayé n'est générée pour ce niveau.

---

## 6. ACCÈS RAPIDE

6 boutons d'accès rapide vers les modules principaux :
- Paramètres → `menu_list.setCurrentRow(6)`
- Scolarité → `menu_list.setCurrentRow(1)`
- Versements → `menu_list.setCurrentRow(1)` (sous-onglet Scolarité)
- Kiosque → `menu_list.setCurrentRow(2)`
- Comptabilité → `menu_list.setCurrentRow(3)`
- Statistiques → `menu_list.setCurrentRow(4)`

Si `main_window` n'est pas disponible → `QMessageBox.information("Navigation rapide à connecter.")`

---

## 7. TESTS EXÉCUTÉS

### 7.1 Compilation Python
```
Commande : py -m compileall . -q
Résultat  : COMPILATION OK — 0 erreur de syntaxe
```

### 7.2 Tests d'import
```
from services.dashboard_service import DashboardService → DashboardService OK
from views.dashboard_view import DashboardView         → DashboardView OK
from views.main_window import MainWindow               → MainWindow OK
```

### 7.3 Vérifications de sécurité UI
```
Qt.GlobalColor.fromRgb         → ABSENT dans dashboard_view.py
setFont(QColor                 → ABSENT dans dashboard_view.py
color: white (hors sidebar)    → ABSENT dans dashboard_view.py
DROP TABLE / DROP DATABASE     → ABSENT dans dashboard_service.py
DELETE FROM                    → ABSENT dans dashboard_service.py
```

---

## 8. RÉSULTAT DES TESTS

| Test | Résultat |
|------|---------|
| py -m compileall . | ✅ OK |
| import DashboardService | ✅ OK |
| import DashboardView | ✅ OK |
| import MainWindow | ✅ OK |
| Qt.GlobalColor.fromRgb absent | ✅ ABSENT |
| setFont(QColor absent | ✅ ABSENT |
| style blanc global hors sidebar | ✅ ABSENT |
| méthode inexistante appelée | ✅ ABSENT |
| Requêtes destructives | ✅ ABSENTES |

---

## 9. DÉCISIONS TECHNIQUES

### Pourquoi des dictionnaires et non des objets SQLAlchemy ?
Tous les services retournent des `dict` prêts à afficher, évitant ainsi les `DetachedInstanceError` une fois la session fermée. Les `joinedload` sont utilisés pour les relations nécessaires avant la fermeture de session.

### Pourquoi `format_fcfa` dans le service et non la vue ?
Pour garder la vue pure (affichage seulement) et permettre la réutilisation du formatage depuis d'autres contextes futurs.

### Pourquoi les impayés calculés en Python et non en SQL pur ?
Le calcul `montant_du - total_verse` nécessite un `montant_du` qui vient d'une table différente (`MontantScol`) corrélée par niveau. Le calcul Python sur des données déjà chargées est plus lisible, maintenable, et évite un SQL complexe potentiellement difficile à déboguer. La limite `limit=10` rend ce choix acceptable en termes de performance.

### Navigation Versements
Il n'existe pas de menu dédié "Versements" dans le menu principal (c'est un sous-onglet de Scolarité). Le bouton "Versements" navigue donc vers Scolarité (index 1), ce qui est la navigation correcte sans être fragile.

---

## 10. LIMITES RESTANTES

| Limite | Description | Impact |
|--------|-------------|--------|
| Authentification fictive | `get_logged_in_username()` retourne "KANGA JULIEN" hardcodé | Mineur — existait déjà avant cette phase |
| Rafraîchissement automatique | Le tableau de bord ne se rafraîchit pas automatiquement lors d'un changement d'année scolaire dans le header | Mineur — le bouton Actualiser compense |
| Impression | Aucun bouton "Imprimer" sur le tableau de bord | Non requis dans le cahier des charges |
| Autres frais impayés | Les impayés sur Cantine et Transport ne sont pas calculés dans la zone alertes | Hors périmètre de cette phase |
| SMS module | Toujours un placeholder | Hors périmètre de cette phase |
| Bibliothèque | Toujours un placeholder | Hors périmètre de cette phase |

---

## 11. PROCHAINE PHASE RECOMMANDÉE

### Phase 6 — Impressions (PDF / QPrinter)
**Estimé :** 6-10 heures  
**Objectif :** Implémenter les 8 boutons "Impression à venir" dans les vues statistiques et la balance des comptes.

**Fichiers concernés :**
- `views/stat_inscrits_view.py`
- `views/stat_nouveaux_view.py`
- `views/stat_scolarite_view.py`
- `views/stat_cantine_view.py`
- `views/stat_transport_view.py`
- `views/stat_vente_view.py`
- `views/stat_stock_view.py`
- `views/balance_comptes_view.py`

**Approche recommandée :** Utiliser `QPrinter` + `QPrintDialog` de PySide6, ou générer du HTML et l'exporter en PDF via `QTextDocument.print_()`.

---

*Rapport généré par Claude Code (Sonnet 4.6) — Phase Tableau de bord Easy School 2.0 — 2026-06-20*
