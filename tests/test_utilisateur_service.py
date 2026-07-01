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
    assert "6 caractères" in msg


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
