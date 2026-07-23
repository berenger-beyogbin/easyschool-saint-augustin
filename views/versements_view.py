from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from app.styles import COLORS, TAB_STYLE_NESTED
from views.caisse_view import CaisseView
from views.montant_scolarite_view import MontantScolariteView
from views.montant_transport_view import MontantTransportView
from views.montant_cantine_view import MontantCantineView
from views.echeancier_view import EcheancierView


class VersementsView(QWidget):
    """Sous-module VERSEMENTS — Caisse, Scolarité, Transport, Cantine."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE_NESTED)

        self.view_caisse        = CaisseView(self.main_window)
        self.view_scolarite     = MontantScolariteView(self.main_window)
        self.view_transport     = MontantTransportView(self.main_window)
        self.view_cantine       = MontantCantineView(self.main_window)
        self.view_echeanciers   = EcheancierView(self.main_window)

        self.tabs.addTab(self.view_caisse,       "Caisse")
        self.tabs.addTab(self.view_scolarite,    "Scolarité")
        self.tabs.addTab(self.view_transport,    "Transport")
        self.tabs.addTab(self.view_cantine,      "Cantine")
        self.tabs.addTab(self.view_echeanciers,  "Échéanciers")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        if index == 0:
            self.view_caisse.load_eleves()
        elif index == 1:
            self.view_scolarite.load_montants()
        elif index == 2:
            self.view_transport.load_montants()
        elif index == 3:
            self.view_cantine.load_montants()
        elif index == 4:
            self.view_echeanciers.load_data()

    def refresh_data(self):
        self.on_tab_changed(self.tabs.currentIndex())
