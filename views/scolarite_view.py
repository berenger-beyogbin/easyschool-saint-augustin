from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from app.styles import COLORS, TAB_STYLE, TAB_STYLE_NESTED
from views.eleve_list_view import EleveListView
from views.inscription_view import InscriptionView
from views.famille_list_view import FamilleListView
from views.versements_view import VersementsView


class ScolariteView(QWidget):
    """Module SCOLARITÉ — Inscriptions (élèves, inscription, parents) et Versements."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        from app.session import AppSession
        has_versements   = AppSession.has_permission("SCOLARITE_VERSEMENTS")
        has_inscriptions = AppSession.has_permission("SCOLARITE_INSCRIPTIONS")
        has_eleves       = AppSession.has_permission("SCOLARITE_ELEVES")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(TAB_STYLE)

        # ---- ONGLET 1 : Versements ----
        self.view_versements = VersementsView(self.main_window)
        self.main_tabs.addTab(self.view_versements, "Versements")

        # ---- ONGLET 2 : Inscriptions ----
        onglet_ins = QWidget()
        onglet_ins.setStyleSheet(f"background-color: {COLORS['bg']};")
        onglet_ins_layout = QVBoxLayout(onglet_ins)
        onglet_ins_layout.setContentsMargins(10, 10, 10, 10)
        onglet_ins_layout.setSpacing(10)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet(TAB_STYLE_NESTED)

        self.view_eleves      = EleveListView(self.main_window)
        self.view_inscription = InscriptionView(self.main_window)
        self.view_familles    = FamilleListView(self.main_window)

        self.sub_tabs.addTab(self.view_inscription, "Inscription")
        self.sub_tabs.addTab(self.view_eleves,      "Élèves")
        self.sub_tabs.addTab(self.view_familles,    "Liste des Parents")

        # Filtrage droits sous-onglets — avant connexion signal pour éviter les chargements parasites
        self.sub_tabs.setTabVisible(0, has_inscriptions)
        self.sub_tabs.setTabVisible(1, has_eleves)
        self.sub_tabs.setTabVisible(2, has_inscriptions or has_eleves)

        self.sub_tabs.currentChanged.connect(self.on_sub_tab_changed)
        onglet_ins_layout.addWidget(self.sub_tabs)
        self.main_tabs.addTab(onglet_ins, "Inscriptions")

        # Filtrage droits onglets principaux — avant connexion signal
        self.main_tabs.setTabVisible(0, has_versements)
        self.main_tabs.setTabVisible(1, has_inscriptions or has_eleves)

        self.main_tabs.currentChanged.connect(self.on_main_tab_changed)
        layout.addWidget(self.main_tabs)

    def on_main_tab_changed(self, index):
        if index == 0:
            self.view_versements.refresh_data()
        elif index == 1:
            self.on_sub_tab_changed(self.sub_tabs.currentIndex())

    def on_sub_tab_changed(self, index):
        if index == 0:
            self.view_inscription.load_responsables()
            self.view_inscription.load_niveaux()
        elif index == 1:
            self.view_eleves.load_data()
        elif index == 2:
            self.view_familles.load_data()
