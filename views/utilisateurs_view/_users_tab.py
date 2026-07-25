from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.styles import COLORS, INPUT_STYLE, apply_table_style, configure_button
from ._dialogs import UtilisateurFormDialog


# ===========================================================================
# Onglet 1 : Gestion des utilisateurs
# ===========================================================================

class _UsersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Barre d'outils
        bar = QHBoxLayout()
        self.f_search = QLineEdit()
        self.f_search.setPlaceholderText("Rechercher par nom, login ou profil…")
        self.f_search.setFixedHeight(36)
        self.f_search.setStyleSheet(INPUT_STYLE)
        self.f_search.textChanged.connect(self._filter)
        bar.addWidget(self.f_search, 1)
        bar.addSpacing(12)

        self.btn_new = QPushButton("+ Nouveau")
        configure_button(self.btn_new, "primary", fixed_height=36, min_width=110)
        self.btn_new.clicked.connect(self._on_new)

        self.btn_edit = QPushButton("Modifier")
        configure_button(self.btn_edit, "secondary", fixed_height=36, min_width=100)
        self.btn_edit.clicked.connect(self._on_edit)

        self.btn_toggle = QPushButton("Activer / Désact.")
        configure_button(self.btn_toggle, "warning", fixed_height=36, min_width=130)
        self.btn_toggle.clicked.connect(self._on_toggle)

        self.btn_del = QPushButton("Supprimer")
        configure_button(self.btn_del, "danger", fixed_height=36, min_width=100)
        self.btn_del.clicked.connect(self._on_delete)

        for btn in (self.btn_new, self.btn_edit, self.btn_toggle, self.btn_del):
            bar.addWidget(btn)

        from app.session import AppSession
        if not AppSession.has_permission("UTILISATEURS_MODIFIER"):
            for btn in (self.btn_new, self.btn_edit, self.btn_toggle, self.btn_del):
                btn.setVisible(False)

        layout.addLayout(bar)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Login", "Nom complet", "Profil", "Statut", "Dernier accès"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        apply_table_style(self.table)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        self._all_users = []
        self.load_data()

    def load_data(self):
        from services.utilisateur_service import UtilisateurService
        self._all_users = UtilisateurService.get_all()
        self._populate(self._all_users)

    def _populate(self, users):
        self.table.setRowCount(0)
        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            nom_complet = f"{u.Nom} {u.Prenoms or ''}".strip()
            profil_lib = u.profil.Libelle if u.profil else "—"
            statut = "Actif" if u.IsActive else "Désactivé"
            dernier_acces = (
                u.DernierAcces.strftime("%d/%m/%Y %H:%M") if u.DernierAcces else "Jamais"
            )
            vals = [str(u.IDUtilisateur), u.Login, nom_complet, profil_lib, statut, dernier_acces]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 4:
                    item.setForeground(
                        QColor(COLORS["success"]) if u.IsActive else QColor(COLORS["muted"])
                    )
                self.table.setItem(row, col, item)

    def _filter(self, text: str):
        txt = text.lower()
        filtered = [
            u for u in self._all_users
            if txt in u.Login.lower()
            or txt in u.Nom.lower()
            or txt in (u.Prenoms or "").lower()
            or txt in (u.profil.Libelle if u.profil else "").lower()
        ]
        self._populate(filtered)

    def _selected_user(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        id_item = self.table.item(row, 0)
        if not id_item:
            return None
        from services.utilisateur_service import UtilisateurService
        return UtilisateurService.get_by_id(int(id_item.text()))

    def _on_new(self):
        dlg = UtilisateurFormDialog(parent=self)
        if dlg.exec():
            self.load_data()

    def _on_edit(self):
        user = self._selected_user()
        if not user:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner un utilisateur.")
            return
        dlg = UtilisateurFormDialog(user=user, parent=self)
        if dlg.exec():
            self.load_data()

    def _on_toggle(self):
        user = self._selected_user()
        if not user:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner un utilisateur.")
            return
        from services.utilisateur_service import UtilisateurService
        ok, msg = UtilisateurService.toggle_active(user.IDUtilisateur)
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.load_data()
        else:
            QMessageBox.warning(self, "Erreur", msg)

    def _on_delete(self):
        user = self._selected_user()
        if not user:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner un utilisateur.")
            return
        rep = QMessageBox.question(
            self, "Confirmation",
            f"Supprimer l'utilisateur '{user.Login}' ?\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if rep != QMessageBox.Yes:
            return
        from services.utilisateur_service import UtilisateurService
        ok, msg = UtilisateurService.delete(user.IDUtilisateur)
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.load_data()
        else:
            QMessageBox.warning(self, "Erreur", msg)
