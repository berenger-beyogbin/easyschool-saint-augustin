"""Widgets réutilisables du parcours d'inscription "élève d'abord" :
recherche/sélection de l'élève, résumé de son identité, contacts famille.

Extraits de InscriptionView pour éviter qu'un seul fichier ne porte à la
fois la recherche, l'affichage élève, l'affichage famille et l'affectation
scolaire (voir views/inscription_view.py).
"""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
)

from app.styles import COLORS, INPUT_STYLE, TABLE_STYLE
from services.eleve_service import EleveService

_FIELD_LABEL_STYLE = (
    f"font-size: 10px; font-weight: 700; color: {COLORS['muted']};"
    "background-color: transparent; border: none; letter-spacing: 0.5px;"
)
_VALUE_STYLE = (
    f"font-size: 13px; font-weight: 600; color: {COLORS['text']};"
    "background-color: transparent; border: none;"
)
_MUTED_STYLE = (
    f"font-size: 12px; font-style: italic; color: {COLORS['muted']};"
    "background-color: transparent; border: none;"
)


def _app_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────────────────────────────────
# 1. Recherche et sélection de l'élève
# ─────────────────────────────────────────────────────────────────────────

class EleveSearchPanel(QWidget):
    """Recherche d'élève (matricule interne/national, nom, prénoms, tél.
    parent) + tableau de résultats. Émet eleveSelected(id_eleve) /
    eleveDeselected() ; ne connaît ni la famille ni l'affectation."""

    eleveSelected = Signal(int)
    eleveDeselected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._id_annee = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(
            "Matricule national, nom, prénoms ou téléphone d'un parent…"
        )
        self.txt_search.setStyleSheet(INPUT_STYLE)
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self.refresh)
        layout.addWidget(self.txt_search)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Matricule national", "Interne", "Nom", "Prénoms", "Sexe",
            "Famille / Responsable", "Statut", "Classe",
        ])
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        # Largeurs initiales resserrees sur les colonnes courtes : la largeur
        # par defaut (100px/colonne) des 6 colonnes non-etirees forcait a elle
        # seule ~600px de largeur minimale, provoquant un defilement horizontal
        # indesirable une fois la vue partagee en deux colonnes cote a cote.
        self.table.setColumnWidth(0, 105)  # Matricule national
        self.table.setColumnWidth(1, 70)   # Matricule interne
        self.table.setColumnWidth(2, 85)   # Nom
        self.table.setColumnWidth(3, 85)   # Prénoms
        self.table.setColumnWidth(4, 45)   # Sexe
        self.table.setColumnWidth(6, 75)   # Statut
        self.table.setColumnWidth(7, 65)   # Classe
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setFixedHeight(220)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_nouveau = QPushButton("+ Nouvel élève")
        self.btn_nouveau.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['success']}; color: #FFFFFF;"
            "font-weight: 700; border-radius: 7px; border: none; padding: 8px 14px; }"
            f"QPushButton:hover {{ background-color: #15803D; }}"
        )
        self.btn_modifier = QPushButton("Modifier l'élève")
        self.btn_modifier.setEnabled(False)
        self.btn_modifier.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['card']}; color: {COLORS['text']};"
            f"border: 1px solid {COLORS['border']}; border-radius: 7px; padding: 8px 14px; font-weight: 600; }}"
            f"QPushButton:disabled {{ color: #CBD5E1; }}"
        )
        btn_row.addWidget(self.btn_nouveau)
        btn_row.addWidget(self.btn_modifier)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    # ── Chargement ───────────────────────────────────────────────────────

    def set_annee_active(self, id_annee):
        self._id_annee = id_annee
        self.refresh()

    def refresh(self):
        """Relance la recherche avec le texte courant."""
        query = self.txt_search.text().strip()
        resultats = EleveService.search_eleves(query, id_annee=self._id_annee)
        self._afficher(resultats)

    def _afficher(self, resultats):
        # Conserver la selection uniquement si le meme eleve existe encore
        # dans les nouveaux resultats. QTableWidget peut sinon conserver une
        # ligne selectionnee par position pendant que ses donnees changent ;
        # comme les signaux sont bloques durant le remplissage, l'ecran parent
        # continuerait alors a afficher la famille de l'ancien eleve.
        selected_id = self.selected_id_eleve()
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.setRowCount(len(resultats))
        row_to_restore = None
        for i, r in enumerate(resultats):
            item_mat = QTableWidgetItem(r["matricule_national"] or "—")
            item_mat.setData(Qt.UserRole, r["id_eleve"])
            self.table.setItem(i, 0, item_mat)
            self.table.setItem(i, 1, QTableWidgetItem(r["matricule"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["nom"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["prenoms"]))
            self.table.setItem(i, 4, QTableWidgetItem("M" if r["sexe"] == 1 else "F"))
            self.table.setItem(i, 5, QTableWidgetItem(r["famille_label"] or "— Aucune famille —"))

            statut_item = QTableWidgetItem("Inscrit ✓" if r["inscrit"] else "Non inscrit")
            statut_item.setForeground(
                Qt.GlobalColor.darkGreen if r["inscrit"] else Qt.GlobalColor.gray
            )
            self.table.setItem(i, 6, statut_item)
            self.table.setItem(i, 7, QTableWidgetItem(r["classe_libelle"]))
            self.table.setRowHeight(i, 30)
            if r["id_eleve"] == selected_id:
                row_to_restore = i
        if row_to_restore is not None:
            self.table.selectRow(row_to_restore)
        self.table.blockSignals(False)
        self.btn_modifier.setEnabled(row_to_restore is not None)

        if row_to_restore is not None:
            self.eleveSelected.emit(selected_id)
        else:
            self.eleveDeselected.emit()

    # ── Sélection ────────────────────────────────────────────────────────

    def _on_selection_changed(self):
        selected = self.table.selectedIndexes()
        if not selected:
            self.btn_modifier.setEnabled(False)
            self.eleveDeselected.emit()
            return
        row = selected[0].row()
        id_eleve = self.table.item(row, 0).data(Qt.UserRole)
        self.btn_modifier.setEnabled(True)
        self.eleveSelected.emit(id_eleve)

    def selected_id_eleve(self):
        selected = self.table.selectedIndexes()
        if not selected:
            return None
        return self.table.item(selected[0].row(), 0).data(Qt.UserRole)

    def select_eleve(self, id_eleve: int) -> bool:
        """Selectionne explicitement un eleve deja affiche dans le tableau."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == id_eleve:
                self.table.selectRow(row)
                return True
        self.table.clearSelection()
        return False


# ─────────────────────────────────────────────────────────────────────────
# 2. Résumé identité de l'élève sélectionné
# ─────────────────────────────────────────────────────────────────────────

class EleveSummaryPanel(QWidget):
    """Résumé en lecture seule : photo, matricules, naissance, sexe,
    nationalité, habitation, statut scolaire de l'année active."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.clear()

    def _init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        self.lbl_photo = QLabel()
        self.lbl_photo.setFixedSize(72, 90)
        self.lbl_photo.setAlignment(Qt.AlignCenter)
        self.lbl_photo.setStyleSheet(
            f"border: 1.5px dashed {COLORS['border']}; border-radius: 6px;"
            f"background-color: {COLORS['bg']}; color: #94A3B8; font-size: 10px;"
        )
        root.addWidget(self.lbl_photo)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        def add_field(row, col, label_text):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(_FIELD_LABEL_STYLE)
            val = QLabel("—")
            val.setStyleSheet(_VALUE_STYLE)
            val.setWordWrap(True)
            grid.addWidget(lbl, row * 2, col)
            grid.addWidget(val, row * 2 + 1, col)
            return val

        self.val_nom = add_field(0, 0, "ÉLÈVE")
        self.val_matricules = add_field(0, 1, "MATRICULE NATIONAL")
        self.val_naissance = add_field(1, 0, "NÉ(E) LE / LIEU")
        self.val_sexe_nat = add_field(1, 1, "SEXE / NATIONALITÉ")
        self.val_habitation = add_field(2, 0, "HABITATION")
        self.val_situation = add_field(2, 1, "SITUATION SCOLAIRE")

        root.addLayout(grid, 1)

    def clear(self):
        self.lbl_photo.setText("📷")
        self.lbl_photo.setPixmap(QPixmap())
        for val in (self.val_nom, self.val_matricules, self.val_naissance,
                    self.val_sexe_nat, self.val_habitation, self.val_situation):
            val.setText("—")

    def set_eleve(self, el):
        self.val_nom.setText(f"{el.Nom} {el.Prenoms}")
        mat_nat = getattr(el, "MatriculeNational", None) or "Non renseigné"
        self.val_matricules.setText(f"{mat_nat}  ·  Interne : {el.Matricule}")

        naiss = el.DateNaissance.strftime("%d/%m/%Y") if el.DateNaissance else "?"
        lieu = el.LieuNaissance or "lieu non renseigné"
        self.val_naissance.setText(f"{naiss} — {lieu}")

        sexe_lib = "Masculin" if el.Sexe == 1 else "Féminin"
        nat_lib = el.nationalite.Nationalite if el.nationalite else "non renseignée"
        self.val_sexe_nat.setText(f"{sexe_lib} — {nat_lib}")

        self.val_habitation.setText(el.Habitation or "Non renseignée")

        if el.PhotoPath:
            full_path = os.path.join(_app_dir(), el.PhotoPath)
            if os.path.exists(full_path):
                pix = QPixmap(full_path)
                self.lbl_photo.setPixmap(
                    pix.scaled(self.lbl_photo.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.lbl_photo.setText("📷")
        else:
            self.lbl_photo.setText("📷")

    def set_situation(self, situation: dict | None):
        if situation:
            statut_lib = "AFFECTÉ ÉTAT" if situation["statut_affectation"] == "AFFECTE_ETAT" else "NON AFFECTÉ"
            self.val_situation.setText(
                f"Inscrit(e) — {situation['classe_libelle']} ({statut_lib})"
            )
        else:
            self.val_situation.setText("Non inscrit(e) cette année")


# ─────────────────────────────────────────────────────────────────────────
# 3. Contacts famille (responsable / père / mère / tuteur)
# ─────────────────────────────────────────────────────────────────────────

class FamilleContactsPanel(QWidget):
    """Affiche automatiquement les contacts de la famille de l'élève
    sélectionné. Émet associerClicked() pour saisir directement le père,
    la mère et le tuteur ; la famille technique reste invisible."""

    associerClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.clear_no_famille()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.lbl_etat = QLabel()
        self.lbl_etat.setWordWrap(True)
        layout.addWidget(self.lbl_etat)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(10)
        layout.addLayout(self.grid)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        self.btn_associer = QPushButton("Renseigner les contacts des parents")
        self.btn_associer.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {COLORS['primary']};"
            f"border: 1.5px dashed {COLORS['primary']}; border-radius: 7px;"
            "font-weight: 700; padding: 8px 12px; }"
            f"QPushButton:hover {{ background-color: {COLORS['surface_soft']}; }}"
        )
        self.btn_associer.clicked.connect(self.associerClicked.emit)
        layout.addWidget(self.btn_associer)
        layout.addStretch()

    def _clear_grid(self):
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clear_no_eleve(self):
        self._clear_grid()
        self.lbl_etat.setText("Sélectionnez un élève pour afficher les contacts de ses parents.")
        self.lbl_etat.setStyleSheet(_MUTED_STYLE)
        self.btn_associer.setEnabled(False)

    def clear_no_famille(self):
        self._clear_grid()
        self.btn_associer.setText("Renseigner les contacts des parents")
        self.lbl_etat.setText(
            "Aucun contact parental renseigné. Ajoutez au moins le père, la mère ou le tuteur avant d'inscrire l'élève."
        )
        self.lbl_etat.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['danger']};")
        self.btn_associer.setEnabled(True)

    def set_famille(self, fam):
        self._clear_grid()
        self.lbl_etat.setText("")
        self.btn_associer.setText("Modifier les contacts des parents")
        self.btn_associer.setEnabled(True)

        def bloc(row, titre, nom, tel, extra=""):
            lbl_titre = QLabel(titre)
            lbl_titre.setStyleSheet(_FIELD_LABEL_STYLE)
            lbl_titre.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.grid.addWidget(lbl_titre, row, 0, Qt.AlignTop)
            lbl_val = QLabel(f"{nom or '—'}" + (f"  ·  {tel}" if tel else "") + (f"\n{extra}" if extra else ""))
            lbl_val.setStyleSheet(_VALUE_STYLE)
            lbl_val.setWordWrap(True)
            self.grid.addWidget(lbl_val, row, 1, Qt.AlignTop)

        qualite_lib = {1: "Tuteur", 2: "Père", 3: "Mère"}.get(fam.QualiteResponsable, "Responsable")
        bloc(0, f"RESPONSABLE ({qualite_lib})", fam.NomResponsable, fam.CellulaireResponsable,
             extra=fam.EmailResponsable or "")
        if fam.NomPere:
            bloc(1, "PÈRE", fam.NomPere, fam.TelPere, getattr(fam, "EmailPere", None) or "")
        if fam.NomMere:
            bloc(2, "MÈRE", fam.NomMere, fam.TelMere, getattr(fam, "EmailMere", None) or "")
        if fam.NomTuteur:
            bloc(3, "TUTEUR", fam.NomTuteur, fam.CelTuteur, getattr(fam, "EmailTuteur", None) or "")
