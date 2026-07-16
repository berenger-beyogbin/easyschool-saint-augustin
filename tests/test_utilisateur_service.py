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


def test_has_any_user_reflects_state(db_session):
    assert UtilisateurService.has_any_user() is False
    _make_profil(db_session, code="ADMIN", is_admin=True)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": "secret123",
        "IDProfil": db_session.query(Profil).filter_by(Code="ADMIN").first().IDProfil,
    })
    assert UtilisateurService.has_any_user() is True


def test_create_first_admin_success(db_session):
    _make_profil(db_session, code="ADMIN", is_admin=True)
    ok, msg = UtilisateurService.create_first_admin({
        "Login": "directeur", "Nom": "Kouassi", "Password": "motdepassefort",
    })
    assert ok is True
    user = db_session.query(Utilisateur).filter_by(Login="directeur").first()
    assert user is not None
    assert user.profil.Code == "ADMIN"


def test_create_first_admin_rejected_when_user_already_exists(db_session):
    id_profil = _make_profil(db_session, code="ADMIN", is_admin=True)
    UtilisateurService.create({
        "Login": "existant", "Nom": "Existant", "Password": "secret123", "IDProfil": id_profil,
    })
    ok, msg = UtilisateurService.create_first_admin({
        "Login": "directeur", "Nom": "Kouassi", "Password": "motdepassefort",
    })
    assert ok is False
    assert "existe deja" in msg or "existe déjà" in msg


def test_create_first_admin_rejected_without_admin_profile(db_session):
    ok, msg = UtilisateurService.create_first_admin({
        "Login": "directeur", "Nom": "Kouassi", "Password": "motdepassefort",
    })
    assert ok is False
    assert "ADMIN" in msg
