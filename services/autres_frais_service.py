from typing import List
from models.autres_frais import AutresFrais
from app.database import get_session
from app.session import AppSession

class AutresFraisService:
    @staticmethod
    def _require_versements_permission() -> tuple[bool, str]:
        return AppSession.require_permission("SCOLARITE_VERSEMENTS")

    @staticmethod
    def get_all_autres_frais() -> List[AutresFrais]:
        """Recupere tous les types d'autres frais."""
        session = get_session()
        try:
            return session.query(AutresFrais).order_by(AutresFrais.CodeFrais.asc()).all()
        except Exception as e:
            print(f"Erreur get_all_autres_frais : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_autres_frais_by_id(id_frais: int) -> AutresFrais | None:
        """Recupere un type d'autre frais par son ID."""
        session = get_session()
        try:
            return session.get(AutresFrais, id_frais)
        except Exception as e:
            print(f"Erreur get_autres_frais_by_id : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def create_autres_frais(code: str, libelle: str) -> tuple[bool, str]:
        """Cree un nouveau type d'autre frais."""
        if not code or not libelle:
            return False, "Le code et le libelle sont obligatoires."
        allowed, msg = AutresFraisService._require_versements_permission()
        if not allowed:
            return False, msg
        
        code_clean = code.strip().upper()
        lib_clean = libelle.strip()

        session = get_session()
        try:
            # Verifier l'unicite du code
            exist = session.query(AutresFrais).filter(AutresFrais.CodeFrais == code_clean).first()
            if exist:
                return False, f"Le code frais '{code_clean}' existe deja."

            nouveau = AutresFrais(CodeFrais=code_clean, LibelleFrais=lib_clean)
            session.add(nouveau)
            session.commit()
            return True, "Type de frais cree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur de base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_autres_frais(id_frais: int, code: str, libelle: str) -> tuple[bool, str]:
        """Met a jour un type d'autre frais existent."""
        if not code or not libelle:
            return False, "Le code et le libelle sont obligatoires."
        allowed, msg = AutresFraisService._require_versements_permission()
        if not allowed:
            return False, msg
        
        code_clean = code.strip().upper()
        lib_clean = libelle.strip()

        session = get_session()
        try:
            frais = session.get(AutresFrais, id_frais)
            if not frais:
                return False, "Type de frais inexistant."

            # Verifier l'unicite du code (hors lui-meme)
            exist = session.query(AutresFrais).filter(
                (AutresFrais.CodeFrais == code_clean) & (AutresFrais.IDAutres_Frais != id_frais)
            ).first()
            if exist:
                return False, f"Le code frais '{code_clean}' est deja utilise par un autre type de frais."

            frais.CodeFrais = code_clean
            frais.LibelleFrais = lib_clean
            session.commit()
            return True, "Frais mis a jour avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur de base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_autres_frais(id_frais: int) -> tuple[bool, str]:
        """Supprime un type d'autre frais s'il n'est pas utilise."""
        allowed, msg = AutresFraisService._require_versements_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            frais = session.get(AutresFrais, id_frais)
            if not frais:
                return False, "Type de frais inexistant."

            # Verifier si associe a des montants
            from models.montant_autres_frais import MontantAutresFrais
            montant_count = session.query(MontantAutresFrais).filter_by(IDAutres_Frais=id_frais).count()
            if montant_count > 0:
                return False, "Impossible de supprimer ce type de frais car il possède des tarifs associes de niveaux."

            session.delete(frais)
            session.commit()
            return True, "Type de frais supprime avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Impossible de supprimer le type de frais : {str(e)}"
        finally:
            session.close()
