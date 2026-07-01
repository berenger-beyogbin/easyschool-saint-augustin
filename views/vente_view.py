import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt
from services.article_service import ArticleService
from services.stock_service import StockService
from app.session import AppSession
from app.styles import (
    COLORS, INPUT_STYLE, COMBO_STYLE, SECTION_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_SUCCESS, BUTTON_DANGER,
    GROUPBOX_ACCENT_STYLE, apply_table_style
)

class VenteView(QWidget):
    """
    Scolarité > Kiosque > Ventes
    Permet de gerer un panier d'achats pour l'eleve, de verifier la disponibilite en direct,
    et d'enregistrer les factures-sorties de stock courantes.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        # Panier temporaire en memoire : { id_article: { "nom": str, "pu": float, "qte": int, "total": float } }
        self.panier = {}

        self.init_ui()
        self.load_articles()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # 1. Splitter general pour separe controle/panier
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #cbd5e1; }")

        # --- PANNEAU GAUCHE : Configuration de la ligne ---
        pane_gauche = QWidget()
        layout_gauche = QVBoxLayout(pane_gauche)
        layout_gauche.setContentsMargins(0, 0, 10, 0)
        layout_gauche.setSpacing(15)

        group_saisie = QGroupBox("1. CHOISIR UN ARTICLE EN COMMANDE")
        group_saisie.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        layout_saisie = QVBoxLayout(group_saisie)
        layout_saisie.setSpacing(10)

        layout_saisie.addWidget(QLabel("Sélectionner l'article ou le KIT :"))
        self.cmb_articles = QComboBox()
        self.cmb_articles.setStyleSheet(COMBO_STYLE)
        self.cmb_articles.currentIndexChanged.connect(self.on_article_changed)
        layout_saisie.addWidget(self.cmb_articles)

        # Label stock disponible en temps réel
        self.lbl_stock_dispo = QLabel("Stock disponible : --")
        self.lbl_stock_dispo.setStyleSheet(
            f"font-weight: bold; color: {COLORS['warning']}; padding-left: 2px; background-color: transparent;"
        )
        layout_saisie.addWidget(self.lbl_stock_dispo)

        layout_saisie.addWidget(QLabel("Prix unitaire de vente (F CFA) :"))
        self.txt_pu = QLineEdit()
        self.txt_pu.setStyleSheet(INPUT_STYLE)
        layout_saisie.addWidget(self.txt_pu)

        layout_saisie.addWidget(QLabel("Quantité à acheter :"))
        self.txt_quantite = QLineEdit("1")
        self.txt_quantite.setStyleSheet(INPUT_STYLE)
        layout_saisie.addWidget(self.txt_quantite)

        self.btn_ajouter = QPushButton("Ajouter au Panier >>")
        self.btn_ajouter.setStyleSheet(BUTTON_SUCCESS)
        self.btn_ajouter.clicked.connect(self.on_ajouter_panier)
        layout_saisie.addWidget(self.btn_ajouter)

        layout_gauche.addWidget(group_saisie)

        self.btn_effacer_sel = QPushButton("Réinitialiser")
        self.btn_effacer_sel.setStyleSheet(BUTTON_SECONDARY)
        self.btn_effacer_sel.clicked.connect(self.on_effacer_selection)
        layout_gauche.addWidget(self.btn_effacer_sel)
        layout_gauche.addStretch()

        splitter.addWidget(pane_gauche)

        # --- PANNEAU DROIT : Contenu du panier ---
        pane_droit = QWidget()
        layout_droit = QVBoxLayout(pane_droit)
        layout_droit.setContentsMargins(10, 0, 0, 0)
        layout_droit.setSpacing(10)

        lbl_panier = QLabel("Contenu de la Vente en Cours (Panier)")
        lbl_panier.setStyleSheet(SECTION_TITLE_STYLE)
        layout_droit.addWidget(lbl_panier)

        self.table_panier = QTableWidget()
        self.table_panier.setColumnCount(5)
        self.table_panier.setHorizontalHeaderLabels([
            "Désignation", "P. Unitaire", "Quantité", "Total Ligne", "ID"
        ])
        apply_table_style(self.table_panier)
        self.table_panier.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_panier.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_panier.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_panier.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_panier.setColumnHidden(4, True)
        layout_droit.addWidget(self.table_panier)

        # Total Général & Actions
        layout_totaux = QHBoxLayout()

        self.btn_retirer = QPushButton("Retirer l'article sélectionné")
        self.btn_retirer.setStyleSheet(BUTTON_DANGER)
        self.btn_retirer.clicked.connect(self.on_retirer_ligne)
        layout_totaux.addWidget(self.btn_retirer)

        layout_totaux.addStretch()

        self.lbl_total_general = QLabel("TOTAL GÉNÉRAL : 0 F CFA")
        self.lbl_total_general.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {COLORS['primary']};"
            "padding-right: 5px; background-color: transparent;"
        )
        layout_totaux.addWidget(self.lbl_total_general)

        layout_droit.addLayout(layout_totaux)

        splitter.addWidget(pane_droit)
        layout_principal.addWidget(splitter, 1)

        # 3. Actions bas de page
        layout_actions_basses = QHBoxLayout()
        layout_actions_basses.setSpacing(10)

        self.btn_annuler_panier = QPushButton("Vider le panier")
        self.btn_annuler_panier.setStyleSheet(BUTTON_SECONDARY)
        self.btn_annuler_panier.clicked.connect(self.on_vider_panier)
        layout_actions_basses.addWidget(self.btn_annuler_panier)

        layout_actions_basses.addStretch()

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.clicked.connect(self.on_fermer)
        layout_actions_basses.addWidget(self.btn_fermer)

        self.btn_valider_vente = QPushButton("Valider la Vente")
        self.btn_valider_vente.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider_vente.clicked.connect(self.on_valider_vente)
        layout_actions_basses.addWidget(self.btn_valider_vente)

        layout_principal.addLayout(layout_actions_basses)

    def load_articles(self):
        """Récupère tous les articles vendables."""
        self.cmb_articles.blockSignals(True)
        self.cmb_articles.clear()
        self.cmb_articles.addItem("-- Sélectionner un article --", None)
        articles = ArticleService.get_all_articles()
        for a in articles:
            suffix = " (KIT)" if a.KIT else ""
            self.cmb_articles.addItem(f"{a.Libelle}{suffix}", a.IDTArticle)

        self.cmb_articles.blockSignals(False)
        self.on_article_changed()

    def on_article_changed(self):
        """Met à jour le stock disponible et pré-alimente le prix unitaire."""
        if self.cmb_articles.currentIndex() <= 0 or self.cmb_articles.currentData() is None:
            self.lbl_stock_dispo.setText("Stock disponible : --")
            self.txt_pu.clear()
            return

        id_art = self.cmb_articles.currentData()
        art = ArticleService.get_article_by_id(id_art)

        if art:
            sc = StockService.get_stock_by_article(id_art)
            stock_qte = sc.QuantiteCour if sc else 0
            self.lbl_stock_dispo.setText(f"Stock disponible : {stock_qte} unités")
            self.txt_pu.setText(str(int(art.PU)))

    def on_effacer_selection(self):
        """Réinitialise la zone gauche de commande."""
        self.cmb_articles.setCurrentIndex(0)
        self.on_article_changed()
        self.txt_quantite.setText("1")

    def on_ajouter_panier(self):
        """Valide et insère la ligne d'achat dans le panier temporaire."""
        if self.cmb_articles.currentIndex() <= 0 or self.cmb_articles.currentData() is None:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner un article à vendre.")
            return

        id_art = self.cmb_articles.currentData()
        qte_str = self.txt_quantite.text().strip()
        pu_str = self.txt_pu.text().strip()

        try:
            qte = int(qte_str)
            if qte <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Quantite", "La quantite de vente doit etre superieure a 0.")
            return

        try:
            pu = float(pu_str)
            if pu < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Tarif", "Le tarif doit etre positif ou nul.")
            return

        art = ArticleService.get_article_by_id(id_art)
        if not art:
            return

        sc = StockService.get_stock_by_article(id_art)
        stock_qte = sc.QuantiteCour if sc else 0

        deja_dans_panier_qte = self.panier.get(id_art, {}).get("qte", 0)
        total_qte_demandee = qte + deja_dans_panier_qte

        if total_qte_demandee > stock_qte:
            QMessageBox.critical(
                self, "Stock Insuffisant",
                f"Impossible d'ajouter cet article. Stock dispo : {stock_qte}. Quantité demandée (avec panier) : {total_qte_demandee}."
            )
            return

        self.panier[id_art] = {
            "nom": art.Libelle + (" (KIT)" if art.KIT else ""),
            "pu": pu,
            "qte": total_qte_demandee,
            "total": total_qte_demandee * pu
        }

        self.update_table_panier()
        self.on_effacer_selection()

    def update_table_panier(self):
        """Peuple le QTableWidget à droite et recalcule les totaux."""
        self.table_panier.setRowCount(0)
        self.table_panier.setRowCount(len(self.panier))

        total_general = 0.0

        for r, (id_art, info) in enumerate(self.panier.items()):
            nom = info["nom"]
            pu = info["pu"]
            qte = info["qte"]
            total_ligne = info["total"]
            total_general += total_ligne

            item_nom = QTableWidgetItem(nom)
            item_nom.setFlags(item_nom.flags() & ~Qt.ItemIsEditable)

            item_pu = QTableWidgetItem(f"{int(pu):,} F")
            item_pu.setFlags(item_pu.flags() & ~Qt.ItemIsEditable)

            item_qte = QTableWidgetItem(str(qte))
            item_qte.setFlags(item_qte.flags() & ~Qt.ItemIsEditable)

            item_tot = QTableWidgetItem(f"{int(total_ligne):,} F")
            item_tot.setFlags(item_tot.flags() & ~Qt.ItemIsEditable)

            item_id = QTableWidgetItem(str(id_art))

            self.table_panier.setItem(r, 0, item_nom)
            self.table_panier.setItem(r, 1, item_pu)
            self.table_panier.setItem(r, 2, item_qte)
            self.table_panier.setItem(r, 3, item_tot)
            self.table_panier.setItem(r, 4, item_id)

        self.lbl_total_general.setText(f"TOTAL GÉNÉRAL : {int(total_general):,} F CFA")

    def on_retirer_ligne(self):
        """Retire l'élément sélectionné du panier."""
        row = self.table_panier.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Sélectionnez un article du panier à retirer.")
            return

        item_id = self.table_panier.item(row, 4)
        if item_id:
            id_art = int(item_id.text())
            if id_art in self.panier:
                del self.panier[id_art]
            self.update_table_panier()

    def on_vider_panier(self):
        """Supprime tous les articles du panier."""
        self.panier.clear()
        self.update_table_panier()

    def on_valider_vente(self):
        """Valide et enregistre la totalité du panier de vente en BDD."""
        if not self.panier:
            QMessageBox.warning(self, "Panier Vide", "Il n'y a aucun article dans le panier à encaisser.")
            return

        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            QMessageBox.critical(self, "Erreur Session", "Aucune année scolaire active n'est configurée.")
            return

        # Audit stock avant écriture
        errs = []
        for id_art, info in self.panier.items():
            sc = StockService.get_stock_by_article(id_art)
            stock_dispo = sc.QuantiteCour if sc else 0
            if info["qte"] > stock_dispo:
                errs.append(f"- {info['nom']} : demandé {info['qte']}, dispo {stock_dispo}")

        if errs:
            msg_err = "Certains articles ne possèdent plus le stock suffisant :\n" + "\n".join(errs)
            QMessageBox.critical(self, "Vente Avortée", msg_err)
            return

        login_util = AppSession.get_logged_in_username() or "admin"
        ventes_reussies = 0

        for id_art, info in self.panier.items():
            success, msg = StockService.remove_stock(
                id_art, info["qte"], active_annee_id, info["pu"], login_util
            )
            if success:
                ventes_reussies += 1
            else:
                QMessageBox.critical(self, "Erreur lors du traitement", f"Erreur durant l'enregistrement de '{info['nom']}' : {msg}")
                break

        if ventes_reussies == len(self.panier):
            QMessageBox.information(
                self, "Vente Validée",
                f"Vente finalisée avec succès ! {ventes_reussies} article(s)/KIT(s) débité(s) des stocks."
            )
            self.on_vider_panier()

            if hasattr(self.main_window, "load_data"):
                try:
                    self.main_window.load_data()
                except:
                    pass
        else:
            self.update_table_panier()

    def on_fermer(self):
        if self.main_window and hasattr(self.main_window, "close_active_tab"):
            self.main_window.close_active_tab()
