import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QDateEdit, QMessageBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QDate
from services.comptabilite_service import ComptabiliteService
from services.compte_service import SYSCOA_INCOME_ACCOUNTS
from app.session import AppSession
from app.styles import (
    COLORS, DATE_STYLE, BUTTON_PRIMARY, BUTTON_SECONDARY,
    GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE, apply_table_style
)

class BalanceComptesView(QWidget):
    """
    Vue de Balance des Résultats - Calcule et affiche les débits, crédits et soldes par compte.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # Layout principal vertical
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Zone des Filtres : Période
        group_filter = QGroupBox("Sélection de la Période à Analyser")
        group_filter.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        filter_layout = QHBoxLayout(group_filter)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)

        # Date Début
        lbl_style = f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"
        lbl_debut = QLabel("Du :")
        lbl_debut.setStyleSheet(lbl_style)
        self.txt_date_debut = QDateEdit()
        self.txt_date_debut.setDisplayFormat("dd/MM/yyyy")
        self.txt_date_debut.setCalendarPopup(True)
        self.txt_date_debut.setDate(QDate.currentDate().addDays(-30))
        self.txt_date_debut.setStyleSheet(DATE_STYLE)
        filter_layout.addWidget(lbl_debut)
        filter_layout.addWidget(self.txt_date_debut, 1)

        # Date Fin
        lbl_fin = QLabel("Au :")
        lbl_fin.setStyleSheet(lbl_style)
        self.txt_date_fin = QDateEdit()
        self.txt_date_fin.setDisplayFormat("dd/MM/yyyy")
        self.txt_date_fin.setCalendarPopup(True)
        self.txt_date_fin.setDate(QDate.currentDate())
        self.txt_date_fin.setStyleSheet(DATE_STYLE)
        filter_layout.addWidget(lbl_fin)
        filter_layout.addWidget(self.txt_date_fin, 1)

        # Bouton Afficher
        self.btn_afficher = QPushButton("Afficher")
        self.btn_afficher.setStyleSheet(BUTTON_PRIMARY)
        self.btn_afficher.clicked.connect(self.load_data)
        filter_layout.addWidget(self.btn_afficher)

        layout.addWidget(group_filter)

        # Tableau Balance
        group_table = QGroupBox("Balance des Comptes")
        group_table.setStyleSheet(GROUPBOX_STYLE)
        table_layout = QVBoxLayout(group_table)
        table_layout.setContentsMargins(15, 15, 15, 15)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["N° Compte", "Compte", "Débit", "Crédit", "Solde (Crédit - Débit)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        apply_table_style(self.table)
        table_layout.addWidget(self.table)

        # Totaux Généraux
        row_totals = QHBoxLayout()
        row_totals.setSpacing(15)
        
        self.lbl_total_debit = QLabel("Total Débit : 0 FCFA")
        self.lbl_total_debit.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {COLORS['danger']}; background-color: transparent;"
        )
        row_totals.addWidget(self.lbl_total_debit)

        self.lbl_total_credit = QLabel("Total Crédit : 0 FCFA")
        self.lbl_total_credit.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {COLORS['success']}; background-color: transparent;"
        )
        row_totals.addWidget(self.lbl_total_credit)

        row_totals.addStretch()

        self.btn_imprimer = QPushButton("Imprimer")
        self.btn_imprimer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_imprimer.clicked.connect(self.print_placeholder)
        row_totals.addWidget(self.btn_imprimer)

        table_layout.addLayout(row_totals)
        layout.addWidget(group_table, 1)

    def load_data(self):
        self.table.setRowCount(0)
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        date_deb = self.txt_date_debut.date().toPython()
        date_fn = self.txt_date_fin.date().toPython()

        rows = ComptabiliteService.get_balance_comptes(
            id_annee=active_annee_id,
            date_debut=date_deb,
            date_fin=date_fn
        )

        sum_debit = 0.0
        sum_credit = 0.0

        for i, item in enumerate(rows):
            self.table.insertRow(i)

            sum_debit += item["Debit"]
            sum_credit += item["Credit"]

            item_num = QTableWidgetItem(item["NumCompte"])
            item_lib = QTableWidgetItem(item["LibCompte"])
            item_deb = QTableWidgetItem(self.format_fcfa(item["Debit"]))
            item_cred = QTableWidgetItem(self.format_fcfa(item["Credit"]))
            item_solde = QTableWidgetItem(self.format_fcfa(item["Solde"]))

            item_num.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item_lib.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item_deb.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_cred.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_solde.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            is_syscoa = item["NumCompte"] in SYSCOA_INCOME_ACCOUNTS
            bg_syscoa = QColor("#e8f5e9")

            if item["Solde"] < 0:
                item_solde.setForeground(QColor(COLORS["danger"]))
            elif item["Solde"] > 0:
                item_solde.setForeground(QColor(COLORS["success"]))
            else:
                item_solde.setForeground(QColor(COLORS["text"]))

            row_items = [item_num, item_lib, item_deb, item_cred, item_solde]
            for col, cell in enumerate(row_items):
                if is_syscoa:
                    cell.setBackground(bg_syscoa)
                self.table.setItem(i, col, cell)

        # Mettre à jour les totaux
        self.lbl_total_debit.setText(f"Total Débit : {self.format_fcfa(sum_debit)}")
        self.lbl_total_credit.setText(f"Total Crédit : {self.format_fcfa(sum_credit)}")

    def print_placeholder(self):
        """Action du bouton Imprimer."""
        QMessageBox.information(self, "Impression", "Impression à venir")

    def format_fcfa(self, montant) -> str:
        try:
            val = int(float(montant))
            return f"{val:,}".replace(",", " ") + " FCFA"
        except Exception:
            return f"{montant} FCFA"
