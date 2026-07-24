from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGroupBox,
    QComboBox, QCheckBox, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from services.niveau_service import NiveauService
from services.autres_frais_service import AutresFraisService
from services.montant_autres_frais_service import MontantAutresFraisService
from app.session import AppSession
from app.styles import (
    INPUT_STYLE, COMBO_STYLE, SECTION_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_DANGER,
    GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE, apply_table_style
)


class AutresFraisView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._niveau_checkboxes = []
        self.selected_ids = []
        self.init_ui()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(20)

        # ---- GAUCHE ----
        pane_gauche = QWidget()
        pane_gauche.setMinimumWidth(320)
        layout_gauche = QVBoxLayout(pane_gauche)
        layout_gauche.setContentsMargins(4, 4, 4, 4)
        layout_gauche.setSpacing(15)

        # Groupe 1 : Créer un type de frais
        group_type = QGroupBox("1. ENREGISTRER UN TYPE DE FRAIS ANNEXE")
        group_type.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        layout_type = QVBoxLayout(group_type)
        layout_type.setSpacing(10)

        layout_type.addWidget(QLabel("Code Frais (Ex: ANG/INFO, MUSIQUE) :"))
        self.txt_code = QLineEdit()
        self.txt_code.setStyleSheet(INPUT_STYLE)
        self.txt_code.setMaxLength(10)
        layout_type.addWidget(self.txt_code)

        layout_type.addWidget(QLabel("Libellé du frais :"))
        self.txt_libelle = QLineEdit()
        self.txt_libelle.setStyleSheet(INPUT_STYLE)
        self.txt_libelle.setMaxLength(50)
        layout_type.addWidget(self.txt_libelle)

        btn_creer_type = QPushButton("Créer le type de frais")
        btn_creer_type.setStyleSheet(BUTTON_PRIMARY)
        btn_creer_type.clicked.connect(self.on_create_type)
        layout_type.addWidget(btn_creer_type)

        layout_gauche.addWidget(group_type)

        # Groupe 2 : Affectation globale
        group_affect = QGroupBox("2. ATTRIBUER UN TARIF AUX NIVEAUX CONCERNÉS")
        group_affect.setStyleSheet(GROUPBOX_STYLE)
        layout_affect = QVBoxLayout(group_affect)
        layout_affect.setSpacing(10)

        layout_affect.addWidget(QLabel("Type de frais :"))
        self.cmb_types = QComboBox()
        self.cmb_types.setStyleSheet(COMBO_STYLE)
        layout_affect.addWidget(self.cmb_types)

        layout_affect.addWidget(QLabel("Montant annuel (F CFA) :"))
        self.txt_montant = QLineEdit("0")
        self.txt_montant.setStyleSheet(INPUT_STYLE)
        layout_affect.addWidget(self.txt_montant)

        layout_affect.addWidget(QLabel("Niveaux concernés (décocher ceux non concernés) :"))

        # Zone de cases à cocher scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(80)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ddd; border-radius: 4px; background: white; }")

        self._niveaux_container = QWidget()
        self._niveaux_layout = QGridLayout(self._niveaux_container)
        self._niveaux_layout.setContentsMargins(8, 8, 8, 8)
        self._niveaux_layout.setSpacing(6)
        self._niveaux_layout.setColumnStretch(0, 1)
        self._niveaux_layout.setColumnStretch(1, 1)
        self._niveaux_layout.setColumnStretch(2, 1)
        scroll.setWidget(self._niveaux_container)
        layout_affect.addWidget(scroll)

        btn_attribuer = QPushButton("✓  Enregistrer pour les niveaux cochés")
        btn_attribuer.setStyleSheet(BUTTON_PRIMARY)
        btn_attribuer.clicked.connect(self.on_save_tarif)
        layout_affect.addWidget(btn_attribuer)

        layout_gauche.addWidget(group_affect)
        layout_gauche.addStretch()

        layout_principal.addWidget(pane_gauche, 1)

        # ---- DROITE ----
        pane_droit = QWidget()
        layout_droit = QVBoxLayout(pane_droit)
        layout_droit.setContentsMargins(0, 0, 0, 0)
        layout_droit.setSpacing(10)

        lbl_titre = QLabel("Tarifs des Autres Frais Programmés")
        lbl_titre.setStyleSheet(SECTION_TITLE_STYLE)
        layout_droit.addWidget(lbl_titre)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Type de Frais", "Niveau", "Tarif annuel", "ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnHidden(3, True)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout_droit.addWidget(self.table)

        self.btn_supprimer = QPushButton("Retirer les tarifs sélectionnés")
        self.btn_supprimer.setStyleSheet(BUTTON_DANGER)
        self.btn_supprimer.setEnabled(False)
        self.btn_supprimer.clicked.connect(self.on_delete_tarif)
        layout_droit.addWidget(self.btn_supprimer)

        layout_principal.addWidget(pane_droit, 2)

        self.load_data()

    def load_data(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        # Combobox types de frais
        self.cmb_types.clear()
        types = AutresFraisService.get_all_autres_frais()
        for t in types:
            self.cmb_types.addItem(f"{t.CodeFrais} - {t.LibelleFrais}", t.IDAutres_Frais)

        # Cases à cocher niveaux (toutes cochées par défaut)
        while self._niveaux_layout.count():
            item = self._niveaux_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._niveau_checkboxes.clear()

        CB_STYLE = """
            QCheckBox { font-size: 13px; font-weight: 600; padding: 4px 6px; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #3b5bdb; border-radius: 4px; background: white; }
            QCheckBox::indicator:checked { background: #3b5bdb; image: url(none); }
            QCheckBox::indicator:checked { background-color: #3b5bdb; border-color: #3b5bdb; }
        """
        niveaux = NiveauService.get_all_with_cycle()
        for i, n in enumerate(niveaux):
            cb = QCheckBox(n["Libelle"])
            cb.setChecked(True)
            cb.setStyleSheet(CB_STYLE)
            row, col = divmod(i, 3)
            self._niveaux_layout.addWidget(cb, row, col)
            self._niveau_checkboxes.append((cb, n["IDT_Niveau"]))

        # Tableau des tarifs programmés
        tarifs = MontantAutresFraisService.get_montants_by_annee(active_annee_id)
        self.table.setRowCount(len(tarifs))
        for i, t in enumerate(tarifs):
            nom_frais = f"{t.autre_frais.CodeFrais} - {t.autre_frais.LibelleFrais}" if t.autre_frais else "Inconnu"
            lib_niv = t.niveau.Libelle if t.niveau else "Inconnu"
            montant_aff = f"{int(t.MontantFrais):,} F"

            for col, val in enumerate([nom_frais, lib_niv, montant_aff, str(t.IDMontantAutres)]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, col, item)

        self.btn_supprimer.setEnabled(False)
        self.selected_ids = []

    def on_row_selected(self):
        rows = set(idx.row() for idx in self.table.selectedIndexes())
        self.selected_ids = []
        for row in rows:
            item_id = self.table.item(row, 3)
            if item_id:
                self.selected_ids.append(int(item_id.text()))
        self.btn_supprimer.setEnabled(len(self.selected_ids) > 0)

    def on_create_type(self):
        code = self.txt_code.text().strip()
        libelle = self.txt_libelle.text().strip()
        if not code or not libelle:
            QMessageBox.warning(self, "Champs Requis", "Veuillez remplir le code et le libellé.")
            return
        success, msg = AutresFraisService.create_autres_frais(code, libelle)
        if success:
            self.txt_code.clear()
            self.txt_libelle.clear()
            self.load_data()
            QMessageBox.information(self, "Type Créé", "Type de frais enregistré avec succès !")
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def on_save_tarif(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        if self.cmb_types.currentIndex() == -1:
            QMessageBox.warning(self, "Sélection Requise", "Veuillez sélectionner un type de frais.")
            return

        niveaux_coches = [(cb, id_niv) for cb, id_niv in self._niveau_checkboxes if cb.isChecked()]
        if not niveaux_coches:
            QMessageBox.warning(self, "Aucun Niveau", "Veuillez cocher au moins un niveau.")
            return

        try:
            val = float(self.txt_montant.text().strip() or 0)
        except ValueError:
            QMessageBox.critical(self, "Erreur", "Montant invalide.")
            return

        if val <= 0:
            QMessageBox.warning(self, "Montant Invalide", "Le montant doit être supérieur à 0.")
            return

        id_frais = self.cmb_types.currentData()
        erreurs = []
        for _, id_niveau in niveaux_coches:
            ok, msg = MontantAutresFraisService.save_montant_autres_frais(active_annee_id, id_niveau, id_frais, val)
            if not ok:
                erreurs.append(msg)

        if erreurs:
            QMessageBox.warning(self, "Avertissement", f"{len(erreurs)} erreur(s) lors de l'enregistrement.")
        else:
            nb = len(niveaux_coches)
            QMessageBox.information(self, "Succès", f"Tarif enregistré pour {nb} niveau(x).")

        self.txt_montant.setText("0")
        self.load_data()

    def on_delete_tarif(self):
        if not self.selected_ids:
            return
        nb = len(self.selected_ids)
        res = QMessageBox.question(
            self, "Confirmation",
            f"Retirer {nb} tarif(s) sélectionné(s) ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.No:
            return
        erreurs = []
        for id_montant in self.selected_ids:
            ok, msg = MontantAutresFraisService.delete_montant_autres_frais(id_montant)
            if not ok:
                erreurs.append(msg)
        if erreurs:
            QMessageBox.critical(self, "Erreur", f"{len(erreurs)} suppression(s) échouée(s).")
        self.load_data()
