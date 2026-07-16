from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt
from services.niveau_service import NiveauService
from services.montant_scolarite_service import MontantScolariteService
from app.session import AppSession
from app.styles import (
    COLORS, INPUT_STYLE, TABLE_STYLE, SECTION_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE,
    apply_table_style
)

class MontantScolariteView(QWidget):
    """
    Vue permettant de paramétrer les montants de scolarité par niveau,
    selon le statut d'affectation de l'État (Non affecté / Affecté).
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        # Layout principal horizontal
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(20)

        # ---------------- CÔTÉ GAUCHE : Saisie / Actions communes ----------------
        pane_gauche = QWidget()
        layout_gauche = QVBoxLayout(pane_gauche)
        layout_gauche.setContentsMargins(0, 0, 0, 0)
        layout_gauche.setSpacing(15)

        # Groupe 1 : Saisie commune (gain de temps !)
        group_commun = QGroupBox("APPLICATION COMMUNE À TOUS LES NIVEAUX")
        group_commun.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        layout_commun = QVBoxLayout(group_commun)
        layout_commun.setSpacing(8)

        lbl_com_info = QLabel("Valeurs par défaut à propager à tous les niveaux :")
        lbl_com_info.setWordWrap(True)
        lbl_com_info.setStyleSheet(
            f"color: {COLORS['muted']}; font-style: italic; font-size: 11px; background-color: transparent;"
        )
        layout_commun.addWidget(lbl_com_info)

        form_commun = QFormLayout()
        form_commun.setSpacing(8)
        form_commun.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.txt_com_non_affecte = QLineEdit("0")
        self.txt_com_non_affecte.setStyleSheet(INPUT_STYLE)
        form_commun.addRow("Non affecté (F CFA) :", self.txt_com_non_affecte)

        self.txt_com_affecte = QLineEdit("0")
        self.txt_com_affecte.setStyleSheet(INPUT_STYLE)
        form_commun.addRow("Affecté (F CFA) :", self.txt_com_affecte)

        layout_commun.addLayout(form_commun)

        btn_appliquer_tout = QPushButton("Appliquer à tous les niveaux")
        btn_appliquer_tout.setStyleSheet(BUTTON_PRIMARY)
        btn_appliquer_tout.clicked.connect(self.on_apply_common)
        layout_commun.addWidget(btn_appliquer_tout)

        layout_gauche.addWidget(group_commun)

        # Groupe 2 : Saisie individuelle niveau selectionné
        self.group_individuel = QGroupBox("MODIFIER LE NIVEAU SÉLECTIONNÉ")
        self.group_individuel.setStyleSheet(GROUPBOX_STYLE)
        layout_indiv = QVBoxLayout(self.group_individuel)
        layout_indiv.setSpacing(8)

        self.lbl_selected_niveau = QLabel("Aucun niveau sélectionné")
        self.lbl_selected_niveau.setStyleSheet(
            f"font-weight: bold; color: {COLORS['text']}; font-size: 12px;"
            "background-color: transparent;"
        )
        layout_indiv.addWidget(self.lbl_selected_niveau)

        form_indiv = QFormLayout()
        form_indiv.setSpacing(8)
        form_indiv.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.txt_ind_non_affecte = QLineEdit("0")
        self.txt_ind_non_affecte.setStyleSheet(INPUT_STYLE)
        form_indiv.addRow("Non affecté (F CFA) :", self.txt_ind_non_affecte)

        self.txt_ind_affecte = QLineEdit("0")
        self.txt_ind_affecte.setStyleSheet(INPUT_STYLE)
        form_indiv.addRow("Affecté (F CFA) :", self.txt_ind_affecte)

        layout_indiv.addLayout(form_indiv)

        self.btn_enregistrer_niveau = QPushButton("✓  Enregistrer ce niveau")
        self.btn_enregistrer_niveau.setStyleSheet(BUTTON_PRIMARY)
        self.btn_enregistrer_niveau.setEnabled(False)
        self.btn_enregistrer_niveau.clicked.connect(self.on_save_individual)
        layout_indiv.addWidget(self.btn_enregistrer_niveau)

        layout_gauche.addWidget(self.group_individuel)
        layout_gauche.addStretch()

        layout_principal.addWidget(pane_gauche, 2)

        # ---------------- CÔTÉ DROIT : Grille des niveaux / tarifs ----------------
        pane_droit = QWidget()
        layout_droit = QVBoxLayout(pane_droit)
        layout_droit.setContentsMargins(0, 0, 0, 0)
        layout_droit.setSpacing(10)

        lbl_titre_table = QLabel("Tarifs de Scolarité par Niveau")
        lbl_titre_table.setStyleSheet(SECTION_TITLE_STYLE)
        layout_droit.addWidget(lbl_titre_table)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Niveau", "Non affecté", "Affecté"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout_droit.addWidget(self.table)

        layout_principal.addWidget(pane_droit, 3)

        # Charger de départ
        self.selected_niveau_id = None
        self.load_montants()

    def load_montants(self):
        """Charge les niveaux de l'année scolaire et leurs tarifs."""
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        # 1. Charger tous les niveaux
        niveaux = NiveauService.get_all_with_cycle()

        # 2. Charger les tarifs déjà configurés
        tarifs = MontantScolariteService.get_montants_by_annee(active_annee_id)
        tarifs_dict = {t.IDNiveau: t for t in tarifs}

        self.table.setRowCount(len(niveaux))
        for i, niv in enumerate(niveaux):
            nid = niv["IDT_Niveau"]
            lib_niv = niv["Libelle"]

            # Rechercher si des montants existent déjà
            m_non_affecte = 0.0
            m_affecte = 0.0
            if nid in tarifs_dict:
                m_non_affecte = float(tarifs_dict[nid].MontantNonAffecte)
                m_affecte = float(tarifs_dict[nid].MontantAffecte)

            # Cellules
            item_niv = QTableWidgetItem(lib_niv)
            item_niv.setData(Qt.UserRole, nid)
            item_niv.setFlags(item_niv.flags() & ~Qt.ItemIsEditable)

            item_non_affecte = QTableWidgetItem(f"{int(m_non_affecte):,} F")
            item_non_affecte.setFlags(item_non_affecte.flags() & ~Qt.ItemIsEditable)

            item_affecte = QTableWidgetItem(f"{int(m_affecte):,} F")
            item_affecte.setFlags(item_affecte.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(i, 0, item_niv)
            self.table.setItem(i, 1, item_non_affecte)
            self.table.setItem(i, 2, item_affecte)

        self.lbl_selected_niveau.setText("Aucun niveau sélectionné")
        self.btn_enregistrer_niveau.setEnabled(False)
        self.selected_niveau_id = None

    def on_row_selected(self):
        """Se déclenche lors de la sélection d'une ligne."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        row = selected_ranges[0].topRow()
        item_niv = self.table.item(row, 0)
        if not item_niv:
            return

        self.selected_niveau_id = item_niv.data(Qt.UserRole)
        self.lbl_selected_niveau.setText(f"Niveau : {item_niv.text()}")
        self.btn_enregistrer_niveau.setEnabled(True)

        # Extraire les montants de la grille
        m_non_affecte = self.clean_amount(self.table.item(row, 1).text())
        m_affecte = self.clean_amount(self.table.item(row, 2).text())

        self.txt_ind_non_affecte.setText(str(m_non_affecte))
        self.txt_ind_affecte.setText(str(m_affecte))

    def clean_amount(self, txt: str) -> int:
        """Nettoie l'affichage pour n'avoir que des chiffres."""
        return int("".join(c for c in txt if c.isdigit()))

    def on_apply_common(self):
        """Applique des valeurs communes à tous les niveaux."""
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            QMessageBox.warning(self, "Erreur", "Aucune annee scolaire active.")
            return

        try:
            val_non_affecte = float(self.txt_com_non_affecte.text().strip() or 0)
            val_affecte = float(self.txt_com_affecte.text().strip() or 0)
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Veuillez saisir des montants valides (nombres entiers).")
            return

        success, msg = MontantScolariteService.apply_common_amount_to_all_levels(
            active_annee_id, val_non_affecte, val_affecte
        )

        if success:
            QMessageBox.information(self, "Succes", "Les montants de scolarite generaux ont ete propages avec succes !")
            self.load_montants()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def on_save_individual(self):
        """Enregistre les valeurs spécifiques pour le niveau sélectionné."""
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id or not self.selected_niveau_id:
            QMessageBox.warning(self, "Selection Requise", "Veuillez choisir un niveau avant de valider.")
            return

        try:
            val_non_affecte = float(self.txt_ind_non_affecte.text().strip() or 0)
            val_affecte = float(self.txt_ind_affecte.text().strip() or 0)
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Veuillez entrer des montants numeriques corrects.")
            return

        success, msg = MontantScolariteService.save_montant_scolarite(
            active_annee_id, self.selected_niveau_id, val_non_affecte, val_affecte
        )

        if success:
            QMessageBox.information(self, "Enregistre", "Le tarif pour ce niveau a ete mis a jour avec succes !")
            self.load_montants()
        else:
            QMessageBox.critical(self, "Erreur", msg)
