# PHASE TEMPLATE UI MODERNE — Easy School 2.0

## 1. Objectif de la phase

Appliquer un template visuel moderne, premium et cohérent à toutes les fenêtres de l'application Easy School 2.0.  
Remplacer l'apparence terne / style WinDev par un design SaaS / ERP inspiré du template de référence fourni.

## 2. Inspiration du template

Interface de référence (capture fournie) :
- Sidebar bleu nuit profond
- Logo Easy School 2.0 visible en haut
- Bloc utilisateur avec avatar circulaire, nom, rôle, statut "En ligne"
- Menus latéraux avec icônes et état actif bleu vif arrondi
- Topbar blanche avec titre module coloré et sélecteur d'année
- Cartes KPI blanches avec valeurs colorées
- Tableaux modernes avec alternance bleue/blanche
- Boutons colorés avec arrondis
- Panneaux blancs arrondis sur fond gris très clair

## 3. Fichiers créés

| Fichier | Description |
|---------|-------------|
| `views/ui_components.py` | Composants UI réutilisables : ModernCard, KpiCard, SectionHeader, EmptyState, QuickActionButton, make_module_header |
| `PHASE_TEMPLATE_UI_MODERNE.md` | Ce document |
| `TESTS_MANUELS_TEMPLATE_UI.md` | Procédure de tests manuels |

## 4. Fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `app/styles.py` | Réécriture complète : COLORS dict, APP_STYLE, SIDEBAR_STYLE, TAB_STYLE, TAB_STYLE_NESTED, BUTTON_*, TABLE_STYLE, TABLE_STYLE_YELLOW, BADGE_*, GROUPBOX_STYLE, fonctions helpers (apply_table_style, format_fcfa, make_section_title, make_placeholder_message, apply_card_shadow), aliases de compatibilité conservés |
| `views/main_window.py` | Sidebar #071B33, AvatarLabel circulaire, bloc utilisateur KANGA JULIEN/Administrateur/● En ligne, menus avec icônes Unicode, topbar blanche avec titre coloré, widget SMS SMSPlaceholderWidget ajouté à stack (index 6), navigation SMS câblée |
| `views/kiosque_view.py` | Suppression bandeau bleu ciel (#bae6fd), remplacement par make_module_header moderne, TAB_STYLE et TAB_STYLE_NESTED appliqués, EmptyState pour Bibliothèque |
| `views/comptabilite_view.py` | Suppression bandeau bleu ciel, make_module_header moderne, TAB_STYLE appliqué |
| `views/statistiques_view.py` | make_module_header ajouté, TAB_STYLE modern appliqué |
| `views/versements_view.py` | TAB_STYLE_NESTED appliqué, fond bg cohérent |
| `views/scolarite_view.py` | TAB_STYLE pour onglets principaux, TAB_STYLE_NESTED pour sous-onglets |

## 5. Styles centralisés (app/styles.py)

### Couleurs COLORS dict
```python
COLORS = {
    "sidebar_bg": "#071B33",    # Bleu nuit sidebar
    "sidebar_bg_2": "#0B1F3A",  # Bleu nuit logo
    "primary": "#2563EB",       # Bleu vif actif/boutons
    "primary_dark": "#1E3A8A",  # Bleu foncé titres
    "success": "#16A34A",       # Vert succès
    "danger": "#DC2626",        # Rouge danger
    "warning": "#F97316",       # Orange avertissement
    "bg": "#F5F7FB",            # Fond général gris clair
    "card": "#FFFFFF",          # Cartes blanches
    "text": "#111827",          # Texte principal
    "muted": "#6B7280",         # Texte secondaire
    "border": "#E5E7EB",        # Bordures fines
    "table_alt_blue": "#EFF6FF",  # Alternance bleue tableaux
    "table_alt_yellow": "#FEF9C3" # Alternance jaune (états financiers)
}
```

### Styles exportés
- `APP_STYLE` — global application (scrollbars)
- `SIDEBAR_MENU_STYLE` — menu latéral sombre
- `TAB_STYLE` — onglets principaux modernes (sélection bleu)
- `TAB_STYLE_NESTED` — sous-onglets plus compacts
- `TABLE_STYLE` — tableaux alternance bleue
- `TABLE_STYLE_YELLOW` — tableaux alternance jaune
- `BUTTON_PRIMARY`, `BUTTON_SUCCESS`, `BUTTON_DANGER`, `BUTTON_SECONDARY`, `BUTTON_PRINT`
- `BADGE_SUCCESS`, `BADGE_WARNING`, `BADGE_DANGER`
- `GROUPBOX_STYLE` — QGroupBox standardisé
- `INPUT_STYLE`, `COMBO_STYLE`
- Aliases rétrocompatibles : `STYLE_TABLE`, `STYLE_BUTTON_PRIMARY`, `STYLE_LINEEDIT`, etc.

### Fonctions helpers
- `apply_table_style(table, alternate)` — applique TABLE_STYLE ou TABLE_STYLE_YELLOW
- `format_fcfa(montant)` — formate les montants avec séparateurs
- `make_section_title(text)` — QLabel titre de section
- `make_placeholder_message(text)` — QLabel placeholder centré
- `apply_card_shadow(widget)` — ombre via QGraphicsDropShadowEffect

## 6. Modules modernisés

| Module | Statut |
|--------|--------|
| Tableau de bord | OK — cartes KPI, alertes, tableaux, accès rapide |
| Paramètres | OK — onglets TAB_STYLE, fond cohérent |
| Scolarité / Inscriptions | OK — TAB_STYLE + TAB_STYLE_NESTED |
| Scolarité / Versements | OK — TAB_STYLE_NESTED vert → bleu standardisé |
| Kiosque | OK — bandeau supprimé, make_module_header, onglets modernes |
| Comptabilité | OK — bandeau supprimé, make_module_header, onglets modernes |
| Statistiques | OK — make_module_header, TAB_STYLE modern |
| SMS placeholder | OK — SMSPlaceholderWidget propre avec badge "BIENTÔT" |

## 7. Limites restantes

- Les vues filles (caisse_view, eleve_form_view, famille_form_view, etc.) conservent leur style individuel non modifié. Elles bénéficient indirectement des nouveaux styles grâce à l'héritage CSS Qt mais n'ont pas été entièrement refondues.
- Les onglets de paramètres en position `West` (sidebar interne) ont un style basique car QTabWidget West ne supporte pas l'arrondi CSS de la même façon.
- Aucune impression réelle n'est implémentée — les boutons "Imprimer" existants doivent afficher "Impression à venir." via leur propre logique.
- Le module SMS est en placeholder propre — aucune fonctionnalité SMS n'est développée.
- L'avatar utilisateur est statique (initiales "KJ") — non connecté à une base de données utilisateurs.

## 8. Tests exécutés

```
python -m compileall app views       : OK (0 erreur)
from app.styles import *             : OK
from views.ui_components import *    : OK
from views.main_window import MainWindow : OK
from views.dashboard_view import DashboardView : OK
from views.scolarite_view import ScolariteView : OK
from views.kiosque_view import KiosqueView : OK
from views.comptabilite_view import ComptabiliteView : OK
from views.statistiques_view import StatistiquesView : OK
from views.versements_view import VersementsView : OK
```

## 9. Recherches finales

| Pattern | Résultat |
|---------|----------|
| `Qt.GlobalColor.fromRgb` | ABSENT |
| `setFont(QColor` | ABSENT |
| `QWidget { color: white }` globalement | ABSENT |
| `QLabel { color: white }` globalement | ABSENT |
| Méthode inexistante `close_active_tab` appelée sans guard | ABSENT (hasattr utilisé) |
| Placeholders dangereux | ABSENT |

## 10. Recommandations pour la suite

1. **Phase UI vues filles** — Appliquer GROUPBOX_STYLE, INPUT_STYLE et BUTTON_* aux formulaires internes (eleve_form_view, famille_form_view, caisse_view, eleve_list_view, etc.)
2. **Phase impression** — Implémenter la génération de PDF/QPrinter pour les boutons "Imprimer"
3. **Phase responsive** — Tester sur différentes résolutions (1366×768, 1920×1080) et ajuster les proportions sidebar/workspace
4. **Phase avatar** — Connecter l'avatar à un système d'authentification réel
5. **Phase SMS** — Intégrer une API SMS (ex: Twilio, Vonage) dans le module placeholder existant
