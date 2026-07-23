"""
Écran de paramétrage des prestations annexes et des prestataires.
Accessible depuis Paramètres > Prestations (ADMIN, DIRECTEUR).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QAbstractItemView, QMessageBox, QSplitter,
    QFormLayout, QGroupBox, QCheckBox, QTabWidget, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.prestation_service import PrestationService
from services.niveau_service import NiveauService
from app.session import AppSession
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    INPUT_STYLE, COMBO_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS,
    BUTTON_SECONDARY, BUTTON_DANGER, TABLE_STYLE, apply_card_shadow
)
from views.ui_components import make_separator, show_confirm, show_info, show_error


def _fmt(v) -> str:
    try:
        return f"{int(float(v)):,} FCFA".replace(",", " ")
    except Exception:
        return "0 FCFA"


class PrestationConfigView(QWidget):
    """Vue de gestion des prestations annexes et des prestataires."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.selected_prestation_id = None
        self._niveau_checkboxes = []
        self.selected_tarif_ids = []
        self.can_modify = AppSession.has_permission("PRESTATIONS_MODIFIER")
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Titre
        titre = QLabel("Paramétrage des Prestations Annexes")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        root.addWidget(titre)

        sous_titre = QLabel(
            "Configurez les prestations incluses dans la scolarité, leurs montants annuels "
            "et, si besoin, un tarif spécifique par niveau."
        )
        sous_titre.setStyleSheet(SECTION_TITLE_STYLE)
        root.addWidget(sous_titre)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_catalogue_tab(), "Catalogue")
        self.tabs.addTab(self._build_tarifs_niveau_tab(), "Tarifs par niveau")
        root.addWidget(self.tabs, 1)

    def _build_catalogue_tab(self) -> QWidget:
        """Onglet 1 : catalogue des prestations, montant par defaut et prestataires."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Corps principal : liste à gauche, formulaire à droite
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E2E8F0; width: 1px; }")

        splitter.addWidget(self._build_list_panel())
        splitter.addWidget(self._build_form_panel())
        splitter.setSizes([560, 380])

        layout.addWidget(splitter)
        return tab

    def _build_tarifs_niveau_tab(self) -> QWidget:
        """Onglet 2 : surcharge du tarif d'une prestation pour des niveaux specifiques."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # ---- GAUCHE : affectation ----
        pane_gauche = QFrame()
        pane_gauche.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-top: 3px solid {COLORS['primary']};
                border-radius: 10px;
            }}
        """)
        apply_card_shadow(pane_gauche)
        layout_gauche = QVBoxLayout(pane_gauche)
        layout_gauche.setContentsMargins(16, 14, 16, 14)
        layout_gauche.setSpacing(10)

        lbl_gauche = QLabel("Attribuer un tarif aux niveaux concernés")
        lbl_gauche.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        layout_gauche.addWidget(lbl_gauche)
        layout_gauche.addWidget(make_separator())

        layout_gauche.addWidget(QLabel("Prestation :"))
        self.cmb_tarif_prestation = QComboBox()
        self.cmb_tarif_prestation.setStyleSheet(COMBO_STYLE)
        layout_gauche.addWidget(self.cmb_tarif_prestation)

        layout_gauche.addWidget(QLabel("Montant annuel (F CFA) :"))
        self.txt_tarif_montant = QLineEdit("0")
        self.txt_tarif_montant.setStyleSheet(INPUT_STYLE)
        layout_gauche.addWidget(self.txt_tarif_montant)

        layout_gauche.addWidget(QLabel("Niveaux concernés (décocher ceux non concernés) :"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(180)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ddd; border-radius: 4px; background: white; }")

        self._niveaux_container = QWidget()
        self._niveaux_layout = QGridLayout(self._niveaux_container)
        self._niveaux_layout.setContentsMargins(8, 8, 8, 8)
        self._niveaux_layout.setSpacing(6)
        self._niveaux_layout.setColumnStretch(0, 1)
        self._niveaux_layout.setColumnStretch(1, 1)
        scroll.setWidget(self._niveaux_container)
        layout_gauche.addWidget(scroll, 1)

        self.btn_tarif_save = QPushButton("Enregistrer pour les niveaux cochés")
        self.btn_tarif_save.setStyleSheet(BUTTON_PRIMARY)
        self.btn_tarif_save.setCursor(Qt.PointingHandCursor)
        self.btn_tarif_save.setEnabled(self.can_modify)
        self.btn_tarif_save.clicked.connect(self._on_save_tarif_niveau)
        layout_gauche.addWidget(self.btn_tarif_save)

        # ---- DROITE : tarifs existants ----
        pane_droit = QFrame()
        pane_droit.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-top: 3px solid {COLORS['success']};
                border-radius: 10px;
            }}
        """)
        apply_card_shadow(pane_droit)
        layout_droit = QVBoxLayout(pane_droit)
        layout_droit.setContentsMargins(16, 14, 16, 14)
        layout_droit.setSpacing(10)

        lbl_droit = QLabel("Tarifs par niveau programmés")
        lbl_droit.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        layout_droit.addWidget(lbl_droit)
        layout_droit.addWidget(make_separator())

        self.table_tarifs = QTableWidget()
        self.table_tarifs.setColumnCount(4)
        self.table_tarifs.setHorizontalHeaderLabels(["Prestation", "Niveau", "Tarif annuel", "ID"])
        self.table_tarifs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_tarifs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_tarifs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_tarifs.setAlternatingRowColors(True)
        self.table_tarifs.setStyleSheet(TABLE_STYLE)
        self.table_tarifs.verticalHeader().setVisible(False)
        self.table_tarifs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tarifs.setColumnHidden(3, True)
        self.table_tarifs.itemSelectionChanged.connect(self._on_tarif_row_selected)
        layout_droit.addWidget(self.table_tarifs, 1)

        self.btn_tarif_delete = QPushButton("Retirer les tarifs sélectionnés")
        self.btn_tarif_delete.setStyleSheet(BUTTON_DANGER)
        self.btn_tarif_delete.setCursor(Qt.PointingHandCursor)
        self.btn_tarif_delete.setEnabled(False)
        self.btn_tarif_delete.clicked.connect(self._on_delete_tarif_niveau)
        layout_droit.addWidget(self.btn_tarif_delete)

        layout.addWidget(pane_gauche, 1)
        layout.addWidget(pane_droit, 2)
        return tab

    # ─── Panneau liste ────────────────────────────────────────────────────────

    def _build_list_panel(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-top: 3px solid {COLORS['primary']};
                border-radius: 10px;
            }}
        """)
        apply_card_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Titre + bouton Nouveau
        header = QHBoxLayout()
        lbl = QLabel("Prestations configurées")
        lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        header.addWidget(lbl, 1)

        self.btn_nouveau = QPushButton("+ Nouvelle prestation")
        self.btn_nouveau.setStyleSheet(BUTTON_PRIMARY)
        self.btn_nouveau.setFixedHeight(34)
        self.btn_nouveau.setCursor(Qt.PointingHandCursor)
        self.btn_nouveau.setEnabled(self.can_modify)
        self.btn_nouveau.clicked.connect(self._on_nouveau)
        header.addWidget(self.btn_nouveau)
        layout.addLayout(header)

        layout.addWidget(make_separator())

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Libellé", "Montant annuel", "Statut", "ID"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setColumnHidden(4, True)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setHighlightSections(False)

        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table, 1)

        # Boutons actions
        btn_row = QHBoxLayout()
        self.btn_toggle = QPushButton("Activer / Désactiver")
        self.btn_toggle.setStyleSheet(BUTTON_SECONDARY)
        self.btn_toggle.setFixedHeight(32)
        self.btn_toggle.setEnabled(False)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self._on_toggle)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setStyleSheet(BUTTON_SECONDARY)
        self.btn_refresh.setFixedHeight(32)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_data)

        btn_row.addWidget(self.btn_toggle)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_refresh)
        layout.addLayout(btn_row)

        return card

    # ─── Panneau formulaire ───────────────────────────────────────────────────

    def _build_form_panel(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-top: 3px solid {COLORS['success']};
                border-radius: 10px;
            }}
        """)
        apply_card_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        self.lbl_form_title = QLabel("Nouvelle prestation")
        self.lbl_form_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(self.lbl_form_title)
        layout.addWidget(make_separator())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        def lbl_style():
            return f"font-size: 12px; font-weight: 600; color: {COLORS['muted']}; background: transparent;"

        # Code
        lbl_code = QLabel("Code :")
        lbl_code.setStyleSheet(lbl_style())
        self.txt_code = QLineEdit()
        self.txt_code.setStyleSheet(INPUT_STYLE)
        self.txt_code.setFixedHeight(34)
        self.txt_code.setPlaceholderText("Ex : MUSIQUE")
        form.addRow(lbl_code, self.txt_code)

        # Libellé
        lbl_lib = QLabel("Libellé :")
        lbl_lib.setStyleSheet(lbl_style())
        self.txt_libelle = QLineEdit()
        self.txt_libelle.setStyleSheet(INPUT_STYLE)
        self.txt_libelle.setFixedHeight(34)
        self.txt_libelle.setPlaceholderText("Ex : Cours de Musique")
        form.addRow(lbl_lib, self.txt_libelle)

        # Montant annuel
        lbl_mnt = QLabel("Montant annuel :")
        lbl_mnt.setStyleSheet(lbl_style())
        self.txt_montant = QLineEdit()
        self.txt_montant.setStyleSheet(INPUT_STYLE)
        self.txt_montant.setFixedHeight(34)
        self.txt_montant.setPlaceholderText("Ex : 8000")
        form.addRow(lbl_mnt, self.txt_montant)

        # Prestataire
        lbl_prest = QLabel("Prestataire :")
        lbl_prest.setStyleSheet(lbl_style())
        self.cmb_prestataire = QComboBox()
        self.cmb_prestataire.setStyleSheet(COMBO_STYLE)
        self.cmb_prestataire.setFixedHeight(34)
        form.addRow(lbl_prest, self.cmb_prestataire)

        layout.addLayout(form)

        # Boutons Enregistrer / Annuler
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setStyleSheet(BUTTON_SUCCESS)
        self.btn_save.setFixedHeight(36)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setEnabled(self.can_modify)
        self.btn_save.clicked.connect(self._on_save)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setStyleSheet(BUTTON_SECONDARY)
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._reset_form)

        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        layout.addStretch()

        # Section prestataires
        layout.addWidget(make_separator())
        lbl_prest_title = QLabel("Prestataires enregistrés")
        lbl_prest_title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(lbl_prest_title)

        prest_row = QHBoxLayout()
        self.txt_new_prestataire = QLineEdit()
        self.txt_new_prestataire.setStyleSheet(INPUT_STYLE)
        self.txt_new_prestataire.setFixedHeight(32)
        self.txt_new_prestataire.setPlaceholderText("Nom du prestataire…")
        self.txt_new_prestataire.setEnabled(self.can_modify)
        prest_row.addWidget(self.txt_new_prestataire, 1)

        self.btn_add_prest = QPushButton("Ajouter")
        self.btn_add_prest.setStyleSheet(BUTTON_PRIMARY)
        self.btn_add_prest.setFixedHeight(32)
        self.btn_add_prest.setCursor(Qt.PointingHandCursor)
        self.btn_add_prest.setEnabled(self.can_modify)
        self.btn_add_prest.clicked.connect(self._on_add_prestataire)
        prest_row.addWidget(self.btn_add_prest)
        layout.addLayout(prest_row)

        for field in (self.txt_code, self.txt_libelle, self.txt_montant, self.cmb_prestataire):
            field.setEnabled(self.can_modify)

        return card

    # ─── Logique ──────────────────────────────────────────────────────────────

    def refresh_data(self):
        """Recharge la liste des prestations, des prestataires et des tarifs par niveau."""
        self._load_prestations()
        self._load_prestataires()
        self._load_tarifs_niveau()

    def _load_prestations(self):
        rows = PrestationService.get_all_prestations()
        self.table.setRowCount(len(rows))
        for i, p in enumerate(rows):
            it_code = QTableWidgetItem(p.Code or "")
            it_lib = QTableWidgetItem(p.Libelle or "")
            it_mnt = QTableWidgetItem(_fmt(p.MontantAnnuel))
            it_mnt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            etat = "Actif" if p.IsActive else "Inactif"
            it_etat = QTableWidgetItem(etat)
            it_etat.setTextAlignment(Qt.AlignCenter)
            if p.IsActive:
                it_etat.setForeground(QColor(COLORS["success"]))
            else:
                it_etat.setForeground(QColor(COLORS["muted"]))
            it_id = QTableWidgetItem(str(p.IDPrestation))

            for col, item in enumerate([it_code, it_lib, it_mnt, it_etat, it_id]):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, col, item)
            self.table.setRowHeight(i, 34)

        self.selected_prestation_id = None
        self.btn_toggle.setEnabled(False)
        self._reset_form()

    def _load_prestataires(self):
        self.cmb_prestataire.blockSignals(True)
        self.cmb_prestataire.clear()
        self.cmb_prestataire.addItem("— Aucun prestataire —", None)
        for prest in PrestationService.get_all_prestataires():
            self.cmb_prestataire.addItem(prest.Nom, prest.IDPrestataire)
        self.cmb_prestataire.blockSignals(False)

    def _on_selection_changed(self):
        ranges = self.table.selectedRanges()
        if not ranges:
            self.selected_prestation_id = None
            self.btn_toggle.setEnabled(False)
            self._reset_form()
            return

        row = ranges[0].topRow()
        id_item = self.table.item(row, 4)
        if not id_item:
            return
        self.selected_prestation_id = int(id_item.text())
        self.btn_toggle.setEnabled(self.can_modify)
        self._populate_form(self.selected_prestation_id)

    def _populate_form(self, id_prestation: int):
        p = PrestationService.get_prestation_by_id(id_prestation)
        if not p:
            return
        self.lbl_form_title.setText(f"Modifier : {p.Libelle}")
        self.txt_code.setText(p.Code or "")
        self.txt_libelle.setText(p.Libelle or "")
        self.txt_montant.setText(str(int(float(p.MontantAnnuel or 0))))

        # Sélectionner le prestataire dans le combo
        idx = self.cmb_prestataire.findData(p.IDPrestataire)
        self.cmb_prestataire.setCurrentIndex(max(idx, 0))

    def _reset_form(self):
        self.lbl_form_title.setText("Nouvelle prestation")
        self.txt_code.clear()
        self.txt_libelle.clear()
        self.txt_montant.clear()
        self.cmb_prestataire.setCurrentIndex(0)
        self.selected_prestation_id = None
        self.table.clearSelection()
        self.btn_toggle.setEnabled(False)

    def _on_nouveau(self):
        self._reset_form()
        self.txt_code.setFocus()

    def _on_save(self):
        if not self.can_modify:
            show_error(self, "Accès refusé", "Vous n'avez pas le droit PRESTATIONS_MODIFIER.")
            return

        data = {
            "Code": self.txt_code.text().strip().upper(),
            "Libelle": self.txt_libelle.text().strip(),
            "MontantAnnuel": self.txt_montant.text().strip() or "0",
            "IDPrestataire": self.cmb_prestataire.currentData(),
        }

        # Validation montant
        try:
            float(data["MontantAnnuel"])
        except ValueError:
            show_error(self, "Erreur de saisie", "Le montant annuel doit être un nombre.")
            return

        if self.selected_prestation_id:
            ok, msg = PrestationService.update_prestation(self.selected_prestation_id, data)
        else:
            ok, msg = PrestationService.create_prestation(data)

        if ok:
            show_info(self, "Succès", msg)
            self.refresh_data()
        else:
            show_error(self, "Erreur", msg)

    def _on_toggle(self):
        if not self.can_modify:
            show_error(self, "Accès refusé", "Vous n'avez pas le droit PRESTATIONS_MODIFIER.")
            return
        if not self.selected_prestation_id:
            return
        ok, msg = PrestationService.toggle_active(self.selected_prestation_id)
        if ok:
            self.refresh_data()
        else:
            show_error(self, "Erreur", msg)

    def _on_add_prestataire(self):
        if not self.can_modify:
            show_error(self, "Accès refusé", "Vous n'avez pas le droit PRESTATIONS_MODIFIER.")
            return
        nom = self.txt_new_prestataire.text().strip()
        if not nom:
            show_error(self, "Erreur", "Saisissez un nom de prestataire.")
            return
        ok, msg = PrestationService.create_prestataire(nom)
        if ok:
            self.txt_new_prestataire.clear()
            self._load_prestataires()
            show_info(self, "Succès", msg)
        else:
            show_error(self, "Erreur", msg)

    # ─── Tarifs par niveau ────────────────────────────────────────────────────

    def _load_tarifs_niveau(self):
        active_annee_id = AppSession.get_active_annee_id()

        # Combo des prestations
        self.cmb_tarif_prestation.blockSignals(True)
        self.cmb_tarif_prestation.clear()
        for p in PrestationService.get_all_prestations():
            self.cmb_tarif_prestation.addItem(f"{p.Code} - {p.Libelle}", p.IDPrestation)
        self.cmb_tarif_prestation.blockSignals(False)

        # Grille des niveaux (toutes cochées par defaut)
        while self._niveaux_layout.count():
            item = self._niveaux_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._niveau_checkboxes.clear()

        if active_annee_id:
            niveaux = NiveauService.get_all_with_cycle()
            for i, n in enumerate(niveaux):
                cb = QCheckBox(n["Libelle"])
                cb.setChecked(True)
                row, col = divmod(i, 2)
                self._niveaux_layout.addWidget(cb, row, col)
                self._niveau_checkboxes.append((cb, n["IDT_Niveau"]))

        # Tableau des tarifs deja programmes
        self.table_tarifs.setRowCount(0)
        self.selected_tarif_ids = []
        self.btn_tarif_delete.setEnabled(False)
        if not active_annee_id:
            return

        tarifs = PrestationService.get_tarifs_niveau_by_annee(active_annee_id)
        self.table_tarifs.setRowCount(len(tarifs))
        for i, t in enumerate(tarifs):
            nom_prestation = f"{t.prestation.Code} - {t.prestation.Libelle}" if t.prestation else "Inconnu"
            lib_niveau = t.niveau.Libelle if t.niveau else "Inconnu"
            montant_aff = f"{int(t.MontantAnnuel):,} F".replace(",", " ")

            for col, val in enumerate([nom_prestation, lib_niveau, montant_aff, str(t.IDPrestationTarif)]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_tarifs.setItem(i, col, item)

    def _on_tarif_row_selected(self):
        rows = set(idx.row() for idx in self.table_tarifs.selectedIndexes())
        self.selected_tarif_ids = []
        for row in rows:
            item_id = self.table_tarifs.item(row, 3)
            if item_id:
                self.selected_tarif_ids.append(int(item_id.text()))
        self.btn_tarif_delete.setEnabled(self.can_modify and len(self.selected_tarif_ids) > 0)

    def _on_save_tarif_niveau(self):
        if not self.can_modify:
            show_error(self, "Accès refusé", "Vous n'avez pas le droit PRESTATIONS_MODIFIER.")
            return

        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            show_error(self, "Erreur", "Aucune année scolaire active.")
            return

        if self.cmb_tarif_prestation.currentIndex() == -1:
            show_error(self, "Sélection requise", "Veuillez sélectionner une prestation.")
            return

        niveaux_coches = [(cb, id_niv) for cb, id_niv in self._niveau_checkboxes if cb.isChecked()]
        if not niveaux_coches:
            show_error(self, "Aucun niveau", "Veuillez cocher au moins un niveau.")
            return

        try:
            montant = float(self.txt_tarif_montant.text().strip() or 0)
        except ValueError:
            show_error(self, "Erreur de saisie", "Montant invalide.")
            return

        if montant <= 0:
            show_error(self, "Montant invalide", "Le montant doit être supérieur à 0.")
            return

        id_prestation = self.cmb_tarif_prestation.currentData()
        erreurs = []
        for _, id_niveau in niveaux_coches:
            ok, msg = PrestationService.save_tarif_niveau(active_annee_id, id_niveau, id_prestation, montant)
            if not ok:
                erreurs.append(msg)

        if erreurs:
            show_error(self, "Avertissement", f"{len(erreurs)} erreur(s) lors de l'enregistrement.")
        else:
            show_info(self, "Succès", f"Tarif enregistré pour {len(niveaux_coches)} niveau(x).")

        self.txt_tarif_montant.setText("0")
        self._load_tarifs_niveau()

    def _on_delete_tarif_niveau(self):
        if not self.can_modify:
            show_error(self, "Accès refusé", "Vous n'avez pas le droit PRESTATIONS_MODIFIER.")
            return
        if not self.selected_tarif_ids:
            return
        if not show_confirm(
            self, "Confirmation",
            f"Retirer {len(self.selected_tarif_ids)} tarif(s) sélectionné(s) ?"
        ):
            return

        erreurs = []
        for id_tarif in self.selected_tarif_ids:
            ok, msg = PrestationService.delete_tarif_niveau(id_tarif)
            if not ok:
                erreurs.append(msg)

        if erreurs:
            show_error(self, "Erreur", f"{len(erreurs)} suppression(s) échouée(s).")
        self._load_tarifs_niveau()
