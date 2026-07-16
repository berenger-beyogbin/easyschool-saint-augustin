from services.audit_log_service import AuditLogService
from services.utilisateur_service import UtilisateurService
from tests.factories import make_annee, make_famille, make_eleve


def _make_user(db_session):
    from models.profil import Profil
    profil = Profil(Code="ADMIN", Libelle="Admin", IsAdmin=True, IsActive=True)
    db_session.add(profil)
    db_session.commit()
    UtilisateurService.create({
        "Login": "auditeur", "Nom": "Auditeur", "Password": "secret123", "IDProfil": profil.IDProfil,
    })
    from models.utilisateur import Utilisateur
    return db_session.query(Utilisateur).filter_by(Login="auditeur").first()


def test_log_creates_entry_with_user_fk(db_session):
    user = _make_user(db_session)

    AuditLogService.log(
        action="ANNULER_VERSEMENT", table_cible="VersementScol", id_cible=42,
        id_utilisateur=user.IDUtilisateur, motif="Erreur de saisie",
    )

    entries = AuditLogService.get_by_cible("VersementScol", 42)
    assert len(entries) == 1
    assert entries[0].Action == "ANNULER_VERSEMENT"
    assert entries[0].Motif == "Erreur de saisie"
    assert entries[0].utilisateur.Login == "auditeur"


def test_get_recent_orders_by_date_desc(db_session):
    AuditLogService.log(action="A1", table_cible="T", id_cible=1)
    AuditLogService.log(action="A2", table_cible="T", id_cible=2)

    recent = AuditLogService.get_recent(limit=10)
    assert [e.Action for e in recent] == ["A2", "A1"]


def test_annuler_versement_writes_audit_log_entry(db_session):
    from services.versement_service import VersementService
    from tests.factories import make_niveau_classe, make_montant_scol, make_inscription
    from datetime import date

    user = _make_user(db_session)
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="AUD001")
    make_montant_scol(db_session, annee, niveau)
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=10000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is True

    ok, msg = VersementService.annuler_versement(
        new_id, motif="Erreur caisse", login="auditeur", id_utilisateur=user.IDUtilisateur
    )
    assert ok is True

    entries = AuditLogService.get_by_cible("VersementScol", new_id)
    assert len(entries) == 1
    assert entries[0].Action == "ANNULER_VERSEMENT"
    assert entries[0].Motif == "Erreur caisse"
    assert entries[0].IDUtilisateur == user.IDUtilisateur
