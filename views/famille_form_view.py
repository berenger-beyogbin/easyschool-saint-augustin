import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QComboBox, QMessageBox, QFrame,
    QGridLayout, QScrollArea, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from services.famille_service import FamilleService
from app.styles import (
    COLORS, BUTTON_SUCCESS, BUTTON_SECONDARY, apply_modal_style
)

# Chemin absolu vers le SVG de coche (résolu depuis l'emplacement du fichier)
_CHECK_SVG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "check_white.svg"
).replace("\\", "/")

# ─── TOKENS LOCAUX ────────────────────────────────────────────────────────────
_BG     = "#F8FAFC"
_CARD   = "#FFFFFF"
_BLUE   = "#2563EB"
_TEXT   = "#0F172A"
_MUTED  = "#334155"
_BORDER = "#E2E8F0"
_H      = 44   # hauteur standard des champs


def _lbl(text: str, color: str = _MUTED) -> QLabel:
    """Label texte simple — sans bordure ni fond."""
    w = QLabel(text)
    w.setStyleSheet(
        f"font-size: 12px; font-weight: 500; color: {color};"
        " background-color: transparent; border: none;"
    )
    return w


def _gl(text: str, width: int = 96) -> QLabel:
    """Label de grille — aligné à droite, largeur fixe."""
    w = _lbl(text)
    w.setFixedWidth(width)
    w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return w


def _card(title: str) -> tuple:
    """Carte sobre : fond blanc, bordure #E2E8F0, coins 10 px, légère ombre."""
    frame = QFrame()
    frame.setObjectName("familleCard")
    frame.setStyleSheet("""
        QFrame#familleCard {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
        }
    """)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(10)
    shadow.setOffset(0, 2)
    shadow.setColor(QColor(0, 0, 0, 18))
    frame.setGraphicsEffect(shadow)

    body = QVBoxLayout(frame)
    body.setContentsMargins(16, 12, 16, 14)
    body.setSpacing(8)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(
        f"font-size: 12px; font-weight: 700; color: {_BLUE};"
        " background-color: transparent; border: none; letter-spacing: 0.4px;"
    )
    body.addWidget(title_lbl)

    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background-color: {_BORDER}; border: none;")
    body.addWidget(sep)

    return frame, body


def _field(placeholder: str = "") -> QLineEdit:
    """Champ 44 px — bordure grise, focus bleu, coins 8 px."""
    f = QLineEdit()
    if placeholder:
        f.setPlaceholderText(placeholder)
    f.setFixedHeight(_H)
    f.setStyleSheet(f"""
        QLineEdit {{
            padding: 0 12px;
            border: 1.5px solid {_BORDER};
            border-radius: 8px;
            background-color: #FFFFFF;
            color: {_TEXT};
            font-size: 13px;
        }}
        QLineEdit:focus {{ border-color: {_BLUE}; }}
        QLineEdit:disabled {{
            background-color: #F1F5F9;
            color: #94A3B8;
        }}
        QLineEdit::placeholder {{ color: #94A3B8; }}
    """)
    return f


def _combo_field() -> QComboBox:
    """Combobox harmonisée avec les champs (même hauteur et style)."""
    c = QComboBox()
    c.setFixedHeight(_H)
    c.setStyleSheet(f"""
        QComboBox {{
            padding: 0 12px;
            border: 1.5px solid {_BORDER};
            border-radius: 8px;
            background-color: #FFFFFF;
            color: {_TEXT};
            font-size: 13px;
        }}
        QComboBox:focus {{ border-color: {_BLUE}; }}
        QComboBox::drop-down {{
            width: 26px;
            border-left: 1px solid {_BORDER};
            border-radius: 0 8px 8px 0;
        }}
        QComboBox QAbstractItemView {{
            background-color: #FFFFFF;
            color: {_TEXT};
            selection-background-color: #DBEAFE;
            border: 1px solid {_BORDER};
        }}
    """)
    return c


def _inline_row(label_text: str, field) -> QHBoxLayout:
    """Ligne label-à-gauche + champ à droite (Père / Mère)."""
    h = QHBoxLayout()
    h.setSpacing(8)
    lbl = _lbl(label_text)
    lbl.setFixedWidth(104)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    h.addWidget(lbl)
    h.addWidget(field, 1)
    return h


class FamilleFormView(QDialog):
    """Dialogue Enregistrement de Parents — compact et moderne."""

    def __init__(self, parent=None, id_famille=None):
        super().__init__(parent)
        self.id_famille = id_famille
        self.setWindowTitle("Enregistrement de Parents")
        self.setMinimumSize(860, 560)
        self.resize(900, 640)
        apply_modal_style(self)
        self.init_ui()
        if self.id_famille:
            self.load_famille()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── EN-TÊTE ──────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['primary_dark']}; border-radius: 0; }}"
        )
        h_lyt = QVBoxLayout(header)
        h_lyt.setContentsMargins(24, 14, 24, 14)
        h_lyt.setSpacing(3)

        lbl_titre = QLabel("Enregistrement de Parents")
        lbl_titre.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #FFFFFF;"
            " background-color: transparent;"
        )
        lbl_sub = QLabel(
            "Informations du père, de la mère, du responsable légal et du contact d'urgence"
        )
        lbl_sub.setStyleSheet(
            "font-size: 11px; color: rgba(255,255,255,0.70);"
            " background-color: transparent;"
        )
        h_lyt.addWidget(lbl_titre)
        h_lyt.addWidget(lbl_sub)
        main_layout.addWidget(header)

        # ─── CORPS SCROLLABLE ─────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: {_BG}; }}"
        )

        container = QWidget()
        container.setStyleSheet(f"background-color: {_BG};")
        body = QVBoxLayout(container)
        body.setContentsMargins(20, 16, 20, 16)
        body.setSpacing(14)

        # ── Père & Mère côte à côte ───────────────────────────────────────────
        parents_row = QHBoxLayout()
        parents_row.setSpacing(14)

        card_pere, lyt_pere = _card("Père")
        self.txt_nom_pere  = _field("Nom et prénoms")
        self.txt_nom_pere.textChanged.connect(self.on_pere_changed)
        self.txt_prof_pere = _field("Profession")
        self.txt_prof_pere.textChanged.connect(self.on_pere_changed)
        self.txt_tel_pere  = _field("Téléphone")
        self.txt_tel_pere.textChanged.connect(self.on_pere_changed)
        lyt_pere.addLayout(_inline_row("Nom & Prénoms :", self.txt_nom_pere))
        lyt_pere.addLayout(_inline_row("Profession :",    self.txt_prof_pere))
        lyt_pere.addLayout(_inline_row("Téléphone :",     self.txt_tel_pere))

        card_mere, lyt_mere = _card("Mère")
        self.txt_nom_mere  = _field("Nom et prénoms")
        self.txt_nom_mere.textChanged.connect(self.on_mere_changed)
        self.txt_prof_mere = _field("Profession")
        self.txt_prof_mere.textChanged.connect(self.on_mere_changed)
        self.txt_tel_mere  = _field("Téléphone")
        self.txt_tel_mere.textChanged.connect(self.on_mere_changed)
        lyt_mere.addLayout(_inline_row("Nom & Prénoms :", self.txt_nom_mere))
        lyt_mere.addLayout(_inline_row("Profession :",    self.txt_prof_mere))
        lyt_mere.addLayout(_inline_row("Téléphone :",     self.txt_tel_mere))

        parents_row.addWidget(card_pere)
        parents_row.addWidget(card_mere)
        body.addLayout(parents_row)

        # ── Responsable légal ─────────────────────────────────────────────────
        card_resp, lyt_resp = _card("Responsable légal  *")

        self.cmb_qualite    = _combo_field()
        self.cmb_qualite.addItems(["Tuteur", "Père", "Mère"])
        self.cmb_qualite.currentIndexChanged.connect(self.on_qualite_changed)

        self.txt_nom_resp   = _field("Nom et prénoms *")
        self.txt_nom_resp.textChanged.connect(self.on_resp_info_changed)
        self.txt_prof_resp  = _field("Profession")
        self.txt_tel_resp   = _field("Tél. portable *")
        self.txt_tel_resp.textChanged.connect(self.on_resp_info_changed)
        self.txt_email_resp = _field("Email")
        self.txt_adr_resp   = _field("Adresse")
        self.txt_hab_resp   = _field("Habitation")
        self.txt_hab_resp.textChanged.connect(self.on_resp_info_changed)

        # Grille 2 colonnes : (label | champ) × 2
        gr = QGridLayout()
        gr.setHorizontalSpacing(10)
        gr.setVerticalSpacing(8)
        gr.setColumnStretch(1, 1)
        gr.setColumnStretch(3, 2)

        # Ligne 0 : Qualité | Nom
        gr.addWidget(_gl("Qualité * :"),          0, 0)
        gr.addWidget(self.cmb_qualite,            0, 1)
        gr.addWidget(_gl("Nom * :"),              0, 2)
        gr.addWidget(self.txt_nom_resp,           0, 3)
        # Ligne 1 : Profession | Téléphone
        gr.addWidget(_gl("Profession :"),         1, 0)
        gr.addWidget(self.txt_prof_resp,          1, 1)
        gr.addWidget(_gl("Tél. portable * :"),    1, 2)
        gr.addWidget(self.txt_tel_resp,           1, 3)
        # Ligne 2 : Email | Adresse
        gr.addWidget(_gl("Email :"),              2, 0)
        gr.addWidget(self.txt_email_resp,         2, 1)
        gr.addWidget(_gl("Adresse :"),            2, 2)
        gr.addWidget(self.txt_adr_resp,           2, 3)
        # Ligne 3 : Habitation pleine largeur
        gr.addWidget(_gl("Habitation :"),         3, 0)
        gr.addWidget(self.txt_hab_resp,           3, 1, 1, 3)

        lyt_resp.addLayout(gr)

        # Statuts particuliers
        chk_style = f"""
QCheckBox {{
    font-size: 12px;
    font-weight: 500;
    color: {_TEXT};
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
QCheckBox::indicator:hover {{
    border-color: {_BLUE};
    background-color: #EFF6FF;
}}
QCheckBox::indicator:checked {{
    background-color: {_BLUE};
    border-color: {_BLUE};
    image: url("{_CHECK_SVG}");
}}
QCheckBox::indicator:checked:hover {{
    background-color: #1D4ED8;
    border-color: #1D4ED8;
}}
"""
        self.chk_ebrie   = QCheckBox("Ebrié d'Abobo-té")
        self.chk_ebrie.setStyleSheet(chk_style)

        chk_row = QHBoxLayout()
        chk_row.setSpacing(16)
        chk_row.addStretch()
        chk_row.addWidget(self.chk_ebrie)
        chk_row.addStretch()
        lyt_resp.addLayout(chk_row)

        body.addWidget(card_resp)

        # ── Contact d'urgence ────────────────────────────────────────────────
        card_urg, lyt_urg = _card("Contact en cas d'urgence")

        self.chk_urg_meme = QCheckBox("Le responsable légal lui-même")
        self.chk_urg_meme.setStyleSheet(chk_style)
        self.chk_urg_meme.toggled.connect(self.on_urg_meme_toggled)
        lyt_urg.addWidget(self.chk_urg_meme)

        self.txt_nom_urg  = _field("Nom et prénoms")
        self.txt_cont_urg = _field("Contact")
        self.txt_hab_urg  = _field("Habitation")

        gu = QGridLayout()
        gu.setHorizontalSpacing(10)
        gu.setVerticalSpacing(8)
        gu.setColumnStretch(1, 1)
        gu.setColumnStretch(3, 1)

        gu.addWidget(_gl("Nom & Prénoms :"), 0, 0)
        gu.addWidget(self.txt_nom_urg,       0, 1)
        gu.addWidget(_gl("Contact :"),       0, 2)
        gu.addWidget(self.txt_cont_urg,      0, 3)
        gu.addWidget(_gl("Habitation :"),    1, 0)
        gu.addWidget(self.txt_hab_urg,       1, 1, 1, 3)

        lyt_urg.addLayout(gu)
        body.addWidget(card_urg)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # ─── PIED DE PAGE FIXE ────────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(
            f"QFrame {{ background-color: #FFFFFF; border-top: 1px solid {_BORDER};"
            " border-radius: 0; }}"
        )
        footer_lyt = QHBoxLayout(footer)
        footer_lyt.setContentsMargins(20, 12, 20, 12)
        footer_lyt.setSpacing(10)
        footer_lyt.addStretch()

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.setFixedSize(110, 40)
        self.btn_fermer.clicked.connect(self.reject)

        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(BUTTON_SUCCESS)
        self.btn_valider.setFixedSize(130, 40)
        self.btn_valider.clicked.connect(self.save_data)

        footer_lyt.addWidget(self.btn_fermer)
        footer_lyt.addWidget(self.btn_valider)
        main_layout.addWidget(footer)

    # ─── LOGIQUE INTERACTION (inchangée) ─────────────────────────────────────

    def on_qualite_changed(self, index):
        if index == 1:
            self.txt_nom_resp.setText(self.txt_nom_pere.text())
            self.txt_prof_resp.setText(self.txt_prof_pere.text())
            self.txt_tel_resp.setText(self.txt_tel_pere.text())
        elif index == 2:
            self.txt_nom_resp.setText(self.txt_nom_mere.text())
            self.txt_prof_resp.setText(self.txt_prof_mere.text())
            self.txt_tel_resp.setText(self.txt_tel_mere.text())

    def on_pere_changed(self):
        if self.cmb_qualite.currentIndex() == 1:
            self.txt_nom_resp.setText(self.txt_nom_pere.text())
            self.txt_prof_resp.setText(self.txt_prof_pere.text())
            self.txt_tel_resp.setText(self.txt_tel_pere.text())

    def on_mere_changed(self):
        if self.cmb_qualite.currentIndex() == 2:
            self.txt_nom_resp.setText(self.txt_nom_mere.text())
            self.txt_prof_resp.setText(self.txt_prof_mere.text())
            self.txt_tel_resp.setText(self.txt_tel_mere.text())

    def on_resp_info_changed(self):
        if self.chk_urg_meme.isChecked():
            self.txt_nom_urg.setText(self.txt_nom_resp.text())
            self.txt_cont_urg.setText(self.txt_tel_resp.text())
            self.txt_hab_urg.setText(self.txt_hab_resp.text())

    def on_urg_meme_toggled(self, checked):
        if checked:
            self.txt_nom_urg.setText(self.txt_nom_resp.text())
            self.txt_cont_urg.setText(self.txt_tel_resp.text())
            self.txt_hab_urg.setText(self.txt_hab_resp.text())
        self.txt_nom_urg.setEnabled(not checked)
        self.txt_cont_urg.setEnabled(not checked)
        self.txt_hab_urg.setEnabled(not checked)

    def load_famille(self):
        fam = FamilleService.get_famille_by_id(self.id_famille)
        if not fam:
            QMessageBox.warning(self, "Erreur", "Impossible de charger la famille.")
            self.reject()
            return
        self.txt_nom_pere.setText(fam.NomPere or "")
        self.txt_prof_pere.setText(fam.ProfessionPere or "")
        self.txt_tel_pere.setText(fam.TelPere or "")
        self.txt_nom_mere.setText(fam.NomMere or "")
        self.txt_prof_mere.setText(fam.ProfessionMere or "")
        self.txt_tel_mere.setText(fam.TelMere or "")
        idx = fam.QualiteResponsable - 1
        if 0 <= idx < 3:
            self.cmb_qualite.setCurrentIndex(idx)
        self.txt_nom_resp.setText(fam.NomResponsable or "")
        self.txt_prof_resp.setText(fam.ProfessionResponsable or "")
        self.txt_tel_resp.setText(fam.CellulaireResponsable or "")
        self.txt_email_resp.setText(fam.EmailResponsable or "")
        self.txt_adr_resp.setText(fam.AdresseResponsable or "")
        self.txt_hab_resp.setText(fam.HabitationParent or "")
        self.chk_ebrie.setChecked(fam.EbrieAbobote)
        self.chk_urg_meme.setChecked(fam.UrgenceMoimeme)
        self.txt_nom_urg.setText(fam.NomUrgence or "")
        self.txt_cont_urg.setText(fam.ContactUrgence or "")
        self.txt_hab_urg.setText(fam.HabitationUrgence or "")

    def save_data(self):
        nom_resp = self.txt_nom_resp.text().strip()
        tel_resp = self.txt_tel_resp.text().strip()
        if not nom_resp:
            QMessageBox.warning(self, "Validation", "Veuillez saisir le nom du responsable légal.")
            self.txt_nom_resp.setFocus()
            return
        if not tel_resp:
            QMessageBox.warning(self, "Validation", "Veuillez saisir le téléphone du responsable légal.")
            self.txt_tel_resp.setFocus()
            return

        data = {
            "NomResponsable":        nom_resp,
            "QualiteResponsable":    self.cmb_qualite.currentIndex() + 1,
            "ProfessionResponsable": self.txt_prof_resp.text().strip(),
            "TypeResponsable":       1,
            "NumeroPieceIdentite":   self.txt_adr_resp.text().strip(),
            "AdresseResponsable":    self.txt_adr_resp.text().strip(),
            "CellulaireResponsable": tel_resp,
            "EmailResponsable":      self.txt_email_resp.text().strip(),
            "SIMaitre":              False,
            "EbrieAbobote":          self.chk_ebrie.isChecked(),
            "NomUrgence":            self.txt_nom_urg.text().strip(),
            "ContactUrgence":        self.txt_cont_urg.text().strip(),
            "HabitationUrgence":     self.txt_hab_urg.text().strip(),
            "UrgenceMoimeme":        self.chk_urg_meme.isChecked(),
            "HabitationParent":      self.txt_hab_resp.text().strip(),
            "NomPere":               self.txt_nom_pere.text().strip(),
            "ProfessionPere":        self.txt_prof_pere.text().strip(),
            "TelPere":               self.txt_tel_pere.text().strip(),
            "NomMere":               self.txt_nom_mere.text().strip(),
            "ProfessionMere":        self.txt_prof_mere.text().strip(),
            "TelMere":               self.txt_tel_mere.text().strip(),
        }
        if self.id_famille:
            success, message = FamilleService.update_famille(self.id_famille, data)
        else:
            success, message = FamilleService.create_famille(data)

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)

