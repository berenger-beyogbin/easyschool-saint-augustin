from app.session import AppSession
from services.etablissement_service import EtablissementService
from utils.print_helpers import get_etablissement_print_info


def _set_parametres_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 4000,
            "Login": "parametres_test",
            "Nom": "Parametres",
            "ProfilCode": "ADMIN",
            "ProfilLibelle": "Administration",
            "IsAdmin": False,
        },
        permissions={"PARAMETRES_MODIFIER"},
    )


def test_fiche_officielle_2026_2027_est_complete(db_session):
    infos = EtablissementService.get_informations_officielles()

    assert infos["RaisonSociale"] == "École Primaire Catholique Saint Augustin Abobo-té"
    assert infos["Telephone"] == "07 57 47 13 43"
    assert infos["TelephoneSecondaire"] == "05 04 08 13 55"
    assert infos["AdressePostale"] == "13 BP 1 434 Abidjan 13"
    assert infos["Email"] == "epcsaintaugustin58@gmail.com"


def test_enregistrement_et_impression_utilisent_les_deux_telephones(db_session):
    _set_parametres_user()
    infos = EtablissementService.get_informations_officielles()

    assert EtablissementService.save_etablissement(infos) is True
    impression = get_etablissement_print_info()

    assert impression is not None
    assert impression.telephone == "07 57 47 13 43 / 05 04 08 13 55"
    assert impression.adresse.startswith("Route d'Alépé")

