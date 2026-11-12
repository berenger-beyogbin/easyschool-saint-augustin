from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTabWidget, QComboBox,
    QFrame, QPushButton
)
from PySide6.QtCore import Qt

from views.main_window_widgets import AvatarLabel, SMSPlaceholderWidget, SidebarItemDelegate

# Import des fiches du module Parametres
from .etablissement_view import EtablissementView
from .annee_scolaire_view import AnneeScolaireView
from .cycle_view import CycleView
from .niveau_view import NiveauView
from .classe_view import ClasseView
from .nationalite_view import NationaliteView
from .religion_view import ReligionView
from .scolarite_view import ScolariteView
from .kiosque_view import KiosqueView
from .comptabilite_view import ComptabiliteView
from .statistiques_view import StatistiquesView
from .dashboard_view import DashboardView
from .utilisateurs_view import UtilisateursView
from .internat_view import InternatView
from .cantine_externe_view import CantineExterneView
from .backup_view import BackupView

from app.styles import (
    COLORS, SIDEBAR_MENU_STYLE, TAB_STYLE, COMBO_STYLE, BUTTON_SECONDARY
)
from app.config import Config
from app.version import __version__


class MainWindow(QMainWindow):
    """Fenêtre principale Easy School 2.0 — Template UI Moderne."""

    # (label, code_permission) — ordre original figé pour les icônes, titres
    # de la topbar (navigation_menu_changed) et routage vers self.stack.
    # Ne pas reordonner cette liste : c'est l'index dans MENU_ITEMS (orig_idx)
    # qui sert de clé partout ailleurs. Pour changer l'ordre d'AFFICHAGE dans
    # la sidebar, modifier MENU_DISPLAY_ORDER ci-dessous, pas cette liste.
    MENU_ITEMS = [
        ("Tableau de bord", "DASHBOARD_VIEW"),
        ("Scolarité",       "SCOLARITE_VIEW"),
        ("Kiosque",         "KIOSQUE_VIEW"),
        ("Comptabilité",    "COMPTABILITE_VIEW"),
        ("Statistiques",    "STATISTIQUES_VIEW"),
        ("SMS",             "SMS_VIEW"),
        ("Paramètres",      "PARAMETRES_VIEW"),
        ("Utilisateurs",    "UTILISATEURS_VIEW"),
        ("Internat",        "INTERNAT_VIEW"),
        ("Cantine",         "CANTINE_EXTERNE_VIEW"),
    ]

    # Ordre d'affichage dans la sidebar, par index MENU_ITEMS (orig_idx).
    # Internat (8) et Cantine externe (9) sont places avant Comptabilite (3).
    MENU_DISPLAY_ORDER = [0, 1, 2, 8, 9, 3, 4, 5, 6, 7]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Easy School 2.0 — Gestion d'École Professionnelle")
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)
        self.init_ui()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def init_ui(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        layout_principal.addWidget(self._build_sidebar())
        layout_principal.addWidget(self._build_workspace(), 1)

        # Activer Tableau de bord au démarrage
        self.menu_list.setCurrentRow(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {COLORS['sidebar_bg']};
                min-width: 235px;
                max-width: 235px;
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Logo ---
        logo_frame = QFrame()
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['sidebar_bg_2']};
                border-bottom: 1px solid rgba(255,255,255,0.07);
                padding: 0;
            }}
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(18, 20, 18, 20)
        logo_layout.setSpacing(0)

        logo_title_row = QHBoxLayout()
        logo_title_row.setSpacing(8)
        logo_title_row.setContentsMargins(0, 0, 0, 0)

        lbl_logo_top = QLabel("Easy School")
        lbl_logo_top.setStyleSheet(
            "color: #FFFFFF; font-size: 18px; font-weight: bold;"
            "background-color: transparent; letter-spacing: 0.2px;"
        )
        logo_title_row.addWidget(lbl_logo_top)

        lbl_logo_sub = QLabel(".".join(__version__.split(".")[:2]))
        lbl_logo_sub.setStyleSheet(
            f"color: #FFFFFF; background-color: {COLORS['primary']}; font-size: 11px;"
            "font-weight: bold; border-radius: 5px; padding: 1px 6px;"
        )
        lbl_logo_sub.setFixedHeight(20)
        logo_title_row.addWidget(lbl_logo_sub, 0, Qt.AlignVCenter)
        logo_title_row.addStretch()

        logo_layout.addLayout(logo_title_row)
        layout.addWidget(logo_frame)

        # --- Bloc Utilisateur (dynamique depuis AppSession) ---
        from app.session import AppSession
        _user_nom = AppSession.get_current_user_nom() or "Administrateur"
        _user_role = AppSession.get_current_user_profil_libelle() or "Administrateur"
        _initiales = "".join(p[0].upper() for p in _user_nom.split()[:2]) or "AD"

        user_frame = QFrame()
        user_frame.setStyleSheet(
            "QFrame { background-color: rgba(255,255,255,0.04); border: none; }"
        )
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 14, 16, 14)
        user_layout.setSpacing(12)

        self.avatar = AvatarLabel(_initiales)
        user_layout.addWidget(self.avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(3)
        user_info.setContentsMargins(0, 0, 0, 0)

        lbl_user_name = QLabel(_user_nom.upper())
        lbl_user_name.setStyleSheet(
            "color: #FFFFFF; font-size: 13px; font-weight: bold;"
            " background-color: transparent; border: none;"
        )

        lbl_user_role = QLabel(_user_role)
        lbl_user_role.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background-color: transparent; border: none;"
        )

        lbl_status = QLabel("● En ligne")
        lbl_status.setStyleSheet(
            "color: #4ADE80; font-size: 11px; background-color: transparent; border: none;"
        )

        user_info.addWidget(lbl_user_name)
        user_info.addWidget(lbl_user_role)
        user_info.addWidget(lbl_status)
        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_frame)

        # --- Séparateur ---
        sep_lbl = QLabel("NAVIGATION")
        sep_lbl.setStyleSheet(
            "color: rgba(255,255,255,225.25); font-size: 10px; font-weight: 700;"
            "letter-spacing: 2px; background-color: transparent;"
        )
        sep_wrap = QFrame()
        sep_wrap.setStyleSheet("background-color: transparent;")
        sep_wrap_layout = QHBoxLayout(sep_wrap)
        sep_wrap_layout.setContentsMargins(18, 12, 18, 4)
        sep_wrap_layout.addWidget(sep_lbl)
        layout.addWidget(sep_wrap)

        # --- Menu de navigation ---
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet(SIDEBAR_MENU_STYLE)
        self.menu_list.setFocusPolicy(Qt.NoFocus)
        self.menu_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for orig_idx in self.MENU_DISPLAY_ORDER:
            label, perm = self.MENU_ITEMS[orig_idx]
            if AppSession.has_permission(perm):
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, orig_idx)
                self.menu_list.addItem(item)

        self.menu_list.setItemDelegate(SidebarItemDelegate(self.menu_list))
        self.menu_list.currentRowChanged.connect(self.navigation_menu_changed)

        menu_wrap = QFrame()
        menu_wrap.setStyleSheet("background-color: transparent;")
        menu_wrap_layout = QVBoxLayout(menu_wrap)
        menu_wrap_layout.setContentsMargins(10, 6, 10, 6)
        menu_wrap_layout.setSpacing(0)
        menu_wrap_layout.addWidget(self.menu_list)
        layout.addWidget(menu_wrap, 1)

        # --- Version en bas ---
        sep_bottom = QFrame()
        sep_bottom.setFrameShape(QFrame.HLine)
        sep_bottom.setStyleSheet("color: rgba(255,255,255,0.07);")
        layout.addWidget(sep_bottom)

        lbl_version = QLabel("Version 2.0 — 2026 © Easy School")
        lbl_version.setStyleSheet(
            "color: rgba(255,255,255,0.25); font-size: 10px; background-color: transparent;"
        )
        lbl_version.setAlignment(Qt.AlignCenter)

        ver_wrap = QFrame()
        ver_wrap.setStyleSheet("background-color: transparent;")
        ver_layout = QVBoxLayout(ver_wrap)
        ver_layout.setContentsMargins(0, 8, 0, 12)
        ver_layout.addWidget(lbl_version)
        layout.addWidget(ver_wrap)

        return sidebar

    def _build_workspace(self) -> QFrame:
        workspace = QFrame()
        workspace.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Topbar ---
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setStyleSheet(f"""
            QFrame#topbar {{
                background-color: {COLORS['card']};
                border-bottom: 1px solid {COLORS['border']};
                min-height: 58px;
                max-height: 58px;
            }}
        """)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(24, 0, 24, 0)
        topbar_layout.setSpacing(12)

        # Titre module
        self.lbl_module_titre = QLabel("MODULE EN COURS : TABLEAU DE BORD")
        self.lbl_module_titre.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['text']};"
            "background-color: transparent;"
        )

        topbar_layout.addWidget(self.lbl_module_titre)
        topbar_layout.addStretch()

        # Sélecteur année scolaire
        lbl_annee = QLabel("Année Académique :")
        lbl_annee.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 12px; font-weight: 500;"
            "background-color: transparent;"
        )

        self.cmb_annee_header = QComboBox()
        self.cmb_annee_header.setFixedWidth(140)
        self.cmb_annee_header.setStyleSheet(COMBO_STYLE)

        self.load_annees_in_header()
        self.cmb_annee_header.currentIndexChanged.connect(self.on_annee_header_changed)

        topbar_layout.addWidget(lbl_annee)
        topbar_layout.addWidget(self.cmb_annee_header)

        # Séparateur vertical
        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setFixedHeight(22)
        sep_v.setStyleSheet(f"color: {COLORS['border']}; margin: 0 4px;")
        topbar_layout.addWidget(sep_v)

        # Bouton sélection imprimante
        btn_imprimante = QPushButton("Imprimante")
        btn_imprimante.setStyleSheet(BUTTON_SECONDARY)
        btn_imprimante.setFixedHeight(34)
        btn_imprimante.setMinimumWidth(110)
        btn_imprimante.setToolTip("Choisir l'imprimante par défaut pour les reçus")
        btn_imprimante.clicked.connect(self._open_printer_dialog)
        topbar_layout.addWidget(btn_imprimante)

        layout.addWidget(topbar)

        # --- Stack des modules ---
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg']};")

        # index 0: Tableau de bord
        self.widget_dashboard = DashboardView(self)
        self.stack.addWidget(self.widget_dashboard)

        # index 1: Paramètres
        self.widget_parametres = QWidget()
        self.widget_parametres.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.setup_parametres_tab()
        self.stack.addWidget(self.widget_parametres)

        # index 2: Scolarité
        self.widget_scolarite = ScolariteView(self)
        self.stack.addWidget(self.widget_scolarite)

        # index 3: Kiosque
        self.widget_kiosque = KiosqueView(self)
        self.stack.addWidget(self.widget_kiosque)

        # index 4: Comptabilité
        self.widget_comptabilite = ComptabiliteView(self)
        self.stack.addWidget(self.widget_comptabilite)

        # index 5: Statistiques
        self.widget_statistiques = StatistiquesView(self)
        self.stack.addWidget(self.widget_statistiques)

        # index 6: SMS placeholder
        self.widget_sms = SMSPlaceholderWidget(self)
        self.stack.addWidget(self.widget_sms)

        # index 7: Utilisateurs
        self.widget_utilisateurs = UtilisateursView(self)
        self.stack.addWidget(self.widget_utilisateurs)

        # index 8: Internat
        self.widget_internat = InternatView(self)
        self.stack.addWidget(self.widget_internat)

        # index 9: Cantine externe
        self.widget_cantine_externe = CantineExterneView(self)
        self.stack.addWidget(self.widget_cantine_externe)

        layout.addWidget(self.stack)
        return workspace

    # =========================================================================
    # SETUP PARAMÈTRES
    # =========================================================================

    def setup_parametres_tab(self):
        layout_param_base = QVBoxLayout(self.widget_parametres)
        layout_param_base.setContentsMargins(16, 16, 16, 16)

        self.tab_parametres_onglets = QTabWidget()
        self.tab_parametres_onglets.setStyleSheet(TAB_STYLE)

        # Onglet 1 : Généraux
        tab_generaux = QTabWidget()
        tab_generaux.setTabPosition(QTabWidget.West)
        tab_generaux.setStyleSheet(TAB_STYLE)
        tab_generaux.addTab(EtablissementView(), "Établissement")

        self.annee_view = AnneeScolaireView()
        self.annee_view.data_changed.connect(self.reload_annee_header)
        tab_generaux.addTab(self.annee_view, "Année Scolaire")

        self.backup_view = BackupView()
        tab_generaux.addTab(self.backup_view, "Sauvegardes")

        support_lbl = QLabel(
            "Support Technique :\nContactez Julien Kanga au 01-xx-xx-xx-xx."
        )
        support_lbl.setAlignment(Qt.AlignCenter)
        support_lbl.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 13px; padding: 30px;"
        )
        tab_generaux.addTab(support_lbl, "Support Technique")
        tab_generaux.currentChanged.connect(self.refresh_active_view)

        # Onglet 2 : Classes
        tab_classes = QTabWidget()
        tab_classes.setTabPosition(QTabWidget.West)
        tab_classes.setStyleSheet(TAB_STYLE)
        tab_classes.addTab(CycleView(), "Cycle")
        tab_classes.addTab(NiveauView(), "Niveau")
        tab_classes.addTab(ClasseView(), "Classe")
        tab_classes.currentChanged.connect(self.refresh_active_view)

        # Onglet 4 : Autres réglages
        tab_autres = QTabWidget()
        tab_autres.setTabPosition(QTabWidget.West)
        tab_autres.setStyleSheet(TAB_STYLE)
        tab_autres.addTab(NationaliteView(), "Nationalités")
        tab_autres.addTab(ReligionView(), "Religions")
        tab_autres.currentChanged.connect(self.refresh_active_view)

        self.tab_parametres_onglets.addTab(tab_generaux, "Généraux")
        self.tab_parametres_onglets.addTab(tab_classes, "Classes")
        self.tab_parametres_onglets.addTab(tab_autres, "Autres réglages")
        self.tab_parametres_onglets.currentChanged.connect(self.refresh_active_view)

        layout_param_base.addWidget(self.tab_parametres_onglets)

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def navigation_menu_changed(self, index):
        """Active l'écran correspondant selon le menu latéral sélectionné."""
        item = self.menu_list.item(index)
        orig = item.data(Qt.UserRole) if item else index

        titles = {
            0: "TABLEAU DE BORD",
            1: "SCOLARITÉ / INSCRIPTIONS",
            2: "KIOSQUE & BIBLIOTHÈQUE" if Config.ENABLE_BIBLIOTHEQUE else "KIOSQUE",
            3: "COMPTABILITÉ FINANCIÈRE",
            4: "STATISTIQUES ET RAPPORTS",
            5: "SMS  ·  BIENTÔT",
            6: "PARAMÈTRES",
            7: "GESTION DES UTILISATEURS",
            8: "INTERNAT FILLES D’ATTINGUIÉ",
            9: "CANTINE",
        }
        label = titles.get(orig, "")
        primary_color = COLORS["primary"]
        self.lbl_module_titre.setText(
            f"MODULE EN COURS :  <span style='color:{primary_color};'>{label}</span>"
        )
        self.lbl_module_titre.setTextFormat(Qt.RichText)

        if orig == 0:
            if hasattr(self.widget_dashboard, "refresh_data"):
                self.widget_dashboard.refresh_data()
            self.stack.setCurrentIndex(0)
        elif orig == 6:
            self.stack.setCurrentIndex(1)
        elif orig == 1:
            if hasattr(self.widget_scolarite, "on_sub_tab_changed"):
                self.widget_scolarite.on_sub_tab_changed(
                    self.widget_scolarite.sub_tabs.currentIndex()
                )
            self.stack.setCurrentIndex(2)
        elif orig == 2:
            if hasattr(self.widget_kiosque, "load_data"):
                self.widget_kiosque.load_data()
            self.stack.setCurrentIndex(3)
        elif orig == 3:
            if hasattr(self.widget_comptabilite, "load_data"):
                self.widget_comptabilite.load_data()
            self.stack.setCurrentIndex(4)
        elif orig == 4:
            if hasattr(self.widget_statistiques, "refresh_data"):
                self.widget_statistiques.refresh_data()
            self.stack.setCurrentIndex(5)
        elif orig == 5:
            self.stack.setCurrentIndex(6)
        elif orig == 7:
            if hasattr(self.widget_utilisateurs, "refresh_data"):
                self.widget_utilisateurs.refresh_data()
            self.stack.setCurrentIndex(7)
        elif orig == 8:
            self.widget_internat.refresh_data()
            self.stack.setCurrentIndex(8)
        elif orig == 9:
            self.widget_cantine_externe.refresh_data()
            self.stack.setCurrentIndex(9)

    def _open_printer_dialog(self):
        from views.imprimante_dialog import ImprimanteDialog
        dlg = ImprimanteDialog(self)
        dlg.exec()

    def reload_annee_header(self):
        """Recharge le sélecteur d'année scolaire après création ou clôture."""
        self.load_annees_in_header()
        self.refresh_active_view()

    def close_active_tab(self):
        """Revient au tableau de bord (index 0)."""
        self.menu_list.setCurrentRow(0)

    def refresh_active_view(self, index=None):
        """Actualise la vue active dans Paramètres."""
        curr_widget = self.tab_parametres_onglets.currentWidget()
        if isinstance(curr_widget, QTabWidget):
            active_view = curr_widget.currentWidget()
        else:
            active_view = curr_widget

        if active_view and hasattr(active_view, "refresh_data"):
            try:
                active_view.refresh_data()
            except Exception as e:
                print(f"Erreur rafraîchissement vue {active_view} : {e}")

    # =========================================================================
    # ANNÉE SCOLAIRE HEADER
    # =========================================================================

    def load_annees_in_header(self):
        from services.annee_scolaire_service import AnneeScolaireService
        from app.session import AppSession

        AppSession.initialize_session()

        annees = AnneeScolaireService.get_all()
        display_list = [a for a in annees if not a.Cloturer]
        if not display_list:
            AppSession._active_annee_id = None
            AppSession._active_annee_libelle = None
            AppSession.initialize_session()
            annees = AnneeScolaireService.get_all()
            display_list = [a for a in annees if not a.Cloturer]

        self.cmb_annee_header.blockSignals(True)
        self.cmb_annee_header.clear()

        for annee in display_list:
            self.cmb_annee_header.addItem(annee.Libelle, annee.IDTAnneeScolaire)

        active_id = AppSession.get_active_annee_id()
        idx = self.cmb_annee_header.findData(active_id)
        if idx >= 0:
            self.cmb_annee_header.setCurrentIndex(idx)
        elif self.cmb_annee_header.count() > 0:
            self.cmb_annee_header.setCurrentIndex(0)
            current_id = self.cmb_annee_header.currentData()
            current_libelle = self.cmb_annee_header.currentText()
            AppSession.set_active_annee(current_id, current_libelle)

        self.cmb_annee_header.blockSignals(False)

    def on_annee_header_changed(self, index=None):
        from app.session import AppSession
        current_id = self.cmb_annee_header.currentData()
        current_libelle = self.cmb_annee_header.currentText()
        if current_id:
            AppSession.set_active_annee(current_id, current_libelle)

            curr_idx = self.stack.currentIndex()
            if curr_idx == 1:
                self.refresh_active_view()
            elif curr_idx == 2:
                if hasattr(self.widget_scolarite, "on_sub_tab_changed"):
                    self.widget_scolarite.on_sub_tab_changed(
                        self.widget_scolarite.sub_tabs.currentIndex()
                    )
            elif curr_idx == 3:
                if hasattr(self.widget_kiosque, "load_data"):
                    self.widget_kiosque.load_data()
            elif curr_idx == 4:
                if hasattr(self.widget_comptabilite, "load_data"):
                    self.widget_comptabilite.load_data()
            elif curr_idx == 8:
                self.widget_internat.refresh_data()
