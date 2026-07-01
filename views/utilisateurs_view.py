from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QTabWidget, QDialog, QFormLayout, QComboBox, QCheckBox,
    QScrollArea, QFrame, QMessageBox, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.styles import (
    COLORS, TAB_STYLE, INPUT_STYLE, COMBO_STYLE,
    BUTTON_PRIMARY, BUTTON_DANGER, BUTTON_WARNING, BUTTON_SUCCESS,
    MESSAGEBOX_STYLE, apply_table_style, configure_button,
    make_title_label, make_section_label
)


# ===========================================================================
# Dialogue : Formulaire Utilisateur
# ===========================================================================

class UtilisateurFormDialog(QDialog):
    """Dialogue de création / modification d'un utilisateur."""

    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user  # None = création, objet = modification
        self.setWindowTitle("Nouvel utilisateur" if not user else "Modifier l'utilisateur")
        self.setMinimumWidth(460)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        layout.addWidget(make_title_label(
            "Nouvel utilisateur" if not self.user else "Modifier l'utilisateur"
        ))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_login = QLineEdit()
        self.f_login.setStyleSheet(INPUT_STYLE)
        self.f_login.setFixedHeight(36)

        self.f_nom = QLineEdit()
        self.f_nom.setStyleSheet(INPUT_STYLE)
        self.f_nom.setFixedHeight(36)

        self.f_prenoms = QLineEdit()
        self.f_prenoms.setStyleSheet(INPUT_STYLE)
        self.f_prenoms.setFixedHeight(36)

        self.f_email = QLineEdit()
        self.f_email.setStyleSheet(INPUT_STYLE)
        self.f_email.setFixedHeight(36)

        self.f_profil = QComboBox()
        self.f_profil.setStyleSheet(COMBO_STYLE)
        self.f_profil.setFixedHeight(36)
        self._load_profils()

        self.f_pwd = QLineEdit()
        self.f_pwd.setEchoMode(QLineEdit.Password)
        self.f_pwd.setStyleSheet(INPUT_STYLE)
        self.f_pwd.setFixedHeight(36)
        pwd_hint = "" if not self.user else "Laisser vide pour conserver le mot de passe actuel"
        if pwd_hint:
            self.f_pwd.setPlaceholderText(pwd_hint)

        self.f_pwd_confirm = QLineEdit()
        self.f_pwd_confirm.setEchoMode(QLineEdit.Password)
        self.f_pwd_confirm.setStyleSheet(INPUT_STYLE)
        self.f_pwd_confirm.setFixedHeight(36)
        if pwd_hint:
            self.f_pwd_confirm.setPlaceholderText(pwd_hint)

        self.f_actif = QCheckBox("Compte actif")
        self.f_actif.setChecked(True)
        self.f_actif.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px;")

        form.addRow("Login *", self.f_login)
        form.addRow("Nom *", self.f_nom)
        form.addRow("Prénoms", self.f_prenoms)
        form.addRow("Email", self.f_email)
        form.addRow("Profil *", self.f_profil)
        form.addRow("Mot de passe" + (" *" if not self.user else ""), self.f_pwd)
        form.addRow("Confirmer", self.f_pwd_confirm)
        form.addRow("", self.f_actif)
        layout.addLayout(form)

        # Pré-remplissage en mode modification
        if self.user:
            self.f_login.setText(self.user.Login or "")
            self.f_nom.setText(self.user.Nom or "")
            self.f_prenoms.setText(self.user.Prenoms or "")
            self.f_email.setText(self.user.Email or "")
            self.f_actif.setChecked(self.user.IsActive)
            # Sélectionner le profil
            idx = self.f_profil.findData(self.user.IDProfil)
            if idx >= 0:
                self.f_profil.setCurrentIndex(idx)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Annuler")
        configure_button(btn_cancel, "secondary", fixed_height=38, min_width=100)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Enregistrer")
        configure_button(btn_ok, "primary", fixed_height=38, min_width=120)
        btn_ok.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _load_profils(self):
        from services.profil_service import ProfilService
        for p in ProfilService.get_all():
            self.f_profil.addItem(p.Libelle, p.IDProfil)

    def _on_save(self):
        from services.utilisateur_service import UtilisateurService
        pwd = self.f_pwd.text().strip()
        pwd2 = self.f_pwd_confirm.text().strip()
        if pwd and pwd != pwd2:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        data = {
            "Login": self.f_login.text().strip(),
            "Nom": self.f_nom.text().strip(),
            "Prenoms": self.f_prenoms.text().strip(),
            "Email": self.f_email.text().strip(),
            "IDProfil": self.f_profil.currentData(),
            "Password": pwd,
            "IsActive": self.f_actif.isChecked(),
        }
        if self.user:
            ok, msg = UtilisateurService.update(self.user.IDUtilisateur, data)
        else:
            ok, msg = UtilisateurService.create(data)

        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", msg)


# ===========================================================================
# Dialogue : Formulaire Profil
# ===========================================================================

class ProfilFormDialog(QDialog):
    """Dialogue de création / modification d'un profil."""

    def __init__(self, profil=None, parent=None):
        super().__init__(parent)
        self.profil = profil
        self.setWindowTitle("Nouveau profil" if not profil else "Modifier le profil")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        layout.addWidget(make_title_label(
            "Nouveau profil" if not self.profil else "Modifier le profil"
        ))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_code = QLineEdit()
        self.f_code.setStyleSheet(INPUT_STYLE)
        self.f_code.setFixedHeight(36)
        self.f_code.setMaxLength(20)
        self.f_code.textChanged.connect(lambda t: self.f_code.setText(t.upper()))

        self.f_libelle = QLineEdit()
        self.f_libelle.setStyleSheet(INPUT_STYLE)
        self.f_libelle.setFixedHeight(36)

        self.f_desc = QLineEdit()
        self.f_desc.setStyleSheet(INPUT_STYLE)
        self.f_desc.setFixedHeight(36)

        self.f_admin = QCheckBox("Super-administrateur (accès total sans restriction)")
        self.f_admin.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px;")

        form.addRow("Code *", self.f_code)
        form.addRow("Libellé *", self.f_libelle)
        form.addRow("Description", self.f_desc)
        form.addRow("", self.f_admin)
        layout.addLayout(form)

        if self.profil:
            self.f_code.setText(self.profil.Code or "")
            self.f_libelle.setText(self.profil.Libelle or "")
            self.f_desc.setText(self.profil.Description or "")
            self.f_admin.setChecked(self.profil.IsAdmin)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Annuler")
        configure_button(btn_cancel, "secondary", fixed_height=38, min_width=100)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Enregistrer")
        configure_button(btn_ok, "primary", fixed_height=38, min_width=120)
        btn_ok.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _on_save(self):
        from services.profil_service import ProfilService
        data = {
            "Code": self.f_code.text().strip(),
            "Libelle": self.f_libelle.text().strip(),
            "Description": self.f_desc.text().strip(),
            "IsAdmin": self.f_admin.isChecked(),
        }
        if self.profil:
            ok, msg = ProfilService.update(self.profil.IDProfil, data)
        else:
            ok, msg = ProfilService.create(data)

        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", msg)


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


# ===========================================================================
# Onglet 3 : Administration des droits par profil
# ===========================================================================

class _DroitsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}  # code → checkbox
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # En-tête : sélecteur de profil + bouton enregistrer
        top = QHBoxLayout()
        lbl = QLabel("Profil sélectionné :")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: 600;")
        self.cmb_profil = QComboBox()
        self.cmb_profil.setStyleSheet(COMBO_STYLE)
        self.cmb_profil.setFixedHeight(36)
        self.cmb_profil.setMinimumWidth(220)
        self._load_profils_combo()
        self.cmb_profil.currentIndexChanged.connect(self._on_profil_changed)

        self.btn_save = QPushButton("Enregistrer les droits")
        configure_button(self.btn_save, "success", fixed_height=36, min_width=160)
        self.btn_save.clicked.connect(self._on_save)

        top.addWidget(lbl)
        top.addWidget(self.cmb_profil)
        top.addSpacing(16)
        top.addWidget(self.btn_save)
        top.addStretch()
        layout.addLayout(top)

        # Note pour les super-admins
        self.lbl_admin_note = QLabel(
            "⚑  Ce profil est Super-administrateur : il dispose automatiquement de tous les droits."
        )
        self.lbl_admin_note.setStyleSheet(
            f"color: {COLORS['danger']}; font-size: 12px; font-weight: 600;"
            "background-color: transparent; padding: 4px 0;"
        )
        self.lbl_admin_note.setVisible(False)
        layout.addWidget(self.lbl_admin_note)

        # Zone scrollable : matrice des permissions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1px solid {COLORS['border']}; border-radius: 8px; }}")

        self.matrix_widget = QWidget()
        self.matrix_widget.setStyleSheet(f"background-color: {COLORS['card']};")
        self.matrix_layout = QVBoxLayout(self.matrix_widget)
        self.matrix_layout.setContentsMargins(20, 16, 20, 16)
        self.matrix_layout.setSpacing(0)

        scroll.setWidget(self.matrix_widget)
        layout.addWidget(scroll, 1)

        self._build_matrix()
        self._on_profil_changed()

    def _load_profils_combo(self):
        from services.profil_service import ProfilService
        self.cmb_profil.blockSignals(True)
        self.cmb_profil.clear()
        for p in ProfilService.get_all():
            self.cmb_profil.addItem(p.Libelle, p.IDProfil)
        self.cmb_profil.blockSignals(False)

    def _build_matrix(self):
        from services.permission_service import PermissionService
        # Vider la matrice actuelle
        while self.matrix_layout.count():
            item = self.matrix_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        by_module = PermissionService.get_by_module()
        first = True
        for module, perms in by_module.items():
            if not first:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet(f"color: {COLORS['border']}; margin: 6px 0;")
                self.matrix_layout.addWidget(sep)
            first = False

            # En-tête du module
            lbl_mod = QLabel(f"  {module}")
            lbl_mod.setStyleSheet(
                f"color: {COLORS['primary_dark']}; font-size: 13px; font-weight: 700;"
                f"background-color: {COLORS['bg']}; border-radius: 4px; padding: 6px 10px;"
                "margin: 4px 0;"
            )
            self.matrix_layout.addWidget(lbl_mod)

            # Permissions du module
            for perm in perms:
                row_widget = QWidget()
                row_widget.setStyleSheet("background-color: transparent;")
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(20, 2, 8, 2)
                row_layout.setSpacing(12)

                cb = QCheckBox(perm.Libelle)
                cb.setStyleSheet(
                    f"QCheckBox {{ color: {COLORS['text']}; font-size: 13px; }}"
                    f"QCheckBox::indicator {{"
                    f"  width: 18px; height: 18px;"
                    f"  border: 2px solid {COLORS['input_border']};"
                    f"  border-radius: 4px;"
                    f"  background-color: {COLORS['surface']};"
                    f"}}"
                    f"QCheckBox::indicator:checked {{"
                    f"  background-color: {COLORS['primary']};"
                    f"  border-color: {COLORS['primary']};"
                    f"}}"
                    f"QCheckBox::indicator:hover {{"
                    f"  border-color: {COLORS['primary']};"
                    f"}}"
                )
                cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self._checkboxes[perm.Code] = cb

                lbl_code = QLabel(f"[{perm.Code}]")
                lbl_code.setStyleSheet(
                    f"color: {COLORS['muted']}; font-size: 11px; font-family: monospace;"
                )
                lbl_code.setFixedWidth(220)

                row_layout.addWidget(cb, 1)
                row_layout.addWidget(lbl_code)
                self.matrix_layout.addWidget(row_widget)

        self.matrix_layout.addStretch()

    def load_data(self):
        self._load_profils_combo()
        self._build_matrix()
        self._on_profil_changed()

    def _on_profil_changed(self):
        from services.profil_service import ProfilService
        id_profil = self.cmb_profil.currentData()
        if not id_profil:
            return

        profil = ProfilService.get_by_id(id_profil)
        is_admin = profil.IsAdmin if profil else False

        self.lbl_admin_note.setVisible(is_admin)
        granted = ProfilService.get_profil_permissions(id_profil)

        for code, cb in self._checkboxes.items():
            cb.setChecked(code in granted or is_admin)
            cb.setEnabled(not is_admin)

    def _on_save(self):
        from services.profil_service import ProfilService
        id_profil = self.cmb_profil.currentData()
        if not id_profil:
            return
        profil = ProfilService.get_by_id(id_profil)
        if profil and profil.IsAdmin:
            QMessageBox.information(
                self, "Super-admin",
                "Les super-administrateurs disposent de tous les droits automatiquement.\n"
                "Aucune modification n'est nécessaire."
            )
            return
        codes = {code for code, cb in self._checkboxes.items() if cb.isChecked()}
        ok, msg = ProfilService.set_profil_permissions(id_profil, codes)
        if ok:
            QMessageBox.information(self, "Succès", msg)
        else:
            QMessageBox.warning(self, "Erreur", msg)


# ===========================================================================
# Vue principale : Hub Utilisateurs
# ===========================================================================

class UtilisateursView(QWidget):
    """Module de gestion des utilisateurs, profils et droits d'accès."""

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.tab_users = _UsersTab()
        self.tab_profils = _ProfilsTab()
        self.tab_droits = _DroitsTab()

        self.tabs.addTab(self.tab_users, "Utilisateurs")
        self.tabs.addTab(self.tab_profils, "Profils")
        self.tabs.addTab(self.tab_droits, "Administration des droits")

        from app.session import AppSession
        can_modify = AppSession.has_permission("UTILISATEURS_MODIFIER")
        self.tabs.setTabVisible(1, can_modify)
        self.tabs.setTabVisible(2, can_modify)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.tab_users.load_data()
        elif index == 1:
            self.tab_profils.load_data()
        elif index == 2:
            self.tab_droits.load_data()

    def refresh_data(self):
        """Appelé lors de la navigation vers ce module."""
        current = self.tabs.currentIndex()
        self._on_tab_changed(current)
