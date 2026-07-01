from typing import List
from models.annee_scolaire import TAnneeScolaire
from app.database import get_session

class AnneeScolaireService:
    @staticmethod
    def get_all() -> List[TAnneeScolaire]:
        """Recupere la liste complete des annees scolaires."""
        session = get_session()
        try:
            return session.query(TAnneeScolaire).order_by(TAnneeScolaire.Libelle.desc()).all()
        except Exception as e:
            print(f"Erreur get_all TAnneeScolaire : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def add_annee(libelle: str) -> tuple[bool, str]:
        """Cree une nouvelle annee scolaire. Format attendu : YYYY-YYYY (ex: 2026-2027) et Y2 = Y1 + 1."""
        import re
        match = re.match(r"^(\d{4})-(\d{4})$", libelle)
        if not match:
            return False, "Le libelle de l'annee doit respecter le format YYYY-YYYY (ex: 2026-2027)."
            
        y1 = int(match.group(1))
        y2 = int(match.group(2))
        if y2 != y1 + 1:
            return False, f"La deuxieme annee ({y2}) doit etre egale a la premiere annee ({y1}) + 1 (ex: {y1}-{y1+1})."
            
        session = get_session()
        try:
            # Verifie si elle existe deja
            exist = session.query(TAnneeScolaire).filter_by(Libelle=libelle).first()
            if exist:
                return False, f"L'annee scolaire {libelle} existe deja."

            nouvelle_annee = TAnneeScolaire(Libelle=libelle, Cloturer=False)
            session.add(nouvelle_annee)
            session.commit()
            return True, "Annee scolaire creee avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def cloturer_annee(id_annee: int) -> bool:
        """Cloture une annee scolaire. Une annee cloturee ne peut plus etre modifiee."""
        from app.session import AppSession
        session = get_session()
        try:
            annee = session.query(TAnneeScolaire).get(id_annee)
            if annee:
                annee.Cloturer = True
                session.commit()
                
                # Verifier si l'annee cloturee etait l'annee active
                active_id = AppSession._active_annee_id
                if active_id == id_annee:
                    # Invalider active_annee_id pour forcer la creation ou selection d'une nouvelle annee non cloturee
                    AppSession._active_annee_id = None
                    AppSession._active_annee_libelle = None
                    AppSession.initialize_session()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Erreur de cloture d'annee : {e}")
            return False
        finally:
            session.close()
