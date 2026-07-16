from app.database import get_session
from models.famille import TFamille
from models.eleve import Eleve
import re

class FamilleService:
    """
    Service gérant les opérations sur les familles et parents d'élèves.
    """

    @staticmethod
    def get_all_familles() -> list[TFamille]:
        """Récupère la liste de toutes les familles."""
        session = get_session()
        try:
            return session.query(TFamille).order_by(TFamille.NomResponsable.asc()).all()
        finally:
            session.close()

    @staticmethod
    def get_famille_by_id(id_famille: int) -> TFamille | None:
        """Trouve une famille par sa clé primaire."""
        session = get_session()
        try:
            return session.get(TFamille, id_famille)
        finally:
            session.close()

    @staticmethod
    def search_familles(query: str) -> list[TFamille]:
        """Recherche des familles par nom de responsable, téléphone ou profession."""
        if not query or not query.strip():
            return FamilleService.get_all_familles()
        
        session = get_session()
        try:
            search_pattern = f"%{query.strip()}%"
            return session.query(TFamille).filter(
                (TFamille.NomResponsable.ilike(search_pattern)) |
                (TFamille.CellulaireResponsable.ilike(search_pattern)) |
                (TFamille.ProfessionResponsable.ilike(search_pattern))
            ).order_by(TFamille.NomResponsable.asc()).all()
        finally:
            session.close()

    @staticmethod
    def create_famille(data: dict) -> tuple[bool, str]:
        """Crée une nouvelle famille de parents."""
        session = get_session()
        try:
            # Validations obligatoires
            nom_resp = data.get("NomResponsable", "").strip()
            tel_resp = data.get("CellulaireResponsable", "").strip()
            
            if not nom_resp:
                return False, "Le nom du responsable est obligatoire."
            if not tel_resp:
                return False, "Le téléphone du responsable est obligatoire."
                
            # Validation de l'email si renseigné
            email = data.get("EmailResponsable", "").strip()
            if email:
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    return False, "Le format de l'e-mail du responsable est invalide."

            # Éviter les doublons exacts Nom + Téléphone
            doublon = session.query(TFamille).filter_by(
                NomResponsable=nom_resp,
                CellulaireResponsable=tel_resp
            ).first()
            if doublon:
                return False, f"Une famille avec ce responsable '{nom_resp}' et ce téléphone existe déjà."

            famille = TFamille(
                NomResponsable=nom_resp,
                QualiteResponsable=data.get("QualiteResponsable", 1),
                ProfessionResponsable=data.get("ProfessionResponsable"),
                TypeResponsable=data.get("TypeResponsable"),
                NumeroPieceIdentite=data.get("NumeroPieceIdentite"),
                AdresseResponsable=data.get("AdresseResponsable"),
                CellulaireResponsable=tel_resp,
                EmailResponsable=email if email else None,
                SIMaitre=data.get("SIMaitre", False),
                EbrieAbobote=data.get("EbrieAbobote", False),
                NomUrgence=data.get("NomUrgence"),
                ContactUrgence=data.get("ContactUrgence"),
                HabitationUrgence=data.get("HabitationUrgence"),
                UrgenceMoimeme=data.get("UrgenceMoimeme", False),
                HabitationParent=data.get("HabitationParent"),
                NomPere=data.get("NomPere"),
                ProfessionPere=data.get("ProfessionPere"),
                TelPere=data.get("TelPere"),
                NomMere=data.get("NomMere"),
                ProfessionMere=data.get("ProfessionMere"),
                TelMere=data.get("TelMere"),
            )
            session.add(famille)
            session.commit()
            return True, "Famille enregistrée avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la création de la famille : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_famille(id_famille: int, data: dict) -> tuple[bool, str]:
        """Modifie une famille existante."""
        session = get_session()
        try:
            famille = session.get(TFamille, id_famille)
            if not famille:
                return False, "La famille à modifier n'existe pas."

            nom_resp = data.get("NomResponsable", "").strip()
            tel_resp = data.get("CellulaireResponsable", "").strip()
            
            if not nom_resp:
                return False, "Le nom du responsable est obligatoire."
            if not tel_resp:
                return False, "Le téléphone du responsable est obligatoire."
                
            email = data.get("EmailResponsable", "").strip()
            if email:
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    return False, "Le format de l'e-mail du responsable est invalide."

            # Éviter les doublons Nom + Téléphone (exclure l'instance actuelle)
            doublon = session.query(TFamille).filter(
                TFamille.NomResponsable == nom_resp,
                TFamille.CellulaireResponsable == tel_resp,
                TFamille.IdTFamille != id_famille
            ).first()
            if doublon:
                return False, f"Une autre famille possède déjà ce couple Responsable / Téléphone."

            # Mise à jour des valeurs
            famille.NomResponsable = nom_resp
            famille.QualiteResponsable = data.get("QualiteResponsable", 1)
            famille.ProfessionResponsable = data.get("ProfessionResponsable")
            famille.TypeResponsable = data.get("TypeResponsable")
            famille.NumeroPieceIdentite = data.get("NumeroPieceIdentite")
            famille.AdresseResponsable = data.get("AdresseResponsable")
            famille.CellulaireResponsable = tel_resp
            famille.EmailResponsable = email if email else None
            famille.SIMaitre = data.get("SIMaitre", False)
            famille.EbrieAbobote = data.get("EbrieAbobote", False)
            famille.NomUrgence = data.get("NomUrgence")
            famille.ContactUrgence = data.get("ContactUrgence")
            famille.HabitationUrgence = data.get("HabitationUrgence")
            famille.UrgenceMoimeme = data.get("UrgenceMoimeme", False)
            famille.HabitationParent = data.get("HabitationParent")
            famille.NomPere = data.get("NomPere")
            famille.ProfessionPere = data.get("ProfessionPere")
            famille.TelPere = data.get("TelPere")
            famille.NomMere = data.get("NomMere")
            famille.ProfessionMere = data.get("ProfessionMere")
            famille.TelMere = data.get("TelMere")

            session.commit()
            return True, "Famille mise à jour avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la modification de la famille : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_famille(id_famille: int) -> tuple[bool, str]:
        """Supprime une famille si elle n'est liée à aucun élève."""
        session = get_session()
        try:
            famille = session.get(TFamille, id_famille)
            if not famille:
                return False, "La famille à supprimer n'existe pas."

            # Vérifier si des élèves y sont rattachés
            has_eleves = session.query(Eleve).filter_by(IDFamille=id_famille).first() is not None
            if has_eleves:
                return False, "Impossible de supprimer cette famille car elle est liée à un ou plusieurs élèves."

            session.delete(famille)
            session.commit()
            return True, "La famille a été supprimée avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la suppression de la famille : {str(e)}"
        finally:
            session.close()
