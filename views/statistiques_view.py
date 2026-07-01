from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from app.styles import COLORS, TAB_STYLE
from views.ui_components import make_module_header

from views.stat_inscrits_view import StatInscritsView
from views.stat_nouveaux_view import StatNouveauxView
from views.stat_scolarite_view import StatScolariteView
from views.stat_cantine_view import StatCantineView
from views.stat_transport_view import StatTransportView
from views.stat_vente_view import StatVenteView
from views.stat_stock_view import StatStockView
from views.stat_prestataire_view import StatPrestatairesView
from views.liste_alphabetique_view import ListeAlphabetiqueView


class StatistiquesView(QWidget):
    """Module STATISTIQUES — 7 rapports : inscrits, nouveaux, scolarité, etc."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.view_inscrits     = StatInscritsView(self.main_window)
        self.view_nouveaux     = StatNouveauxView(self.main_window)
        self.view_scolarite    = StatScolariteView(self.main_window)
        self.view_cantine      = StatCantineView(self.main_window)
        self.view_transport    = StatTransportView(self.main_window)
        self.view_vente        = StatVenteView(self.main_window)
        self.view_stock        = StatStockView(self.main_window)
        self.view_prestataires = StatPrestatairesView(self.main_window)
        self.view_alphabetique = ListeAlphabetiqueView(self.main_window)

        self.tabs.addTab(self.view_inscrits,     "Inscrits")
        self.tabs.addTab(self.view_nouveaux,     "Nouveaux")
        self.tabs.addTab(self.view_scolarite,    "Scolarité")
        self.tabs.addTab(self.view_cantine,      "Cantine")
        self.tabs.addTab(self.view_transport,    "Transport")
        self.tabs.addTab(self.view_vente,        "Vente")
        self.tabs.addTab(self.view_stock,        "Stock")
        self.tabs.addTab(self.view_prestataires, "Prestataires")
        self.tabs.addTab(self.view_alphabetique, "Liste Alphabétique")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget and hasattr(widget, "refresh_data"):
            widget.refresh_data()

    def refresh_data(self):
        self.on_tab_changed(self.tabs.currentIndex())
