from models.profil import Profil
from models.utilisateur import Utilisateur
from services.utilisateur_service import UtilisateurService


def _make_profil(db_session, code="CAISSIER", is_admin=False):
    profil = Profil(Code=code, Libelle=code.title(), IsAdmin=is_admin, IsActive=True)
    db_session.add(profil)
    db_session.commit()
    return profil.IDProfil


def test_create_user_success(db_session):
    id_profil = _make_profil(db_session)
    ok, msg = UtilisateurService.create({
        "Login": "jdupont",
        "Nom": "Dupont",
        "Password": "secret123",
        "IDProfil": id_profil,
    })
    assert ok is True
    assert "créé" in msg


def test_create_user_rejects_short_password(db_session):
    id_profil = _make_profil(db_session)
    ok, msg = UtilisateurService.create({
        "Login": "jdupont",
        "Nom": "Dupont",
        "Password": "abc",
        "IDProfil": id_profil,
    })
    assert ok is False
    assert "8 caract" in msg


def test_create_user_rejects_duplicate_login(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": "secret123", "IDProfil": id_profil,
    })
    ok, msg = UtilisateurService.create({
        "Login": "jdupont", "Nom": "Autre", "Password": "secret123", "IDProfil": id_profil,
    })
    assert ok is False
    assert "déjà utilisé" in msg


def test_authenticate_success(db_session):
    id_profil = _make_profil(db_session, code="ADMIN", is_admin=True)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": "secret123", "IDProfil": id_profil,
    })
    ok, msg, user_data = UtilisateurService.authenticate("jdupont", "secret123")
    assert ok is True
    assert user_data["Login"] == "jdupont"
    assert user_data["IsAdmin"] is True
    assert user_data["MustChangePassword"] is False


def test_authenticate_wrong_password(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": "secret123", "IDProfil": id_profil,
    })
    ok, msg, user_data = UtilisateurService.authenticate("jdupont", "wrong")
    assert ok is False
    assert user_data is None


def test_authenticate_unknown_login(db_session):
    ok, msg, user_data = UtilisateurService.authenticate("inconnu", "secret123")
    assert ok is False
    assert "inconnu" in msg.lower()


def test_authenticate_inactive_account_is_rejected(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": "secret123", "IDProfil": id_profil,
    })
    user = db_session.query(Utilisateur).filter_by(Login="jdupont").first()
    user.IsActive = False
    db_session.commit()

    ok, msg, user_data = UtilisateurService.authenticate("jdupont", "secret123")
    assert ok is False
    assert "désactivé" in msg


def test_create_user_rejects_password_without_digit(db_session):
    id_profil = _make_profil(db_session)
    ok, msg = UtilisateurService.create({
        "Login": "jdupont",
        "Nom": "Dupont",
        "Password": "motdepasse",
        "IDProfil": id_profil,
    })
    assert ok is False
    assert "lettre et un chiffre" in msg


def test_seed_default_admin_requires_password_change_without_exposing_password(db_session, capsys):
    _make_profil(db_session, code="ADMIN", is_admin=True)

    UtilisateurService.seed_default_admin()

    captured = capsys.readouterr()
    assert "admin123" not in captured.out

    db_session.expire_all()
    admin = db_session.query(Utilisateur).filter_by(Login="admin").first()
    assert admin is not None
    assert admin.MustChangePassword is True

    ok, msg, user_data = UtilisateurService.authenticate("admin", "admin123")
    assert ok is True
    assert user_data["MustChangePassword"] is True


def test_change_password_clears_required_change_flag(db_session):
    id_profil = _make_profil(db_session, code="ADMIN", is_admin=True)
    UtilisateurService.create({
        "Login": "admin",
        "Nom": "Administrateur",
        "Password": "secret123",
        "IDProfil": id_profil,
    })
    user = db_session.query(Utilisateur).filter_by(Login="admin").first()
    user.MustChangePassword = True
    db_session.commit()

    ok, msg = UtilisateurService.change_password(user.IDUtilisateur, "secret123", "nouveau123")

    assert ok is True
    db_session.expire_all()
    refreshed = db_session.get(Utilisateur, user.IDUtilisateur)
    assert refreshed.MustChangePassword is False

    ok, msg, user_data = UtilisateurService.authenticate("admin", "nouveau123")
    assert ok is True
    assert user_data["MustChangePassword"] is False
