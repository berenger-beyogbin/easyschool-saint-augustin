from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QFrame
)
from PySide6.QtCore import Qt
from views.vente_view import VenteView
from views.approvisionnement_view import ApprovisionnementView
from views.article_list_view import ArticleListView
from views.ticket_journal_view import TicketJournalView
from app.styles import COLORS, TAB_STYLE, TAB_STYLE_NESTED
from views.ui_components import EmptyState


class KiosqueView(QWidget):
    """Module KIOSQUE — Ventes, Approvisionnement, Articles & KITs."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)


        # QTabWidget Principal (Kiosque / Bibliothèque)
        self.tab_principal = QTabWidget()
        self.tab_principal.setStyleSheet(TAB_STYLE)

        # ---- ONGLET 1 : KIOSQUE ----
        tab_kiosque_widget = QWidget()
        tab_kiosque_widget.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout_kiosque = QVBoxLayout(tab_kiosque_widget)
        layout_kiosque.setContentsMargins(12, 12, 12, 12)
        layout_kiosque.setSpacing(10)

        self.tab_sous_nav = QTabWidget()
        self.tab_sous_nav.setStyleSheet(TAB_STYLE_NESTED)

        self.view_vente = VenteView(self)
        self.view_approvis = ApprovisionnementView(self)
        self.view_articles = ArticleListView(self)
        self.view_tickets = TicketJournalView(self)

        self.tab_sous_nav.addTab(self.view_vente, "Vendre")
        self.tab_sous_nav.addTab(self.view_approvis, "Approvisionnement")
        self.tab_sous_nav.addTab(self.view_articles, "Articles & KITS")
        self.tab_sous_nav.addTab(self.view_tickets, "Journal des tickets")

        from app.session import AppSession
        self.tab_sous_nav.setTabVisible(0, AppSession.has_permission("KIOSQUE_VENTES"))
        self.tab_sous_nav.setTabVisible(1, AppSession.has_permission("KIOSQUE_STOCKS"))
        self.tab_sous_nav.setTabVisible(2, AppSession.has_permission("KIOSQUE_ARTICLES"))
        self.tab_sous_nav.setTabVisible(3, AppSession.has_permission("KIOSQUE_VENTES"))

        layout_kiosque.addWidget(self.tab_sous_nav)
        self.tab_principal.addTab(tab_kiosque_widget, "KIOSQUE")

        # ---- ONGLET 2 : BIBLIOTHÈQUE (Placeholder) ----
        tab_biblio_widget = QWidget()
        tab_biblio_widget.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout_biblio = QVBoxLayout(tab_biblio_widget)
        layout_biblio.setContentsMargins(20, 20, 20, 20)

        placeholder = EmptyState(
            icon="📚",
            title="SERVICE BIBLIOTHÈQUE",
            message="Module Bibliothèque à venir.\nCette fonctionnalité sera connectée ultérieurement."
        )
        layout_biblio.addWidget(placeholder)
        self.tab_principal.addTab(tab_biblio_widget, "BIBLIOTHÈQUE")

        layout_principal.addWidget(self.tab_principal)

    def show_welcome_screen(self):
        if self.main_window and hasattr(self.main_window, "close_active_tab"):
            self.main_window.close_active_tab()

    def load_data(self):
        from app.session import AppSession
        if AppSession.has_permission("KIOSQUE_VENTES"):
            self.view_vente.load_articles()
        if AppSession.has_permission("KIOSQUE_STOCKS"):
            self.view_approvis.load_combos()
            self.view_approvis.load_historique()
        if AppSession.has_permission("KIOSQUE_ARTICLES"):
            self.view_articles.load_data()
        if AppSession.has_permission("KIOSQUE_VENTES"):
            self.view_tickets.load_data()
