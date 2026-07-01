"""
Rapport prestataire — ventilation analytique des prestations annexes.
Affiche les montants ventilés par classe / prestation et le détail par élève.
Export CSV disponible.
"""

import csv
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QFrame, QTabWidget,
    QFileDialog, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from services.ventilation_service import VentilationService
from services.prestation_service import PrestationService
from services.statistiques_service import StatistiquesService
from app.session import AppSession
from utils.list_printer import PrestationSyntheseStatPrinter, PrestationDetailStatPrinter
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    COMBO_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS, BUTTON_SECONDARY,
    apply_table_style, make_totaux_panel_widget
)


def _fmt(v) -> str:
    try:
        return f"{int(float(v)):,} FCFA".replace(",", " ")
    except Exception:
        return "0 FCFA"

def _pct(v) -> str:
    try:
        return f"{float(v) * 100:.1f} %"
    except Exception:
        return "—"


# ─── Thread recalcul global ───────────────────────────────────────────────────

class RecalculThread(QThread):
    """Thread de recalcul en arrière-plan pour ne pas bloquer l'UI."""
    finished = Signal(dict)

    def __init__(self, id_annee: int):
        super().__init__()
        self.id_annee = id_annee

    def run(self):
        result = VentilationService.recalculate_all_for_annee(self.id_annee)
        self.finished.emit(result)


# ─── Vue principale ───────────────────────────────────────────────────────────

class StatPrestatairesView(QWidget):
    """Module rapport prestataires (ventilation analytique des prestations annexes)."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self._recalcul_thread = None
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(12)

        # Titre
        titre = QLabel("Rapport Prestataires — Ventilation Analytique")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        root.addWidget(titre)

        sous_titre = QLabel(
            "Part des paiements de scolarité correspondant aux prestations annexes (Anglais/Informatique, "
            "Entrepreneuriat, Musique…). Chaque prestation est couverte intégralement, dans l'ordre de "
            "création des prestations, avant de passer à la suivante — statistiques à titre informatif."
        )
        sous_titre.setStyleSheet(SECTION_TITLE_STYLE)
        sous_titre.setWordWrap(True)
        root.addWidget(sous_titre)

        # ─ Filtres ─────────────────────────────────────────────────────────
        filtres_row = QHBoxLayout()
        filtres_row.setSpacing(10)
        lbl_s = f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"

        lbl_prest = QLabel("Prestation :")
        lbl_prest.setStyleSheet(lbl_s)
        self.cmb_prestation = QComboBox()
        self.cmb_prestation.setStyleSheet(COMBO_STYLE)
        self.cmb_prestation.setMinimumWidth(200)

        lbl_cls = QLabel("Classe :")
        lbl_cls.setStyleSheet(lbl_s)
        self.cmb_classe = QComboBox()
        self.cmb_classe.setStyleSheet(COMBO_STYLE)
        self.cmb_classe.setMinimumWidth(160)

        self.btn_afficher = QPushButton("Afficher")
        self.btn_afficher.setStyleSheet(BUTTON_PRIMARY)
        self.btn_afficher.setFixedHeight(34)
        self.btn_afficher.clicked.connect(self.refresh_data)

        self.btn_csv = QPushButton("Exporter CSV")
        self.btn_csv.setStyleSheet(BUTTON_SUCCESS)
        self.btn_csv.setFixedHeight(34)
        self.btn_csv.clicked.connect(self._export_csv)

        self.btn_imprimer = QPushButton("Imprimer")
        self.btn_imprimer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_imprimer.setFixedHeight(34)
        self.btn_imprimer.setToolTip(
            "Imprime le rapport de l'onglet actif (Synthèse par classe ou Détail par élève)."
        )
        self.btn_imprimer.clicked.connect(self._print_current_tab)

        self.btn_recalcul = QPushButton("Recalculer tout")
        self.btn_recalcul.setStyleSheet(BUTTON_SECONDARY)
        self.btn_recalcul.setFixedHeight(34)
        self.btn_recalcul.setToolTip(
            "Recalcule les ventilations de tous les élèves inscrits pour l'année active.\n"
            "Utile après modification d'un tarif de scolarité ou d'une prestation."
        )
        self.btn_recalcul.clicked.connect(self._on_recalcul_global)

        filtres_row.addWidget(lbl_prest)
        filtres_row.addWidget(self.cmb_prestation)
        filtres_row.addWidget(lbl_cls)
        filtres_row.addWidget(self.cmb_classe)
        filtres_row.addWidget(self.btn_afficher)
        filtres_row.addWidget(self.btn_csv)
        filtres_row.addWidget(self.btn_imprimer)
        filtres_row.addStretch()
        filtres_row.addWidget(self.btn_recalcul)
        root.addLayout(filtres_row)

        # ─ Onglets synthèse / détail ───────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['card']};
                border-radius: 0 0 8px 8px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['border_soft']};
                color: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px 6px 0 0;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['card']};
                color: {COLORS['primary']};
                border-bottom: 2px solid {COLORS['primary']};
            }}
        """)

        # Tab 1 — Synthèse par classe
        self.tab_synthese = QWidget()
        self._build_synthese_tab(self.tab_synthese)
        self.tabs.addTab(self.tab_synthese, "Synthèse par classe")

        # Tab 2 — Détail par élève
        self.tab_detail = QWidget()
        self._build_detail_tab(self.tab_detail)
        self.tabs.addTab(self.tab_detail, "Détail par élève")

        root.addWidget(self.tabs, 1)

        # Charger les filtres
        self._load_filters()

    # ─── Tab Synthèse ─────────────────────────────────────────────────────────

    def _build_synthese_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.table_synthese = QTableWidget()
        self.table_synthese.setColumnCount(6)
        self.table_synthese.setHorizontalHeaderLabels([
            "Classe", "Prestation", "Nb élèves",
            "Montant théorique", "Montant ventilé", "Reste à recouvrer"
        ])
        self.table_synthese.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_synthese.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_synthese.setAlternatingRowColors(True)
        apply_table_style(self.table_synthese)

        hdr = self.table_synthese.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        for i in range(3, 6):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hdr.setHighlightSections(False)
        layout.addWidget(self.table_synthese, 1)

        self.totaux_s, (
            self.lbl_s_nb,
            self.lbl_s_theo,
            self.lbl_s_ventile,
            self.lbl_s_reste,
        ) = make_totaux_panel_widget([
            ("Nb élèves",          COLORS["primary"]),
            ("Total théorique",    COLORS["text"]),
            ("Total ventilé",      COLORS["success"]),
            ("Reste à recouvrer",  COLORS["warning"]),
        ])
        layout.addWidget(self.totaux_s)

    # ─── Tab Détail ───────────────────────────────────────────────────────────

    def _build_detail_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.table_detail = QTableWidget()
        self.table_detail.setColumnCount(7)
        self.table_detail.setHorizontalHeaderLabels([
            "Matricule", "Nom & Prénoms", "Classe", "Prestation",
            "Montant théorique", "Montant ventilé", "Reste"
        ])
        self.table_detail.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_detail.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_detail.setAlternatingRowColors(True)
        apply_table_style(self.table_detail)

        hdr = self.table_detail.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for i in range(4, 7):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hdr.setHighlightSections(False)
        layout.addWidget(self.table_detail, 1)

        self.totaux_d, (
            self.lbl_d_theo,
            self.lbl_d_ventile,
            self.lbl_d_reste,
        ) = make_totaux_panel_widget([
            ("Total théorique",   COLORS["text"]),
            ("Total ventilé",     COLORS["success"]),
            ("Reste à recouvrer", COLORS["warning"]),
        ])
        layout.addWidget(self.totaux_d)

    # ─── Logique ──────────────────────────────────────────────────────────────

    def _load_filters(self):
        id_annee = AppSession.get_active_annee_id()

        # Prestation
        self.cmb_prestation.blockSignals(True)
        self.cmb_prestation.clear()
        self.cmb_prestation.addItem("— Toutes les prestations —", None)
        for p in PrestationService.get_all_prestations():
            self.cmb_prestation.addItem(p.Libelle, p.IDPrestation)
        self.cmb_prestation.blockSignals(False)

        # Classe
        self.cmb_classe.blockSignals(True)
        self.cmb_classe.clear()
        self.cmb_classe.addItem("— Toutes les classes —", None)
        classes = StatistiquesService.get_classes_by_niveau(None)
        for cls in classes:
            self.cmb_classe.addItem(cls["LibClasse"], cls["IDTClasse"])
        self.cmb_classe.blockSignals(False)

    def refresh_data(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return

        id_prestation = self.cmb_prestation.currentData()
        id_classe = self.cmb_classe.currentData()

        self._load_synthese(id_annee, id_prestation, id_classe)
        self._load_detail(id_annee, id_prestation, id_classe)

    def _load_synthese(self, id_annee, id_prestation, id_classe):
        data = VentilationService.get_provider_report(id_annee, id_prestation, id_classe)
        self.table_synthese.setRowCount(len(data))

        sum_nb, sum_theo, sum_ventile, sum_reste = 0, 0.0, 0.0, 0.0

        for i, row in enumerate(data):
            sum_nb += row["nb_eleves"]
            sum_theo += row["total_theorique"]
            sum_ventile += row["total_ventile"]
            sum_reste += row["reste"]

            it_cls = QTableWidgetItem(row["classe"])
            it_prest = QTableWidgetItem(row["prestation"])
            it_nb = QTableWidgetItem(str(row["nb_eleves"]))
            it_nb.setTextAlignment(Qt.AlignCenter)
            it_theo = QTableWidgetItem(_fmt(row["total_theorique"]))
            it_theo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_vent = QTableWidgetItem(_fmt(row["total_ventile"]))
            it_vent.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_vent.setForeground(QColor(COLORS["success"]))
            it_reste = QTableWidgetItem(_fmt(row["reste"]))
            it_reste.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row["reste"] > 0:
                it_reste.setForeground(QColor(COLORS["warning"]))

            for col, it in enumerate([it_cls, it_prest, it_nb, it_theo, it_vent, it_reste]):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.table_synthese.setItem(i, col, it)
            self.table_synthese.setRowHeight(i, 34)

        self.lbl_s_nb.setText(str(sum_nb))
        self.lbl_s_theo.setText(_fmt(sum_theo))
        self.lbl_s_ventile.setText(_fmt(sum_ventile))
        self.lbl_s_reste.setText(_fmt(sum_reste))

    def _load_detail(self, id_annee, id_prestation, id_classe):
        data = VentilationService.get_detail_eleves_report(id_annee, id_prestation, id_classe)
        self.table_detail.setRowCount(len(data))

        sum_theo, sum_ventile, sum_reste = 0.0, 0.0, 0.0

        for i, row in enumerate(data):
            sum_theo += row["montant_theorique"]
            sum_ventile += row["montant_ventile"]
            sum_reste += row["reste"]

            it_mat = QTableWidgetItem(row["matricule"])
            it_mat.setTextAlignment(Qt.AlignCenter)
            it_nom = QTableWidgetItem(row["nom"].upper())
            it_cls = QTableWidgetItem(row["classe"])
            it_prest = QTableWidgetItem(row["prestation"])
            it_theo = QTableWidgetItem(_fmt(row["montant_theorique"]))
            it_theo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_vent = QTableWidgetItem(_fmt(row["montant_ventile"]))
            it_vent.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_vent.setForeground(QColor(COLORS["success"]))
            it_reste = QTableWidgetItem(_fmt(row["reste"]))
            it_reste.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row["reste"] > 0:
                it_reste.setForeground(QColor(COLORS["warning"]))

            for col, it in enumerate([it_mat, it_nom, it_cls, it_prest, it_theo, it_vent, it_reste]):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.table_detail.setItem(i, col, it)
            self.table_detail.setRowHeight(i, 34)

        self.lbl_d_theo.setText(_fmt(sum_theo))
        self.lbl_d_ventile.setText(_fmt(sum_ventile))
        self.lbl_d_reste.setText(_fmt(sum_reste))

    # ─── Recalcul global ──────────────────────────────────────────────────────

    def _on_recalcul_global(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            QMessageBox.warning(self, "Attention", "Aucune année scolaire active sélectionnée.")
            return

        reply = QMessageBox.question(
            self,
            "Recalculer toutes les ventilations",
            "Cette opération va recalculer les ventilations de tous les élèves inscrits.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.btn_recalcul.setEnabled(False)
        self.btn_recalcul.setText("Recalcul en cours…")

        self._recalcul_thread = RecalculThread(id_annee)
        self._recalcul_thread.finished.connect(self._on_recalcul_done)
        self._recalcul_thread.start()

    def _on_recalcul_done(self, result: dict):
        self.btn_recalcul.setEnabled(True)
        self.btn_recalcul.setText("Recalculer tout")

        traites = result.get("traites", 0)
        erreurs = result.get("erreurs", 0)
        msg = f"Recalcul terminé.\n\n{traites} élève(s) traité(s)."
        if erreurs:
            msg += f"\n{erreurs} erreur(s) détectée(s)."
            for e in result.get("detail_erreurs", [])[:5]:
                msg += f"\n• {e}"

        QMessageBox.information(self, "Recalcul terminé", msg)
        self.refresh_data()

    # ─── Impression ───────────────────────────────────────────────────────────

    def _build_titre_filtre(self) -> str:
        parts = []
        if self.cmb_prestation.currentData() is not None:
            parts.append(self.cmb_prestation.currentText())
        if self.cmb_classe.currentData() is not None:
            parts.append(self.cmb_classe.currentText())
        return " — ".join(parts)

    def _print_current_tab(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            QMessageBox.warning(self, "Attention", "Aucune année scolaire active.")
            return

        id_prestation = self.cmb_prestation.currentData()
        id_classe = self.cmb_classe.currentData()
        titre_filtre = self._build_titre_filtre()

        if self.tabs.currentIndex() == 0:
            data = VentilationService.get_provider_report(id_annee, id_prestation, id_classe)
            if not data:
                QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
                return
            PrestationSyntheseStatPrinter.print_report(self, data, titre_filtre)
        else:
            data = VentilationService.get_detail_eleves_report(id_annee, id_prestation, id_classe)
            if not data:
                QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
                return
            PrestationDetailStatPrinter.print_report(self, data, titre_filtre)

    # ─── Export CSV ───────────────────────────────────────────────────────────

    def _export_csv(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            QMessageBox.warning(self, "Attention", "Aucune année scolaire active.")
            return

        id_prestation = self.cmb_prestation.currentData()
        id_classe = self.cmb_classe.currentData()
        data = VentilationService.get_detail_eleves_report(id_annee, id_prestation, id_classe)

        if not data:
            QMessageBox.information(self, "Export CSV", "Aucune donnée à exporter.")
            return

        default_name = f"rapport_prestataires_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le rapport CSV", default_name,
            "Fichiers CSV (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "Matricule", "Nom & Prénoms", "Classe", "Prestation",
                    "Montant théorique (FCFA)", "Montant ventilé (FCFA)",
                    "Reste à recouvrer (FCFA)", "Taux paiement (%)"
                ])
                for row in data:
                    writer.writerow([
                        row["matricule"],
                        row["nom"],
                        row["classe"],
                        row["prestation"],
                        int(row["montant_theorique"]),
                        int(row["montant_ventile"]),
                        int(row["reste"]),
                        f"{row['taux'] * 100:.1f}",
                    ])
            QMessageBox.information(
                self, "Export réussi",
                f"Rapport exporté avec succès.\n{len(data)} lignes exportées.\n\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Impossible d'écrire le fichier :\n{str(e)}")
