import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from services.statistiques_service import StatistiquesService
from utils.list_printer import PeriodiqueStatPrinter
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    DATE_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS,
    apply_table_style, make_totaux_panel_widget,
)


class StatPeriodiqueView(QWidget):
    """État récapitulatif des encaissements par rubrique sur une période choisie."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        titre = QLabel("État Périodique des Encaissements")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        lbl_section = QLabel("Récapitulatif des encaissements par rubrique sur une période")
        lbl_section.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(lbl_section)

        lbl_style = f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"

        layout_filtres = QHBoxLayout()
        layout_filtres.setSpacing(10)

        lbl_debut = QLabel("Date du :")
        lbl_debut.setStyleSheet(lbl_style)
        self.dte_debut = QDateEdit()
        self.dte_debut.setCalendarPopup(True)
        self.dte_debut.setDisplayFormat("dd/MM/yyyy")
        curr_year = QDate.currentDate().year()
        self.dte_debut.setDate(QDate(curr_year - 1, 9, 1))
        self.dte_debut.setStyleSheet(DATE_STYLE)

        lbl_fin = QLabel("Date au :")
        lbl_fin.setStyleSheet(lbl_style)
        self.dte_fin = QDateEdit()
        self.dte_fin.setCalendarPopup(True)
        self.dte_fin.setDisplayFormat("dd/MM/yyyy")
        self.dte_fin.setDate(QDate.currentDate())
        self.dte_fin.setStyleSheet(DATE_STYLE)

        self.btn_afficher = QPushButton("Afficher")
        self.btn_afficher.setStyleSheet(BUTTON_PRIMARY)
        self.btn_afficher.clicked.connect(self.refresh_data)

        self.btn_imprimer = QPushButton("Imprimer")
        self.btn_imprimer.setStyleSheet(BUTTON_SUCCESS)
        self.btn_imprimer.clicked.connect(self.imprimer_clic)

        layout_filtres.addWidget(lbl_debut)
        layout_filtres.addWidget(self.dte_debut)
        layout_filtres.addWidget(lbl_fin)
        layout_filtres.addWidget(self.dte_fin)
        layout_filtres.addWidget(self.btn_afficher)
        layout_filtres.addWidget(self.btn_imprimer)
        layout_filtres.addStretch()

        layout.addLayout(layout_filtres)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Rubrique", "Montant encaissé"])
        apply_table_style(self.table, alternate="yellow")

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        self.totaux_panel, (self.lbl_tot_general,) = make_totaux_panel_widget([
            ("Total général encaissé", COLORS['primary']),
        ])
        layout.addWidget(self.totaux_panel)

    def _get_periode(self):
        q_start = self.dte_debut.date()
        q_end = self.dte_fin.date()
        start_date = datetime.date(q_start.year(), q_start.month(), q_start.day())
        end_date = datetime.date(q_end.year(), q_end.month(), q_end.day())
        return start_date, end_date

    def refresh_data(self):
        start_date, end_date = self._get_periode()
        data = StatistiquesService.get_etat_periodique(start_date, end_date)

        self.table.setRowCount(0)
        self.table.setRowCount(len(data))

        total_general = 0.0

        for idx, item in enumerate(data):
            montant = item["Montant"]
            total_general += montant

            it_rubrique = QTableWidgetItem(item["Rubrique"])

            it_montant = QTableWidgetItem(StatistiquesService.format_fcfa(montant))
            it_montant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(idx, 0, it_rubrique)
            self.table.setItem(idx, 1, it_montant)

        self.lbl_tot_general.setText(StatistiquesService.format_fcfa(total_general))

    def imprimer_clic(self):
        start_date, end_date = self._get_periode()
        data = StatistiquesService.get_etat_periodique(start_date, end_date)
        if not data:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return

        PeriodiqueStatPrinter.print_report(self, data, start_date, end_date)
