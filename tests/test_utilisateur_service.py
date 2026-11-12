from models.profil import Profil
from models.utilisateur import Utilisateur
from services.utilisateur_service import (
    AUTH_FAILURE_MESSAGE,
    MAX_AUTH_FAILURES,
    UtilisateurService,
    _reset_auth_throttle,
    _verify_password,
)


PASSWORD = "secret1234"


def setup_function():
    _reset_auth_throttle()


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
        "Password": PASSWORD,
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
    assert "10 caractères" in msg


def test_create_user_rejects_duplicate_login(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD, "IDProfil": id_profil,
    })
    ok, msg = UtilisateurService.create({
        "Login": "jdupont", "Nom": "Autre", "Password": PASSWORD, "IDProfil": id_profil,
    })
    assert ok is False
    assert "déjà utilisé" in msg


def test_authenticate_success(db_session):
    id_profil = _make_profil(db_session, code="ADMIN", is_admin=True)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD, "IDProfil": id_profil,
    })
    ok, msg, user_data = UtilisateurService.authenticate("jdupont", PASSWORD)
    assert ok is True
    assert user_data["Login"] == "jdupont"
    assert user_data["IsAdmin"] is True


def test_authenticate_wrong_password(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD, "IDProfil": id_profil,
    })
    ok, msg, user_data = UtilisateurService.authenticate("jdupont", "wrong")
    assert ok is False
    assert msg == AUTH_FAILURE_MESSAGE
    assert user_data is None


def test_authenticate_unknown_login(db_session):
    ok, msg, user_data = UtilisateurService.authenticate("inconnu", PASSWORD)
    assert ok is False
    assert msg == AUTH_FAILURE_MESSAGE
    assert user_data is None


def test_authenticate_inactive_account_is_rejected(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD, "IDProfil": id_profil,
    })
    user = db_session.query(Utilisateur).filter_by(Login="jdupont").first()
    user.IsActive = False
    db_session.commit()

    ok, msg, user_data = UtilisateurService.authenticate("jdupont", PASSWORD)
    assert ok is False
    assert msg == AUTH_FAILURE_MESSAGE
    assert user_data is None


def test_has_any_user_reflects_state(db_session):
    assert UtilisateurService.has_any_user() is False
    _make_profil(db_session, code="ADMIN", is_admin=True)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD,
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
        "Login": "existant", "Nom": "Existant", "Password": PASSWORD, "IDProfil": id_profil,
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


def test_verify_password_uses_constant_time_comparison(monkeypatch):
    calls = []

    def compare_digest(left, right):
        calls.append((left, right))
        return left == right

    monkeypatch.setattr("services.utilisateur_service.hmac.compare_digest", compare_digest)
    from services.utilisateur_service import _hash_password

    stored = _hash_password(PASSWORD)
    assert _verify_password(PASSWORD, stored) is True
    assert calls and all(isinstance(value, bytes) for value in calls[0])


def test_authenticate_temporarily_locks_after_repeated_failures(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD, "IDProfil": id_profil,
    })

    for _ in range(MAX_AUTH_FAILURES):
        ok, msg, _ = UtilisateurService.authenticate("jdupont", "incorrect-password")
        assert ok is False
        assert msg == AUTH_FAILURE_MESSAGE

    ok, msg, user_data = UtilisateurService.authenticate("jdupont", PASSWORD)
    assert ok is False
    assert msg == AUTH_FAILURE_MESSAGE
    assert user_data is None


def test_successful_authentication_clears_failure_counter(db_session):
    id_profil = _make_profil(db_session)
    UtilisateurService.create({
        "Login": "jdupont", "Nom": "Dupont", "Password": PASSWORD, "IDProfil": id_profil,
    })

    for _ in range(MAX_AUTH_FAILURES - 1):
        UtilisateurService.authenticate("jdupont", "incorrect-password")

    assert UtilisateurService.authenticate("jdupont", PASSWORD)[0] is True
    assert UtilisateurService.authenticate("jdupont", "incorrect-password")[0] is False
    assert UtilisateurService.authenticate("jdupont", PASSWORD)[0] is True
