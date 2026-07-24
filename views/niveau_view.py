from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame
)
from services.niveau_service import NiveauService
from app.styles import (
    COLORS, INPUT_STYLE, COMBO_STYLE, PAGE_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, apply_table_style, configure_table_action_button, make_table_action_container
)


class NiveauView(QWidget):
    """Écran — Enregistrement des niveaux scolaires."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.load_cycles()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        titre = QLabel("Gestion des Niveaux")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        # Avertissement
        self.lbl_warning_cycle = QLabel(
            "Veuillez d'abord créer un cycle dans l'onglet Cycle."
        )
        self.lbl_warning_cycle.setStyleSheet(
            f"color: {COLORS['danger']}; font-weight: bold;"
            f"background-color: #FEF2F2; padding: 8px 12px;"
            f"border: 1px solid #FEE2E2; border-radius: 6px; font-size: 12px;"
        )
        self.lbl_warning_cycle.setVisible(False)
        layout.addWidget(self.lbl_warning_cycle)

        # Formulaire
        form_card = QFrame()
        form_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(10)

        lbl_style = (
            f"font-size: 12px; font-weight: 600; color: {COLORS['text_soft']};"
            "background-color: transparent;"
        )

        lbl_cycle = QLabel("Cycle * :")
        lbl_cycle.setStyleSheet(lbl_style)
        self.cmb_cycle = QComboBox()
        self.cmb_cycle.setStyleSheet(COMBO_STYLE)

        lbl_niveau = QLabel("Niveau * :")
        lbl_niveau.setStyleSheet(lbl_style)
        self.txt_niveau = QLineEdit()
        self.txt_niveau.setPlaceholderText("Ex : CP1, CP2, Moyenne Section")
        self.txt_niveau.setStyleSheet(INPUT_STYLE)

        form_layout.addWidget(lbl_cycle, 0, 0)
        form_layout.addWidget(self.cmb_cycle, 0, 1)
        form_layout.addWidget(lbl_niveau, 1, 0)
        form_layout.addWidget(self.txt_niveau, 1, 1)

        layout.addWidget(form_card)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_nouveau = QPushButton("Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SECONDARY)
        self.btn_nouveau.clicked.connect(self.clear_fields)

        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.save_niveau)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        btn_fermer.clicked.connect(self.close_tab)

        btn_layout.addWidget(self.btn_nouveau)
        btn_layout.addWidget(self.btn_valider)
        btn_layout.addWidget(btn_fermer)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Niveau", "Cycle", "Supprimer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        apply_table_style(self.table)
        layout.addWidget(self.table)

    def load_cycles(self):
        self.cmb_cycle.clear()
        cycles = NiveauService.get_cycles()
        if not cycles:
            self.lbl_warning_cycle.setVisible(True)
            self.btn_valider.setEnabled(False)
        else:
            self.lbl_warning_cycle.setVisible(False)
            self.btn_valider.setEnabled(True)
            self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        for cycle in cycles:
            self.cmb_cycle.addItem(cycle.Libelle, cycle.IDT_Cycle)

    def load_data(self):
        self.table.setRowCount(0)
        for i, niv in enumerate(NiveauService.get_all_with_cycle()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(niv["Libelle"]))
            self.table.setItem(i, 1, QTableWidgetItem(niv["CycleLibelle"]))
            btn_suppr = QPushButton("Supprimer")
            configure_table_action_button(btn_suppr, "danger")
            btn_suppr.clicked.connect(
                lambda checked=False, id_n=niv["IDT_Niveau"], lib=niv["Libelle"]:
                self.supprimer_niveau(id_n, lib)
            )
            self.table.setCellWidget(i, 2, make_table_action_container(btn_suppr))
            self.table.setRowHeight(i, 44)

    def save_niveau(self):
        lib = self.txt_niveau.text().strip()
        if not lib:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le nom du niveau !")
            return
        id_cycle = self.cmb_cycle.currentData()
        if not id_cycle:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez associer un cycle au niveau !")
            return
        reussite, msg = NiveauService.add_niveau(lib, id_cycle)
        if reussite:
            QMessageBox.information(self, "Enregistrement réussi", msg)
            self.txt_niveau.clear()
            self.load_data()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def supprimer_niveau(self, id_niveau, libelle):
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer le niveau '{libelle}' ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            reussite, msg = NiveauService.delete_niveau(id_niveau)
            if reussite:
                QMessageBox.information(self, "Suppression réussie", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur lors de la suppression", msg)

    def clear_fields(self):
        self.txt_niveau.clear()
        if self.cmb_cycle.count() > 0:
            self.cmb_cycle.setCurrentIndex(0)
        self.txt_niveau.setFocus()

    def refresh_data(self):
        self.load_cycles()
        self.load_data()

    def close_tab(self):
        self.clear_fields()
