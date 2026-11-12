from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFrame
)
from services.religion_service import ReligionService
from app.styles import (
    COLORS, INPUT_STYLE, PAGE_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, apply_table_style, configure_table_action_button, make_table_action_container
)


class ReligionView(QWidget):
    """Écran — Gestion des religions."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        titre = QLabel("Gestion des Religions")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        form_card = QFrame()
        form_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        form_layout = QHBoxLayout(form_card)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(12)

        lbl = QLabel("Religion * :")
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {COLORS['text_soft']};"
            "background-color: transparent;"
        )
        self.txt_rel = QLineEdit()
        self.txt_rel.setPlaceholderText("Ex : ISLAM, CATHOLIQUE, PROTESTANT")
        self.txt_rel.setStyleSheet(INPUT_STYLE)
        self.txt_rel.setMaximumWidth(280)

        self.btn_nouveau = QPushButton("Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SECONDARY)
        self.btn_nouveau.clicked.connect(self.clear_fields)

        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.save_religion)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        btn_fermer.clicked.connect(self.close_tab)

        form_layout.addWidget(lbl)
        form_layout.addWidget(self.txt_rel)
        form_layout.addStretch()
        form_layout.addWidget(self.btn_nouveau)
        form_layout.addWidget(self.btn_valider)
        form_layout.addWidget(btn_fermer)

        layout.addWidget(form_card)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Religion", "Supprimer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        apply_table_style(self.table)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for i, item in enumerate(ReligionService.get_all()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(item.Religion))
            btn_suppr = QPushButton("Supprimer")
            configure_table_action_button(btn_suppr, "danger")
            btn_suppr.clicked.connect(
                lambda checked=False, id_r=item.IDTReligion, lib=item.Religion:
                self.supprimer_religion(id_r, lib)
            )
            self.table.setCellWidget(i, 1, make_table_action_container(btn_suppr))
            self.table.setRowHeight(i, 44)

    def save_religion(self):
        lib = self.txt_rel.text().strip().upper()
        if not lib:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le libellé de la religion !")
            return
        reussite, msg = ReligionService.add_religion(lib)
        if reussite:
            QMessageBox.information(self, "Enregistrement réussi", msg)
            self.txt_rel.clear()
            self.load_data()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def supprimer_religion(self, id_rel, libelle):
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment retirer la religion '{libelle}' ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            reussite, msg = ReligionService.delete_religion(id_rel)
            if reussite:
                QMessageBox.information(self, "Suppression réussie", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur", msg)

    def clear_fields(self):
        self.txt_rel.clear()
        self.txt_rel.setFocus()

    def refresh_data(self):
        self.load_data()

    def close_tab(self):
        self.clear_fields()
