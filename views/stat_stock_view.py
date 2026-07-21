from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from services.statistiques_service import StatistiquesService
from utils.list_printer import StockStatPrinter
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    INPUT_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS,
    apply_table_style, make_totaux_panel_widget
)


class StatStockView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.raw_data = []
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        titre = QLabel("État du Stock Kiosque")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        lbl_section = QLabel("État du stock en temps réel")
        lbl_section.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(lbl_section)

        lbl_style = f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"

        layout_filtres = QHBoxLayout()
        layout_filtres.setSpacing(10)

        lbl_recherche = QLabel("Rechercher un article :")
        lbl_recherche.setStyleSheet(lbl_style)

        self.txt_recherche = QLineEdit()
        self.txt_recherche.setStyleSheet(INPUT_STYLE)
        self.txt_recherche.setPlaceholderText("Saisissez un libellé d'article...")
        self.txt_recherche.setMinimumWidth(220)
        self.txt_recherche.textChanged.connect(self.filter_articles)

        self.btn_afficher = QPushButton("Afficher")
        self.btn_afficher.setStyleSheet(BUTTON_PRIMARY)
        self.btn_afficher.clicked.connect(self.refresh_data)

        self.btn_imprimer = QPushButton("Imprimer")
        self.btn_imprimer.setStyleSheet(BUTTON_SUCCESS)
        self.btn_imprimer.clicked.connect(self.imprimer_clic)

        layout_filtres.addWidget(lbl_recherche)
        layout_filtres.addWidget(self.txt_recherche)
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
            "Article", "Prix de Vente Unitaire", "Seuil d'Alerte", "Stock Courant", "État"
        ])
        apply_table_style(self.table, alternate="yellow")

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        self.totaux_panel, (self.lbl_tot_valeur,) = make_totaux_panel_widget([
            ("Valeur globale valorisée", COLORS['primary']),
        ])
        layout.addWidget(self.totaux_panel)

    def refresh_data(self):
        self.raw_data = StatistiquesService.get_etat_stock()
        self.filter_articles()

    def filter_articles(self):
        search_txt = self.txt_recherche.text().strip().lower()

        filtered = [
            item for item in self.raw_data
            if not search_txt or search_txt in item["Libelle"].lower()
        ]

        self.table.setRowCount(0)
        self.table.setRowCount(len(filtered))

        val_total = 0.0

        for idx, item in enumerate(filtered):
            val_total += item["ValeurStock"]

            lib = item["Libelle"] or ""
            if item["KIT"]:
                lib += " (KIT)"
            pu = StatistiquesService.format_fcfa(item["PU"])
            seuil = str(item["QTESeuil"])
            qty = str(item["QuantiteCour"])
            etat = item["Etat"]

            it_art = QTableWidgetItem(lib)

            it_pu = QTableWidgetItem(pu)
            it_pu.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_seuil = QTableWidgetItem(seuil)
            it_seuil.setTextAlignment(Qt.AlignCenter)

            it_qty = QTableWidgetItem(qty)
            it_qty.setTextAlignment(Qt.AlignCenter)

            it_etat = QTableWidgetItem(etat)
            it_etat.setTextAlignment(Qt.AlignCenter)
            if etat == "Rupture":
                it_etat.setForeground(QColor(COLORS["danger"]))
                it_etat.setFont(QFont("", weight=QFont.Bold))
            elif etat == "Alerte":
                it_etat.setForeground(QColor(COLORS["warning"]))
                it_etat.setFont(QFont("", weight=QFont.Bold))
            else:
                it_etat.setForeground(QColor(COLORS["success"]))

            self.table.setItem(idx, 0, it_art)
            self.table.setItem(idx, 1, it_pu)
            self.table.setItem(idx, 2, it_seuil)
            self.table.setItem(idx, 3, it_qty)
            self.table.setItem(idx, 4, it_etat)

        self.lbl_tot_valeur.setText(StatistiquesService.format_fcfa(val_total))

    def imprimer_clic(self):
        search_txt = self.txt_recherche.text().strip()
        data = [
            item for item in self.raw_data
            if not search_txt or search_txt.lower() in item["Libelle"].lower()
        ]
        if not data:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return

        filtre = search_txt if search_txt else ""
        StockStatPrinter.print_report(self, data, filtre)
