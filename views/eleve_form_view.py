from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QGroupBox, QGridLayout,
    QScrollArea, QWidget, QDateEdit, QFileDialog, QFrame,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from services.eleve_service import EleveService
from services.nationalite_service import NationaliteService
from services.religion_service import ReligionService
from services.famille_service import FamilleService
from datetime import date
import os
import pathlib
from app.styles import (
    COLORS, apply_modal_style
)

_ASSETS = str(pathlib.Path(__file__).parent.parent / "assets").replace("\\", "/")

# ---------------------------------------------------------------------------
# Styles locaux — design premium pour EleveFormView
# ---------------------------------------------------------------------------
_SECTION_CARD = f"""
QGroupBox {{
    font-size: 11px;
    font-weight: 700;
    color: {COLORS['primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    margin-top: 20px;
    background-color: {COLORS['card']};
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    color: {COLORS['primary']};
    background-color: {COLORS['card']};
    font-size: 11px;
    font-weight: 700;
}}
"""

_INPUT = f"""
QLineEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    padding: 0 12px;
    min-height: 44px;
    max-height: 48px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1.5px solid {COLORS['primary']};
    background-color: #FAFCFF;
}}
QLineEdit::placeholder {{
    color: #94A3B8;
    font-style: normal;
}}
"""

_COMBO = f"""
QComboBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    padding: 0 12px;
    min-height: 44px;
    max-height: 48px;
    font-size: 13px;
}}
QComboBox:focus {{
    border: 1.5px solid {COLORS['primary']};
    background-color: #FAFCFF;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {COLORS['border']};
    border-radius: 0 8px 8px 0;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['selection']};
    selection-color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
"""

_DATE = f"""
QDateEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    padding: 0 12px;
    min-height: 44px;
    max-height: 48px;
    font-size: 13px;
}}
QDateEdit:focus {{
    border: 1.5px solid {COLORS['primary']};
    background-color: #FAFCFF;
}}
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: transparent;
}}
QDateEdit::down-arrow {{
    image: url({_ASSETS}/arrow_down.svg);
    width: 12px;
    height: 8px;
}}
"""

_AGE_BADGE = f"""
QLineEdit {{
    background-color: #F1F5F9;
    color: #64748B;
    font-weight: 600;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 0 12px;
    min-height: 44px;
    max-height: 48px;
    font-size: 13px;
}}
"""

_BTN_FOOTER_SECONDARY = f"""
QPushButton {{
    background-color: {COLORS['card']};
    color: #374151;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 0 20px;
    min-height: 40px;
    max-height: 44px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {COLORS['bg']};
    border-color: #CBD5E1;
}}
QPushButton:pressed {{
    background-color: #F1F5F9;
}}
"""

_BTN_FOOTER_PRIMARY = f"""
QPushButton {{
    background-color: {COLORS['primary']};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 0 28px;
    min-height: 40px;
    max-height: 44px;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton:hover {{
    background-color: {COLORS['primary_dark']};
}}
QPushButton:pressed {{
    background-color: #1E3A8A;
}}
QPushButton:disabled {{
    background-color: #E5E7EB;
    color: #9CA3AF;
}}
"""

_CHECKBOX = f"""
QCheckBox {{
    font-size: 12px;
    font-weight: 500;
    color: {COLORS['text']};
    background-color: transparent;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1.5px solid #CBD5E1;
    border-radius: 4px;
    background-color: #FFFFFF;
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
"""


class EleveFormView(QDialog):
    """Formulaire d'enregistrement / modification d'un élève."""

    def __init__(self, parent=None, id_eleve=None):
        super().__init__(parent)
        self.id_eleve = id_eleve
        self.setWindowTitle("Fiche Élève")
        self.resize(800, 720)
        self.photo_path = None
        apply_modal_style(self)
        self.init_ui()
        self.load_combos()
        if self.id_eleve:
            self.load_eleve()
        else:
            self.proposer_matricule()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── En-tête ──────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary_dark']};
                border-radius: 0;
            }}
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(24, 16, 24, 16)
        h_layout.setSpacing(4)

        lbl_titre = QLabel("ENREGISTREMENT ÉLÈVE")
        lbl_titre.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #FFFFFF;"
            "background-color: transparent; border: none;"
        )
        lbl_soustitre = QLabel(
            "Saisir l'identité, l'extrait de naissance et les contacts d'urgence de l'élève"
        )
        lbl_soustitre.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.7);"
            "background-color: transparent; border: none;"
        )
        h_layout.addWidget(lbl_titre)
        h_layout.addWidget(lbl_soustitre)
        main_layout.addWidget(header)

        # ── Corps scrollable ─────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: {COLORS['bg']}; }}"
        )

        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['bg']};")
        grid_layout = QVBoxLayout(container)
        grid_layout.setContentsMargins(20, 18, 20, 20)
        grid_layout.setSpacing(16)

        # ── SECTION 1 : Identification ───────────────────────────────────────
        box_id = QGroupBox("ÉLÈVE — IDENTIFICATION")
        box_id.setStyleSheet(_SECTION_CARD)
        id_layout = QGridLayout(box_id)
        id_layout.setContentsMargins(16, 18, 16, 16)
        id_layout.setHorizontalSpacing(14)
        id_layout.setVerticalSpacing(10)
        id_layout.setColumnStretch(1, 1)
        id_layout.setColumnStretch(3, 1)
        id_layout.setColumnMinimumWidth(0, 120)
        id_layout.setColumnMinimumWidth(2, 100)

        lbl_mat = self._lbl("Matricule interne * :")
        self.txt_matricule = self._field("Ex : 26-001")

        lbl_nom = self._lbl("Nom * :")
        self.txt_nom = self._field()

        lbl_prenoms = self._lbl("Prénoms * :")
        self.txt_prenoms = self._field()

        lbl_sexe = self._lbl("Sexe * :")
        self.cmb_sexe = self._combo(["Masculin", "Féminin"])

        lbl_nais = self._lbl("Né(e) le * :")
        self.date_nais = QDateEdit()
        self.date_nais.setCalendarPopup(True)
        self.date_nais.setDisplayFormat("dd/MM/yyyy")
        self.date_nais.setDate(QDate.currentDate().addYears(-6))
        self.date_nais.setStyleSheet(_DATE)
        self.date_nais.dateChanged.connect(self.calculer_age)

        lbl_age = self._lbl("Âge :")
        self.txt_age = QLineEdit()
        self.txt_age.setReadOnly(True)
        self.txt_age.setMaximumWidth(100)
        self.txt_age.setStyleSheet(_AGE_BADGE)

        lbl_lieu = self._lbl("Lieu naissance :")
        self.txt_lieu_nais = self._field()

        lbl_hab = self._lbl("Habitation :")
        self.txt_habitation = self._field()

        lbl_nat = self._lbl("Nationalité :")
        self.cmb_nationalite = self._combo()

        lbl_rel = self._lbl("Religion :")
        self.cmb_religion = self._combo()

        lbl_fam = self._lbl("Famille Responsable :")
        self.cmb_famille = self._combo()

        lbl_mat_nat = self._lbl("Matricule national (principal) :")
        self.txt_matricule_national = self._field("N° Ministère")

        lbl_2lang = self._lbl("2ème langue :")
        self.txt_deuxieme_langue = self._field()

        lbl_etab_orig = self._lbl("Établissement d'origine :")
        self.txt_etablissement_origine = self._field()

        lbl_classe_orig = self._lbl("Classe suivie :")
        self.txt_classe_origine = self._field()

        lbl_vit_chez = self._lbl("L'élève vit chez :")
        self.cmb_vit_chez = self._combo(["Ses parents (père et mère)", "Son père", "Sa mère", "Un tuteur"])

        id_layout.addWidget(lbl_mat, 0, 0)
        id_layout.addWidget(self.txt_matricule, 0, 1)
        id_layout.addWidget(lbl_nom, 0, 2)
        id_layout.addWidget(self.txt_nom, 0, 3)

        id_layout.addWidget(lbl_prenoms, 1, 0)
        id_layout.addWidget(self.txt_prenoms, 1, 1, 1, 3)

        id_layout.addWidget(lbl_nais, 2, 0)
        id_layout.addWidget(self.date_nais, 2, 1)
        id_layout.addWidget(lbl_age, 2, 2)
        id_layout.addWidget(self.txt_age, 2, 3, Qt.AlignLeft | Qt.AlignVCenter)

        id_layout.addWidget(lbl_lieu, 3, 0)
        id_layout.addWidget(self.txt_lieu_nais, 3, 1)
        id_layout.addWidget(lbl_sexe, 3, 2)
        id_layout.addWidget(self.cmb_sexe, 3, 3)

        id_layout.addWidget(lbl_hab, 4, 0)
        id_layout.addWidget(self.txt_habitation, 4, 1)
        id_layout.addWidget(lbl_nat, 4, 2)
        id_layout.addWidget(self.cmb_nationalite, 4, 3)

        id_layout.addWidget(lbl_rel, 5, 0)
        id_layout.addWidget(self.cmb_religion, 5, 1)
        id_layout.addWidget(lbl_fam, 5, 2)
        id_layout.addWidget(self.cmb_famille, 5, 3)

        id_layout.addWidget(lbl_mat_nat, 6, 0)
        id_layout.addWidget(self.txt_matricule_national, 6, 1)
        id_layout.addWidget(lbl_2lang, 6, 2)
        id_layout.addWidget(self.txt_deuxieme_langue, 6, 3)

        id_layout.addWidget(lbl_etab_orig, 7, 0)
        id_layout.addWidget(self.txt_etablissement_origine, 7, 1)
        id_layout.addWidget(lbl_classe_orig, 7, 2)
        id_layout.addWidget(self.txt_classe_origine, 7, 3)

        id_layout.addWidget(lbl_vit_chez, 8, 0)
        id_layout.addWidget(self.cmb_vit_chez, 8, 1, 1, 3)

        grid_layout.addWidget(box_id)

        # ── SECTION 2 : Extrait + Photo ──────────────────────────────────────
        extraits_photo_layout = QHBoxLayout()
        extraits_photo_layout.setSpacing(16)

        box_extr = QGroupBox("INFOS COMPLÉMENTAIRES / EXTRAIT")
        box_extr.setStyleSheet(_SECTION_CARD)
        extr_layout = QGridLayout(box_extr)
        extr_layout.setContentsMargins(16, 18, 16, 16)
        extr_layout.setHorizontalSpacing(14)
        extr_layout.setVerticalSpacing(10)
        extr_layout.setColumnStretch(1, 1)
        extr_layout.setColumnMinimumWidth(0, 120)

        lbl_num_ext = self._lbl("N° Extrait :")
        self.txt_num_ext = self._field()

        lbl_date_ext = self._lbl("Délivré le :")
        self.date_ext = QDateEdit()
        self.date_ext.setCalendarPopup(True)
        self.date_ext.setDisplayFormat("dd/MM/yyyy")
        self.date_ext.setDate(QDate.currentDate())
        self.date_ext.setStyleSheet(_DATE)

        lbl_lieu_ext = self._lbl("Lieu Délivrance :")
        self.txt_lieu_ext = self._field()

        extr_layout.addWidget(lbl_num_ext, 0, 0)
        extr_layout.addWidget(self.txt_num_ext, 0, 1)
        extr_layout.addWidget(lbl_date_ext, 1, 0)
        extr_layout.addWidget(self.date_ext, 1, 1)
        extr_layout.addWidget(lbl_lieu_ext, 2, 0)
        extr_layout.addWidget(self.txt_lieu_ext, 2, 1)

        extraits_photo_layout.addWidget(box_extr, 2)

        # --- Zone Photo ---
        box_photo = QGroupBox("PHOTO DE L'ÉLÈVE")
        box_photo.setStyleSheet(_SECTION_CARD)
        photo_layout = QVBoxLayout(box_photo)
        photo_layout.setAlignment(Qt.AlignCenter)
        photo_layout.setSpacing(12)
        photo_layout.setContentsMargins(14, 18, 14, 16)

        self.lbl_image_frame = QLabel()
        self.lbl_image_frame.setFixedSize(120, 148)
        self.lbl_image_frame.setStyleSheet(
            f"border: 2px dashed {COLORS['input_border']};"
            f"background-color: {COLORS['bg']};"
            "border-radius: 8px;"
            "color: #94A3B8; font-size: 12px;"
        )
        self.lbl_image_frame.setAlignment(Qt.AlignCenter)
        self.lbl_image_frame.setText("📷\nAucune photo")

        self.btn_parcourir = QPushButton("📂  Parcourir…")
        self.btn_parcourir.setStyleSheet(_BTN_FOOTER_SECONDARY)
        self.btn_parcourir.setFixedWidth(140)
        self.btn_parcourir.setFixedHeight(40)
        self.btn_parcourir.clicked.connect(self.parcourir_photo)

        photo_layout.addWidget(self.lbl_image_frame)
        photo_layout.addWidget(self.btn_parcourir)

        extraits_photo_layout.addWidget(box_photo, 1)
        grid_layout.addLayout(extraits_photo_layout)

        # ── SECTION 3 : Urgence ──────────────────────────────────────────────
        box_urg = QGroupBox("PERSONNE À CONTACTER EN CAS D'URGENCE")
        box_urg.setStyleSheet(_SECTION_CARD)
        urg_layout = QGridLayout(box_urg)
        urg_layout.setContentsMargins(16, 18, 16, 16)
        urg_layout.setHorizontalSpacing(14)
        urg_layout.setVerticalSpacing(10)
        urg_layout.setColumnStretch(1, 1)
        urg_layout.setColumnStretch(3, 1)
        urg_layout.setColumnMinimumWidth(0, 120)
        urg_layout.setColumnMinimumWidth(2, 90)

        lbl_nom_u = self._lbl("Nom & Prénoms :")
        self.txt_nom_urg = self._field()

        lbl_cont_u = self._lbl("Contact :")
        self.txt_cont_urg = self._field()

        lbl_hab_u = self._lbl("Habitation :")
        self.txt_hab_urg = self._field()

        urg_layout.addWidget(lbl_nom_u, 0, 0)
        urg_layout.addWidget(self.txt_nom_urg, 0, 1)
        urg_layout.addWidget(lbl_cont_u, 0, 2)
        urg_layout.addWidget(self.txt_cont_urg, 0, 3)
        urg_layout.addWidget(lbl_hab_u, 1, 0)
        urg_layout.addWidget(self.txt_hab_urg, 1, 1)

        grid_layout.addWidget(box_urg)

        # ── SECTION 4 : Religion ─────────────────────────────────────────────
        box_rel = QGroupBox("RENSEIGNEMENTS D'ORDRE RELIGIEUX")
        box_rel.setStyleSheet(_SECTION_CARD)
        rel_layout = QGridLayout(box_rel)
        rel_layout.setContentsMargins(16, 18, 16, 16)
        rel_layout.setHorizontalSpacing(14)
        rel_layout.setVerticalSpacing(10)
        rel_layout.setColumnStretch(1, 1)
        rel_layout.setColumnStretch(3, 1)
        rel_layout.setColumnMinimumWidth(0, 120)
        rel_layout.setColumnMinimumWidth(2, 100)

        self.chk_baptise = QCheckBox("Baptisé(e)")
        self.chk_baptise.setStyleSheet(_CHECKBOX)
        self.chk_confirme = QCheckBox("Confirmé(e)")
        self.chk_confirme.setStyleSheet(_CHECKBOX)

        lbl_paroisse = self._lbl("Paroisse actuelle :")
        self.txt_paroisse = self._field()
        lbl_activite = self._lbl("Activité paroissiale :")
        self.txt_activite_paroisse = self._field()
        lbl_eglise = self._lbl("Préciser l'église :")
        self.txt_preciser_eglise = self._field("Si protestant ou autre confession")

        rel_layout.addWidget(self.chk_baptise, 0, 0, 1, 2)
        rel_layout.addWidget(self.chk_confirme, 0, 2, 1, 2)
        rel_layout.addWidget(lbl_paroisse, 1, 0)
        rel_layout.addWidget(self.txt_paroisse, 1, 1)
        rel_layout.addWidget(lbl_activite, 1, 2)
        rel_layout.addWidget(self.txt_activite_paroisse, 1, 3)
        rel_layout.addWidget(lbl_eglise, 2, 0)
        rel_layout.addWidget(self.txt_preciser_eglise, 2, 1, 1, 3)

        grid_layout.addWidget(box_rel)

        # ── SECTION 5 : Cursus scolaire antérieur ────────────────────────────
        box_cursus = QGroupBox("CURSUS SCOLAIRE ANTÉRIEUR")
        box_cursus.setStyleSheet(_SECTION_CARD)
        cursus_layout = QVBoxLayout(box_cursus)
        cursus_layout.setContentsMargins(16, 18, 16, 16)
        cursus_layout.setSpacing(8)

        self.tbl_cursus = QTableWidget(0, 4)
        self.tbl_cursus.setHorizontalHeaderLabels(["Années", "Classe", "Moyenne annuelle", "Établissement"])
        self.tbl_cursus.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_cursus.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_cursus.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_cursus.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_cursus.verticalHeader().setVisible(False)
        self.tbl_cursus.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_cursus.setFixedHeight(160)
        cursus_layout.addWidget(self.tbl_cursus)

        cursus_btns = QHBoxLayout()
        self.btn_cursus_ajouter = QPushButton("+ Ajouter une ligne")
        self.btn_cursus_ajouter.setStyleSheet(_BTN_FOOTER_SECONDARY)
        self.btn_cursus_ajouter.clicked.connect(self.ajouter_ligne_cursus)
        self.btn_cursus_supprimer = QPushButton("Supprimer la ligne sélectionnée")
        self.btn_cursus_supprimer.setStyleSheet(_BTN_FOOTER_SECONDARY)
        self.btn_cursus_supprimer.clicked.connect(self.supprimer_ligne_cursus)
        cursus_btns.addWidget(self.btn_cursus_ajouter)
        cursus_btns.addWidget(self.btn_cursus_supprimer)
        cursus_btns.addStretch()
        cursus_layout.addLayout(cursus_btns)

        grid_layout.addWidget(box_cursus)

        # ── SECTION 6 : Documents à fournir + cadre direction ────────────────
        docs_dossier_layout = QHBoxLayout()
        docs_dossier_layout.setSpacing(16)

        box_docs = QGroupBox("DOCUMENTS À FOURNIR")
        box_docs.setStyleSheet(_SECTION_CARD)
        docs_layout = QGridLayout(box_docs)
        docs_layout.setContentsMargins(16, 18, 16, 16)
        docs_layout.setHorizontalSpacing(14)
        docs_layout.setVerticalSpacing(6)

        self.chk_doc_extrait = QCheckBox("Copie de l'extrait d'acte de naissance")
        self.chk_doc_certif_scol = QCheckBox("Certificat de scolarité")
        self.chk_doc_bulletins = QCheckBox("Photocopie des 3 bulletins / relevé de notes")
        self.chk_doc_photos = QCheckBox("6 photos d'identité")
        self.chk_doc_carnet_vaccin = QCheckBox("Photocopie du carnet de vaccination")
        self.chk_doc_carnet_sante = QCheckBox("Carnet de santé")
        self.chk_doc_dispense_eps = QCheckBox("Dispensé(e) d'éducation physique et sportive")
        self.chk_doc_dispense_eps_certif = QCheckBox("Certificat de dispense fourni")
        self.chk_doc_carte_sejour = QCheckBox("Photocopie carte de séjour (étranger, 16 ans et +)")
        self.chk_doc_livret_scol = QCheckBox("Livret scolaire")
        self.chk_autorisation_courrier = QCheckBox("Autorise l'élève à recevoir du courrier par l'école")

        for i, chk in enumerate([
            self.chk_doc_extrait, self.chk_doc_certif_scol, self.chk_doc_bulletins,
            self.chk_doc_photos, self.chk_doc_carnet_vaccin, self.chk_doc_carnet_sante,
            self.chk_doc_dispense_eps, self.chk_doc_dispense_eps_certif,
            self.chk_doc_carte_sejour, self.chk_doc_livret_scol,
            self.chk_autorisation_courrier,
        ]):
            chk.setStyleSheet(_CHECKBOX)
            docs_layout.addWidget(chk, i, 0)

        docs_dossier_layout.addWidget(box_docs, 2)

        box_dossier = QGroupBox("CADRE RÉSERVÉ À LA DIRECTION")
        box_dossier.setStyleSheet(_SECTION_CARD)
        dossier_layout = QGridLayout(box_dossier)
        dossier_layout.setContentsMargins(16, 18, 16, 16)
        dossier_layout.setHorizontalSpacing(14)
        dossier_layout.setVerticalSpacing(10)
        dossier_layout.setColumnMinimumWidth(0, 110)

        lbl_ndossier = self._lbl("N° du dossier :")
        self.txt_ndossier = self._field()
        lbl_date_admission = self._lbl("Date d'admission :")
        self.date_admission = QDateEdit()
        self.date_admission.setCalendarPopup(True)
        self.date_admission.setDisplayFormat("dd/MM/yyyy")
        self.date_admission.setSpecialValueText(" ")
        self.date_admission.setDate(QDate(2000, 1, 1))
        self.date_admission.setMinimumDate(QDate(2000, 1, 1))
        self.date_admission.setStyleSheet(_DATE)

        dossier_layout.addWidget(lbl_ndossier, 0, 0)
        dossier_layout.addWidget(self.txt_ndossier, 0, 1)
        dossier_layout.addWidget(lbl_date_admission, 1, 0)
        dossier_layout.addWidget(self.date_admission, 1, 1)
        dossier_layout.setRowStretch(2, 1)

        docs_dossier_layout.addWidget(box_dossier, 1)
        grid_layout.addLayout(docs_dossier_layout)

        # ── SECTION 7 : Renseignements médicaux ──────────────────────────────
        box_med = QGroupBox("RENSEIGNEMENTS MÉDICAUX")
        box_med.setStyleSheet(_SECTION_CARD)
        med_layout = QGridLayout(box_med)
        med_layout.setContentsMargins(16, 18, 16, 16)
        med_layout.setHorizontalSpacing(14)
        med_layout.setVerticalSpacing(10)
        med_layout.setColumnStretch(1, 1)
        med_layout.setColumnStretch(3, 1)
        med_layout.setColumnMinimumWidth(0, 130)
        med_layout.setColumnMinimumWidth(2, 90)

        self.txt_accident_nom1 = self._field("Nom du responsable")
        self.txt_accident_tel1 = self._field("Tél.")
        self.txt_accident_cel1 = self._field("Cel.")
        self.txt_accident_bureau1 = self._field("Bureau")
        self.txt_accident_nom2 = self._field("Nom du responsable")
        self.txt_accident_tel2 = self._field("Tél.")
        self.txt_accident_cel2 = self._field("Cel.")
        self.txt_accident_bureau2 = self._field("Bureau")
        self.txt_accident_adresse = self._field()

        self.chk_conduire_hopital = QCheckBox("Faut-il la conduire à l'hôpital ?")
        self.chk_conduire_hopital.setStyleSheet(_CHECKBOX)
        self.txt_conduire_hopital_precision = self._field("Précisez")
        self.chk_conduire_clinique = QCheckBox("Faut-il la conduire à la clinique ?")
        self.chk_conduire_clinique.setStyleSheet(_CHECKBOX)
        self.txt_conduire_clinique_precision = self._field("Précisez")

        self.txt_medecin_nom = self._field("Nom du médecin traitant")
        self.txt_medecin_tel = self._field("Tél.")
        self.txt_medecin_cel = self._field("Cel.")
        self.txt_medecin_bureau = self._field("Bureau")
        self.txt_medecin_adresse = self._field()

        self.txt_maladie = self._field("Asthme, diabète, drépanocytose, épilepsie…")
        self.txt_contre_indications = self._field("Aspirine, nivaquine…")

        r = 0
        med_layout.addWidget(self._section_hdr("Responsable à prévenir en cas d'accident"), r, 0, 1, 4)
        r += 1
        med_layout.addWidget(self._lbl("Nom 1 :"), r, 0)
        med_layout.addWidget(self.txt_accident_nom1, r, 1)
        med_layout.addWidget(self._lbl("Tél. / Cel. / Bureau :"), r, 2)
        med_layout.addWidget(self.txt_accident_tel1, r, 3)
        r += 1
        med_layout.addWidget(self.txt_accident_cel1, r, 2)
        med_layout.addWidget(self.txt_accident_bureau1, r, 3)
        r += 1
        med_layout.addWidget(self._lbl("Nom 2 :"), r, 0)
        med_layout.addWidget(self.txt_accident_nom2, r, 1)
        med_layout.addWidget(self._lbl("Tél. / Cel. / Bureau :"), r, 2)
        med_layout.addWidget(self.txt_accident_tel2, r, 3)
        r += 1
        med_layout.addWidget(self.txt_accident_cel2, r, 2)
        med_layout.addWidget(self.txt_accident_bureau2, r, 3)
        r += 1
        med_layout.addWidget(self._lbl("Adresse :"), r, 0)
        med_layout.addWidget(self.txt_accident_adresse, r, 1, 1, 3)
        r += 1
        med_layout.addWidget(self.chk_conduire_hopital, r, 0, 1, 2)
        med_layout.addWidget(self.txt_conduire_hopital_precision, r, 2, 1, 2)
        r += 1
        med_layout.addWidget(self.chk_conduire_clinique, r, 0, 1, 2)
        med_layout.addWidget(self.txt_conduire_clinique_precision, r, 2, 1, 2)
        r += 1

        med_layout.addWidget(self._section_hdr("Médecin traitant"), r, 0, 1, 4)
        r += 1
        med_layout.addWidget(self._lbl("Nom :"), r, 0)
        med_layout.addWidget(self.txt_medecin_nom, r, 1)
        med_layout.addWidget(self._lbl("Tél. :"), r, 2)
        med_layout.addWidget(self.txt_medecin_tel, r, 3)
        r += 1
        med_layout.addWidget(self._lbl("Cel. :"), r, 0)
        med_layout.addWidget(self.txt_medecin_cel, r, 1)
        med_layout.addWidget(self._lbl("Bureau :"), r, 2)
        med_layout.addWidget(self.txt_medecin_bureau, r, 3)
        r += 1
        med_layout.addWidget(self._lbl("Adresse :"), r, 0)
        med_layout.addWidget(self.txt_medecin_adresse, r, 1, 1, 3)
        r += 1

        med_layout.addWidget(self._section_hdr("Informations complémentaires"), r, 0, 1, 4)
        r += 1
        med_layout.addWidget(self._lbl("Maladie(s) :"), r, 0)
        med_layout.addWidget(self.txt_maladie, r, 1, 1, 3)
        r += 1
        med_layout.addWidget(self._lbl("Contre-indications :"), r, 0)
        med_layout.addWidget(self.txt_contre_indications, r, 1, 1, 3)

        grid_layout.addWidget(box_med)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # ── Pied de page ─────────────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 14, 20, 14)
        footer_layout.setSpacing(10)
        footer_layout.addStretch()

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(_BTN_FOOTER_SECONDARY)
        self.btn_fermer.setFixedWidth(120)
        self.btn_fermer.clicked.connect(self.reject)

        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(_BTN_FOOTER_PRIMARY)
        self.btn_valider.setFixedWidth(140)
        self.btn_valider.clicked.connect(self.save_data)

        footer_layout.addWidget(self.btn_fermer)
        footer_layout.addWidget(self.btn_valider)
        main_layout.addWidget(footer)

        self.calculer_age()

    # ── Helpers constructeurs ────────────────────────────────────────────────

    def _lbl(self, text: str = "", color: str = "#374151") -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {color};"
            "background-color: transparent; border: none;"
        )
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _section_hdr(self, text: str) -> QLabel:
        """Libellé d'en-tête interne (sous-section dans un QGroupBox), aligné à gauche."""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {COLORS['primary']};"
            "background-color: transparent; border: none; letter-spacing: 0.3px;"
        )
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        return lbl

    def _field(self, placeholder: str = "") -> QLineEdit:
        f = QLineEdit()
        if placeholder:
            f.setPlaceholderText(placeholder)
        f.setStyleSheet(_INPUT)
        return f

    def _combo(self, items: list = None) -> QComboBox:
        c = QComboBox()
        if items:
            c.addItems(items)
        c.setStyleSheet(_COMBO)
        return c

    # ── Logique ──────────────────────────────────────────────────────────────

    def load_combos(self):
        self.cmb_nationalite.clear()
        self.cmb_nationalite.addItem("[Aucune]", None)
        for nt in NationaliteService.get_all():
            self.cmb_nationalite.addItem(nt.Nationalite, nt.IDTNationalite)

        self.cmb_religion.clear()
        self.cmb_religion.addItem("[Aucune]", None)
        for rl in ReligionService.get_all():
            self.cmb_religion.addItem(rl.Religion, rl.IDTReligion)

        self.cmb_famille.clear()
        self.cmb_famille.addItem("[Aucune]", None)
        for fm in FamilleService.get_all_familles():
            self.cmb_famille.addItem(
                f"{fm.NomResponsable} ({fm.CellulaireResponsable})", fm.IdTFamille
            )

    def proposer_matricule(self):
        self.txt_matricule.setText(EleveService.generate_matricule())

    def calculer_age(self):
        qdate = self.date_nais.date()
        born = date(qdate.year(), qdate.month(), qdate.day())
        today = date.today()
        age = (
            today.year - born.year
            - ((today.month, today.day) < (born.month, born.day))
        )
        self.txt_age.setText(f"{age} an{'s' if age > 1 else ''}")

    def parcourir_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choisir la photo de l'élève", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.photo_path = file_path
            self.afficher_photo_preview(file_path)

    def afficher_photo_preview(self, path):
        if path and os.path.exists(path):
            pix = QPixmap(path)
            self.lbl_image_frame.setPixmap(
                pix.scaled(self.lbl_image_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.lbl_image_frame.clear()
            self.lbl_image_frame.setText("📷\nAucune photo")

    def load_eleve(self):
        el = EleveService.get_eleve_by_id(self.id_eleve)
        if not el:
            QMessageBox.warning(self, "Erreur", "L'élève demandé n'existe pas.")
            self.reject()
            return

        self.txt_matricule.setText(el.Matricule)
        self.txt_nom.setText(el.Nom)
        self.txt_prenoms.setText(el.Prenoms)
        self.cmb_sexe.setCurrentIndex(0 if el.Sexe == 1 else 1)

        if el.DateNaissance:
            self.date_nais.setDate(
                QDate(el.DateNaissance.year, el.DateNaissance.month, el.DateNaissance.day)
            )

        self.txt_lieu_nais.setText(el.LieuNaissance or "")
        self.txt_habitation.setText(el.Habitation or "")

        self._select_combo(self.cmb_nationalite, el.IDNationalite)
        self._select_combo(self.cmb_religion, el.IDReligion)
        self._select_combo(self.cmb_famille, el.IDFamille)

        self.txt_num_ext.setText(el.NumExtrait or "")
        if el.DateExtrait:
            self.date_ext.setDate(
                QDate(el.DateExtrait.year, el.DateExtrait.month, el.DateExtrait.day)
            )
        self.txt_lieu_ext.setText(el.LieuDelivrance or "")

        self.txt_nom_urg.setText(el.NomUrgence or "")
        self.txt_cont_urg.setText(el.ContactUrgence or "")
        self.txt_hab_urg.setText(el.HabitationUrgence or "")

        self.txt_matricule_national.setText(el.MatriculeNational or "")
        self.txt_deuxieme_langue.setText(el.DeuxiemeLangue or "")
        self.txt_etablissement_origine.setText(el.EtablissementOrigine or "")
        self.txt_classe_origine.setText(el.ClasseSuivieOrigine or "")
        try:
            self.cmb_vit_chez.setCurrentIndex(self.VIT_CHEZ_VALUES.index(el.VitChezQui) if el.VitChezQui else -1)
        except ValueError:
            self.cmb_vit_chez.setCurrentIndex(-1)

        self.chk_baptise.setChecked(bool(el.Baptise))
        self.chk_confirme.setChecked(bool(el.Confirme))
        self.txt_paroisse.setText(el.ParoisseActuelle or "")
        self.txt_activite_paroisse.setText(el.ActiviteParoisse or "")
        self.txt_preciser_eglise.setText(el.PreciserEglise or "")

        self.tbl_cursus.setRowCount(0)
        for ligne in (el.cursus_anterieur or []):
            self._ajouter_ligne_cursus_data(
                ligne.AnneeScolaire or "", ligne.Classe or "",
                "" if ligne.MoyenneAnnuelle is None else str(ligne.MoyenneAnnuelle),
                ligne.Etablissement or "",
            )

        self.chk_doc_extrait.setChecked(bool(el.DocExtraitNaissance))
        self.chk_doc_certif_scol.setChecked(bool(el.DocCertifScolarite))
        self.chk_doc_bulletins.setChecked(bool(el.DocBulletins))
        self.chk_doc_photos.setChecked(bool(el.DocPhotos))
        self.chk_doc_carnet_vaccin.setChecked(bool(el.DocCarnetVaccination))
        self.chk_doc_carnet_sante.setChecked(bool(el.DocCarnetSante))
        self.chk_doc_dispense_eps.setChecked(bool(el.DocDispenseEPS))
        self.chk_doc_dispense_eps_certif.setChecked(bool(el.DocDispenseEPSCertificat))
        self.chk_doc_carte_sejour.setChecked(bool(el.DocCarteSejour))
        self.chk_doc_livret_scol.setChecked(bool(el.DocLivretScolaire))
        self.chk_autorisation_courrier.setChecked(bool(el.AutorisationCourrier))

        self.txt_ndossier.setText(el.NDossier or "")
        if el.DateAdmission:
            self.date_admission.setDate(
                QDate(el.DateAdmission.year, el.DateAdmission.month, el.DateAdmission.day)
            )
        else:
            self.date_admission.setDate(self.date_admission.minimumDate())

        self.txt_accident_nom1.setText(el.AccidentNom1 or "")
        self.txt_accident_tel1.setText(el.AccidentTel1 or "")
        self.txt_accident_cel1.setText(el.AccidentCel1 or "")
        self.txt_accident_bureau1.setText(el.AccidentBureau1 or "")
        self.txt_accident_nom2.setText(el.AccidentNom2 or "")
        self.txt_accident_tel2.setText(el.AccidentTel2 or "")
        self.txt_accident_cel2.setText(el.AccidentCel2 or "")
        self.txt_accident_bureau2.setText(el.AccidentBureau2 or "")
        self.txt_accident_adresse.setText(el.AccidentAdresse or "")
        self.chk_conduire_hopital.setChecked(bool(el.ConduireHopital))
        self.txt_conduire_hopital_precision.setText(el.ConduireHopitalPrecision or "")
        self.chk_conduire_clinique.setChecked(bool(el.ConduireClinique))
        self.txt_conduire_clinique_precision.setText(el.ConduireCliniquePrecision or "")

        self.txt_medecin_nom.setText(el.MedecinNom or "")
        self.txt_medecin_tel.setText(el.MedecinTel or "")
        self.txt_medecin_cel.setText(el.MedecinCel or "")
        self.txt_medecin_bureau.setText(el.MedecinBureau or "")
        self.txt_medecin_adresse.setText(el.MedecinAdresse or "")

        self.txt_maladie.setText(el.Maladie or "")
        self.txt_contre_indications.setText(el.ContreIndications or "")

        if el.PhotoPath:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.photo_path = el.PhotoPath
            self.afficher_photo_preview(os.path.join(app_dir, el.PhotoPath))

        self.calculer_age()

    # ── Cursus scolaire antérieur (tableau libre) ───────────────────────────

    VIT_CHEZ_VALUES = ["PARENTS", "PERE", "MERE", "TUTEUR"]

    def _ajouter_ligne_cursus_data(self, annee: str, classe: str, moyenne: str, etablissement: str):
        row = self.tbl_cursus.rowCount()
        self.tbl_cursus.insertRow(row)
        self.tbl_cursus.setItem(row, 0, QTableWidgetItem(annee))
        self.tbl_cursus.setItem(row, 1, QTableWidgetItem(classe))
        self.tbl_cursus.setItem(row, 2, QTableWidgetItem(moyenne))
        self.tbl_cursus.setItem(row, 3, QTableWidgetItem(etablissement))

    def ajouter_ligne_cursus(self):
        self._ajouter_ligne_cursus_data("", "", "", "")

    def supprimer_ligne_cursus(self):
        rows = sorted({idx.row() for idx in self.tbl_cursus.selectedIndexes()}, reverse=True)
        for row in rows:
            self.tbl_cursus.removeRow(row)

    def _lire_lignes_cursus(self) -> list[dict]:
        def cell(row, col):
            item = self.tbl_cursus.item(row, col)
            return item.text().strip() if item else ""

        lignes = []
        for row in range(self.tbl_cursus.rowCount()):
            moyenne_txt = cell(row, 2).replace(",", ".")
            try:
                moyenne = float(moyenne_txt) if moyenne_txt else None
            except ValueError:
                moyenne = None
            lignes.append({
                "AnneeScolaire": cell(row, 0),
                "Classe": cell(row, 1),
                "MoyenneAnnuelle": moyenne,
                "Etablissement": cell(row, 3),
            })
        return lignes

    def _select_combo(self, combo: QComboBox, val):
        for idx in range(combo.count()):
            if combo.itemData(idx) == val:
                combo.setCurrentIndex(idx)
                break

    # Alias pour compatibilité appels existants
    def select_combo_by_data(self, combobox, val):
        self._select_combo(combobox, val)

    def save_data(self):
        if getattr(self, "_saving", False):
            return
        mat = self.txt_matricule.text().strip()
        nom = self.txt_nom.text().strip()
        prenoms = self.txt_prenoms.text().strip()

        q_dat_nais = self.date_nais.date()
        dt_nais = date(q_dat_nais.year(), q_dat_nais.month(), q_dat_nais.day())
        sexe_val = 1 if self.cmb_sexe.currentIndex() == 0 else 2

        if not mat:
            QMessageBox.warning(self, "Validation", "Le matricule est obligatoire.")
            self.txt_matricule.setFocus()
            return
        if not nom:
            QMessageBox.warning(self, "Validation", "Le nom de l'élève est obligatoire.")
            self.txt_nom.setFocus()
            return
        if not prenoms:
            QMessageBox.warning(self, "Validation", "Le prénom de l'élève est obligatoire.")
            self.txt_prenoms.setFocus()
            return
        if dt_nais > date.today():
            QMessageBox.warning(self, "Validation", "La date de naissance ne peut pas être dans le futur.")
            return
        # La famille n'est plus obligatoire à la création (parcours "élève
        # d'abord") : Eleve.IDFamille reste nullable en base, et l'inscription
        # elle-même refuse déjà tout élève sans famille associée
        # (InscriptionService.create_inscription) — pas besoin de bloquer ici.

        q_dat_extr = self.date_ext.date()
        dt_extr = date(q_dat_extr.year(), q_dat_extr.month(), q_dat_extr.day())

        data = {
            "Matricule":        mat,
            "Nom":              nom.upper(),
            "Prenoms":          prenoms,
            "DateNaissance":    dt_nais,
            "LieuNaissance":    self.txt_lieu_nais.text().strip(),
            "Sexe":             sexe_val,
            "IDNationalite":    self.cmb_nationalite.currentData(),
            "IDReligion":       self.cmb_religion.currentData(),
            "IDFamille":        self.cmb_famille.currentData(),
            "PhotoPath":        self.photo_path,
            "NumExtrait":       self.txt_num_ext.text().strip(),
            "DateExtrait":      dt_extr,
            "LieuDelivrance":   self.txt_lieu_ext.text().strip(),
            "Habitation":       self.txt_habitation.text().strip(),
            "NomUrgence":       self.txt_nom_urg.text().strip(),
            "ContactUrgence":   self.txt_cont_urg.text().strip(),
            "HabitationUrgence": self.txt_hab_urg.text().strip(),
            "MatriculeNational": self.txt_matricule_national.text().strip(),
            "DeuxiemeLangue":   self.txt_deuxieme_langue.text().strip(),
            "EtablissementOrigine": self.txt_etablissement_origine.text().strip(),
            "ClasseSuivieOrigine": self.txt_classe_origine.text().strip(),
            "VitChezQui":       (
                self.VIT_CHEZ_VALUES[self.cmb_vit_chez.currentIndex()]
                if self.cmb_vit_chez.currentIndex() >= 0 else None
            ),
            "Baptise":          self.chk_baptise.isChecked(),
            "Confirme":         self.chk_confirme.isChecked(),
            "ParoisseActuelle": self.txt_paroisse.text().strip(),
            "ActiviteParoisse": self.txt_activite_paroisse.text().strip(),
            "PreciserEglise":   self.txt_preciser_eglise.text().strip(),
            "CursusAnterieur":  self._lire_lignes_cursus(),
            "DocExtraitNaissance": self.chk_doc_extrait.isChecked(),
            "DocCertifScolarite": self.chk_doc_certif_scol.isChecked(),
            "DocBulletins":     self.chk_doc_bulletins.isChecked(),
            "DocPhotos":        self.chk_doc_photos.isChecked(),
            "DocCarnetVaccination": self.chk_doc_carnet_vaccin.isChecked(),
            "DocCarnetSante":   self.chk_doc_carnet_sante.isChecked(),
            "DocDispenseEPS":   self.chk_doc_dispense_eps.isChecked(),
            "DocDispenseEPSCertificat": self.chk_doc_dispense_eps_certif.isChecked(),
            "DocCarteSejour":   self.chk_doc_carte_sejour.isChecked(),
            "DocLivretScolaire": self.chk_doc_livret_scol.isChecked(),
            "AutorisationCourrier": self.chk_autorisation_courrier.isChecked(),
            "NDossier":         self.txt_ndossier.text().strip(),
            "DateAdmission":    (
                None if self.date_admission.date() == self.date_admission.minimumDate()
                else date(self.date_admission.date().year(), self.date_admission.date().month(), self.date_admission.date().day())
            ),
            "AccidentNom1":     self.txt_accident_nom1.text().strip(),
            "AccidentTel1":     self.txt_accident_tel1.text().strip(),
            "AccidentCel1":     self.txt_accident_cel1.text().strip(),
            "AccidentBureau1":  self.txt_accident_bureau1.text().strip(),
            "AccidentNom2":     self.txt_accident_nom2.text().strip(),
            "AccidentTel2":     self.txt_accident_tel2.text().strip(),
            "AccidentCel2":     self.txt_accident_cel2.text().strip(),
            "AccidentBureau2":  self.txt_accident_bureau2.text().strip(),
            "AccidentAdresse":  self.txt_accident_adresse.text().strip(),
            "ConduireHopital":  self.chk_conduire_hopital.isChecked(),
            "ConduireHopitalPrecision": self.txt_conduire_hopital_precision.text().strip(),
            "ConduireClinique": self.chk_conduire_clinique.isChecked(),
            "ConduireCliniquePrecision": self.txt_conduire_clinique_precision.text().strip(),
            "MedecinNom":       self.txt_medecin_nom.text().strip(),
            "MedecinTel":       self.txt_medecin_tel.text().strip(),
            "MedecinCel":       self.txt_medecin_cel.text().strip(),
            "MedecinBureau":    self.txt_medecin_bureau.text().strip(),
            "MedecinAdresse":   self.txt_medecin_adresse.text().strip(),
            "Maladie":          self.txt_maladie.text().strip(),
            "ContreIndications": self.txt_contre_indications.text().strip(),
        }

        self._saving = True
        self.btn_valider.setEnabled(False)
        try:
            if self.id_eleve:
                success, message = EleveService.update_eleve(self.id_eleve, data)
            else:
                success, message = EleveService.create_eleve(data)
        finally:
            self._saving = False

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            self.btn_valider.setEnabled(True)
            QMessageBox.critical(self, "Erreur d'enregistrement", message)
