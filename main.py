import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QPalette, QColor

# Configurer les chemins d'importation pour s'assurer qu'on charge
# les modules du dossier courant sans conflit
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import init_db, test_connection, create_tables
from app.session import AppSession
from app.styles import MESSAGEBOX_STYLE
from views.main_window import MainWindow
from views.login_dialog import LoginDialog


def _apply_light_palette(app: QApplication) -> None:
    """Force une palette claire pour éviter le texte blanc sur fond clair en mode sombre Windows."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#F1F5F9"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#F1F5F9"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#059669"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9CA3AF"))
    app.setPalette(palette)


def main():
    """Point d'entree principal d'Easy School 2.0."""
    print("Initialisation de l'application Easy School 2.0...")

    # 1. Demarrage de l'interface graphique PySide6 (Application Qt) en premier
    app = QApplication(sys.argv)

    # Style Fusion + palette claire forcée (neutralise le mode sombre Windows)
    app.setStyle("Fusion")
    _apply_light_palette(app)
    # Style global pour les popups QMessageBox / QDialog (texte et boutons lisibles)
    app.setStyleSheet(MESSAGEBOX_STYLE)
    
    # 2. Tentative de connexion PostgreSQL et creation des tables
    try:
        init_db()
        test_connection()
        # Creation automatique des tables si inexistantes sur PostgreSQL
        create_tables()

        # 3. Seeding du référentiel utilisateurs (idempotent)
        from services.permission_service import PermissionService
        from services.profil_service import ProfilService
        from services.utilisateur_service import UtilisateurService
        from services.compte_service import CompteService
        PermissionService.seed_permissions()
        ProfilService.seed_default_profiles()
        UtilisateurService.seed_default_admin()
        CompteService.seed_comptes_syscoa()

        from services.prestation_service import PrestationService
        PrestationService.seed_default_prestations()

        # 4. Initialisation de la session active avant la fenetre principale
        AppSession.initialize_session()

    except Exception as e:
        print(f"Erreur au démarrage de l'application: {e}")
        QMessageBox.critical(
            None,
            "Erreur de démarrage",
            f"Impossible de démarrer l'application :\n\n{str(e)}\n\nVérifiez que PostgreSQL est démarré et que vos paramètres de session sont valides."
        )
        sys.exit(1)

    # 5. Écran de connexion
    login_dlg = LoginDialog()
    if login_dlg.exec() != LoginDialog.Accepted:
        # L'utilisateur a fermé la fenêtre sans se connecter
        sys.exit(0)

    # Stocker l'utilisateur et ses permissions dans la session
    user_data = login_dlg.authenticated_user_data
    from services.profil_service import ProfilService as _PS
    permissions = _PS.get_profil_permissions(user_data["IDProfil"])
    AppSession.set_current_user(user_data, permissions)

    # 6. Instanciation de la fenetre principale
    window = MainWindow()
    window.showMaximized()

    # Execution de la boucle principale d'evenements
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
