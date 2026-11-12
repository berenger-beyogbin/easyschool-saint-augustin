from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.styles import COLORS, apply_table_style, configure_button
from ._dialogs import ProfilFormDialog


# ===========================================================================
# Onglet 2 : Gestion des profils
# ===========================================================================

class _ProfilsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        bar.addStretch()

        self.btn_new = QPushButton("+ Nouveau profil")
        configure_button(self.btn_new, "primary", fixed_height=36, min_width=130)
        self.btn_new.clicked.connect(self._on_new)

        self.btn_edit = QPushButton("Modifier")
        configure_button(self.btn_edit, "secondary", fixed_height=36, min_width=100)
        self.btn_edit.clicked.connect(self._on_edit)

        self.btn_del = QPushButton("Supprimer")
        configure_button(self.btn_del, "danger", fixed_height=36, min_width=100)
        self.btn_del.clicked.connect(self._on_delete)

        for btn in (self.btn_new, self.btn_edit, self.btn_del):
            bar.addWidget(btn)
        layout.addLayout(bar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Code", "Libellé", "Description", "Admin / Utilisateurs"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(4, 200)
        apply_table_style(self.table)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        from services.profil_service import ProfilService
        self.table.setRowCount(0)
        for p in ProfilService.get_all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            nb_users = ProfilService.count_users(p.IDProfil)
            admin_label = "⚑ Super-admin" if p.IsAdmin else f"{nb_users} utilisateur(s)"
            vals = [str(p.IDProfil), p.Code, p.Libelle, p.Description or "", admin_label]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 4 and p.IsAdmin:
                    item.setForeground(QColor(COLORS["danger"]))
                self.table.setItem(row, col, item)

    def _selected_profil(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        id_item = self.table.item(row, 0)
        if not id_item:
            return None
        from services.profil_service import ProfilService
        return ProfilService.get_by_id(int(id_item.text()))

    def _on_new(self):
        dlg = ProfilFormDialog(parent=self)
        if dlg.exec():
            self.load_data()

    def _on_edit(self):
        profil = self._selected_profil()
        if not profil:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner un profil.")
            return
        dlg = ProfilFormDialog(profil=profil, parent=self)
        if dlg.exec():
            self.load_data()

    def _on_delete(self):
        profil = self._selected_profil()
        if not profil:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner un profil.")
            return
        rep = QMessageBox.question(
            self, "Confirmation",
            f"Supprimer le profil '{profil.Libelle}' ?\nSes permissions seront également supprimées.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if rep != QMessageBox.Yes:
            return
        from services.profil_service import ProfilService
        ok, msg = ProfilService.delete(profil.IDProfil)
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.load_data()
        else:
            QMessageBox.warning(self, "Erreur", msg)
