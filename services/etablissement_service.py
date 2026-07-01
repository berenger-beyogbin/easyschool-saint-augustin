from sqlalchemy.orm import Session
from models.etablissement import EtablissementEcole
from app.database import get_session

class EtablissementService:
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
                    RaisonSociale="EPC SAINT AUGUSTIN",
                    Sigle="EPC",
                    Telephone="01 01 01 01 01 / 01 01 01 01 01",
                    Adresse="ABOBOTE",
                    Localite="ABOBOTE",
                    ChefEtab="DONGO KOUAME",
                    CodeEtab="0037",
                    TypeEtab="Enseignement Primaire",
                    Ministere="MENAET",
                    Dren="ABIDJAN 4",
                    IEP="PLATEAU DOKUI",
                    Slogan="Discipline - Success",
                    Email="contact@epcsaintaugustin.ci"
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
            ecole.Email = data.get("Email", ecole.Email)
            ecole.Adresse = data.get("Adresse", ecole.Adresse)
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
