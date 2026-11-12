from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from app.styles import COLORS, TAB_STYLE
from app.config import Config
from app.session import AppSession

from views.stat_inscrits_view import StatInscritsView
from views.stat_nouveaux_view import StatNouveauxView
from views.stat_scolarite_view import StatScolariteView
from views.stat_cantine_externe_view import StatCantineExterneView
from views.stat_transport_view import StatTransportView
from views.stat_vente_view import StatVenteView
from views.stat_stock_view import StatStockView
from views.stat_internat_view import StatInternatView
from views.liste_alphabetique_view import ListeAlphabetiqueView
from views.stat_liste_pensionnaires_view import StatListeCantineExterneView, StatListeInternatView
from views.stat_periodique_view import StatPeriodiqueView


class StatistiquesView(QWidget):
    """Module STATISTIQUES — 8 rapports : inscrits, nouveaux, scolarité, etc."""

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
        self.view_vente        = StatVenteView(self.main_window)
        self.view_stock        = StatStockView(self.main_window)
        self.view_internat     = StatInternatView(self.main_window)
        self.view_alphabetique = ListeAlphabetiqueView(self.main_window)
        self.view_periodique   = StatPeriodiqueView(self.main_window)
        # Vues instanciees seulement si leur module est actif (sinon on
        # construirait une UI pour rien : cf. audit P2-06).
        self.view_cantine = StatCantineExterneView(self.main_window)
        self.view_liste_internat = StatListeInternatView(self.main_window)
        self.view_liste_cantine = StatListeCantineExterneView(self.main_window)
        self.view_transport = StatTransportView(self.main_window) if Config.ENABLE_TRANSPORT else None

        self.tabs.addTab(self.view_inscrits,     "Inscrits")
        self.tabs.addTab(self.view_nouveaux,     "Nouveaux")
        self.tabs.addTab(self.view_scolarite,    "Scolarité")
        self.tabs.addTab(self.view_internat,     "Internat")
        self.tabs.addTab(self.view_cantine,   "Cantine")
        self.tabs.addTab(self.view_liste_internat, "Liste Internat")
        self.tabs.addTab(self.view_liste_cantine,  "Liste Cantine")
        if Config.ENABLE_TRANSPORT:
            self.tabs.addTab(self.view_transport, "Transport")
        self.tabs.addTab(self.view_vente,        "Vente")
        self.tabs.addTab(self.view_stock,        "Stock")
        self.tabs.addTab(self.view_alphabetique, "Liste Alphabétique")
        self.tabs.addTab(self.view_periodique,   "État Périodique")

        # Filtrage droits par rapport — avant connexion signal, pour éviter
        # les chargements parasites (même pattern que ScolariteView).
        permission_par_vue = {
            self.view_inscrits:     "STAT_INSCRITS_VIEW",
            self.view_nouveaux:     "STAT_NOUVEAUX_VIEW",
            self.view_scolarite:    "STAT_SCOLARITE_VIEW",
            self.view_internat:     "STAT_INTERNAT_VIEW",
            self.view_cantine:      "STAT_CANTINE_VIEW",
            self.view_liste_internat: "STAT_LISTE_INTERNAT_VIEW",
            self.view_liste_cantine:  "STAT_LISTE_CANTINE_VIEW",
            self.view_transport:    "STAT_TRANSPORT_VIEW",
            self.view_vente:        "STAT_VENTE_VIEW",
            self.view_stock:        "STAT_STOCK_VIEW",
            self.view_alphabetique: "STAT_ALPHABETIQUE_VIEW",
            self.view_periodique:   "STAT_PERIODIQUE_VIEW",
        }
        for index in range(self.tabs.count()):
            code = permission_par_vue[self.tabs.widget(index)]
            self.tabs.setTabVisible(index, AppSession.has_permission(code))

        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget and hasattr(widget, "refresh_data"):
            widget.refresh_data()

    def refresh_data(self):
        self.on_tab_changed(self.tabs.currentIndex())
