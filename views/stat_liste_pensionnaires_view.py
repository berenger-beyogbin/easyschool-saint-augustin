from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHeaderView, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from app.styles import (
    BUTTON_PRIMARY, BUTTON_SUCCESS, COLORS, COMBO_STYLE, PAGE_TITLE_STYLE,
    SECTION_TITLE_STYLE, apply_table_style, make_totaux_panel_widget,
)
from services.statistiques_service import StatistiquesService
from utils.list_printer import CantineExterneListPrinter, InternatListPrinter


class _StatListePensionnairesView(QWidget):
    """Liste nominative des pensionnaires, sans aucun montant."""

    TITLE = ""
    SUBTITLE = ""
    COL_LAST = ""
    PRINTER = None
    WITH_ORIGIN = False

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._shown = []
        self._init_ui()
        self.refresh_data()

    def _load_rows(self):
        raise NotImplementedError

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel(self.TITLE)
        title.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(title)
        subtitle = QLabel(self.SUBTITLE)
        subtitle.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)
        self.origin_filter = QComboBox()
        self.origin_filter.setStyleSheet(COMBO_STYLE)
        if self.WITH_ORIGIN:
            label = QLabel("Origine :")
            label.setStyleSheet(f"font-size:12px;color:{COLORS['text_soft']};background:transparent;")
            self.origin_filter.addItem("Toutes les origines", "")
            self.origin_filter.addItem("Élèves du collège", "Collège")
            self.origin_filter.addItem("Pensionnaires externes", "Externe")
            filters.addWidget(label)
            filters.addWidget(self.origin_filter)
        display_button = QPushButton("Afficher")
        display_button.setStyleSheet(BUTTON_PRIMARY)
        display_button.clicked.connect(self.refresh_data)
        print_button = QPushButton("Imprimer")
        print_button.setStyleSheet(BUTTON_SUCCESS)
        print_button.clicked.connect(self._print)
        filters.addWidget(display_button)
        filters.addWidget(print_button)
        filters.addStretch()
        layout.addLayout(filters)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["N°", "Matricule", "Noms", self.COL_LAST])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        apply_table_style(self.table)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        self.totals_panel, (self.total_count,) = make_totaux_panel_widget([
            ("Effectif", COLORS["primary"]),
        ])
        layout.addWidget(self.totals_panel)

    def refresh_data(self):
        origin = self.origin_filter.currentData() if self.WITH_ORIGIN else ""
        rows = [r for r in self._load_rows() if not origin or r.get("Origine") == origin]
        self._shown = rows
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            values = [index + 1, row["Matricule"], row["Nom"].upper(), row["LibClasse"] or ""]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column in (0, 1):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(index, column, item)
        self.total_count.setText(str(len(rows)))

    def _print(self):
        if not self._shown:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return
        filtre = self.origin_filter.currentText() if self.WITH_ORIGIN and self.origin_filter.currentData() else ""
        self.PRINTER.print_list(self, self._shown, filtre)


class StatListeInternatView(_StatListePensionnairesView):
    TITLE = "Liste des Pensionnaires de l’Internat"
    SUBTITLE = "Liste nominative (sans montants)"
    COL_LAST = "Classe / origine"
    PRINTER = InternatListPrinter
    WITH_ORIGIN = True

    def _load_rows(self):
        return StatistiquesService.get_etat_versements_internat()


class StatListeCantineExterneView(_StatListePensionnairesView):
    TITLE = "Liste des Pensionnaires de la Cantine Externe"
    SUBTITLE = "Liste nominative (sans montants)"
    COL_LAST = "Responsable"
    PRINTER = CantineExterneListPrinter

    def _load_rows(self):
        return StatistiquesService.get_etat_versements_cantine_externe()
