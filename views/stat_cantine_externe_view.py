from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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
from utils.list_printer import CantineExterneStatPrinter


class StatCantineExterneView(QWidget):
    """État financier des pensionnaires de la cantine externe."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._rows = []
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel("État des Versements de la Cantine Externe")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(title)
        subtitle = QLabel("Suivi des cotisations, encaissements et restes à recouvrer")
        subtitle.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)
        label_style = f"font-size:12px;color:{COLORS['text_soft']};background:transparent;"

        state_label = QLabel("État :")
        state_label.setStyleSheet(label_style)
        self.state_filter = QComboBox()
        self.state_filter.setStyleSheet(COMBO_STYLE)
        self.state_filter.addItem("Tous les états", "")
        self.state_filter.addItem("Soldés", "Payé")
        self.state_filter.addItem("Paiements partiels", "Partiel")
        self.state_filter.addItem("Impayés", "Impayé")

        display_button = QPushButton("Afficher")
        display_button.setStyleSheet(BUTTON_PRIMARY)
        display_button.clicked.connect(self._apply_filters)
        print_button = QPushButton("Imprimer")
        print_button.setStyleSheet(BUTTON_SUCCESS)
        print_button.clicked.connect(self._print)

        filters.addWidget(state_label)
        filters.addWidget(self.state_filter)
        filters.addWidget(display_button)
        filters.addWidget(print_button)
        filters.addStretch()
        layout.addLayout(filters)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "N°", "Matricule", "Pensionnaire", "Responsable",
            "Montant dû", "Montant versé", "Reste", "État",
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        apply_table_style(self.table, alternate="yellow")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for column in range(3, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        self.totals_panel, (
            self.total_count, self.total_due, self.total_paid, self.total_left,
        ) = make_totaux_panel_widget([
            ("Pensionnaires", COLORS["warning"]),
            ("Total attendu", COLORS["primary"]),
            ("Total encaissé", COLORS["success"]),
            ("Reste à recouvrer", COLORS["warning"]),
        ])
        layout.addWidget(self.totals_panel)

    def refresh_data(self):
        self._rows = StatistiquesService.get_etat_versements_cantine_externe()
        self._apply_filters()

    def _filtered_rows(self):
        state = self.state_filter.currentData()
        return [
            row for row in self._rows
            if (not state or row["Etat"] == state)
        ]

    def _apply_filters(self):
        rows = self._filtered_rows()
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            values = [
                index + 1, row["Matricule"], row["Nom"].upper(), row["LibClasse"],
                StatistiquesService.format_fcfa(row["MontantDu"]),
                StatistiquesService.format_fcfa(row["MontantVerse"]),
                StatistiquesService.format_fcfa(row["Reste"]), row["Etat"],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column in (0, 1, 7):
                    item.setTextAlignment(Qt.AlignCenter)
                elif column in (4, 5, 6):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if column == 7:
                    color = COLORS["success"] if row["Etat"] == "Payé" else (
                        COLORS["warning"] if row["Etat"] == "Partiel" else COLORS["danger"]
                    )
                    item.setForeground(QColor(color))
                self.table.setItem(index, column, item)

        self.total_count.setText(str(len(rows)))
        self.total_due.setText(StatistiquesService.format_fcfa(sum(r["MontantDu"] for r in rows)))
        self.total_paid.setText(StatistiquesService.format_fcfa(sum(r["MontantVerse"] for r in rows)))
        self.total_left.setText(StatistiquesService.format_fcfa(sum(r["Reste"] for r in rows)))

    def _print(self):
        rows = self._filtered_rows()
        if not rows:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return
        filters = [
            text for text, value in (
                (self.state_filter.currentText(), self.state_filter.currentData()),
            ) if value
        ]
        CantineExterneStatPrinter.print_report(self, rows, " — ".join(filters))
