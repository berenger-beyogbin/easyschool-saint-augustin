from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from services.article_service import ArticleService
from app.styles import (
    COLORS, INPUT_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, apply_modal_style
)

class ArticleFormView(QDialog):
    """
    Formulaire d'enregistrement / modification d'un article simple.
    """
    def __init__(self, parent=None, id_art=None):
        super().__init__(parent)
        self.id_art = id_art
        self.setWindowTitle("Fiche Article")
        self.resize(500, 380)
        apply_modal_style(self)

        self.init_ui()
        if self.id_art:
            self.load_article_data()

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

        lbl_titre = QLabel("ARTICLE SIMPLE" if not self.id_art else "MODIFIER L'ARTICLE")
        lbl_titre.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: transparent;")
        lbl_soustitre = QLabel("Enregistrer les spécifications de l'article de vente")
        lbl_soustitre.setStyleSheet(
            f"font-size: 11px; color: {COLORS['surface_soft']}; background-color: transparent;"
        )
        entete_layout.addWidget(lbl_titre)
        entete_layout.addWidget(lbl_soustitre)
        main_layout.addWidget(entete)

        # 2. Zone Formulaire
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Désignation de l'article (* Numérique/Texte libre) :"))
        self.txt_libelle = QLineEdit()
        self.txt_libelle.setStyleSheet(INPUT_STYLE)
        self.txt_libelle.setPlaceholderText("Ex: Cahier de 100 pages de devoirs")
        form_layout.addWidget(self.txt_libelle)

        form_layout.addWidget(QLabel("Prix de vente standard (F CFA) :"))
        self.txt_pu = QLineEdit("0")
        self.txt_pu.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.txt_pu)

        form_layout.addWidget(QLabel("Stock minimum critique d'alerte :"))
        self.txt_seuil = QLineEdit("5")
        self.txt_seuil.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.txt_seuil)

        form_layout.addStretch()
        main_layout.addWidget(form_widget)

        # 3. Barre boutons du bas
        barre_boutons = QWidget()
        barre_boutons.setStyleSheet(
            f"background-color: {COLORS['surface']}; border-top: 1px solid {COLORS['border']};"
        )
        layout_boutons = QHBoxLayout(barre_boutons)
        layout_boutons.setContentsMargins(15, 12, 15, 12)
        layout_boutons.setSpacing(10)
        layout_boutons.addStretch()

        self.btn_annuler = QPushButton("Fermer")
        self.btn_annuler.setStyleSheet(BUTTON_SECONDARY)
        self.btn_annuler.clicked.connect(self.reject)
        layout_boutons.addWidget(self.btn_annuler)

        self.btn_valider = QPushButton("Enregistrer")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.on_valider)
        layout_boutons.addWidget(self.btn_valider)

        main_layout.addWidget(barre_boutons)

    def load_article_data(self):
        """Remplit les données de l'article existant."""
        art = ArticleService.get_article_by_id(self.id_art)
        if art:
            self.txt_libelle.setText(art.Libelle)
            self.txt_pu.setText(str(int(art.PU)))
            self.txt_seuil.setText(str(art.QTESeuil))

    def on_valider(self):
        """Valide la saisie et enregistre l'article simple."""
        libelle = self.txt_libelle.text().strip()
        pu_str = self.txt_pu.text().strip()
        seuil_str = self.txt_seuil.text().strip()

        if not libelle:
            QMessageBox.warning(self, "Validation", "Veuillez saisir la désignation de l'article.")
            return

        try:
            pu = float(pu_str or 0)
            if pu < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Le prix unitaire doit etre un nombre positif.")
            return

        try:
            seuil = int(seuil_str or 0)
            if seuil < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.critical(self, "Saisie Incorrecte", "Le seuil de stock doit etre un entier positif.")
            return

        if self.id_art:
            success, msg = ArticleService.update_article(
                self.id_art, libelle, pu, seuil, is_kit=False
            )
        else:
            success, msg = ArticleService.create_article(libelle, pu, seuil)

        if success:
            QMessageBox.information(self, "Succes", "Enregistrement effectue avec succes !")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur lors de l'enregistrement", msg)
