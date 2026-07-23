from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from views.dashboard_v2_view import DashboardV2View
from views.dashboard_view import DashboardView


class DashboardSwitcherView(QWidget):
    """Héberge la V2 et l'ancien écran afin de permettre un retour immédiat."""

    def __init__(self, main_window=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.stack = QStackedWidget()
        self.v2 = DashboardV2View(main_window)
        self.legacy = DashboardView(main_window)
        self.stack.addWidget(self.v2)
        self.stack.addWidget(self.legacy)
        layout.addWidget(self.stack)

    def show_legacy(self):
        self.legacy.refresh_data()
        self.stack.setCurrentWidget(self.legacy)

    def show_v2(self):
        self.v2.refresh_data()
        self.stack.setCurrentWidget(self.v2)

    def refresh_data(self):
        self.show_v2()
