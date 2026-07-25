from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from app.styles import COLORS, TAB_STYLE
from ._users_tab import _UsersTab
from ._profils_tab import _ProfilsTab
from ._droits_tab import _DroitsTab


# ===========================================================================
# Vue principale : Hub Utilisateurs
# ===========================================================================

class UtilisateursView(QWidget):
    """Module de gestion des utilisateurs, profils et droits d'accès."""

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.tab_users = _UsersTab()
        self.tab_profils = _ProfilsTab()
        self.tab_droits = _DroitsTab()

        self.tabs.addTab(self.tab_users, "Utilisateurs")
        self.tabs.addTab(self.tab_profils, "Profils")
        self.tabs.addTab(self.tab_droits, "Administration des droits")

        from app.session import AppSession
        can_modify = AppSession.has_permission("UTILISATEURS_MODIFIER")
        self.tabs.setTabVisible(1, can_modify)
        self.tabs.setTabVisible(2, can_modify)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.tab_users.load_data()
        elif index == 1:
            self.tab_profils.load_data()
        elif index == 2:
            self.tab_droits.load_data()

    def refresh_data(self):
        """Appelé lors de la navigation vers ce module."""
        current = self.tabs.currentIndex()
        self._on_tab_changed(current)
