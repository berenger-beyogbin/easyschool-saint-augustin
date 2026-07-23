from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QInputDialog,
)

from app.session import AppSession
from app.styles import BUTTON_DANGER, BUTTON_PRIMARY, BUTTON_SECONDARY, apply_table_style
from services.stock_service import StockService
from utils.kiosque_ticket_printer import KiosqueTicketPrinter


class TicketJournalView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.reference = None
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Heure", "Référence", "Caissier", "Lignes", "Total", "Statut"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        apply_table_style(self.table)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.doubleClicked.connect(self.on_detail)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_actualiser = QPushButton("Actualiser")
        self.btn_actualiser.setStyleSheet(BUTTON_SECONDARY)
        self.btn_actualiser.clicked.connect(self.load_data)
        actions.addWidget(self.btn_actualiser)
        actions.addStretch()
        self.btn_detail = QPushButton("Voir / Imprimer")
        self.btn_detail.setStyleSheet(BUTTON_PRIMARY)
        self.btn_detail.clicked.connect(self.on_detail)
        self.btn_annuler = QPushButton("Annuler / Rembourser")
        self.btn_annuler.setStyleSheet(BUTTON_DANGER)
        self.btn_annuler.clicked.connect(self.on_annuler)
        actions.addWidget(self.btn_detail)
        actions.addWidget(self.btn_annuler)
        layout.addLayout(actions)
        self.load_data()

    def load_data(self):
        tickets = StockService.get_journal_tickets(AppSession.get_active_annee_id())
        self.table.setRowCount(len(tickets))
        for row, ticket in enumerate(tickets):
            values = [
                ticket["date"].strftime("%d/%m/%Y"), str(ticket["heure"])[:8],
                ticket["reference"], ticket["login"], str(ticket["lignes"]),
                f'{int(ticket["total"]):,} F', ticket["statut"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.UserRole, ticket["reference"])
                self.table.setItem(row, col, item)
        self.reference = None
        self._update_actions()

    def _selection_changed(self):
        row = self.table.currentRow()
        self.reference = self.table.item(row, 0).data(Qt.UserRole) if row >= 0 else None
        self._update_actions()

    def _update_actions(self):
        selected = bool(self.reference)
        self.btn_detail.setEnabled(selected)
        statut = self.table.item(self.table.currentRow(), 6).text() if selected else ""
        self.btn_annuler.setEnabled(
            selected and statut == "VALIDE" and AppSession.has_permission("KIOSQUE_REMBOURSEMENTS")
        )

    def on_detail(self):
        if self.reference:
            KiosqueTicketPrinter.print_ticket(self, StockService.get_ticket(self.reference))

    def on_annuler(self):
        if not self.reference:
            return
        motif, ok = QInputDialog.getMultiLineText(self, "Annulation du ticket", "Motif obligatoire :")
        if not ok:
            return
        success, msg = StockService.annuler_ticket(self.reference, motif)
        if success:
            QMessageBox.information(self, "Ticket annulé", msg)
            self.load_data()
            if self.main_window and hasattr(self.main_window, "load_data"):
                self.main_window.load_data()
        else:
            QMessageBox.critical(self, "Annulation refusée", msg)
