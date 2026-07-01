from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QGroupBox, QGridLayout,
    QScrollArea, QWidget, QDateEdit, QFileDialog, QFrame
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
_ASSETS = str(pathlib.Path(__file__).parent.parent / "assets").replace("\\", "/")
from app.styles import (
    COLORS, GROUPBOX_ACCENT_STYLE, INPUT_STYLE, COMBO_STYLE, DATE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, apply_modal_style
)

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

        lbl_mat = self._lbl("Matricule * :")
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

    def _lbl(self, text: str = "") -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #374151;"
            "background-color: transparent; border: none;"
        )
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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

        if el.PhotoPath:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.photo_path = el.PhotoPath
            self.afficher_photo_preview(os.path.join(app_dir, el.PhotoPath))

        self.calculer_age()

    def _select_combo(self, combo: QComboBox, val):
        for idx in range(combo.count()):
            if combo.itemData(idx) == val:
                combo.setCurrentIndex(idx)
                break

    # Alias pour compatibilité appels existants
    def select_combo_by_data(self, combobox, val):
        self._select_combo(combobox, val)

    def save_data(self):
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
        if not self.id_eleve and not self.cmb_famille.currentData():
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner la famille (parent responsable) de l'élève.")
            self.cmb_famille.setFocus()
            return

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
        }

        if self.id_eleve:
            success, message = EleveService.update_eleve(self.id_eleve, data)
        else:
            success, message = EleveService.create_eleve(data)

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur d'enregistrement", message)
