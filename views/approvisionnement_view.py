from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from services.article_service import ArticleService
from services.stock_service import StockService
from app.session import AppSession
from app.styles import (
    INPUT_STYLE, COMBO_STYLE, DATE_STYLE, SECTION_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY,
    GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE, apply_table_style
)

class ApprovisionnementView(QWidget):
    """
    Scolarité > Kiosque > Approvisionnement
    Permet d'ajouter du stock pour un article/kit et de consulter l'historique des entrees.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_combos()
        self.load_historique()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(20)

        # ---------------- CÔTÉ GAUCHE : Formulaire d'enregistrement ----------------
        pane_gauche = QWidget()
        layout_gauche = QVBoxLayout(pane_gauche)
        layout_gauche.setContentsMargins(0, 0, 0, 0)
        layout_gauche.setSpacing(15)

        group_form = QGroupBox("ENREGISTRER UN RÉAPPROVISIONNEMENT")
        group_form.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        layout_form = QVBoxLayout(group_form)
        layout_form.setSpacing(10)

        layout_form.addWidget(QLabel("Sélectionner un article ou KIT :"))
        self.cmb_articles = QComboBox()
        self.cmb_articles.setStyleSheet(COMBO_STYLE)
        layout_form.addWidget(self.cmb_articles)

        layout_form.addWidget(QLabel("Quantité à approvisionner :"))
        self.txt_quantite = QLineEdit()
        self.txt_quantite.setStyleSheet(INPUT_STYLE)
        self.txt_quantite.setPlaceholderText("Ex: 50")
        layout_form.addWidget(self.txt_quantite)

        layout_form.addWidget(QLabel("Date d'enregistrement :"))
        self.txt_date_ent = QDateEdit(QDate.currentDate())
        self.txt_date_ent.setCalendarPopup(True)
        self.txt_date_ent.setDisplayFormat("dd/MM/yyyy")
        self.txt_date_ent.setStyleSheet(DATE_STYLE)
        layout_form.addWidget(self.txt_date_ent)

        layout_btns = QHBoxLayout()
        layout_btns.setSpacing(10)

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setStyleSheet(BUTTON_SECONDARY)
        self.btn_annuler.clicked.connect(self.on_annuler)
        layout_btns.addWidget(self.btn_annuler)

        self.btn_valider = QPushButton("Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.on_valider)
        layout_btns.addWidget(self.btn_valider)

        layout_form.addLayout(layout_btns)
        layout_gauche.addWidget(group_form)

        self.btn_fermer = QPushButton("Fermer le module")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.clicked.connect(self.on_fermer)
        layout_gauche.addStretch()
        layout_gauche.addWidget(self.btn_fermer)

        layout_principal.addWidget(pane_gauche, 1)

        # ---------------- CÔTÉ DROIT : Historique et filtres ----------------
        pane_droit = QWidget()
        layout_droit = QVBoxLayout(pane_droit)
        layout_droit.setContentsMargins(0, 0, 0, 0)
        layout_droit.setSpacing(10)

        group_filtres = QGroupBox("Filtres d'historique")
        group_filtres.setStyleSheet(GROUPBOX_STYLE)
        layout_filtres = QHBoxLayout(group_filtres)
        layout_filtres.setSpacing(10)

        layout_filtres.addWidget(QLabel("Du :"))
        self.filter_date_deb = QDateEdit(QDate.currentDate().addMonths(-3))
        self.filter_date_deb.setCalendarPopup(True)
        self.filter_date_deb.setDisplayFormat("dd/MM/yyyy")
        self.filter_date_deb.setStyleSheet(DATE_STYLE)
        layout_filtres.addWidget(self.filter_date_deb)

        layout_filtres.addWidget(QLabel("Au :"))
        self.filter_date_fin = QDateEdit(QDate.currentDate())
        self.filter_date_fin.setCalendarPopup(True)
        self.filter_date_fin.setDisplayFormat("dd/MM/yyyy")
        self.filter_date_fin.setStyleSheet(DATE_STYLE)
        layout_filtres.addWidget(self.filter_date_fin)

        self.btn_filtrer = QPushButton("Filtrer")
        self.btn_filtrer.setStyleSheet(BUTTON_PRIMARY)
        self.btn_filtrer.clicked.connect(self.load_historique)
        layout_filtres.addWidget(self.btn_filtrer)

        layout_droit.addWidget(group_filtres)

        lbl_titre_table = QLabel("Historique des Entrées de Stock")
        lbl_titre_table.setStyleSheet(SECTION_TITLE_STYLE)
        layout_droit.addWidget(lbl_titre_table)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Article / KIT", "Quantité Entrée", "Caissier / Login"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout_droit.addWidget(self.table)

        layout_principal.addWidget(pane_droit, 2)

    def load_combos(self):
        """Remplit le ComboBox des articles/kits."""
        self.cmb_articles.clear()
        articles = ArticleService.get_all_articles()
        for a in articles:
            suffix = " (KIT)" if a.KIT else ""
            self.cmb_articles.addItem(f"{a.Libelle}{suffix}", a.IDTArticle)

    def load_historique(self):
        """Récupère l'historique des entrées selon la plage de dates."""
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        date_deb_py = self.filter_date_deb.date().toPython()
        date_fin_py = self.filter_date_fin.date().toPython()

        entrees = StockService.get_stock_history_entrees(
            id_annee=active_annee_id,
            date_debut=date_deb_py,
            date_fin=date_fin_py
        )

        self.table.setRowCount(0)
        self.table.setRowCount(len(entrees))

        for idx, e in enumerate(entrees):
            item_date = QTableWidgetItem(e.DateEnt.strftime("%d/%m/%Y"))
            item_date.setFlags(item_date.flags() & ~Qt.ItemIsEditable)

            nom_art = e.article.Libelle if e.article else "Inconnu"
            if e.article and e.article.KIT:
                nom_art += " (KIT)"
            item_art = QTableWidgetItem(nom_art)
            item_art.setFlags(item_art.flags() & ~Qt.ItemIsEditable)

            item_qte = QTableWidgetItem(str(e.QuantiteEnt))
            item_qte.setFlags(item_qte.flags() & ~Qt.ItemIsEditable)

            item_login = QTableWidgetItem(e.Login or "admin")
            item_login.setFlags(item_login.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(idx, 0, item_date)
            self.table.setItem(idx, 1, item_art)
            self.table.setItem(idx, 2, item_qte)
            self.table.setItem(idx, 3, item_login)

    def on_annuler(self):
        """Vide l'entrée."""
        self.txt_quantite.clear()
        self.cmb_articles.setCurrentIndex(0)
        self.txt_date_ent.setDate(QDate.currentDate())

    def on_valider(self):
        """Valide et enregistre le réapprovisionnement."""
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            QMessageBox.critical(self, "Erreur Session", "Aucune année scolaire n'est configurée active dans l'application.")
            return

        if self.cmb_articles.currentIndex() == -1:
            QMessageBox.warning(self, "Sélection Requise", "Veuillez d'abord créer des articles simples ou des kits.")
            return

        id_art = self.cmb_articles.currentData()
        qte_str = self.txt_quantite.text().strip()

        try:
            qte = int(qte_str)
            if qte <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Veuillez saisir une quantité entière supérieure à 0.")
            return

        login_util = AppSession.get_logged_in_username() or "admin"
        date_ent = self.txt_date_ent.date().toPython()
        success, msg = StockService.add_stock(id_art, qte, active_annee_id, login_util, date_ent=date_ent)

        if success:
            QMessageBox.information(self, "Succès", msg)
            self.on_annuler()
            self.load_historique()

            if hasattr(self.main_window, "load_data"):
                try:
                    self.main_window.load_data()
                except Exception:
                    pass
        else:
            QMessageBox.critical(self, "Erreur de Stock", msg)

    def on_fermer(self):
        if self.main_window and hasattr(self.main_window, "close_active_tab"):
            self.main_window.close_active_tab()
