from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.styles import COLORS


class FirstRunSetupDialog(QDialog):
    """Affiche a la toute premiere ouverture de l'application (aucun utilisateur en base) :
    fait creer le premier compte administrateur avec un mot de passe choisi par l'utilisateur,
    au lieu d'un compte admin/admin123 auto-cree et imprime en console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Easy School 2.0 — Premiere configuration")
        self.setFixedSize(440, 620)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['sidebar_bg']};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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

        lbl_app = QLabel("Easy School 2.0")
        lbl_app.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold; background-color: transparent;")
        h_layout.addWidget(lbl_app)

        sub = QLabel("Premiere configuration : creez votre compte administrateur.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px; background-color: transparent;")
        h_layout.addWidget(sub)
        root.addWidget(header)

        form = QFrame()
        form.setStyleSheet(f"background-color: {COLORS['sidebar_bg']}; border: none;")
        f_layout = QVBoxLayout(form)
        f_layout.setContentsMargins(40, 32, 40, 32)
        f_layout.setSpacing(0)

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

        def add_field(label_text, placeholder, echo_password=False):
            f_layout.addWidget(self._make_field_label(label_text))
            f_layout.addSpacing(5)
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setFixedHeight(44)
            field.setStyleSheet(_field_style)
            if echo_password:
                field.setEchoMode(QLineEdit.Password)
            f_layout.addWidget(field)
            f_layout.addSpacing(14)
            return field

        self.field_nom = add_field("Nom", "Votre nom")
        self.field_login = add_field("Identifiant", "Identifiant de connexion")
        self.field_pwd = add_field("Mot de passe", "Au moins 6 caracteres", echo_password=True)
        self.field_pwd_confirm = add_field("Confirmer le mot de passe", "Ressaisissez le mot de passe", echo_password=True)

        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setMinimumHeight(18)
        self.lbl_error.setStyleSheet("color: #F87171; font-size: 12px; background-color: transparent;")
        f_layout.addWidget(self.lbl_error)
        f_layout.addSpacing(16)

        self.btn_create = QPushButton("Creer mon compte administrateur")
        self.btn_create.setFixedHeight(48)
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.setStyleSheet(f"""
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
        self.btn_create.clicked.connect(self._do_create)
        f_layout.addWidget(self.btn_create)
        f_layout.addStretch()

        root.addWidget(form, 1)
        self.field_nom.setFocus()

    @staticmethod
    def _make_field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 600; background-color: transparent;")
        return lbl

    def _do_create(self):
        from services.utilisateur_service import UtilisateurService

        nom = self.field_nom.text().strip()
        login = self.field_login.text().strip()
        password = self.field_pwd.text()
        password_confirm = self.field_pwd_confirm.text()

        if password != password_confirm:
            self.lbl_error.setText("Les deux mots de passe ne correspondent pas.")
            return

        self.lbl_error.setText("")
        self.btn_create.setEnabled(False)
        self.btn_create.setText("Creation en cours…")

        ok, msg = UtilisateurService.create_first_admin({
            "Login": login,
            "Nom": nom,
            "Password": password,
        })

        if ok:
            self.accept()
        else:
            self.lbl_error.setText(msg)
            self.btn_create.setEnabled(True)
            self.btn_create.setText("Creer mon compte administrateur")
