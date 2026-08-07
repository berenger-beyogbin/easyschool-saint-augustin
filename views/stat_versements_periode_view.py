import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from services.statistiques_service import StatistiquesService
from utils.list_printer import VersementsPeriodiqueStatPrinter
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    DATE_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS,
    apply_table_style, make_totaux_panel_widget
)


class StatVersementsPeriodeView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        titre = QLabel("État Périodique des Versements")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        lbl_section = QLabel("Totaux journaliers scolarité / cantine / transport sur une période")
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Date", "Scolarité", "Cantine", "Transport", "Total"
        ])
        apply_table_style(self.table, alternate="yellow")

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        layout.addWidget(self.table)

        self.totaux_panel, (
            self.lbl_tot_scol,
            self.lbl_tot_cant,
            self.lbl_tot_trans,
            self.lbl_tot_general,
        ) = make_totaux_panel_widget([
            ("Total scolarité", COLORS['primary']),
            ("Total cantine",   COLORS['success']),
            ("Total transport", COLORS['warning']),
            ("Total général",   COLORS['purple']),
        ])
        layout.addWidget(self.totaux_panel)

    def _get_period(self):
        q_start = self.dte_debut.date()
        q_end = self.dte_fin.date()
        start_date = datetime.date(q_start.year(), q_start.month(), q_start.day())
        end_date = datetime.date(q_end.year(), q_end.month(), q_end.day())
        return start_date, end_date

    def refresh_data(self):
        start_date, end_date = self._get_period()
        data = StatistiquesService.get_etat_periodique_versements(start_date, end_date)

        self.table.setRowCount(0)
        self.table.setRowCount(len(data))

        sum_scol = 0.0
        sum_cant = 0.0
        sum_trans = 0.0
        sum_total = 0.0

        for idx, item in enumerate(data):
            sum_scol += item["Scolarite"]
            sum_cant += item["Cantine"]
            sum_trans += item["Transport"]
            sum_total += item["Total"]

            d = item["DateVers"].strftime("%d/%m/%Y") if item["DateVers"] else ""

            it_date = QTableWidgetItem(d)
            it_date.setTextAlignment(Qt.AlignCenter)

            it_scol = QTableWidgetItem(StatistiquesService.format_fcfa(item["Scolarite"]))
            it_scol.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_cant = QTableWidgetItem(StatistiquesService.format_fcfa(item["Cantine"]))
            it_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_trans = QTableWidgetItem(StatistiquesService.format_fcfa(item["Transport"]))
            it_trans.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_total = QTableWidgetItem(StatistiquesService.format_fcfa(item["Total"]))
            it_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(idx, 0, it_date)
            self.table.setItem(idx, 1, it_scol)
            self.table.setItem(idx, 2, it_cant)
            self.table.setItem(idx, 3, it_trans)
            self.table.setItem(idx, 4, it_total)

        self.lbl_tot_scol.setText(StatistiquesService.format_fcfa(sum_scol))
        self.lbl_tot_cant.setText(StatistiquesService.format_fcfa(sum_cant))
        self.lbl_tot_trans.setText(StatistiquesService.format_fcfa(sum_trans))
        self.lbl_tot_general.setText(StatistiquesService.format_fcfa(sum_total))

    def imprimer_clic(self):
        start_date, end_date = self._get_period()
        data = StatistiquesService.get_etat_periodique_versements(start_date, end_date)
        if not data:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return

        VersementsPeriodiqueStatPrinter.print_report(self, data, start_date, end_date)
