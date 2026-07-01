from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtPrintSupport import QPrinterInfo
from PySide6.QtCore import Qt

from app.session import AppSession
from app.styles import COLORS, BUTTON_PRIMARY, BUTTON_SECONDARY, apply_modal_style


class ImprimanteDialog(QDialog):
    """Dialogue de sélection de l'imprimante par défaut pour l'utilisateur connecté."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Imprimante par défaut")
        self.setFixedSize(500, 420)
        apply_modal_style(self)
        self._build_ui()
        self._load_printers()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Choisir l'imprimante par défaut")
        title.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {COLORS['text']};"
            "background-color: transparent;"
        )
        layout.addWidget(title)

        desc = QLabel(
            "Sélectionnez l'imprimante à utiliser pour l'impression des reçus de paiement. "
            "Ce choix est enregistré pour votre compte utilisateur."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"font-size: 12px; color: {COLORS['muted']}; background-color: transparent;"
        )
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']}; margin: 2px 0;")
        layout.addWidget(sep)

        self.list_printers = QListWidget()
        self.list_printers.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['surface']};
                padding: 4px;
                font-size: 13px;
                color: {COLORS['text']};
                outline: none;
            }}
            QListWidget::item {{
                padding: 11px 14px;
                border-radius: 6px;
                margin: 1px 2px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {COLORS['primary_soft']};
            }}
        """)
        layout.addWidget(self.list_printers)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(
            f"font-size: 11px; color: {COLORS['muted']}; background-color: transparent;"
        )
        layout.addWidget(self.lbl_status)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet(BUTTON_SECONDARY)
        btn_cancel.setFixedHeight(38)
        btn_cancel.setMinimumWidth(110)
        btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setStyleSheet(BUTTON_PRIMARY)
        self.btn_save.setFixedHeight(38)
        self.btn_save.setMinimumWidth(130)
        self.btn_save.clicked.connect(self._save)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

    def _load_printers(self):
        current = AppSession.get_current_user_imprimante() or ""

        default_item = QListWidgetItem("  Imprimante par défaut du système")
        default_item.setData(Qt.UserRole, "")
        self.list_printers.addItem(default_item)

        available = QPrinterInfo.availablePrinterNames()
        for name in available:
            item = QListWidgetItem(f"  {name}")
            item.setData(Qt.UserRole, name)
            self.list_printers.addItem(item)

        # Sélectionner l'imprimante actuelle
        matched = False
        for i in range(self.list_printers.count()):
            item = self.list_printers.item(i)
            if item.data(Qt.UserRole) == current:
                self.list_printers.setCurrentItem(item)
                matched = True
                break

        if not matched:
            self.list_printers.setCurrentRow(0)

        if not available:
            self.lbl_status.setText("Aucune imprimante détectée sur ce poste.")
        else:
            count = len(available)
            self.lbl_status.setText(f"{count} imprimante(s) disponible(s) sur ce poste.")

    def _save(self):
        item = self.list_printers.currentItem()
        if not item:
            return

        printer_name = item.data(Qt.UserRole) or None
        user_id = AppSession.get_current_user_id()

        from services.utilisateur_service import UtilisateurService
        ok, msg = UtilisateurService.set_printer_preference(user_id, printer_name)

        if ok:
            AppSession.set_current_user_imprimante(printer_name)
            if printer_name:
                label = f"Imprimante « {printer_name} » définie comme imprimante par défaut."
            else:
                label = "L'imprimante par défaut du système sera utilisée."
            QMessageBox.information(self, "Préférence enregistrée", label)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", msg)
