from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from app.styles import COLORS, INPUT_STYLE, COMBO_STYLE, configure_button, make_title_label


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
