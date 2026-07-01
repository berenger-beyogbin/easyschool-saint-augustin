from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from services.article_service import ArticleService
from services.stock_service import StockService
from views.article_form_view import ArticleFormView
from views.kit_form_view import KitFormView
from app.styles import (
    COLORS, INPUT_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_SUCCESS, BUTTON_WARNING, BUTTON_DANGER,
    apply_table_style
)

class ArticleListView(QWidget):
    """
    Scolarite > Kiosque > Articles et KITS
    Permet de lister, creer, modifier et supprimer les articles et les kits.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.selected_art_id = None
        self.selected_is_kit = False

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # 1. Zone Recherche & Boutons superieurs
        layout_haut = QHBoxLayout()
        layout_haut.addWidget(QLabel("Rechercher un article / KIT :"))

        self.txt_recherche = QLineEdit()
        self.txt_recherche.setStyleSheet(INPUT_STYLE)
        self.txt_recherche.setPlaceholderText("Saisissez un mot-clé...")
        self.txt_recherche.textChanged.connect(self.on_recherche_changed)
        layout_haut.addWidget(self.txt_recherche)

        self.btn_nouvel_article = QPushButton("Nouvel Article")
        self.btn_nouvel_article.setStyleSheet(BUTTON_PRIMARY)
        self.btn_nouvel_article.clicked.connect(self.on_nouvel_article)
        layout_haut.addWidget(self.btn_nouvel_article)

        self.btn_nouveau_kit = QPushButton("Nouveau KIT")
        self.btn_nouveau_kit.setStyleSheet(BUTTON_SUCCESS)
        self.btn_nouveau_kit.clicked.connect(self.on_nouveau_kit)
        layout_haut.addWidget(self.btn_nouveau_kit)

        layout_principal.addLayout(layout_haut)

        # 2. Tableau de donnees
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "DESCRIPTION", "P.U. VENTES (F CFA)", "SEUIL CRITIQUE", "EST UN KIT ?", "STOCK COURANT"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout_principal.addWidget(self.table)

        # 3. Actions bas de tableau
        layout_bas = QHBoxLayout()
        layout_bas.setSpacing(10)

        self.btn_modifier = QPushButton("Modifier la sélection")
        self.btn_modifier.setStyleSheet(BUTTON_WARNING)
        self.btn_modifier.setEnabled(False)
        self.btn_modifier.clicked.connect(self.on_modifier)
        layout_bas.addWidget(self.btn_modifier)

        self.btn_supprimer = QPushButton("Supprimer la sélection")
        self.btn_supprimer.setStyleSheet(BUTTON_DANGER)
        self.btn_supprimer.setEnabled(False)
        self.btn_supprimer.clicked.connect(self.on_supprimer)
        layout_bas.addWidget(self.btn_supprimer)

        layout_bas.addStretch()

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.clicked.connect(self.on_fermer)
        layout_bas.addWidget(self.btn_fermer)

        layout_principal.addLayout(layout_bas)

    def load_data(self):
        """Récupère et rafraîchit tous les articles avec leurs stocks."""
        self.table.setRowCount(0)
        query = self.txt_recherche.text().strip()
        articles = ArticleService.search_articles(query)
        self.table.setRowCount(len(articles))

        for idx, art in enumerate(articles):
            sc = StockService.get_stock_by_article(art.IDTArticle)
            stock_qte = sc.QuantiteCour if sc else 0

            est_kit = "OUI" if art.KIT else "NON"

            item_desc = QTableWidgetItem(art.Libelle)
            item_desc.setData(Qt.UserRole, (art.IDTArticle, art.KIT))
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)

            item_pu = QTableWidgetItem(f"{int(art.PU):,} F CFA")
            item_pu.setFlags(item_pu.flags() & ~Qt.ItemIsEditable)

            item_seuil = QTableWidgetItem(str(art.QTESeuil))
            item_seuil.setFlags(item_seuil.flags() & ~Qt.ItemIsEditable)

            item_kit = QTableWidgetItem(est_kit)
            item_kit.setFlags(item_kit.flags() & ~Qt.ItemIsEditable)

            item_stock = QTableWidgetItem(str(stock_qte))
            item_stock.setFlags(item_stock.flags() & ~Qt.ItemIsEditable)

            # Alerte stock critique : coloration rouge (logique métier)
            if stock_qte <= art.QTESeuil:
                item_stock.setForeground(QColor(COLORS["danger"]))

            self.table.setItem(idx, 0, item_desc)
            self.table.setItem(idx, 1, item_pu)
            self.table.setItem(idx, 2, item_seuil)
            self.table.setItem(idx, 3, item_kit)
            self.table.setItem(idx, 4, item_stock)

        self.btn_modifier.setEnabled(False)
        self.btn_supprimer.setEnabled(False)
        self.selected_art_id = None

    def on_recherche_changed(self):
        self.load_data()

    def on_row_selected(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.btn_modifier.setEnabled(False)
            self.btn_supprimer.setEnabled(False)
            self.selected_art_id = None
            return

        row = selected_ranges[0].topRow()
        item_desc = self.table.item(row, 0)
        if item_desc:
            id_art, is_kit = item_desc.data(Qt.UserRole)
            self.selected_art_id = id_art
            self.selected_is_kit = is_kit
            self.btn_modifier.setEnabled(True)
            self.btn_supprimer.setEnabled(True)

    def on_nouvel_article(self):
        dlg = ArticleFormView(self)
        if dlg.exec() == ArticleFormView.Accepted:
            self.load_data()

    def on_nouveau_kit(self):
        dlg = KitFormView(self)
        if dlg.exec() == KitFormView.Accepted:
            self.load_data()

    def on_modifier(self):
        if not self.selected_art_id:
            return

        if self.selected_is_kit:
            dlg = KitFormView(self, id_kit=self.selected_art_id)
        else:
            dlg = ArticleFormView(self, id_art=self.selected_art_id)

        if dlg.exec() == QDialog.Accepted or dlg.result() == 1:
            self.load_data()

    def on_supprimer(self):
        if not self.selected_art_id:
            return

        res = QMessageBox.question(
            self, "Confirmation",
            "Êtes-vous sûr de vouloir supprimer cet article du catalogue ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.No:
            return

        success, msg = ArticleService.delete_article(self.selected_art_id)
        if success:
            QMessageBox.information(self, "Supprimé", msg)
            self.load_data()
        else:
            QMessageBox.critical(self, "Action Interdite", msg)

    def on_fermer(self):
        if self.main_window and hasattr(self.main_window, "close_active_tab"):
            self.main_window.close_active_tab()

# Import QDialog de compatibilité
from PySide6.QtWidgets import QDialog
