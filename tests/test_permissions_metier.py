from app.session import AppSession
from datetime import date
from decimal import Decimal

from models.article import Article
from models.classe import TClasse
from models.etablissement import EtablissementEcole
from models.permission import Permission
from models.profil import Profil
from models.profil_permission import ProfilPermission
from models.prestation_annexe import PrestationAnnexe
from models.stock_cour import StockCour
from models.stock_entree import StockEntree
from models.stock_sortie import StockSortie
from models.utilisateur import Utilisateur
from models.versement_scol import VersementScol
from services.article_service import ArticleService
from services.classe_service import ClasseService
from services.profil_service import ProfilService
from services.prestation_service import PrestationService
from services.stock_service import StockService
from services.utilisateur_service import UtilisateurService
from services.versement_service import VersementService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_inscription,
    make_montant_scol,
    make_niveau_classe,
)


def _set_user_without_param_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 999,
            "Login": "lecture",
            "Nom": "Lecture",
            "Prenoms": "Seule",
            "ProfilCode": "LECTURE",
            "ProfilLibelle": "Lecture seule",
            "IsAdmin": False,
        },
        permissions={"PARAMETRES_VIEW"},
    )


def _set_user_with_param_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1000,
            "Login": "param_admin",
            "Nom": "Param",
            "Prenoms": "Admin",
            "ProfilCode": "PARAM",
            "ProfilLibelle": "Parametres",
            "IsAdmin": False,
        },
        permissions={"PARAMETRES_VIEW", "PARAMETRES_MODIFIER"},
    )


def _set_user_without_prestation_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1001,
            "Login": "prest_lecture",
            "Nom": "Prest",
            "Prenoms": "Lecture",
            "ProfilCode": "PREST_READ",
            "ProfilLibelle": "Prestations lecture",
            "IsAdmin": False,
        },
        permissions={"PRESTATIONS_VIEW"},
    )


def _set_user_with_prestation_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1002,
            "Login": "prest_admin",
            "Nom": "Prest",
            "Prenoms": "Admin",
            "ProfilCode": "PREST_WRITE",
            "ProfilLibelle": "Prestations ecriture",
            "IsAdmin": False,
        },
        permissions={"PRESTATIONS_VIEW", "PRESTATIONS_MODIFIER"},
    )


def _set_user_without_versements_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1003,
            "Login": "caisse_lecture",
            "Nom": "Caisse",
            "ProfilCode": "CAISSE_READ",
            "ProfilLibelle": "Caisse lecture",
            "IsAdmin": False,
        },
        permissions={"SCOLARITE_VIEW"},
    )


def _set_user_without_kiosque_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1004,
            "Login": "kiosque_lecture",
            "Nom": "Kiosque",
            "ProfilCode": "KIOSQUE_READ",
            "ProfilLibelle": "Kiosque lecture",
            "IsAdmin": False,
        },
        permissions={"KIOSQUE_VIEW"},
    )


def _set_user_without_users_modifier_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1005,
            "Login": "users_lecture",
            "Nom": "Users",
            "ProfilCode": "USERS_READ",
            "ProfilLibelle": "Utilisateurs lecture",
            "IsAdmin": False,
        },
        permissions={"UTILISATEURS_VIEW"},
    )


def _set_user_with_users_modifier_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1006,
            "Login": "users_admin",
            "Nom": "Users",
            "ProfilCode": "USERS_WRITE",
            "ProfilLibelle": "Utilisateurs ecriture",
            "IsAdmin": False,
        },
        permissions={"UTILISATEURS_VIEW", "UTILISATEURS_MODIFIER"},
    )


def _setup_active_param_context(db_session):
    annee = make_annee(db_session)
    etablissement = EtablissementEcole(RaisonSociale="Ecole test")
    db_session.add(etablissement)
    db_session.commit()
    niveau, classe = make_niveau_classe(db_session, annee)

    AppSession._active_annee_id = annee.IDTAnneeScolaire
    AppSession._active_annee_libelle = annee.Libelle
    AppSession._active_etab_id = etablissement.IDEtablissement_Ecole
    return annee, etablissement, niveau, classe


def _setup_payment_context(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="PAY-PERM-001")
    make_montant_scol(db_session, annee, niveau, montant=100000, montant_pri=100000, montant_sec=100000)
    make_inscription(db_session, annee, famille, eleve, niveau, classe)
    return annee, famille, eleve


def _setup_stock_context(db_session, qte=5):
    annee = make_annee(db_session)
    article = Article(
        Libelle="Article permission test",
        PU=Decimal("500"),
        KIT=False,
        QTESeuil=1,
    )
    db_session.add(article)
    db_session.commit()
    stock = StockCour(IDTArticle=article.IDTArticle, QuantiteCour=qte)
    db_session.add(stock)
    db_session.commit()
    return annee, article, stock


def _make_direct_profil(db_session, code="TEST_PROFILE"):
    profil = Profil(Code=code, Libelle=code.title(), IsAdmin=False, IsActive=True)
    db_session.add(profil)
    db_session.commit()
    return profil


def test_parametres_write_service_requires_modifier_permission(db_session):
    annee, etablissement, niveau, classe = _setup_active_param_context(db_session)
    _set_user_without_param_write_permission()

    ok, msg = ClasseService.add_classe(
        lib_classe="CM2 NON AUTORISEE",
        sigle="CM2NA",
        id_cycle=niveau.IDT_Cycle,
        id_niveau=niveau.IDT_Niveau,
        capacite=40,
    )

    db_session.expire_all()
    assert ok is False
    assert "PARAMETRES_MODIFIER" in msg
    assert (
        db_session.query(TClasse)
        .filter_by(LibClasse="CM2 NON AUTORISEE")
        .first()
        is None
    )


def test_parametres_write_service_allows_modifier_permission(db_session):
    annee, etablissement, niveau, classe = _setup_active_param_context(db_session)
    _set_user_with_param_write_permission()

    ok, msg = ClasseService.add_classe(
        lib_classe="CM2 AUTORISEE",
        sigle="CM2A",
        id_cycle=niveau.IDT_Cycle,
        id_niveau=niveau.IDT_Niveau,
        capacite=40,
    )

    db_session.expire_all()
    assert ok is True, msg
    assert (
        db_session.query(TClasse)
        .filter_by(LibClasse="CM2 AUTORISEE")
        .first()
        is not None
    )


def test_prestations_write_service_requires_modifier_permission(db_session):
    _set_user_without_prestation_write_permission()

    ok, msg = PrestationService.create_prestation({
        "Code": "MUSIQUE_TEST",
        "Libelle": "Musique test",
        "MontantAnnuel": 8000,
    })

    db_session.expire_all()
    assert ok is False
    assert "PRESTATIONS_MODIFIER" in msg
    assert db_session.query(PrestationAnnexe).filter_by(Code="MUSIQUE_TEST").first() is None


def test_prestations_write_service_allows_modifier_permission(db_session):
    _set_user_with_prestation_write_permission()

    ok, msg = PrestationService.create_prestation({
        "Code": "MUSIQUE_TEST",
        "Libelle": "Musique test",
        "MontantAnnuel": 8000,
    })

    db_session.expire_all()
    assert ok is True, msg
    assert db_session.query(PrestationAnnexe).filter_by(Code="MUSIQUE_TEST").first() is not None


def test_versements_write_service_requires_versements_permission(db_session):
    annee, famille, eleve = _setup_payment_context(db_session)
    _set_user_without_versements_permission()

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire,
        eleve.IDEleve,
        famille.IdTFamille,
        date.today(),
        m_scol=10000,
        m_trans=0,
        m_cant=0,
        m_autres=0,
    )

    db_session.expire_all()
    assert ok is False
    assert "SCOLARITE_VERSEMENTS" in msg
    assert new_id is None
    assert db_session.query(VersementScol).count() == 0


def test_stock_entry_service_requires_stock_permission(db_session):
    annee, article, stock = _setup_stock_context(db_session, qte=0)
    _set_user_without_kiosque_write_permission()

    ok, msg = StockService.add_stock(
        article.IDTArticle,
        qte=5,
        id_annee=annee.IDTAnneeScolaire,
        login="TEST",
    )

    db_session.expire_all()
    assert ok is False
    assert "KIOSQUE_STOCKS" in msg
    assert db_session.get(StockCour, stock.IDStockCour).QuantiteCour == 0
    assert db_session.query(StockEntree).count() == 0


def test_stock_sale_service_requires_sales_permission(db_session):
    annee, article, stock = _setup_stock_context(db_session, qte=5)
    _set_user_without_kiosque_write_permission()

    ok, msg = StockService.remove_stock(
        article.IDTArticle,
        qte=1,
        id_annee=annee.IDTAnneeScolaire,
        prix_vente=500,
        login="TEST",
    )

    db_session.expire_all()
    assert ok is False
    assert "KIOSQUE_VENTES" in msg
    assert db_session.get(StockCour, stock.IDStockCour).QuantiteCour == 5
    assert db_session.query(StockSortie).count() == 0


def test_article_write_service_requires_articles_permission(db_session):
    _set_user_without_kiosque_write_permission()

    ok, msg = ArticleService.create_article("Cahier interdit", pu=500, seuil=2)

    db_session.expire_all()
    assert ok is False
    assert "KIOSQUE_ARTICLES" in msg
    assert db_session.query(Article).filter_by(Libelle="Cahier interdit").first() is None


def test_user_write_service_requires_users_modifier_permission(db_session):
    profil = _make_direct_profil(db_session)
    _set_user_without_users_modifier_permission()

    ok, msg = UtilisateurService.create({
        "Login": "interdit",
        "Nom": "Interdit",
        "Password": "secret123",
        "IDProfil": profil.IDProfil,
    })

    db_session.expire_all()
    assert ok is False
    assert "UTILISATEURS_MODIFIER" in msg
    assert db_session.query(Utilisateur).filter_by(Login="interdit").first() is None


def test_profile_write_service_requires_users_modifier_permission(db_session):
    _set_user_without_users_modifier_permission()

    ok, msg = ProfilService.create({
        "Code": "NOPE",
        "Libelle": "Profil interdit",
        "IsAdmin": False,
    })

    db_session.expire_all()
    assert ok is False
    assert "UTILISATEURS_MODIFIER" in msg
    assert db_session.query(Profil).filter_by(Code="NOPE").first() is None


def test_profile_write_service_allows_users_modifier_permission(db_session):
    _set_user_with_users_modifier_permission()

    ok, msg = ProfilService.create({
        "Code": "OKUSERS",
        "Libelle": "Profil autorise",
        "IsAdmin": False,
    })

    db_session.expire_all()
    assert ok is True, msg
    assert db_session.query(Profil).filter_by(Code="OKUSERS").first() is not None


def test_profile_permissions_write_requires_users_modifier_permission(db_session):
    profil = _make_direct_profil(db_session, code="PROFIL_DROITS")
    permission = Permission(
        Code="DROIT_TEST",
        Libelle="Droit test",
        Module="Tests",
        Ordre=999,
    )
    db_session.add(permission)
    db_session.commit()
    _set_user_without_users_modifier_permission()

    ok, msg = ProfilService.set_profil_permissions(profil.IDProfil, {"DROIT_TEST"})

    db_session.expire_all()
    assert ok is False
    assert "UTILISATEURS_MODIFIER" in msg
    assert db_session.query(ProfilPermission).filter_by(IDProfil=profil.IDProfil).count() == 0
