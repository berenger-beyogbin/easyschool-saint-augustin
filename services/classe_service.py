from typing import List
from models.classe import TClasse
from models.niveau import TNiveau
from app.database import get_session
from app.session import AppSession

class ClasseService:
    @staticmethod
    def get_niveaux_par_cycle(id_cycle: int) -> List[TNiveau]:
        """Charge uniquement les niveaux lies au cycle selectionne (cascade), filtres par session active."""
        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()
            return session.query(TNiveau).filter_by(
                IDT_Cycle=id_cycle,
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).all()
        except Exception as e:
            print(f"Erreur get_niveaux_par_cycle : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_all() -> list:
        """Recupere la liste complete des classes pour la session active."""
        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()
            classes = session.query(TClasse).filter_by(
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).all()
            resultat = []
            for c in classes:
                resultat.append({
                    "IDTClasse": c.IDTClasse,
                    "LibClasse": c.LibClasse,
                    "Sigle": c.Sigle,
                    "Capacite": c.Capacite,
                    "CycleLibelle": c.cycle.Libelle if c.cycle else "Non defini",
                    "NiveauLibelle": c.niveau.Libelle if c.niveau else "Non defini"
                })
            return resultat
        except Exception as e:
            print(f"Erreur get_all TClasse : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def add_classe(lib_classe: str, sigle: str, id_cycle: int, id_niveau: int, capacite: int) -> tuple[bool, str]:
        """Cree une nouvelle classe d'eleves."""
        allowed, msg = AppSession.require_permission("PARAMETRES_MODIFIER")
        if not allowed:
            return False, msg

        if not lib_classe or not id_niveau:
            return False, "Le libelle de la classe et le niveau sont obligatoires."

        if capacite < 1 or capacite > 200:
            return False, "La capacite de la classe doit etre comprise entre 1 et 200."

        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()

            # Verifier les doublons pour le meme niveau, la meme academie et le meme etablissement
            exist = session.query(TClasse).filter_by(
                LibClasse=lib_classe.upper(),
                IDT_Niveau=id_niveau,
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).first()
            if exist:
                return False, f"La classe '{lib_classe}' existe deja pour ce niveau et cette session active."

            nouvelle = TClasse(
                LibClasse=lib_classe.upper(),
                Sigle=sigle.upper() if sigle else lib_classe[:10].replace(" ", "").upper(),
                IDT_Cycle=id_cycle,
                IDT_Niveau=id_niveau,
                Capacite=capacite,
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            )
            session.add(nouvelle)
            session.commit()
            return True, "Classe creee avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_classe(id_classe: int) -> tuple[bool, str]:
        """Supprime une classe d'eleves."""
        allowed, msg = AppSession.require_permission("PARAMETRES_MODIFIER")
        if not allowed:
            return False, msg

        from models.inscription import TInscription

        session = get_session()
        try:
            classe = session.get(TClasse, id_classe)
            if classe:
                has_inscriptions = (
                    session.query(TInscription)
                    .filter_by(IDClasse=id_classe)
                    .first()
                    is not None
                )
                if has_inscriptions:
                    return False, "Impossible de supprimer cette classe car elle contient déjà des inscriptions."

                session.delete(classe)
                session.commit()
                return True, "Classe supprimee avec succes !"
            return False, "Classe inexistante."
        except Exception as e:
            session.rollback()
            return False, f"Impossible de supprimer la classe : {str(e)}"
        finally:
            session.close()
