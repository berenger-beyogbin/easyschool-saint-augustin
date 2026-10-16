from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QMessageBox,
    QComboBox, QCheckBox, QFrame, QScrollArea,
    QSizePolicy,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QDialog, QPlainTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt
from services.eleve_service import EleveService
from services.niveau_service import NiveauService
from services.inscription_service import InscriptionService
from services.inscription_autres_frais_service import InscriptionAutresFraisService
from app.session import AppSession
from app.database import get_session
from app.config import Config
from models.classe import TClasse
from app.styles import (
    COLORS, COMBO_STYLE, format_fcfa,
    BUTTON_PRIMARY, BUTTON_SECONDARY, INPUT_STYLE
)
from views.inscription_widgets import (
    _FRAIS_LIST_STYLE, _FIELD_LABEL_STYLE, _CHK_STYLE,
    _BTN_INSCRIRE, _BTN_MODIFIER,
    make_step_card, make_option_row,
)
from views.eleve_selector_widgets import (
    EleveSearchPanel, EleveSummaryPanel, FamilleContactsPanel,
)
from views.eleve_form_view import EleveFormView
from views.famille_association_dialog import FamilleAssociationDialog


class InscriptionView(QWidget):
    """Vue INSCRIPTION ÉLÈVE — parcours "élève d'abord" : rechercher/
    sélectionner l'élève en premier, la famille (déjà associée à l'élève)
    s'affiche automatiquement, puis la situation scolaire de l'année active."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.selected_eleve_id = None
        self._eleve_courant = None  # Eleve (avec famille chargée) ou None
        self._mode_modification = False
        self._id_inscription_courante = None
        self._frais_items = []  # [(QListWidgetItem, frais_dict)] — liste dynamique selon le niveau
        self._form_enabled = False
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.refresh_recherche()
        self.load_niveaux()
        self._set_form_enabled(False)

    # ── Construction UI ───────────────────────────────────────────────────────

    def init_ui(self):
        # Deux colonnes INDÉPENDANTES (chacune son propre QVBoxLayout, pas de
        # rowspan de grille) : évite tout couplage de hauteur entre la carte
        # "Situation scolaire" (colonne droite, souvent haute) et les cartes
        # de gauche, qui provoquait un chevauchement des boutons sur le
        # tableau de résultats quand la fenêtre manquait de hauteur. Le tout
        # est enveloppé dans un QScrollArea pour rester utilisable même à
        # résolution réduite (cf. retour utilisateur sur les chevauchements).
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {COLORS['bg']}; border: none; }}")
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['bg']};")
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)
        scroll.setWidget(container)

        col_gauche = QVBoxLayout()
        col_gauche.setSpacing(14)
        col_droite = QVBoxLayout()
        col_droite.setSpacing(14)

        # ── Carte 1 : Recherche élève ─────────────────────────────────────────
        card1, c1 = make_step_card("1", "Rechercher et sélectionner l'élève")

        self.panel_recherche = EleveSearchPanel()
        self.panel_recherche.eleveSelected.connect(self.on_eleve_selected)
        self.panel_recherche.eleveDeselected.connect(self.on_eleve_deselected)
        self.panel_recherche.btn_nouveau.clicked.connect(self.on_nouvel_eleve)
        self.panel_recherche.btn_modifier.clicked.connect(self.on_modifier_eleve)
        c1.addWidget(self.panel_recherche)
        col_gauche.addWidget(card1)

        # ── Carte 2 : Élève sélectionné + famille (auto-affichée) ──────────────
        card2, c2 = make_step_card("2", "Élève sélectionné et famille")

        self.panel_resume = EleveSummaryPanel()
        c2.addWidget(self.panel_resume)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        sep.setFixedHeight(1)
        c2.addWidget(sep)

        self.panel_famille = FamilleContactsPanel()
        self.panel_famille.associerClicked.connect(self.on_associer_famille)
        c2.addWidget(self.panel_famille)

        col_gauche.addWidget(card2)
        col_gauche.addStretch(1)

        # ── Carte 3 : Situation scolaire (affectation classe/année) ────────────
        # Contenu repris à l'identique de l'ancienne carte d'affectation : seul
        # le pilotage mode création/modification change (piloté par
        # InscriptionService.get_situation_scolaire_active au lieu d'une carte
        # de sélection famille→enfants).
        card3, c3 = make_step_card("3", "Situation scolaire", scrollable=False)
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
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        sep2.setFixedHeight(1)
        c3.addSpacing(14)
        c3.addWidget(sep2)

        # Bloc 4 — Options de services scolarité
        c3.addSpacing(10)
        lbl_services = QLabel("OPTIONS DE SERVICES SCOLARITÉ")
        lbl_services.setStyleSheet(_FIELD_LABEL_STYLE)
        c3.addWidget(lbl_services)

        self.chk_scolarite = QCheckBox("Scolarité de base")
        self.chk_scolarite.setChecked(True)
        self.chk_scolarite.setStyleSheet(_CHK_STYLE)

        self.chk_nouveau = QCheckBox("Nouvel élève arrivant")
        self.chk_nouveau.setChecked(False)
        self.chk_nouveau.setStyleSheet(_CHK_STYLE)
        self.chk_nouveau.stateChanged.connect(
            lambda _state: self._load_frais_annexes(self.cmb_niveau.currentData())
        )

        self.chk_transport = QCheckBox("Option Transport bus")
        self.chk_transport.setStyleSheet(_CHK_STYLE)

        self.chk_cantine = QCheckBox("Option Cantine midi")
        self.chk_cantine.setStyleSheet(_CHK_STYLE)

        c3.addSpacing(6)
        row_base = QHBoxLayout()
        row_base.setSpacing(10)
        row_base.addWidget(make_option_row(self.chk_scolarite))
        row_base.addWidget(make_option_row(self.chk_nouveau))
        c3.addLayout(row_base)

        # Transport / Cantine désactivés pour la version collège CJGA
        # (voir app.config.Config) — masqués, non proposés en saisie.
        self.row_transport = make_option_row(self.chk_transport)
        self.row_transport.setVisible(Config.ENABLE_TRANSPORT)
        c3.addWidget(self.row_transport)

        self.row_cantine = make_option_row(self.chk_cantine)
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

        # Visible uniquement en mode modification (inscription existante).
        self.btn_supprimer = QPushButton("Supprimer l'inscription")
        self.btn_supprimer.setStyleSheet(
            f"QPushButton {{ color: {COLORS['danger']}; background: transparent; "
            f"border: 1px solid {COLORS['danger']}; border-radius: 8px; "
            "padding: 8px 14px; font-weight: 700; }"
            "QPushButton:hover { background-color: #FEF2F2; }"
        )
        self.btn_supprimer.setMinimumHeight(44)
        self.btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_supprimer.clicked.connect(self.on_supprimer_inscription)
        # Conteneur avec marge haute : l'espacement disparait avec le bouton.
        self.zone_supprimer = QWidget()
        self.zone_supprimer.setStyleSheet("background: transparent;")
        zl = QVBoxLayout(self.zone_supprimer)
        zl.setContentsMargins(0, 10, 0, 0)
        zl.addWidget(self.btn_supprimer)
        self.zone_supprimer.setVisible(False)
        c3.addWidget(self.zone_supprimer)

        col_droite.addWidget(card3)
        col_droite.addStretch(1)

        main_layout.addLayout(col_gauche, 1)
        main_layout.addLayout(col_droite, 1)

    # ── Activation/désactivation du formulaire ────────────────────────────────

    def _set_form_enabled(self, enabled: bool):
        """Active ou désactive les champs du panneau d'affectation."""
        self._form_enabled = enabled
        for w in [self.cmb_niveau, self.cmb_classe, self.cmb_statut_affectation,
                  self.chk_scolarite, self.chk_nouveau,
                  self.chk_transport, self.chk_cantine,
                  self.btn_inscrire, self.frais_annexes_list]:
            w.setEnabled(enabled)

    def _prefill_inscription(self, situation: dict):
        """Pré-remplit le formulaire à partir de get_situation_scolaire_active
        (dict simple, jamais un objet SQLAlchemy détaché)."""
        idx = self.cmb_niveau.findData(situation["id_niveau"])
        if idx >= 0:
            self.cmb_niveau.setCurrentIndex(idx)  # déclenche load_classes_par_niveau puis on_classe_changed
        idx = self.cmb_classe.findData(situation["id_classe"])
        if idx >= 0:
            self.cmb_classe.setCurrentIndex(idx)  # déclenche on_classe_changed (recharge les frais annexes)
        self.chk_scolarite.setChecked(situation["scolarite"])
        self.chk_nouveau.setChecked(situation["nouveau"])
        self.chk_transport.setChecked(situation["transport"])
        self.chk_cantine.setChecked(situation["cantine"])
        idx = self.cmb_statut_affectation.findData(situation["statut_affectation"] or "AFFECTE_ETAT")
        self.cmb_statut_affectation.setCurrentIndex(idx if idx >= 0 else 0)

        # Précoche les frais annexes déjà enregistrés pour cette inscription.
        self._precocher_frais_annexes(situation["id_inscription"])

    def _reset_form(self):
        """Réinitialise le formulaire aux valeurs par défaut pour une nouvelle inscription."""
        self.cmb_niveau.setCurrentIndex(0)
        self.cmb_classe.setCurrentIndex(0)
        self.cmb_statut_affectation.setCurrentIndex(0)
        self.chk_scolarite.setChecked(True)
        self.chk_nouveau.setChecked(False)
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
        """
        self._clear_frais_annexes_layout()

        id_annee = AppSession.get_active_annee_id()
        if not id_niveau or not id_annee:
            self._update_total_frais_annexes()
            return

        frais_list = InscriptionAutresFraisService.get_frais_proposes(id_niveau, id_annee)

        if self._eleve_courant:
            frais_list = (
                InscriptionAutresFraisService.get_frais_obligatoires_attendus(
                    id_annee,
                    self.chk_nouveau.isChecked(),
                    self._eleve_courant.Sexe,
                    id_niveau,
                )
                + frais_list
            )

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
            if frais.get("Obligatoire"):
                libelle_complet += " (obligatoire)"
                item.setText(libelle_complet)
                item.setFlags(Qt.ItemIsEnabled)
                item.setCheckState(Qt.Checked)
                item.setToolTip("Frais obligatoire, non décochable.")
            else:
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

    def refresh_recherche(self):
        """Recharge le panneau de recherche élève pour l'année active
        (appelé à l'ouverture de la vue/de l'onglet)."""
        self.panel_recherche.set_annee_active(AppSession.get_active_annee_id())

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

    # ── Sélection élève ───────────────────────────────────────────────────────

    def on_eleve_selected(self, id_eleve):
        """Point d'entrée central du parcours "élève d'abord" : recharge la
        fiche élève complète (avec famille), la situation scolaire de
        l'année active, et pilote le mode création/modification."""
        eleve = EleveService.get_eleve_by_id(id_eleve)
        if not eleve:
            self.on_eleve_deselected()
            return

        self.selected_eleve_id = id_eleve
        self._eleve_courant = eleve
        self.panel_resume.set_eleve(eleve)

        if eleve.famille:
            self.panel_famille.set_famille(eleve.famille)
        else:
            self.panel_famille.clear_no_famille()

        id_annee = AppSession.get_active_annee_id()
        situation = InscriptionService.get_situation_scolaire_active(id_eleve, id_annee) if id_annee else None
        self.panel_resume.set_situation(situation)

        if situation:
            self._mode_modification = True
            self._id_inscription_courante = situation["id_inscription"]
            self._prefill_inscription(situation)
            self.btn_inscrire.setText("Modifier l'Inscription")
            self.btn_inscrire.setStyleSheet(_BTN_MODIFIER)
            self.zone_supprimer.setVisible(AppSession.has_permission("SCOLARITE_INSCRIPTIONS"))
        else:
            self.zone_supprimer.setVisible(False)
            self._mode_modification = False
            self._id_inscription_courante = None
            self._reset_form()
            self.btn_inscrire.setText("Inscrire l'Élève")
            self.btn_inscrire.setStyleSheet(_BTN_INSCRIRE)

        self._set_form_enabled(True)

    def on_eleve_deselected(self):
        self.selected_eleve_id = None
        self._eleve_courant = None
        self._mode_modification = False
        self._id_inscription_courante = None
        self.zone_supprimer.setVisible(False)
        self.panel_resume.clear()
        self.panel_famille.clear_no_eleve()
        self._set_form_enabled(False)

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

    # ── Actions rapides depuis la recherche élève ───────────────────────────

    def on_nouvel_eleve(self):
        dlg = EleveFormView(self)
        if dlg.exec() == EleveFormView.Accepted:
            # Invalider explicitement l'ancien eleve avant de rechercher le
            # nouveau : aucune information parentale precedente ne doit rester
            # active pendant le rechargement du tableau.
            self.on_eleve_deselected()
            self.panel_recherche.txt_search.setText(dlg.txt_matricule.text().strip())
            self.panel_recherche.refresh()

    def on_modifier_eleve(self):
        id_eleve = self.panel_recherche.selected_id_eleve()
        if not id_eleve:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un élève dans le tableau.")
            return
        dlg = EleveFormView(self, id_eleve=id_eleve)
        if dlg.exec() == EleveFormView.Accepted:
            self.panel_recherche.refresh()
            self.on_eleve_selected(id_eleve)

    # ── Saisie directe des contacts parentaux ────────────────────────────────

    def on_associer_famille(self):
        if not self.selected_eleve_id or not self._eleve_courant:
            return

        eleve = self._eleve_courant
        matricule_affiche = eleve.MatriculeNational or eleve.Matricule
        eleve_label = f"{eleve.Nom} {eleve.Prenoms} ({matricule_affiche})"
        dlg = FamilleAssociationDialog(
            self,
            id_eleve=self.selected_eleve_id,
            eleve_label=eleve_label,
            famille=eleve.famille,
        )
        if dlg.exec() != FamilleAssociationDialog.Accepted or not dlg.id_famille_choisie:
            return

        self.on_eleve_selected(self.selected_eleve_id)
        self.panel_recherche.refresh()

    # ── Action inscription / modification ─────────────────────────────────────

    def on_inscrire(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            QMessageBox.critical(self, "Erreur", "Aucune session active d'année scolaire configurée.")
            return
        if not self.selected_eleve_id or not self._eleve_courant:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un élève dans la recherche ci-dessus.")
            return
        if not self._eleve_courant.IDFamille:
            QMessageBox.warning(
                self, "Validation",
                "Aucun contact parental n'est renseigné. Utilisez le bouton "
                "« Renseigner les contacts des parents » avant de l'inscrire."
            )
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
            frais.get("IDMontantAutres") for item, frais in self._frais_items
            if item.checkState() == Qt.Checked and frais.get("IDMontantAutres")
        ]

        payload = {
            "IDEleve":     self.selected_eleve_id,
            # Transmis pour info/audit : le service revalide qu'il correspond
            # bien à Eleve.IDFamille et ne fait jamais confiance à l'UI seule.
            "IDFamille":   self._eleve_courant.IDFamille,
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
            if not success and message == InscriptionService.MSG_BLOQUE_PAR_PAIEMENT:
                if self._proposer_correction_avec_annulation(payload):
                    self.on_eleve_selected(self.selected_eleve_id)
                    self.panel_recherche.refresh()
                return
            title_ok = "Modification Réussie"
            title_err = "Erreur de Modification"
            id_inscription = self._id_inscription_courante
        else:
            success, message = InscriptionService.create_inscription(payload)
            title_ok = "Inscription Réussie"
            title_err = "Erreur d'Inscription"
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
            self.on_eleve_selected(self.selected_eleve_id)
            self.panel_recherche.refresh()
        else:
            QMessageBox.critical(self, title_err, message)

    def _proposer_correction_avec_annulation(self, payload) -> bool:
        """Flux guidé quand le niveau/statut ne peut pas être modifié à
        cause d'un paiement existant : propose d'annuler (piste d'audit
        conservée) le(s) versement(s) de scolarité bloquant(s), puis
        applique la correction."""
        versements = InscriptionService.get_versements_scolarite_bloquants(
            self._id_inscription_courante
        )
        if not versements:
            QMessageBox.critical(self, "Erreur de Modification", InscriptionService.MSG_BLOQUE_PAR_PAIEMENT)
            return False

        lignes = "\n".join(
            f"  •  {v.DateVers:%d/%m/%Y} — {format_fcfa(v.MontantVersSco)}"
            for v in versements
        )
        reponse = QMessageBox.question(
            self, "Correction impossible directement",
            "Le niveau ou le statut d'affectation ne peut pas être changé car "
            f"{len(versements)} versement(s) de scolarité existent déjà pour cet élève :\n\n"
            f"{lignes}\n\n"
            "Voulez-vous ANNULER ce(s) versement(s) (piste d'audit conservée) pour "
            "appliquer la correction ? Il faudra ensuite ressaisir le paiement correct.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reponse != QMessageBox.Yes:
            return False

        motif = self._prompt_motif_correction()
        if motif is None:
            return False
        if not motif.strip():
            QMessageBox.warning(self, "Correction", "Le motif est obligatoire pour annuler les versements.")
            return False

        success, message = InscriptionService.corriger_inscription_avec_annulation(
            self._id_inscription_courante, payload, motif.strip(),
            login=AppSession.get_logged_in_username(),
            id_utilisateur=AppSession.get_current_user_id(),
        )
        if success:
            QMessageBox.information(self, "Correction appliquée", message)
        else:
            QMessageBox.critical(self, "Erreur", message)
        return success

    def on_supprimer_inscription(self):
        """Supprime l'inscription courante (erreur de saisie) apres
        confirmation et motif ; le service refuse s'il reste des versements
        actifs ou un dossier d'internat."""
        if not self._mode_modification or not self._id_inscription_courante:
            return
        if not AppSession.has_permission("SCOLARITE_INSCRIPTIONS"):
            QMessageBox.warning(self, "Permission", "Permission insuffisante pour supprimer une inscription.")
            return

        obstacles = InscriptionService.get_obstacles_suppression(self._id_inscription_courante)
        if obstacles:
            QMessageBox.warning(
                self, "Suppression impossible",
                "Cette inscription ne peut pas être supprimée :\n\n  •  " + "\n  •  ".join(obstacles)
            )
            return

        e = self._eleve_courant
        reponse = QMessageBox.question(
            self, "Supprimer l'inscription",
            f"Supprimer définitivement l'inscription de {e.Nom} {e.Prenoms} pour l'année active ?\n\n"
            "L'élève restera dans la base mais ne sera plus inscrit. "
            "Les frais annexes cochés seront supprimés.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reponse != QMessageBox.Yes:
            return

        motif = self._prompt_motif_correction(
            titre="Supprimer l'inscription", libelle="Motif de la suppression (obligatoire) :"
        )
        if motif is None:
            return
        if not motif.strip():
            QMessageBox.warning(self, "Suppression", "Le motif est obligatoire.")
            return

        success, message = InscriptionService.supprimer_inscription(
            self._id_inscription_courante, motif.strip(),
            id_utilisateur=AppSession.get_current_user_id(),
        )
        if success:
            QMessageBox.information(self, "Inscription supprimée", message)
            self.on_eleve_selected(self.selected_eleve_id)
            self.panel_recherche.refresh()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def _prompt_motif_correction(self, titre="Corriger l'inscription",
                                 libelle="Motif de la correction (obligatoire) :"):
        """Boîte de dialogue dédiée pour saisir le motif de la correction.

        Construite à la main (plutôt que QInputDialog.getMultiLineText) car
        les boutons standard de QInputDialog n'héritent pas de manière
        fiable du style global de l'appli (le sélecteur QSS [text="OK"] ne
        s'applique pas toujours), ce qui rendait le bouton OK illisible
        (même pattern que caisse_view._prompt_motif_annulation).

        Retourne le texte saisi, ou None si l'utilisateur a annulé.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(titre)
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(10)

        lbl = QLabel(libelle)
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px; border: none;")
        layout.addWidget(lbl)

        txt_motif = QPlainTextEdit()
        txt_motif.setStyleSheet(INPUT_STYLE)
        txt_motif.setFixedHeight(90)
        layout.addWidget(txt_motif)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_ok = buttons.button(QDialogButtonBox.Ok)
        btn_ok.setText("Valider")
        btn_ok.setStyleSheet(BUTTON_PRIMARY)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_cancel = buttons.button(QDialogButtonBox.Cancel)
        btn_cancel.setText("Annuler")
        btn_cancel.setStyleSheet(BUTTON_SECONDARY)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        txt_motif.setFocus()
        if dialog.exec() != QDialog.Accepted:
            return None
        return txt_motif.toPlainText()
