import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from services.compte_service import CompteService
from services.comptabilite_service import ComptabiliteService
from app.session import AppSession
from app.styles import (
    COLORS, DATE_STYLE, COMBO_STYLE, BUTTON_PRIMARY,
    GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE, apply_table_style
)

class EtatSortiesView(QWidget):
    """
    Vue Etat des Sorties - Affiche et filtre uniquement les mouvements DEBIT (dépenses).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.comptes_list = []
        self.init_ui()
        self.load_comptes_filter()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Zone de Filtres
        group_filter = QGroupBox("Recherche & Filtres de l'État des Sorties")
        group_filter.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        filter_layout = QHBoxLayout(group_filter)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)

        lbl_style = f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"

        # Filtre Compte
        lbl_compte = QLabel("Compte :")
        lbl_compte.setStyleSheet(lbl_style)
        self.combo_filter_compte = QComboBox()
        self.combo_filter_compte.setStyleSheet(COMBO_STYLE)
        filter_layout.addWidget(lbl_compte)
        filter_layout.addWidget(self.combo_filter_compte, 2)

        # Date Début
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

        # Tableau des Sorties
        group_table = QGroupBox("Mouvements de Sortie d'Argent (Débits)")
        group_table.setStyleSheet(GROUPBOX_STYLE)
        table_layout = QVBoxLayout(group_table)
        table_layout.setContentsMargins(15, 15, 15, 15)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Bénéficiaire", "Téléphone", "Montant", "Compte"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        apply_table_style(self.table)
        table_layout.addWidget(self.table)

        # Totalisateur en bas de tableau
        row_total = QHBoxLayout()
        row_total.addStretch()
        self.lbl_total = QLabel("Total Général des Sorties : 0 FCFA")
        self.lbl_total.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {COLORS['danger']};"
            "background-color: transparent; margin-top: 5px;"
        )
        row_total.addWidget(self.lbl_total)
        table_layout.addLayout(row_total)

        layout.addWidget(group_table, 1)

    def load_comptes_filter(self):
        """Remplit le filtre de sélection de comptes."""
        self.combo_filter_compte.clear()
        self.comptes_list = CompteService.get_all_comptes()
        self.combo_filter_compte.addItem("--- Tous les comptes ---", None)
        for c in self.comptes_list:
            self.combo_filter_compte.addItem(f"{c.NumCompte} - {c.LibCompte}", c.IDCompte)

    def load_data(self):
        self.table.setRowCount(0)
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        compte_id = self.combo_filter_compte.currentData()
        date_deb = self.txt_date_debut.date().toPython()
        date_fn = self.txt_date_fin.date().toPython()

        rows = ComptabiliteService.get_etat_sorties(
            id_annee=active_annee_id,
            id_compte=compte_id,
            date_debut=date_deb,
            date_fin=date_fn
        )

        total_sorties = 0.0

        for i, item in enumerate(rows):
            self.table.insertRow(i)

            total_sorties += float(item.Montant)

            date_str = item.DateSortie.strftime("%d/%m/%Y") if item.DateSortie else ""
            compte_str = f"{item.compte.NumCompte} - {item.compte.LibCompte}" if item.compte else str(item.IDCompte)
            tel_str = item.NumBenef or "N/A"

            item_date = QTableWidgetItem(date_str)
            item_benef = QTableWidgetItem(item.Benef)
            item_tel = QTableWidgetItem(tel_str)
            item_montant = QTableWidgetItem(self.format_fcfa(item.Montant))
            item_compte = QTableWidgetItem(compte_str)

            item_montant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(i, 0, item_date)
            self.table.setItem(i, 1, item_benef)
            self.table.setItem(i, 2, item_tel)
            self.table.setItem(i, 3, item_montant)
            self.table.setItem(i, 4, item_compte)

        self.lbl_total.setText(f"Total Général des Sorties : {self.format_fcfa(total_sorties)}")

    def format_fcfa(self, montant) -> str:
        try:
            val = int(float(montant))
            return f"{val:,}".replace(",", " ") + " FCFA"
        except Exception:
            return f"{montant} FCFA"
