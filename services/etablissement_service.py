from sqlalchemy.orm import Session
from models.etablissement import EtablissementEcole
from app.database import get_session
from app.session import AppSession

class EtablissementService:
    INFORMATIONS_OFFICIELLES_2026_2027 = {
        "RaisonSociale": "École Primaire Catholique Saint Augustin Abobo-té",
        "Sigle": "EPC SAINT AUGUSTIN",
        "Telephone": "07 57 47 13 43",
        "TelephoneSecondaire": "05 04 08 13 55",
        "Email": "epcsaintaugustin58@gmail.com",
        "Adresse": "Route d'Alépé, 1ère rue à droite après la pharmacie MONASTERE",
        "AdressePostale": "13 BP 1 434 Abidjan 13",
        "Localite": "Abobo-té",
        "TypeEtab": "École primaire catholique",
        "Slogan": "L’EPC Saint Augustin, l’école pour la paix",
        "LogoPath": "assets/logo.jpg",
    }

    @staticmethod
    def get_informations_officielles() -> dict:
        return dict(EtablissementService.INFORMATIONS_OFFICIELLES_2026_2027)

    @staticmethod
    def get_etablissement() -> EtablissementEcole:
        """Recupere la fiche de l'etablissement (s'il n'y en a pas, en cree une par defaut)."""
        session = get_session()
        try:
            # On recupere le premier etablissement trouve
            ecole = session.query(EtablissementEcole).first()
            if not ecole:
                # S'il n'existe aucun etablissement, on en cree un par defaut pour eviter une erreur
                ecole = EtablissementEcole(
                    **EtablissementService.get_informations_officielles(),
                    ChefEtab="DONGO KOUAME",
                    CodeEtab="0037",
                    Ministere="MENAET",
                    Dren="ABIDJAN 4",
                    IEP="PLATEAU DOKUI",
                )
                session.add(ecole)
                session.commit()
                session.refresh(ecole)
            return ecole
        except Exception as e:
            session.rollback()
            print(f"Erreur de lecture de l'etablissement : {e}")
            raise e
        finally:
            session.close()

    @staticmethod
    def save_etablissement(data: dict) -> bool:
        """Met a jour ou cree l'etablissement."""
        allowed, _ = AppSession.require_permission("PARAMETRES_MODIFIER")
        if not allowed:
            return False

        session = get_session()
        try:
            ecole = session.query(EtablissementEcole).first()
            if not ecole:
                ecole = EtablissementEcole()
                session.add(ecole)

            # Mise a jour des champs
            ecole.RaisonSociale = data.get("RaisonSociale", ecole.RaisonSociale)
            ecole.Sigle = data.get("Sigle", ecole.Sigle)
            ecole.Telephone = data.get("Telephone", ecole.Telephone)
            ecole.TelephoneSecondaire = data.get("TelephoneSecondaire", ecole.TelephoneSecondaire)
            ecole.Email = data.get("Email", ecole.Email)
            ecole.Adresse = data.get("Adresse", ecole.Adresse)
            ecole.AdressePostale = data.get("AdressePostale", ecole.AdressePostale)
            ecole.ChefEtab = data.get("ChefEtab", ecole.ChefEtab)
            ecole.Slogan = data.get("Slogan", ecole.Slogan)
            ecole.Localite = data.get("Localite", ecole.Localite)
            ecole.CodeEtab = data.get("CodeEtab", ecole.CodeEtab)
            ecole.TypeEtab = data.get("TypeEtab", ecole.TypeEtab)
            ecole.Ministere = data.get("Ministere", ecole.Ministere)
            ecole.Dren = data.get("Dren", ecole.Dren)
            ecole.IEP = data.get("IEP", ecole.IEP)
            if "LogoPath" in data:
                ecole.LogoPath = data["LogoPath"]

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Erreur d'enregistrement de l'etablissement : {e}")
            return False
        finally:
            session.close()
