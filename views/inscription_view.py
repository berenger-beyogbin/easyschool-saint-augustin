from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QComboBox, QCheckBox, QFrame,
    QDialog, QDialogButtonBox, QScrollArea, QSizePolicy,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from services.famille_service import FamilleService
from services.eleve_service import EleveService
from services.niveau_service import NiveauService
from services.inscription_service import InscriptionService
from services.inscription_autres_frais_service import InscriptionAutresFraisService
from app.session import AppSession
from app.database import get_session
from app.config import Config
from models.classe import TClasse
from app.styles import (
    COLORS, INPUT_STYLE, COMBO_STYLE, TABLE_STYLE,
    apply_card_shadow, format_fcfa
)

_CARD_STYLE = """
QFrame#stepCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}
"""

_HEADER_STYLE = """
QFrame#cardHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #EFF6FF, stop:1 #F8FAFC);
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    border-bottom: 1px solid #DBEAFE;
}
"""

_BADGE_STYLE = """
QLabel {
    background-color: #2563EB;
    color: #FFFFFF;
    border-radius: 13px;
    font-size: 11px;
    font-weight: bold;
    border: none;
}
"""

_HEADER_TITLE_STYLE = (
    "font-size: 13px; font-weight: 700; color: #1D4ED8;"
    "background-color: transparent; border: none;"
)

_FIELD_LABEL_STYLE = (
    f"font-size: 10px; font-weight: 700; color: {COLORS['muted']};"
    "background-color: transparent; border: none; letter-spacing: 0.5px;"
)

_CHK_STYLE = f"""
QCheckBox {{
    color: {COLORS['text_soft']};
    font-size: 12px;
    font-weight: 500;
    background-color: transparent;
    spacing: 10px;
}}
QCheckBox:hover {{
    color: {COLORS['primary_dark']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['input_border']};
    border-radius: 4px;
    background-color: {COLORS['card']};
}}
QCheckBox::indicator:unchecked:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_soft']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
QCheckBox::indicator:checked:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
}}
"""

_FRAIS_LIST_STYLE = f"""
QListWidget {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    outline: none;
    font-size: 12px;
    color: {COLORS['text_soft']};
}}
QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS['border']};
}}
QListWidget::item:hover {{
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['input_border']};
    border-radius: 4px;
    background-color: {COLORS['card']};
}}
QListWidget::indicator:unchecked:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
QListWidget::indicator:checked:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
}}
"""

_BTN_INSCRIRE = f"""
QPushButton {{
    background-color: {COLORS['success']};
    color: #FFFFFF;
    padding: 0 20px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 9px;
    border: none;
    min-height: 50px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{ background-color: #15803D; }}
QPushButton:pressed {{ background-color: #166534; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

_BTN_MODIFIER = f"""
QPushButton {{
    background-color: {COLORS['warning']};
    color: #FFFFFF;
    padding: 0 20px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 9px;
    border: none;
    min-height: 50px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{ background-color: #EA6C00; }}
QPushButton:pressed {{ background-color: #C05500; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""


class InscriptionView(QWidget):
    """Vue INSCRIPTION ÉLÈVE — liaison élève / classe / année académique."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.selected_famille_id = None
        self.selected_eleve_id = None
        self._mode_modification = False
        self._id_inscription_courante = None
        self._inscriptions_map = {}  # {id_eleve: TInscription}
        self._frais_items = []  # [(QListWidgetItem, frais_dict)] — liste dynamique selon le niveau
        self._form_enabled = False
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.load_responsables()
        self.load_niveaux()
        self._set_form_enabled(False)

    # ── Helpers UI ────────────────────────────────────────────────────────────

    def _make_step_card(self, step_num: str, title: str, scrollable: bool = False):
        """Crée une carte premium avec badge numéroté et header dégradé.

        Si scrollable=True, le corps de la carte est placé dans une QScrollArea :
        utile pour les cartes à contenu de longueur variable (ex. liste de frais
        annexes dépendant du niveau), qui ne doivent jamais être écrasées par la
        hauteur imposée par les cartes voisines dans la grille.
        """
        card = QFrame()
        card.setObjectName("stepCard")
        card.setStyleSheet(_CARD_STYLE)
        apply_card_shadow(card)

        card_vbox = QVBoxLayout(card)
        card_vbox.setContentsMargins(0, 0, 0, 0)
        card_vbox.setSpacing(0)

        header = QFrame()
        header.setObjectName("cardHeader")
        header.setStyleSheet(_HEADER_STYLE)
        header.setFixedHeight(46)
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(14, 0, 14, 0)
        hdr_layout.setSpacing(10)

        badge = QLabel(step_num)
        badge.setFixedSize(26, 26)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(_BADGE_STYLE)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(_HEADER_TITLE_STYLE)

        hdr_layout.addWidget(badge)
        hdr_layout.addWidget(lbl_title)
        hdr_layout.addStretch()
        card_vbox.addWidget(header)

        content = QFrame()
        content.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 14)
        content_layout.setSpacing(10)

        if scrollable:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(content)
            card_vbox.addWidget(scroll)
        else:
            card_vbox.addWidget(content)

        return card, content_layout

    def _make_option_row(self, checkbox: QCheckBox, wrap_text: str = None) -> QFrame:
        """Enveloppe un checkbox dans une ligne stylisée avec hover.

        Si wrap_text est fourni, le libellé est affiché via un QLabel à part
        (avec retour à la ligne automatique) plutôt que sur le texte natif du
        checkbox — un QCheckBox ne wrap jamais son texte, ce qui provoquait un
        débordement horizontal de la carte pour les libellés de frais longs.
        """
        frame = QFrame()
        frame.setObjectName("optionRow")
        frame.setStyleSheet("""
            QFrame#optionRow {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 7px;
            }
            QFrame#optionRow:hover {
                border-color: #93C5FD;
                background-color: #EFF6FF;
            }
        """)
        row = QHBoxLayout(frame)
        if wrap_text is not None:
            # Lignes de la liste des frais annexes : plus compactes pour
            # afficher davantage d'éléments avant de devoir défiler.
            row.setContentsMargins(10, 4, 10, 4)
            row.setSpacing(8)
        else:
            row.setContentsMargins(12, 7, 12, 7)
            row.setSpacing(10)
        row.addWidget(checkbox)
        if wrap_text is not None:
            checkbox.setText("")
            lbl = QLabel(wrap_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"font-size: 11px; font-weight: 500; color: {COLORS['text_soft']};"
                "background-color: transparent; border: none;"
            )
            row.addWidget(lbl, 1)
        else:
            row.addStretch()
        return frame

    # ── Construction UI ───────────────────────────────────────────────────────

    def init_ui(self):
        # QGridLayout : col 0 (stretch 4) = gauche, col 1 (stretch 3) = droite
        # card1 → ligne 0 col 0 | card3 → lignes 0-1 col 1 (rowspan=2)
        # card2 → ligne 1 col 0
        # ligne 2 = stretch vertical pour coller les cartes en haut
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setHorizontalSpacing(16)
        main_layout.setVerticalSpacing(14)
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(2, 1)

        # ── Carte 1 : Responsable ──────────────────────────────────────────────
        card1, c1 = self._make_step_card("1", "Sélectionner le parent / responsable")

        lbl_search = QLabel("RECHERCHER UN RESPONSABLE")
        lbl_search.setStyleSheet(_FIELD_LABEL_STYLE)

        self.txt_search_resp = QLineEdit()
        self.txt_search_resp.setPlaceholderText("Nom ou téléphone du parent…")
        self.txt_search_resp.setStyleSheet(INPUT_STYLE)
        self.txt_search_resp.setFixedHeight(36)
        self.txt_search_resp.textChanged.connect(self.load_responsables)

        self.table_resp = QTableWidget()
        self.table_resp.setColumnCount(2)
        self.table_resp.setHorizontalHeaderLabels(["Responsable", "Téléphone"])
        self.table_resp.setStyleSheet(TABLE_STYLE)
        self.table_resp.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_resp.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_resp.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_resp.setSelectionMode(QTableWidget.SingleSelection)
        self.table_resp.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_resp.setAlternatingRowColors(True)
        self.table_resp.verticalHeader().setVisible(False)
        self.table_resp.horizontalHeader().setHighlightSections(False)
        self.table_resp.setFixedHeight(180)
        self.table_resp.itemSelectionChanged.connect(self.on_responsable_selected)

        c1.addWidget(lbl_search)
        c1.addWidget(self.txt_search_resp)
        c1.addWidget(self.table_resp)
        main_layout.addWidget(card1, 0, 0)

        # ── Carte 2 : Élèves ───────────────────────────────────────────────────
        card2, c2 = self._make_step_card("2", "Sélectionner l'élève de cette famille")

        self.table_eleves = QTableWidget()
        self.table_eleves.setColumnCount(4)
        self.table_eleves.setHorizontalHeaderLabels(["Matricule", "Nom", "Prénoms", "Statut"])
        self.table_eleves.setStyleSheet(TABLE_STYLE)
        self.table_eleves.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_eleves.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_eleves.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_eleves.setSelectionMode(QTableWidget.SingleSelection)
        self.table_eleves.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_eleves.setAlternatingRowColors(True)
        self.table_eleves.verticalHeader().setVisible(False)
        self.table_eleves.horizontalHeader().setHighlightSections(False)
        self.table_eleves.setFixedHeight(180)
        self.table_eleves.itemSelectionChanged.connect(self.on_eleve_selected)

        c2.addWidget(self.table_eleves)

        self.btn_lier_eleve = QPushButton("+ Lier un élève existant sans famille")
        self.btn_lier_eleve.setEnabled(False)
        self.btn_lier_eleve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lier_eleve.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2563EB;
                border: 1px dashed #93C5FD;
                border-radius: 7px;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #EFF6FF; border-color: #2563EB; }
            QPushButton:disabled { color: #CBD5E1; border-color: #E2E8F0; }
        """)
        self.btn_lier_eleve.clicked.connect(self.on_lier_eleve)
        c2.addWidget(self.btn_lier_eleve)

        main_layout.addWidget(card2, 1, 0)

        # ── Carte 3 : Affectation (rowspan=2 → aligne haut sur card1, bas sur card2)
        # Reconstruite intégralement : un seul QVBoxLayout (c3, fourni par
        # _make_step_card) porte tous les blocs de la carte dans l'ordre visuel,
        # chacun séparé par une marge explicite. Seule la liste des frais
        # annexes (bloc 5, longueur variable selon le niveau) a son propre
        # QScrollArea borné en hauteur ; le total et le bouton restent toujours
        # visibles sous elle, jamais à l'intérieur.
        card3, c3 = self._make_step_card("3", "Choix de l'affectation de classe", scrollable=False)
        c3.setSpacing(0)

        # Bloc 1 — Affectation classe : niveau + classe, grille à 2 colonnes égales
        lbl_niveau = QLabel("NIVEAU SCOLAIRE *")
        lbl_niveau.setStyleSheet(_FIELD_LABEL_STYLE)
        self.cmb_niveau = QComboBox()
        self.cmb_niveau.setStyleSheet(COMBO_STYLE)
        self.cmb_niveau.setFixedHeight(36)
        self.cmb_niveau.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_niveau.currentIndexChanged.connect(self.load_classes_par_niveau)

        lbl_classe = QLabel("CLASSE DE DESTINATION *")
        lbl_classe.setStyleSheet(_FIELD_LABEL_STYLE)
        self.cmb_classe = QComboBox()
        self.cmb_classe.setStyleSheet(COMBO_STYLE)
        self.cmb_classe.setFixedHeight(36)
        self.cmb_classe.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_classe.currentIndexChanged.connect(self.on_classe_changed)

        grid_affectation = QGridLayout()
        grid_affectation.setHorizontalSpacing(10)
        grid_affectation.setVerticalSpacing(4)
        grid_affectation.setColumnStretch(0, 1)
        grid_affectation.setColumnStretch(1, 1)
        grid_affectation.addWidget(lbl_niveau, 0, 0)
        grid_affectation.addWidget(lbl_classe, 0, 1)
        grid_affectation.addWidget(self.cmb_niveau, 1, 0)
        grid_affectation.addWidget(self.cmb_classe, 1, 1)
        c3.addLayout(grid_affectation)

        # Bloc 2 — Effectif actuel (badge pleine largeur)
        c3.addSpacing(10)
        self.lbl_effectif = QLabel("Effectif actuel : — / —")
        self._set_effectif_style("default")
        c3.addWidget(self.lbl_effectif)

        # Bloc 3 — Statut affectation (pleine largeur, pour ne tronquer aucune valeur)
        c3.addSpacing(14)
        lbl_statut_affectation = QLabel("STATUT AFFECTATION *")
        lbl_statut_affectation.setStyleSheet(_FIELD_LABEL_STYLE)
        self.cmb_statut_affectation = QComboBox()
        self.cmb_statut_affectation.setStyleSheet(COMBO_STYLE)
        self.cmb_statut_affectation.setFixedHeight(36)
        self.cmb_statut_affectation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_statut_affectation.addItem("Affecté de l'État", "AFFECTE_ETAT")
        self.cmb_statut_affectation.addItem("Non affecté de l'État", "NON_AFFECTE_ETAT")
        c3.addWidget(lbl_statut_affectation)
        c3.addSpacing(4)
        c3.addWidget(self.cmb_statut_affectation)

        # Séparateur avant les options de service
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        sep.setFixedHeight(1)
        c3.addSpacing(14)
        c3.addWidget(sep)

        # Bloc 4 — Options de services scolarité
        c3.addSpacing(10)
        lbl_services = QLabel("OPTIONS DE SERVICES SCOLARITÉ")
        lbl_services.setStyleSheet(_FIELD_LABEL_STYLE)
        c3.addWidget(lbl_services)

        self.chk_scolarite = QCheckBox("Scolarité de base")
        self.chk_scolarite.setChecked(True)
        self.chk_scolarite.setStyleSheet(_CHK_STYLE)

        self.chk_nouveau = QCheckBox("Nouvel élève arrivant")
        self.chk_nouveau.setChecked(True)
        self.chk_nouveau.setStyleSheet(_CHK_STYLE)

        self.chk_transport = QCheckBox("Option Transport bus")
        self.chk_transport.setStyleSheet(_CHK_STYLE)

        self.chk_cantine = QCheckBox("Option Cantine midi")
        self.chk_cantine.setStyleSheet(_CHK_STYLE)

        c3.addSpacing(6)
        row_base = QHBoxLayout()
        row_base.setSpacing(10)
        row_base.addWidget(self._make_option_row(self.chk_scolarite))
        row_base.addWidget(self._make_option_row(self.chk_nouveau))
        c3.addLayout(row_base)

        # Transport / Cantine désactivés pour la version collège CJGA
        # (voir app.config.Config) — masqués, non proposés en saisie.
        self.row_transport = self._make_option_row(self.chk_transport)
        self.row_transport.setVisible(Config.ENABLE_TRANSPORT)
        c3.addWidget(self.row_transport)

        self.row_cantine = self._make_option_row(self.chk_cantine)
        self.row_cantine.setVisible(Config.ENABLE_CANTINE)
        c3.addWidget(self.row_cantine)

        # Séparateur avant la section frais annexes
        sep_frais = QFrame()
        sep_frais.setFrameShape(QFrame.HLine)
        sep_frais.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        sep_frais.setFixedHeight(1)
        c3.addSpacing(14)
        c3.addWidget(sep_frais)

        # Bloc 5 — Frais annexes à l'inscription : liste cochable, dépend du niveau choisi
        c3.addSpacing(10)
        lbl_frais_annexes = QLabel("FRAIS ANNEXES À L'INSCRIPTION")
        lbl_frais_annexes.setStyleSheet(_FIELD_LABEL_STYLE)
        c3.addWidget(lbl_frais_annexes)

        # Liste de frais annexes, de longueur variable selon le niveau choisi.
        # QListWidget gère nativement son propre défilement (ascenseur vertical
        # affiché automatiquement seulement si le contenu dépasse la hauteur
        # fixée) : plus robuste qu'un QScrollArea+QVBoxLayout artisanal, qui
        # provoquait un chevauchement visuel avec le total affiché en dessous.
        self.frais_annexes_list = QListWidget()
        self.frais_annexes_list.setStyleSheet(_FRAIS_LIST_STYLE)
        self.frais_annexes_list.setFrameShape(QFrame.NoFrame)
        self.frais_annexes_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frais_annexes_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.frais_annexes_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.frais_annexes_list.setFocusPolicy(Qt.NoFocus)
        self.frais_annexes_list.setFixedHeight(130)
        self.frais_annexes_list.itemChanged.connect(self._update_total_frais_annexes)
        c3.addSpacing(6)
        c3.addWidget(self.frais_annexes_list)

        # Bloc 6 — Total des frais annexes (toujours hors du QScrollArea)
        c3.addSpacing(12)
        self.lbl_total_frais_annexes = QLabel("Total frais annexes sélectionnés : 0 FCFA")
        self.lbl_total_frais_annexes.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {COLORS['primary_dark']};"
            "background-color: transparent; border: none;"
        )
        c3.addWidget(self.lbl_total_frais_annexes)

        # Bloc 7 — Bouton final (toujours hors du QScrollArea, pleine largeur)
        c3.addSpacing(12)
        self.btn_inscrire = QPushButton("Inscrire l'Élève")
        self.btn_inscrire.setStyleSheet(_BTN_INSCRIRE)
        self.btn_inscrire.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_inscrire.clicked.connect(self.on_inscrire)
        c3.addWidget(self.btn_inscrire)

        main_layout.addWidget(card3, 0, 1, 2, 1)  # rowspan=2 : de card1 à card2

    # ── Activation/désactivation du formulaire ────────────────────────────────

    def _set_form_enabled(self, enabled: bool):
        """Active ou désactive les champs du panneau d'affectation."""
        self._form_enabled = enabled
        for w in [self.cmb_niveau, self.cmb_classe, self.cmb_statut_affectation,
                  self.chk_scolarite, self.chk_nouveau,
                  self.chk_transport, self.chk_cantine,
                  self.btn_inscrire, self.frais_annexes_list]:
            w.setEnabled(enabled)

    def _prefill_inscription(self, inscription):
        """Pré-remplit le formulaire à partir d'une inscription existante."""
        idx = self.cmb_niveau.findData(inscription.IDNiveau)
        if idx >= 0:
            self.cmb_niveau.setCurrentIndex(idx)  # déclenche load_classes_par_niveau puis on_classe_changed
        idx = self.cmb_classe.findData(inscription.IDClasse)
        if idx >= 0:
            self.cmb_classe.setCurrentIndex(idx)  # déclenche on_classe_changed (recharge les frais annexes)
        self.chk_scolarite.setChecked(bool(inscription.Scolarite))
        self.chk_nouveau.setChecked(bool(inscription.Nouveau))
        self.chk_transport.setChecked(bool(inscription.Transport))
        self.chk_cantine.setChecked(bool(inscription.Cantine))
        idx = self.cmb_statut_affectation.findData(inscription.StatutAffectation or "AFFECTE_ETAT")
        self.cmb_statut_affectation.setCurrentIndex(idx if idx >= 0 else 0)

        # Précoche les frais annexes déjà enregistrés pour cette inscription.
        # La liste des frais proposés a déjà été rechargée ci-dessus (changement niveau/classe).
        self._precocher_frais_annexes(inscription.IDTInscription)

    def _reset_form(self):
        """Réinitialise le formulaire aux valeurs par défaut pour une nouvelle inscription."""
        self.cmb_niveau.setCurrentIndex(0)
        self.cmb_classe.setCurrentIndex(0)
        self.cmb_statut_affectation.setCurrentIndex(0)
        self.chk_scolarite.setChecked(True)
        self.chk_nouveau.setChecked(True)
        self.chk_transport.setChecked(False)
        self.chk_cantine.setChecked(False)
        # La remise à zéro de cmb_niveau ci-dessus déclenche on_classe_changed,
        # qui recharge (et donc vide) la sélection des frais annexes.

    # ── Frais annexes cochables ───────────────────────────────────────────────

    def _clear_frais_annexes_layout(self):
        """Retire toutes les entrées actuellement affichées dans la liste des frais annexes."""
        self.frais_annexes_list.blockSignals(True)
        self.frais_annexes_list.clear()
        self.frais_annexes_list.blockSignals(False)
        self._frais_items = []

    def _load_frais_annexes(self, id_niveau):
        """
        Recharge la liste des frais annexes cochables pour le niveau sélectionné.
        Vide systématiquement l'ancienne sélection avant de reconstruire la liste.

        NOTE : pas de filtrage par sexe pour l'instant — le catalogue MontantAutresFrais
        ne porte pas cette dimension aujourd'hui. Un filtrage par sexe pourra être
        ajouté ici plus tard si le modèle évolue pour le supporter.
        """
        self._clear_frais_annexes_layout()

        id_annee = AppSession.get_active_annee_id()
        if not id_niveau or not id_annee:
            self._update_total_frais_annexes()
            return

        frais_list = InscriptionAutresFraisService.get_frais_proposes(id_niveau, id_annee)

        if not frais_list:
            lbl_vide = QListWidgetItem("Aucun frais annexe paramétré pour ce niveau.")
            lbl_vide.setFlags(Qt.ItemIsEnabled)
            self.frais_annexes_list.addItem(lbl_vide)
            self._update_total_frais_annexes()
            return

        self.frais_annexes_list.blockSignals(True)
        for frais in frais_list:
            libelle = frais.get("LibelleFrais") or frais.get("CodeFrais") or "Frais"
            montant = frais.get("MontantFrais") or 0
            libelle_complet = f"{libelle} — {format_fcfa(montant)}"
            item = QListWidgetItem(libelle_complet)
            item.setToolTip(libelle_complet)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.frais_annexes_list.addItem(item)
            self._frais_items.append((item, frais))
        self.frais_annexes_list.blockSignals(False)

        self._update_total_frais_annexes()

    def _update_total_frais_annexes(self):
        """Recalcule et affiche le total des frais annexes actuellement cochés."""
        total = sum(
            (frais.get("MontantFrais") or 0)
            for item, frais in self._frais_items
            if item.checkState() == Qt.Checked
        )
        self.lbl_total_frais_annexes.setText(f"Total frais annexes sélectionnés : {format_fcfa(total)}")

    def _precocher_frais_annexes(self, id_inscription):
        """Précoche les frais annexes déjà enregistrés pour une inscription existante."""
        if not id_inscription:
            return
        coches = InscriptionAutresFraisService.get_frais_coches(id_inscription)
        ids_montant_coches = {c["IDMontantAutres"] for c in coches if c.get("IDMontantAutres")}
        self.frais_annexes_list.blockSignals(True)
        for item, frais in self._frais_items:
            if frais.get("IDMontantAutres") in ids_montant_coches:
                item.setCheckState(Qt.Checked)
        self.frais_annexes_list.blockSignals(False)
        self._update_total_frais_annexes()

    # ── Helpers effectif ──────────────────────────────────────────────────────

    def _set_effectif_style(self, state: str):
        base = (
            "font-size: 12px; font-weight: 700; padding: 7px 12px;"
            "border-radius: 7px; border: 1px solid;"
        )
        if state == "full":
            self.lbl_effectif.setStyleSheet(
                base + f"color: {COLORS['danger']}; background-color: #FEF2F2;"
                f"border-color: {COLORS['danger']};"
            )
        elif state == "warning":
            self.lbl_effectif.setStyleSheet(
                base + "color: #B45309; background-color: #FFFBEB; border-color: #FCD34D;"
            )
        else:
            self.lbl_effectif.setStyleSheet(
                base + f"color: {COLORS['primary_dark']}; background-color: {COLORS['surface_soft']};"
                f"border-color: {COLORS['border']};"
            )

    # ── Chargement ────────────────────────────────────────────────────────────

    def load_responsables(self):
        self.table_resp.setRowCount(0)
        query = self.txt_search_resp.text().strip()
        familles = FamilleService.search_familles(query)
        for i, fam in enumerate(familles):
            self.table_resp.insertRow(i)
            item_nom = QTableWidgetItem(fam.NomResponsable)
            item_nom.setData(Qt.UserRole, fam.IdTFamille)
            self.table_resp.setItem(i, 0, item_nom)
            self.table_resp.setItem(i, 1, QTableWidgetItem(fam.CellulaireResponsable or ""))
            self.table_resp.setRowHeight(i, 32)

    def load_niveaux(self):
        self.cmb_niveau.clear()
        self.cmb_niveau.addItem("[Choisir un niveau scolaire…]", None)
        for nv in NiveauService.get_all_with_cycle():
            self.cmb_niveau.addItem(f"{nv['Libelle']} ({nv['CycleLibelle']})", nv["IDT_Niveau"])

    def load_classes_par_niveau(self):
        self.cmb_classe.clear()
        self.cmb_classe.addItem("[Choisir une classe…]", None)

        id_niveau = self.cmb_niveau.currentData()
        if not id_niveau:
            self.lbl_effectif.setText("Effectif actuel : — / —")
            self._set_effectif_style("default")
            return

        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return

        session = get_session()
        try:
            classes_list = session.query(TClasse).filter_by(
                IDT_Niveau=id_niveau,
                IDAnneeScolaire=id_annee
            ).order_by(TClasse.LibClasse.asc()).all()
            for cl in classes_list:
                self.cmb_classe.addItem(cl.LibClasse, cl.IDTClasse)
        except Exception as e:
            print(f"Erreur chargement classes par niveau : {e}")
        finally:
            session.close()

    # ── Sélection ─────────────────────────────────────────────────────────────

    def on_responsable_selected(self):
        # Réinitialisation de l'état
        self.selected_eleve_id = None
        self._inscriptions_map = {}
        self._mode_modification = False
        self._id_inscription_courante = None
        self._set_form_enabled(False)
        self.table_eleves.setRowCount(0)

        selected_indexes = self.table_resp.selectedIndexes()
        if not selected_indexes:
            self.selected_famille_id = None
            self.btn_lier_eleve.setEnabled(False)
            return

        row = selected_indexes[0].row()
        self.selected_famille_id = self.table_resp.item(row, 0).data(Qt.UserRole)
        self.btn_lier_eleve.setEnabled(bool(self.selected_famille_id))

        id_annee = AppSession.get_active_annee_id()
        if not id_annee or not self.selected_famille_id:
            return

        # Charger TOUS les enfants de la famille (inscrits et non inscrits)
        eleves = EleveService.get_eleves_by_famille(self.selected_famille_id)
        eleve_ids = [el.IDEleve for el in eleves]

        # Récupérer en une seule requête les inscriptions de l'année en cours
        self._inscriptions_map = InscriptionService.get_inscriptions_by_eleves(eleve_ids, id_annee)

        for i, el in enumerate(eleves):
            self.table_eleves.insertRow(i)
            item_mat = QTableWidgetItem(el.Matricule)
            item_mat.setData(Qt.UserRole, el.IDEleve)
            self.table_eleves.setItem(i, 0, item_mat)
            self.table_eleves.setItem(i, 1, QTableWidgetItem(el.Nom))
            self.table_eleves.setItem(i, 2, QTableWidgetItem(el.Prenoms))

            if el.IDEleve in self._inscriptions_map:
                statut_item = QTableWidgetItem("Inscrit ✓")
                statut_item.setForeground(QColor(COLORS['success']))
            else:
                statut_item = QTableWidgetItem("Non inscrit")
                statut_item.setForeground(QColor("#9CA3AF"))
            self.table_eleves.setItem(i, 3, statut_item)
            self.table_eleves.setRowHeight(i, 32)

    def on_eleve_selected(self):
        selected_indexes = self.table_eleves.selectedIndexes()
        if not selected_indexes:
            self.selected_eleve_id = None
            self._set_form_enabled(False)
            return

        row = selected_indexes[0].row()
        item = self.table_eleves.item(row, 0)
        if not item:
            return

        self.selected_eleve_id = item.data(Qt.UserRole)

        if self.selected_eleve_id in self._inscriptions_map:
            # Élève déjà inscrit → mode modification
            self._mode_modification = True
            inscription = self._inscriptions_map[self.selected_eleve_id]
            self._id_inscription_courante = inscription.IDTInscription
            self._prefill_inscription(inscription)
            self.btn_inscrire.setText("Modifier l'Inscription")
            self.btn_inscrire.setStyleSheet(_BTN_MODIFIER)
        else:
            # Élève non inscrit → mode création
            self._mode_modification = False
            self._id_inscription_courante = None
            self._reset_form()
            self.btn_inscrire.setText("Inscrire l'Élève")
            self.btn_inscrire.setStyleSheet(_BTN_INSCRIRE)

        self._set_form_enabled(True)

    def on_classe_changed(self):
        # Le niveau pilote les frais annexes proposés (indépendant de la classe) :
        # on recharge ici pour couvrir à la fois un changement de niveau (qui repeuple
        # cmb_classe et déclenche ce slot) et un changement de classe direct.
        self._load_frais_annexes(self.cmb_niveau.currentData())

        id_classe = self.cmb_classe.currentData()
        id_annee = AppSession.get_active_annee_id()
        if not id_classe or not id_annee:
            self.lbl_effectif.setText("Effectif actuel : — / —")
            self._set_effectif_style("default")
            return

        session = get_session()
        try:
            classe_obj = session.get(TClasse, id_classe)
            if not classe_obj:
                self.lbl_effectif.setText("Effectif actuel : — / —")
                self._set_effectif_style("default")
                return
            effectif = InscriptionService.get_effectif_classe(id_classe, id_annee)
            capacite = classe_obj.Capacite if classe_obj.Capacite else 40
            self.lbl_effectif.setText(f"Effectif actuel : {effectif} / {capacite} élèves")

            if effectif >= capacite:
                self._set_effectif_style("full")
            elif effectif >= capacite * 0.8:
                self._set_effectif_style("warning")
            else:
                self._set_effectif_style("default")
        finally:
            session.close()

    # ── Liaison élève sans famille ────────────────────────────────────────────

    def on_lier_eleve(self):
        if not self.selected_famille_id:
            return

        eleves_sans_famille = EleveService.get_eleves_sans_famille()
        if not eleves_sans_famille:
            QMessageBox.information(
                self, "Aucun élève disponible",
                "Tous les élèves sont déjà liés à une famille."
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Associer un élève à cette famille")
        dlg.resize(520, 380)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setSpacing(12)
        dlg_layout.setContentsMargins(16, 16, 16, 16)

        lbl = QLabel("Sélectionnez l'élève à associer à cette famille :")
        lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #1E293B;")
        dlg_layout.addWidget(lbl)

        tbl = QTableWidget()
        tbl.setColumnCount(3)
        tbl.setHorizontalHeaderLabels(["Matricule", "Nom", "Prénoms"])
        tbl.setStyleSheet(TABLE_STYLE)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setSelectionMode(QTableWidget.SingleSelection)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.verticalHeader().setVisible(False)
        tbl.horizontalHeader().setHighlightSections(False)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i, el in enumerate(eleves_sans_famille):
            tbl.insertRow(i)
            item = QTableWidgetItem(el.Matricule)
            item.setData(Qt.UserRole, el.IDEleve)
            tbl.setItem(i, 0, item)
            tbl.setItem(i, 1, QTableWidgetItem(el.Nom))
            tbl.setItem(i, 2, QTableWidgetItem(el.Prenoms))
            tbl.setRowHeight(i, 32)
        dlg_layout.addWidget(tbl)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Associer")
        btns.button(QDialogButtonBox.Cancel).setText("Annuler")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        dlg_layout.addWidget(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        selected = tbl.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un élève dans la liste.")
            return

        id_eleve = tbl.item(selected[0].row(), 0).data(Qt.UserRole)
        success, msg = EleveService.link_famille(id_eleve, self.selected_famille_id)
        if success:
            QMessageBox.information(self, "Association réussie", msg)
            self.on_responsable_selected()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    # ── Action inscription / modification ─────────────────────────────────────

    def on_inscrire(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            QMessageBox.critical(self, "Erreur", "Aucune session active d'année scolaire configurée.")
            return
        if not self.selected_famille_id:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un parent à gauche avant d'initier l'inscription.")
            return
        if not self.selected_eleve_id:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner l'élève à inscrire à gauche.")
            return
        id_niveau = self.cmb_niveau.currentData()
        if not id_niveau:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un niveau scolaire.")
            self.cmb_niveau.setFocus()
            return
        id_classe = self.cmb_classe.currentData()
        if not id_classe:
            QMessageBox.warning(self, "Validation", "Veuillez affecter une classe de destination.")
            self.cmb_classe.setFocus()
            return

        # Frais annexes actuellement cochés (IDMontantAutres du catalogue paramétré)
        ids_montant_frais = [
            frais["IDMontantAutres"] for item, frais in self._frais_items
            if item.checkState() == Qt.Checked
        ]

        payload = {
            "IDEleve":     self.selected_eleve_id,
            "IDFamille":   self.selected_famille_id,
            "IDNiveau":    id_niveau,
            "IDClasse":    id_classe,
            "Nouveau":     self.chk_nouveau.isChecked(),
            "Scolarite":   self.chk_scolarite.isChecked(),
            "Transport":   self.chk_transport.isChecked(),
            "Cantine":     self.chk_cantine.isChecked(),
            # Indicateur global : au moins un frais annexe coché.
            "AutresFrais": bool(ids_montant_frais),
            "StatutAffectation": self.cmb_statut_affectation.currentData(),
        }

        id_inscription = None
        if self._mode_modification:
            success, message = InscriptionService.update_inscription(
                self._id_inscription_courante, payload
            )
            title_ok = "Modification Réussie"
            title_err = "Erreur de Modification"
            id_inscription = self._id_inscription_courante
        else:
            success, message = InscriptionService.create_inscription(payload)
            title_ok = "Inscription Réussie"
            title_err = "Régulation d'Inscription"
            if success:
                inscription_creee = InscriptionService.get_inscription_by_eleve_annee(
                    self.selected_eleve_id, id_annee
                )
                id_inscription = inscription_creee.IDTInscription if inscription_creee else None

        if success and id_inscription:
            ok_frais, msg_frais = InscriptionAutresFraisService.set_frais_coches(
                id_inscription, ids_montant_frais, login=None
            )
            if not ok_frais:
                QMessageBox.warning(
                    self, "Frais annexes",
                    f"L'inscription a été enregistrée mais les frais annexes n'ont pas pu être "
                    f"sauvegardés : {msg_frais}"
                )

        if success:
            QMessageBox.information(self, title_ok, message)
            self.on_responsable_selected()
            self.on_classe_changed()
        else:
            QMessageBox.critical(self, title_err, message)
