from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from views.compte_view import CompteView
from views.enregistrement_mouvement_view import EnregistrementMouvementView
from views.etat_sorties_view import EtatSortiesView
from views.balance_comptes_view import BalanceComptesView
from app.styles import COLORS, TAB_STYLE
from views.ui_components import make_module_header


class ComptabiliteView(QWidget):
    """Module COMPTABILITÉ — Enregistrements, Sorties, Comptes, Balance."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.view_enregistrements = EnregistrementMouvementView(self)
        self.view_etat_sorties = EtatSortiesView(self)
        self.view_creer_compte = CompteView(self)
        self.view_balance = BalanceComptesView(self)

        self.tabs.addTab(self.view_enregistrements, "Enregistrements")
        self.tabs.addTab(self.view_etat_sorties, "État des Sorties")
        self.tabs.addTab(self.view_creer_compte, "Créer un compte")
        self.tabs.addTab(self.view_balance, "Balance des Comptes")

        from app.session import AppSession
        can_saisie = AppSession.has_permission("COMPTABILITE_SAISIE")
        self.tabs.setTabVisible(0, can_saisie)
        self.tabs.setTabVisible(2, can_saisie)

        layout_principal.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.tab_changed)

    def tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget == self.view_enregistrements:
            self.view_enregistrements.load_comptes()
            self.view_enregistrements.load_data()
        elif widget == self.view_etat_sorties:
            self.view_etat_sorties.load_comptes_filter()
            self.view_etat_sorties.load_data()
        elif widget == self.view_creer_compte:
            self.view_creer_compte.load_data()
        elif widget == self.view_balance:
            self.view_balance.load_data()

    def load_data(self):
        from app.session import AppSession
        can_saisie = AppSession.has_permission("COMPTABILITE_SAISIE")
        if can_saisie:
            self.view_enregistrements.load_comptes()
            self.view_enregistrements.load_data()
        self.view_etat_sorties.load_comptes_filter()
        self.view_etat_sorties.load_data()
        if can_saisie:
            self.view_creer_compte.load_data()
        self.view_balance.load_data()
