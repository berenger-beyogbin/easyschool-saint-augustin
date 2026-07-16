from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.styles import COLORS


class PasswordChangeDialog(QDialog):
    """Dialogue minimal de changement obligatoire du mot de passe."""

    def __init__(self, user_id: int, old_password: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.old_password = old_password
        self.setWindowTitle("Changement de mot de passe requis")
        self.setFixedSize(420, 300)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['sidebar_bg']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 24)
        layout.setSpacing(12)

        title = QLabel("Choisissez un nouveau mot de passe")
        title.setStyleSheet("color: #FFFFFF; font-size: 17px; font-weight: bold; background-color: transparent;")
        layout.addWidget(title)

        hint = QLabel("Il doit contenir au moins 8 caractères, avec une lettre et un chiffre.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 12px; background-color: transparent;")
        layout.addWidget(hint)

        field_style = """
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 0 12px;
            }
            QLineEdit:focus { border: 1px solid #2563EB; }
        """

        self.field_new_pwd = QLineEdit()
        self.field_new_pwd.setEchoMode(QLineEdit.Password)
        self.field_new_pwd.setPlaceholderText("Nouveau mot de passe")
        self.field_new_pwd.setFixedHeight(42)
        self.field_new_pwd.setStyleSheet(field_style)
        layout.addWidget(self.field_new_pwd)

        self.field_confirm_pwd = QLineEdit()
        self.field_confirm_pwd.setEchoMode(QLineEdit.Password)
        self.field_confirm_pwd.setPlaceholderText("Confirmer le mot de passe")
        self.field_confirm_pwd.setFixedHeight(42)
        self.field_confirm_pwd.setStyleSheet(field_style)
        layout.addWidget(self.field_confirm_pwd)

        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setMinimumHeight(18)
        self.lbl_error.setStyleSheet("color: #F87171; font-size: 12px; background-color: transparent;")
        layout.addWidget(self.lbl_error)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                font-weight: bold;
                border-radius: 8px;
                padding: 0 18px;
            }}
            QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
        """)
        self.btn_save.clicked.connect(self._save)
        buttons.addWidget(self.btn_save)
        layout.addLayout(buttons)

        self.field_new_pwd.returnPressed.connect(self._save)
        self.field_confirm_pwd.returnPressed.connect(self._save)
        self.field_new_pwd.setFocus()

    def _save(self):
        from services.utilisateur_service import UtilisateurService

        new_password = self.field_new_pwd.text()
        confirm_password = self.field_confirm_pwd.text()
        if new_password != confirm_password:
            self.lbl_error.setText("Les deux mots de passe ne correspondent pas.")
            return

        ok, msg = UtilisateurService.change_password(self.user_id, self.old_password, new_password)
        if ok:
            self.accept()
        else:
            self.lbl_error.setText(msg)


class LoginDialog(QDialog):
    """Écran de connexion affiché au démarrage de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Easy School 2.0 — Connexion")
        self.setFixedSize(440, 530)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.authenticated_user_data: dict | None = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['sidebar_bg']};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- En-tête ---
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['sidebar_bg_2']};
                border-bottom: 1px solid rgba(255,255,255,0.07);
            }}
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(40, 36, 40, 28)
        h_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        lbl_app = QLabel("Easy School")
        lbl_app.setStyleSheet(
            "color: #FFFFFF; font-size: 22px; font-weight: bold; background-color: transparent;"
        )
        lbl_ver = QLabel("2.0")
        lbl_ver.setFixedHeight(22)
        lbl_ver.setStyleSheet(
            f"color: #FFFFFF; background-color: {COLORS['primary']};"
            "font-size: 11px; font-weight: bold; border-radius: 5px; padding: 2px 8px;"
        )
        title_row.addWidget(lbl_app)
        title_row.addWidget(lbl_ver, 0, Qt.AlignVCenter)
        title_row.addStretch()
        h_layout.addLayout(title_row)

        sub = QLabel("Gestion d'École Professionnelle")
        sub.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px; background-color: transparent;")
        h_layout.addWidget(sub)
        root.addWidget(header)

        # --- Formulaire ---
        form = QFrame()
        form.setStyleSheet(f"background-color: {COLORS['sidebar_bg']}; border: none;")
        f_layout = QVBoxLayout(form)
        f_layout.setContentsMargins(40, 32, 40, 32)
        f_layout.setSpacing(0)

        lbl_conn = QLabel("Connexion")
        lbl_conn.setStyleSheet(
            "color: #FFFFFF; font-size: 20px; font-weight: bold; background-color: transparent;"
        )
        f_layout.addWidget(lbl_conn)
        f_layout.addSpacing(4)

        lbl_hint = QLabel("Entrez vos identifiants pour accéder à l'application.")
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px; background-color: transparent;")
        f_layout.addWidget(lbl_hint)
        f_layout.addSpacing(28)

        _field_style = """
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 0 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: rgba(255,255,255,0.12);
            }
            QLineEdit::placeholder { color: rgba(255,255,255,0.3); }
        """

        f_layout.addWidget(self._make_field_label("Identifiant"))
        f_layout.addSpacing(5)
        self.field_login = QLineEdit()
        self.field_login.setPlaceholderText("Votre identifiant")
        self.field_login.setFixedHeight(46)
        self.field_login.setStyleSheet(_field_style)
        f_layout.addWidget(self.field_login)
        f_layout.addSpacing(16)

        f_layout.addWidget(self._make_field_label("Mot de passe"))
        f_layout.addSpacing(5)
        self.field_pwd = QLineEdit()
        self.field_pwd.setPlaceholderText("Votre mot de passe")
        self.field_pwd.setEchoMode(QLineEdit.Password)
        self.field_pwd.setFixedHeight(46)
        self.field_pwd.setStyleSheet(_field_style)
        f_layout.addWidget(self.field_pwd)
        f_layout.addSpacing(10)

        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setMinimumHeight(18)
        self.lbl_error.setStyleSheet(
            "color: #F87171; font-size: 12px; background-color: transparent;"
        )
        f_layout.addWidget(self.lbl_error)
        f_layout.addSpacing(20)

        self.btn_login = QPushButton("Se connecter")
        self.btn_login.setFixedHeight(48)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
            QPushButton:disabled {{ background-color: rgba(37,99,235,0.4); }}
        """)
        self.btn_login.clicked.connect(self._do_login)
        f_layout.addWidget(self.btn_login)
        f_layout.addStretch()

        root.addWidget(form, 1)

        # Validation sur Entrée
        self.field_login.returnPressed.connect(self._do_login)
        self.field_pwd.returnPressed.connect(self._do_login)
        self.field_login.setFocus()

    @staticmethod
    def _make_field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #94A3B8; font-size: 12px; font-weight: 600; background-color: transparent;"
        )
        return lbl

    def _do_login(self):
        from services.utilisateur_service import UtilisateurService

        login = self.field_login.text().strip()
        password = self.field_pwd.text()

        if not login or not password:
            self.lbl_error.setText("Veuillez renseigner l'identifiant et le mot de passe.")
            return

        self.lbl_error.setText("")
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Connexion en cours…")

        ok, msg, user_data = UtilisateurService.authenticate(login, password)

        if ok:
            if user_data and user_data.get("MustChangePassword"):
                change_dialog = PasswordChangeDialog(user_data["IDUtilisateur"], password, self)
                if change_dialog.exec() != QDialog.Accepted:
                    self.lbl_error.setText("Le changement du mot de passe est requis pour continuer.")
                    self.btn_login.setEnabled(True)
                    self.btn_login.setText("Se connecter")
                    self.field_pwd.clear()
                    self.field_pwd.setFocus()
                    return
                user_data["MustChangePassword"] = False
            self.authenticated_user_data = user_data
            self.accept()
        else:
            self.lbl_error.setText(msg)
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Se connecter")
            self.field_pwd.clear()
            self.field_pwd.setFocus()
