from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFrame
)
from services.cycle_service import CycleService
from app.styles import (
    COLORS, INPUT_STYLE, PAGE_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, apply_table_style, configure_table_action_button, make_table_action_container
)


class CycleView(QWidget):
    """Écran — Gestion des cycles d'enseignement."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        titre = QLabel("Gestion des Cycles")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        # Formulaire
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

        lbl = QLabel("Nom du Cycle * :")
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {COLORS['text_soft']};"
            "background-color: transparent;"
        )
        self.txt_cycle = QLineEdit()
        self.txt_cycle.setPlaceholderText("Ex : PRIMAIRE, LYCÉE, COLLÈGE")
        self.txt_cycle.setStyleSheet(INPUT_STYLE)
        self.txt_cycle.setMaximumWidth(280)

        self.btn_nouveau = QPushButton("Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SECONDARY)
        self.btn_nouveau.clicked.connect(self.clear_fields)

        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.save_cycle)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        btn_fermer.clicked.connect(self.close_tab)

        form_layout.addWidget(lbl)
        form_layout.addWidget(self.txt_cycle)
        form_layout.addStretch()
        form_layout.addWidget(self.btn_nouveau)
        form_layout.addWidget(self.btn_valider)
        form_layout.addWidget(btn_fermer)

        layout.addWidget(form_card)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Cycle Scolaire", "Supprimer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        apply_table_style(self.table)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for i, cyc in enumerate(CycleService.get_all()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(cyc.Libelle))
            btn_suppr = QPushButton("Supprimer")
            configure_table_action_button(btn_suppr, "danger")
            btn_suppr.clicked.connect(
                lambda checked=False, id_c=cyc.IDT_Cycle, lib=cyc.Libelle:
                self.supprimer_cycle(id_c, lib)
            )
            self.table.setCellWidget(i, 1, make_table_action_container(btn_suppr))
            self.table.setRowHeight(i, 44)

    def save_cycle(self):
        lib = self.txt_cycle.text().strip().upper()
        if not lib:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le nom du cycle !")
            return
        reussite, msg = CycleService.add_cycle(lib)
        if reussite:
            QMessageBox.information(self, "Enregistrement réussi", msg)
            self.clear_fields()
            self.load_data()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def supprimer_cycle(self, id_cycle, libelle):
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer le cycle '{libelle}' ?\n"
            "Toutes les données rattachées subiront les contraintes de base de données.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            reussite, msg = CycleService.delete_cycle(id_cycle)
            if reussite:
                QMessageBox.information(self, "Suppression réussie", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur lors de la suppression", msg)

    def clear_fields(self):
        self.txt_cycle.clear()
        self.txt_cycle.setFocus()

    def refresh_data(self):
        self.load_data()

    def close_tab(self):
        self.clear_fields()
