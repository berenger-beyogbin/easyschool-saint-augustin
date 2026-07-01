from typing import List, Dict, Any, Optional
from app.database import get_session
from models.prestataire import Prestataire
from models.prestation_annexe import PrestationAnnexe

# Prestations annexes incluses dans la scolarité — données par défaut
_DEFAULT_PRESTATIONS = [
    {"Code": "ANGLAIS_INFORMATIQUE", "Libelle": "Anglais / Informatique", "MontantAnnuel": 10000.0},
    {"Code": "ENTREPRENEURIAT",      "Libelle": "Entrepreneuriat",         "MontantAnnuel": 10000.0},
    {"Code": "MUSIQUE",              "Libelle": "Musique",                  "MontantAnnuel": 8000.0},
]


class PrestationService:

    # ─── Prestataires ─────────────────────────────────────────────────────────

    @staticmethod
    def get_all_prestataires(actifs_seulement: bool = False) -> List[Prestataire]:
        session = get_session()
        try:
            q = session.query(Prestataire)
            if actifs_seulement:
                q = q.filter(Prestataire.IsActive == True)
            return q.order_by(Prestataire.Nom.asc()).all()
        except Exception as e:
            print(f"Erreur get_all_prestataires : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def create_prestataire(nom: str, contact: str = None, telephone: str = None, email: str = None) -> tuple[bool, str]:
        session = get_session()
        try:
            nom = nom.strip()
            if not nom:
                return False, "Le nom du prestataire est obligatoire."
            p = Prestataire(Nom=nom, Contact=contact, Telephone=telephone, Email=email, IsActive=True)
            session.add(p)
            session.commit()
            return True, f"Prestataire '{nom}' créé avec succès."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_prestataire(id_prestataire: int, data: Dict[str, Any]) -> tuple[bool, str]:
        session = get_session()
        try:
            p = session.get(Prestataire, id_prestataire)
            if not p:
                return False, "Prestataire introuvable."
            nom = data.get("Nom", p.Nom).strip()
            if not nom:
                return False, "Le nom est obligatoire."
            p.Nom = nom
            p.Contact = data.get("Contact", p.Contact)
            p.Telephone = data.get("Telephone", p.Telephone)
            p.Email = data.get("Email", p.Email)
            p.IsActive = data.get("IsActive", p.IsActive)
            session.commit()
            return True, "Prestataire mis à jour avec succès."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    # ─── Prestations annexes ──────────────────────────────────────────────────

    @staticmethod
    def get_all_prestations(actives_seulement: bool = False) -> List[PrestationAnnexe]:
        session = get_session()
        try:
            q = session.query(PrestationAnnexe)
            if actives_seulement:
                q = q.filter(PrestationAnnexe.IsActive == True)
            return q.order_by(PrestationAnnexe.Libelle.asc()).all()
        except Exception as e:
            print(f"Erreur get_all_prestations : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_prestations_actives() -> List[PrestationAnnexe]:
        return PrestationService.get_all_prestations(actives_seulement=True)

    @staticmethod
    def get_prestation_by_id(id_prestation: int) -> Optional[PrestationAnnexe]:
        session = get_session()
        try:
            return session.get(PrestationAnnexe, id_prestation)
        except Exception:
            return None
        finally:
            session.close()

    @staticmethod
    def create_prestation(data: Dict[str, Any]) -> tuple[bool, str]:
        session = get_session()
        try:
            code = data.get("Code", "").strip().upper()
            libelle = data.get("Libelle", "").strip()
            montant = float(data.get("MontantAnnuel", 0))
            id_prestataire = data.get("IDPrestataire") or None

            if not code:
                return False, "Le code est obligatoire."
            if not libelle:
                return False, "Le libellé est obligatoire."
            if montant < 0:
                return False, "Le montant annuel ne peut pas être négatif."
            if session.query(PrestationAnnexe).filter_by(Code=code).first():
                return False, f"Une prestation avec le code '{code}' existe déjà."

            p = PrestationAnnexe(
                Code=code, Libelle=libelle, MontantAnnuel=montant,
                IDPrestataire=id_prestataire, IsActive=True
            )
            session.add(p)
            session.commit()
            return True, f"Prestation '{libelle}' créée avec succès."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_prestation(id_prestation: int, data: Dict[str, Any]) -> tuple[bool, str]:
        session = get_session()
        try:
            p = session.get(PrestationAnnexe, id_prestation)
            if not p:
                return False, "Prestation introuvable."

            code = data.get("Code", p.Code).strip().upper()
            libelle = data.get("Libelle", p.Libelle).strip()
            montant = float(data.get("MontantAnnuel", float(p.MontantAnnuel)))

            if not code or not libelle:
                return False, "Code et libellé sont obligatoires."
            if montant < 0:
                return False, "Le montant annuel ne peut pas être négatif."

            doublon = session.query(PrestationAnnexe).filter(
                PrestationAnnexe.Code == code,
                PrestationAnnexe.IDPrestation != id_prestation
            ).first()
            if doublon:
                return False, f"Le code '{code}' est déjà utilisé."

            p.Code = code
            p.Libelle = libelle
            p.MontantAnnuel = montant
            p.IDPrestataire = data.get("IDPrestataire") or p.IDPrestataire
            p.IsActive = data.get("IsActive", p.IsActive)
            session.commit()
            return True, "Prestation mise à jour avec succès."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def toggle_active(id_prestation: int) -> tuple[bool, str]:
        session = get_session()
        try:
            p = session.get(PrestationAnnexe, id_prestation)
            if not p:
                return False, "Prestation introuvable."
            p.IsActive = not p.IsActive
            session.commit()
            etat = "activée" if p.IsActive else "désactivée"
            return True, f"Prestation '{p.Libelle}' {etat}."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def seed_default_prestations():
        """Insère les prestations par défaut si elles n'existent pas (idempotent)."""
        session = get_session()
        try:
            for item in _DEFAULT_PRESTATIONS:
                if not session.query(PrestationAnnexe).filter_by(Code=item["Code"]).first():
                    session.add(PrestationAnnexe(
                        Code=item["Code"],
                        Libelle=item["Libelle"],
                        MontantAnnuel=item["MontantAnnuel"],
                        IsActive=True,
                    ))
            session.commit()
            print("Seeding prestations annexes terminé avec succès.")
        except Exception as e:
            session.rollback()
            print(f"Erreur seeding prestations : {e}")
        finally:
            session.close()
