from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from app.styles import BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_SUCCESS, TABLE_STYLE
from services.eleve_import_service import EleveImportService


class EleveImportDialog(QDialog):
    """Aperçu, simulation et lancement contrôlé d'un import Excel d'élèves."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.setWindowTitle("Importer des élèves depuis Excel")
        self.resize(1250, 720)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Sélectionnez le fichier Excel. Les lignes invalides ou en double seront exclues. "
            "Les élèves seront créés sans famille et sans inscription."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        actions = QHBoxLayout()
        self.btn_file = QPushButton("Choisir le fichier Excel")
        self.btn_file.setStyleSheet(BUTTON_PRIMARY)
        self.btn_file.clicked.connect(self.choose_file)
        self.lbl_summary = QLabel("Aucun fichier sélectionné")
        actions.addWidget(self.btn_file)
        actions.addWidget(self.lbl_summary, 1)
        layout.addLayout(actions)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Ligne", "Code", "Matricule national", "Identité source", "Nom", "Prénoms",
            "Naissance", "Sexe", "LV2", "Résultat", "Messages",
        ])
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        cancel = QPushButton("Fermer")
        cancel.setStyleSheet(BUTTON_SECONDARY)
        cancel.clicked.connect(self.reject)
        self.btn_import = QPushButton("Importer les lignes valides")
        self.btn_import.setStyleSheet(BUTTON_SUCCESS)
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.run_import)
        footer.addWidget(cancel)
        footer.addWidget(self.btn_import)
        layout.addLayout(footer)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir le fichier des élèves", "", "Excel (*.xlsx)")
        if not path:
            return
        try:
            self.rows = EleveImportService.simulate(EleveImportService.read_xlsx(path))
        except Exception as exc:
            QMessageBox.critical(self, "Import impossible", str(exc))
            return
        self._populate()

    def _populate(self):
        self.table.setRowCount(len(self.rows))
        for index, row in enumerate(self.rows):
            values = [
                row.excel_row, row.code_externe, row.matricule_national or "", row.identite_originale,
                row.nom, row.prenoms, row.date_naissance.strftime("%d/%m/%Y") if row.date_naissance else "",
                "M" if row.sexe == 1 else "F" if row.sexe == 2 else "", row.deuxieme_langue or "",
                row.action, " | ".join(row.errors + row.warnings),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column not in {4, 5}:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(index, column, item)
        summary = EleveImportService.summary(self.rows)
        valid = summary.get("A_CREER", 0)
        self.lbl_summary.setText(
            f"{summary.get('total', 0)} lignes — {valid} à créer — "
            f"{summary.get('DOUBLON', 0)} doublons — {summary.get('INVALIDE', 0)} invalides — "
            f"{summary.get('DEJA_IMPORTE', 0)} déjà importées"
        )
        self.btn_import.setEnabled(valid > 0)
        self.table.resizeColumnsToContents()

    def _apply_name_edits(self):
        for index, row in enumerate(self.rows):
            row.nom = self.table.item(index, 4).text().strip().upper()
            row.prenoms = self.table.item(index, 5).text().strip().upper()
            if not row.nom or not row.prenoms:
                if "Nom ou prénoms vide" not in row.errors:
                    row.errors.append("Nom ou prénoms vide")
                row.action = "INVALIDE"

    def run_import(self):
        self._apply_name_edits()
        valid = sum(row.valide for row in self.rows)
        if not valid:
            QMessageBox.warning(self, "Import", "Aucune ligne valide à importer.")
            return
        answer = QMessageBox.question(
            self,
            "Confirmer l'import",
            f"Créer {valid} élèves sans famille et sans inscription ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            EleveImportService.import_rows(self.rows)
            report = Path("reports") / f"import_eleves_{datetime.now():%Y%m%d_%H%M%S}.csv"
            EleveImportService.export_report(self.rows, str(report))
        except Exception as exc:
            QMessageBox.critical(self, "Échec de l'import", str(exc))
            return
        self._populate()
        QMessageBox.information(
            self, "Import terminé",
            f"{sum(row.action == 'CREE' for row in self.rows)} élèves créés.\nRapport : {report.resolve()}",
        )
        self.accept()
