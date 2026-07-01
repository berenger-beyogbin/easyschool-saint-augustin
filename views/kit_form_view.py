from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QWidget, QListWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QListWidgetItem
)
from PySide6.QtCore import Qt
from services.article_service import ArticleService
from app.styles import (
    COLORS, INPUT_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_DANGER,
    GROUPBOX_ACCENT_STYLE, apply_modal_style, apply_table_style
)

class KitFormView(QDialog):
    """
    Formulaire de creation / modification d'un KIT.
    Permet d'associer plusieurs articles simples avec leurs quantites respectives.
    """
    def __init__(self, parent=None, id_kit=None):
        super().__init__(parent)
        self.id_kit = id_kit
        self.setWindowTitle("Fiche KIT")
        self.resize(780, 580)
        apply_modal_style(self)

        # Liste locale des composants de kit (id_article -> quantite)
        self.composition = {}  # {id_article: quantite}

        self.init_ui()
        self.load_articles_disponibles()

        if self.id_kit:
            self.load_kit_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. En-tête
        entete = QWidget()
        entete.setStyleSheet(
            f"background-color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary_dark']};"
        )
        entete_layout = QVBoxLayout(entete)
        entete_layout.setContentsMargins(15, 12, 15, 12)

        lbl_titre = QLabel("KIT D'ARTICLES" if not self.id_kit else "MODIFIER LE KIT")
        lbl_titre.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: transparent;")
        lbl_soustitre = QLabel("Configurer le kit de vente en associant des fournitures individuelles")
        lbl_soustitre.setStyleSheet(
            f"font-size: 11px; color: {COLORS['surface_soft']}; background-color: transparent;"
        )
        entete_layout.addWidget(lbl_titre)
        entete_layout.addWidget(lbl_soustitre)
        main_layout.addWidget(entete)

        # 2. Zone Formulaire Generale
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        # Infos de base du kit
        layout_infos = QHBoxLayout()
        layout_infos.setSpacing(15)

        v_lib = QVBoxLayout()
        v_lib.addWidget(QLabel("Désignation du KIT (* oblig.) :"))
        self.txt_libelle = QLineEdit()
        self.txt_libelle.setStyleSheet(INPUT_STYLE)
        self.txt_libelle.setPlaceholderText("Ex: Trousseau 6e Classique")
        v_lib.addWidget(self.txt_libelle)
        layout_infos.addLayout(v_lib, 2)

        v_pu = QVBoxLayout()
        v_pu.addWidget(QLabel("Tarif ventes (F CFA) :"))
        self.txt_pu = QLineEdit("0")
        self.txt_pu.setStyleSheet(INPUT_STYLE)
        v_pu.addWidget(self.txt_pu)
        layout_infos.addLayout(v_pu, 1)

        v_seuil = QVBoxLayout()
        v_seuil.addWidget(QLabel("Stock Alerte :"))
        self.txt_seuil = QLineEdit("5")
        self.txt_seuil.setStyleSheet(INPUT_STYLE)
        v_seuil.addWidget(self.txt_seuil)
        layout_infos.addLayout(v_seuil, 1)

        form_layout.addLayout(layout_infos)

        # Section composition : Split gauche/droite
        group_composition = QGroupBox("Composition du KIT")
        group_composition.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        layout_comp = QHBoxLayout(group_composition)
        layout_comp.setSpacing(15)

        # Partie gauche : Articles disponibles
        v_dispo = QVBoxLayout()
        v_dispo.addWidget(QLabel("Articles Simples Disponibles :"))
        self.list_dispo = QListWidget()
        self.list_dispo.setStyleSheet(
            f"QListWidget {{ border: 1px solid {COLORS['border']}; background-color: {COLORS['surface']};"
            f"color: {COLORS['text']}; padding: 5px; }}"
        )
        v_dispo.addWidget(self.list_dispo)
        layout_comp.addLayout(v_dispo, 3)

        # Colonne centrale : Boutons fleches >> et <<
        v_fleches = QVBoxLayout()
        v_fleches.addStretch()
        self.btn_ajouter = QPushButton(">>")
        self.btn_ajouter.setStyleSheet(BUTTON_PRIMARY)
        self.btn_ajouter.clicked.connect(self.on_ajouter_composant)
        v_fleches.addWidget(self.btn_ajouter)

        self.btn_retirer = QPushButton("<<")
        self.btn_retirer.setStyleSheet(BUTTON_DANGER)
        self.btn_retirer.clicked.connect(self.on_retirer_composant)
        v_fleches.addWidget(self.btn_retirer)
        v_fleches.addStretch()
        layout_comp.addLayout(v_fleches, 1)

        # Partie droite : Composition du kit (quantités modifiables)
        v_actuel = QVBoxLayout()
        v_actuel.addWidget(QLabel("Table de Composition (Double Clic qté pour changer) :"))
        self.table_comp = QTableWidget()
        self.table_comp.setColumnCount(3)
        self.table_comp.setHorizontalHeaderLabels(["Article", "Quantité", "ID"])
        apply_table_style(self.table_comp)
        self.table_comp.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_comp.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_comp.setColumnHidden(2, True)
        self.table_comp.cellChanged.connect(self.on_quantite_changed)
        v_actuel.addWidget(self.table_comp)
        layout_comp.addLayout(v_actuel, 4)

        form_layout.addWidget(group_composition)
        main_layout.addWidget(form_widget)

        # 3. Boutons du bas
        barre_boutons = QWidget()
        barre_boutons.setStyleSheet(
            f"background-color: {COLORS['surface']}; border-top: 1px solid {COLORS['border']};"
        )
        layout_boutons = QHBoxLayout(barre_boutons)
        layout_boutons.setContentsMargins(15, 12, 15, 12)
        layout_boutons.setSpacing(10)
        layout_boutons.addStretch()

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.clicked.connect(self.reject)
        layout_boutons.addWidget(self.btn_fermer)

        self.btn_enregistrer = QPushButton("Valider")
        self.btn_enregistrer.setStyleSheet(BUTTON_PRIMARY)
        self.btn_enregistrer.clicked.connect(self.on_valider)
        layout_boutons.addWidget(self.btn_enregistrer)

        main_layout.addWidget(barre_boutons)

    def load_articles_disponibles(self):
        """Charge la liste à gauche avec uniquement les articles simples de la base."""
        self.list_dispo.clear()
        articles = ArticleService.get_articles_simples()
        for a in articles:
            item = QListWidgetItem(a.Libelle)
            item.setData(Qt.UserRole, a.IDTArticle)
            self.list_dispo.addItem(item)

    def load_kit_data(self):
        """Charge l'ancien kit et peuple le formulaire."""
        art = ArticleService.get_article_by_id(self.id_kit)
        if not art:
            return

        self.txt_libelle.setText(art.Libelle)
        self.txt_pu.setText(str(int(art.PU)))
        self.txt_seuil.setText(str(art.QTESeuil))

        if art.ContenuKit and art.QteKit:
            ids_str = art.ContenuKit.split(';')
            qtes_str = art.QteKit.split(';')
            for i, qte in zip(ids_str, qtes_str):
                if i.strip() and qte.strip():
                    try:
                        self.composition[int(i)] = int(qte)
                    except ValueError:
                        pass

        self.update_table_composition()

    def update_table_composition(self):
        """Peuple le tableau des composants à droite."""
        self.table_comp.blockSignals(True)
        self.table_comp.setRowCount(0)
        self.table_comp.setRowCount(len(self.composition))

        for idx, (id_art, qte) in enumerate(self.composition.items()):
            nom_art = "Article Inconnu"
            art = ArticleService.get_article_by_id(id_art)
            if art:
                nom_art = art.Libelle

            item_nom = QTableWidgetItem(nom_art)
            item_nom.setFlags(item_nom.flags() & ~Qt.ItemIsEditable)

            item_qte = QTableWidgetItem(str(qte))
            item_qte.setFlags(item_qte.flags() | Qt.ItemIsEditable)

            item_id = QTableWidgetItem(str(id_art))

            self.table_comp.setItem(idx, 0, item_nom)
            self.table_comp.setItem(idx, 1, item_qte)
            self.table_comp.setItem(idx, 2, item_id)

        self.table_comp.blockSignals(False)

    def on_ajouter_composant(self):
        """Deplace l'article simple vers la composition."""
        sel_items = self.list_dispo.selectedItems()
        if not sel_items:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner un article simple dans la liste de gauche.")
            return

        for item in sel_items:
            id_art = item.data(Qt.UserRole)
            if id_art in self.composition:
                self.composition[id_art] += 1
            else:
                self.composition[id_art] = 1

        self.update_table_composition()

    def on_retirer_composant(self):
        """Retire l'article selectionne dans la composition."""
        row = self.table_comp.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Selectionnez une ligne du tableau de composition à droite.")
            return

        item_id = self.table_comp.item(row, 2)
        if item_id:
            id_art = int(item_id.text())
            if id_art in self.composition:
                del self.composition[id_art]

        self.update_table_composition()

    def on_quantite_changed(self, row, column):
        """Intercepte les modifications manuelles de quantites dans le tableau."""
        if column == 1:
            item_qte = self.table_comp.item(row, column)
            item_id = self.table_comp.item(row, 2)
            if item_qte and item_id:
                try:
                    new_qte = int(item_qte.text() or 1)
                    if new_qte <= 0:
                        new_qte = 1
                except ValueError:
                    new_qte = 1

                id_art = int(item_id.text())
                if id_art in self.composition:
                    self.composition[id_art] = new_qte

                self.table_comp.blockSignals(True)
                item_qte.setText(str(new_qte))
                self.table_comp.blockSignals(False)

    def on_valider(self):
        """Valide la composition, construit les strings et appelle le service."""
        libelle = self.txt_libelle.text().strip()
        pu_str = self.txt_pu.text().strip()
        seuil_str = self.txt_seuil.text().strip()

        if not libelle:
            QMessageBox.warning(self, "Nom requis", "Le libelle du KIT est obligatoire.")
            return

        try:
            pu = float(pu_str or 0)
            if pu < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Le prix unitaire doit etre positif.")
            return

        try:
            seuil = int(seuil_str or 0)
            if seuil < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Le seuil doit etre un entier positif.")
            return

        if not self.composition:
            QMessageBox.warning(self, "Composition vide", "Un KIT doit contenir au moins un article simple.")
            return

        ids_list = []
        qtes_list = []
        for id_art, qte in self.composition.items():
            ids_list.append(str(id_art))
            qtes_list.append(str(qte))

        contenu_kit = ";".join(ids_list)
        qte_kit = ";".join(qtes_list)

        if self.id_kit:
            success, msg = ArticleService.update_article(
                self.id_kit, libelle, pu, seuil, contenu_kit=contenu_kit, qte_kit=qte_kit, is_kit=True
            )
        else:
            success, msg = ArticleService.create_kit(
                libelle, pu, seuil, contenu_kit, qte_kit
            )

        if success:
            QMessageBox.information(self, "Succes", "KIT enregistre avec succes !")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", msg)
