from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QSpinBox, QFrame
)
from PySide6.QtCore import Qt
from services.classe_service import ClasseService
from services.niveau_service import NiveauService
from app.styles import (
    COLORS, INPUT_STYLE, COMBO_STYLE, TABLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SUCCESS, BUTTON_SECONDARY, BUTTON_DANGER,
    PAGE_TITLE_STYLE, apply_table_style,
    configure_table_action_button, make_table_action_container
)


class ClasseView(QWidget):
    """Écran — Création des classes."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.load_cycles()
        self.load_classes()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 16, 18, 16)
        self.main_layout.setSpacing(14)

        # Titre
        titre = QLabel("Création des Classes")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        self.main_layout.addWidget(titre)

        # Avertissement
        self.lbl_warning_classe = QLabel(
            "Veuillez d'abord créer un cycle et un niveau dans les onglets correspondants."
        )
        self.lbl_warning_classe.setStyleSheet(
            f"color: {COLORS['danger']}; font-weight: bold;"
            f"background-color: #FEF2F2; padding: 8px 12px;"
            f"border: 1px solid #FEE2E2; border-radius: 6px; font-size: 12px;"
        )
        self.lbl_warning_classe.setVisible(False)
        self.main_layout.addWidget(self.lbl_warning_classe)

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

        lbl_cycle = QLabel("1. Choisir le Cycle * :")
        lbl_cycle.setStyleSheet(lbl_style)
        self.cmb_cycle = QComboBox()
        self.cmb_cycle.setStyleSheet(COMBO_STYLE)
        self.cmb_cycle.currentIndexChanged.connect(self.on_cycle_changed)

        lbl_niveau = QLabel("2. Choisir le Niveau * :")
        lbl_niveau.setStyleSheet(lbl_style)
        self.cmb_niveau = QComboBox()
        self.cmb_niveau.setStyleSheet(COMBO_STYLE)

        lbl_nom = QLabel("3. Nom / Libellé de Classe * :")
        lbl_nom.setStyleSheet(lbl_style)
        self.txt_nom = QLineEdit()
        self.txt_nom.setPlaceholderText("Ex : CP1 A, CE1 Rouge")
        self.txt_nom.setStyleSheet(INPUT_STYLE)

        lbl_capacite = QLabel("4. Capacité d'élèves :")
        lbl_capacite.setStyleSheet(lbl_style)
        self.spin_capacite = QSpinBox()
        self.spin_capacite.setRange(1, 200)
        self.spin_capacite.setValue(40)
        self.spin_capacite.setStyleSheet(
            f"padding: 6px 10px; border: 1px solid {COLORS['input_border']};"
            f"border-radius: 6px; background-color: {COLORS['card']};"
            f"color: {COLORS['text']}; min-height: 34px; font-size: 13px;"
        )

        form_layout.addWidget(lbl_cycle, 0, 0)
        form_layout.addWidget(self.cmb_cycle, 0, 1)
        form_layout.addWidget(lbl_niveau, 1, 0)
        form_layout.addWidget(self.cmb_niveau, 1, 1)
        form_layout.addWidget(lbl_nom, 2, 0)
        form_layout.addWidget(self.txt_nom, 2, 1)
        form_layout.addWidget(lbl_capacite, 3, 0)
        form_layout.addWidget(self.spin_capacite, 3, 1)

        self.main_layout.addWidget(form_card)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_nouveau = QPushButton("Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SECONDARY)
        self.btn_nouveau.clicked.connect(self.clear_fields)

        self.btn_valider = QPushButton("✓  Valider la Classe")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.save_classe)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        btn_fermer.clicked.connect(self.close_tab)

        btn_layout.addWidget(self.btn_nouveau)
        btn_layout.addWidget(self.btn_valider)
        btn_layout.addWidget(btn_fermer)
        self.main_layout.addLayout(btn_layout)

        # Tableau récapitulatif
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Classe", "Cycle", "Niveau", "Capacité", "Supprimer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        apply_table_style(self.table)
        self.main_layout.addWidget(self.table)

    # ── Logique ──────────────────────────────────────────────────────────────

    def check_requirements(self):
        cycles = NiveauService.get_cycles()
        id_cycle = self.cmb_cycle.currentData()
        has_cycles = len(cycles) > 0
        has_niveaux = False
        if id_cycle:
            niveaux = ClasseService.get_niveaux_par_cycle(id_cycle)
            has_niveaux = len(niveaux) > 0

        if not has_cycles or not has_niveaux:
            msg = (
                "Veuillez d'abord créer un cycle dans l'onglet Cycle."
                if not has_cycles
                else "Veuillez d'abord créer un niveau pour ce cycle dans l'onglet Niveau."
            )
            self.lbl_warning_classe.setText(msg)
            self.lbl_warning_classe.setVisible(True)
            self.btn_valider.setEnabled(False)
            self.btn_valider.setStyleSheet(
                f"background-color: {COLORS['border']}; color: {COLORS['muted']};"
                "padding: 5px 16px; font-weight: 700; font-size: 14px;"
                "border-radius: 7px; border: none; min-height: 32px; max-height: 36px;"
            )
        else:
            self.lbl_warning_classe.setVisible(False)
            self.btn_valider.setEnabled(True)
            self.btn_valider.setStyleSheet(BUTTON_PRIMARY)

    def load_cycles(self):
        self.cmb_cycle.blockSignals(True)
        self.cmb_cycle.clear()
        for cycle in NiveauService.get_cycles():
            self.cmb_cycle.addItem(cycle.Libelle, cycle.IDT_Cycle)
        self.cmb_cycle.blockSignals(False)
        self.on_cycle_changed()

    def on_cycle_changed(self, index=None):
        self.cmb_niveau.clear()
        id_cycle = self.cmb_cycle.currentData()
        if id_cycle:
            for niv in ClasseService.get_niveaux_par_cycle(id_cycle):
                self.cmb_niveau.addItem(niv.Libelle, niv.IDT_Niveau)
        self.check_requirements()

    def load_classes(self):
        self.table.setRowCount(0)
        for i, c in enumerate(ClasseService.get_all()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(c["LibClasse"]))
            self.table.setItem(i, 1, QTableWidgetItem(c["CycleLibelle"]))
            self.table.setItem(i, 2, QTableWidgetItem(c["NiveauLibelle"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(c["Capacite"])))

            btn_suppr = QPushButton("Supprimer")
            configure_table_action_button(btn_suppr, "danger")
            btn_suppr.clicked.connect(
                lambda checked=False, id_c=c["IDTClasse"], lib=c["LibClasse"]:
                self.supprimer_classe(id_c, lib)
            )
            self.table.setCellWidget(i, 4, make_table_action_container(btn_suppr))
            self.table.setRowHeight(i, 44)

    def supprimer_classe(self, id_classe, libelle):
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la classe '{libelle}' ?\nCette action est irréversible !",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            reussite, msg = ClasseService.delete_classe(id_classe)
            if reussite:
                QMessageBox.information(self, "Suppression réussie", msg)
                self.load_classes()
            else:
                QMessageBox.critical(self, "Erreur", msg)

    def save_classe(self):
        lib = self.txt_nom.text().strip()
        if not lib:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le nom de la classe !")
            return
        id_niveau = self.cmb_niveau.currentData()
        if not id_niveau:
            QMessageBox.warning(self, "Champ obligatoire", "Le niveau est requis.")
            return
        id_cycle = self.cmb_cycle.currentData()
        capacite = self.spin_capacite.value()
        sigle = lib[:10].replace(" ", "").upper()
        reussite, msg = ClasseService.add_classe(lib, sigle, id_cycle, id_niveau, capacite)
        if reussite:
            QMessageBox.information(self, "Enregistrement réussi", msg)
            self.txt_nom.clear()
            self.load_classes()
        else:
            QMessageBox.critical(self, "Erreur lors de la création", msg)

    def clear_fields(self):
        self.txt_nom.clear()
        if self.cmb_cycle.count() > 0:
            self.cmb_cycle.setCurrentIndex(0)
        self.spin_capacite.setValue(40)
        self.txt_nom.setFocus()

    def refresh_data(self):
        self.load_cycles()
        self.load_classes()

    def close_tab(self):
        self.clear_fields()
