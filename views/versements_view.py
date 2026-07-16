from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from app.styles import COLORS, TAB_STYLE_NESTED
from app.config import Config
from views.caisse_view import CaisseView
from views.montant_scolarite_view import MontantScolariteView
from views.montant_transport_view import MontantTransportView
from views.montant_cantine_view import MontantCantineView
from views.autres_frais_view import AutresFraisView


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
        self.view_autres_frais  = AutresFraisView(self.main_window)
        # Vues instanciees seulement si leur module est actif (sinon on
        # construirait une UI pour rien : cf. audit P2-06).
        self.view_transport = MontantTransportView(self.main_window) if Config.ENABLE_TRANSPORT else None
        self.view_cantine = MontantCantineView(self.main_window) if Config.ENABLE_CANTINE else None

        self.tabs.addTab(self.view_caisse,       "Caisse")
        self.tabs.addTab(self.view_scolarite,    "Scolarité")
        if Config.ENABLE_TRANSPORT:
            self.tabs.addTab(self.view_transport, "Transport")
        if Config.ENABLE_CANTINE:
            self.tabs.addTab(self.view_cantine,   "Cantine")
        self.tabs.addTab(self.view_autres_frais, "Autres Frais")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget is self.view_caisse:
            widget.load_eleves()
        elif widget in (self.view_scolarite, self.view_transport, self.view_cantine):
            widget.load_montants()
        elif widget is self.view_autres_frais:
            widget.load_data()

    def refresh_data(self):
        self.on_tab_changed(self.tabs.currentIndex())
