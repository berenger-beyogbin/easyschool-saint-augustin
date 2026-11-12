from app.database import get_session
from models.famille import TFamille
from models.eleve import Eleve
import re
from sqlalchemy.orm import joinedload

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
    def find_by_nom_et_telephone(nom: str, telephone: str) -> TFamille | None:
        """Récupération exacte (Nom + Téléphone du responsable) : ce couple
        est contraint unique (uq_famille_nom_cellulaire), donc fiable juste
        après une création réussie pour retrouver l'IdTFamille sans changer
        la signature de create_famille."""
        session = get_session()
        try:
            return session.query(TFamille).filter_by(
                NomResponsable=nom, CellulaireResponsable=telephone
            ).first()
        finally:
            session.close()

    @staticmethod
    def search_parent_contacts(query: str, limit: int = 8) -> list[dict]:
        """Recherche un parent existant par nom ou téléphone normalisé."""
        query = (query or "").strip()
        query_digits = re.sub(r"\D", "", query)
        query_name = query.casefold()
        if len(query_name) < 3 and len(query_digits) < 6:
            return []

        session = get_session()
        try:
            results = []
            seen = set()
            families = session.query(TFamille).options(
                joinedload(TFamille.eleves)
            ).order_by(TFamille.NomResponsable).all()
            role_fields = (
                ("Père", "NomPere", "TelPere", "TelBureauPere", "EmailPere"),
                ("Mère", "NomMere", "TelMere", "TelBureauMere", "EmailMere"),
                ("Tuteur", "NomTuteur", "CelTuteur", "TelBureauTuteur", "EmailTuteur"),
            )
            contact_keys = (
                "NomPere", "TelPere", "TelBureauPere", "EmailPere",
                "NomMere", "TelMere", "TelBureauMere", "EmailMere",
                "NomTuteur", "CelTuteur", "TelBureauTuteur", "EmailTuteur",
            )
            for family in families:
                children = ", ".join(
                    f"{child.Nom} {child.Prenoms}" for child in family.eleves
                )
                contacts = {key: getattr(family, key, None) or "" for key in contact_keys}
                for role, name_key, phone_key, phone2_key, email_key in role_fields:
                    name = getattr(family, name_key, None) or ""
                    phone = getattr(family, phone_key, None) or ""
                    phone2 = getattr(family, phone2_key, None) or ""
                    haystack_digits = re.sub(r"\D", "", f"{phone}{phone2}")
                    name_match = len(query_name) >= 3 and query_name in name.casefold()
                    phone_match = len(query_digits) >= 6 and query_digits in haystack_digits
                    identity = (family.IdTFamille, role, name.casefold(), re.sub(r"\D", "", phone))
                    if (name_match or phone_match) and identity not in seen:
                        seen.add(identity)
                        results.append({
                            "family_id": family.IdTFamille,
                            "role": role,
                            "name": name,
                            "phone": phone,
                            "phone2": phone2,
                            "email": getattr(family, email_key, None) or "",
                            "children": children,
                            "contacts": contacts,
                        })
                        if len(results) >= limit:
                            return results
            return results
        finally:
            session.close()

    @staticmethod
    def enregistrer_contacts_eleve(id_eleve: int, data: dict) -> tuple[bool, str, int | None]:
        """Crée/met à jour la famille derrière une saisie simple des contacts.

        Le père, la mère ou le tuteur choisi comme contact principal alimente
        les champs responsables obligatoires. Pour un élève sans famille, une
        famille existante portant le même nom/téléphone principal est réutilisée
        afin de regrouper naturellement les frères et sœurs.
        """
        session = get_session()
        try:
            eleve = session.get(Eleve, id_eleve)
            if not eleve:
                return False, "Élève introuvable.", None

            principal = data.get("Principal")
            contacts = {
                "PERE": (data.get("NomPere", "").strip(), data.get("TelPere", "").strip(), 2),
                "MERE": (data.get("NomMere", "").strip(), data.get("TelMere", "").strip(), 3),
                "TUTEUR": (data.get("NomTuteur", "").strip(), data.get("CelTuteur", "").strip(), 1),
            }
            if principal not in contacts:
                return False, "Choisissez le contact principal.", None
            nom_resp, tel_resp, qualite = contacts[principal]
            if not nom_resp or not tel_resp:
                return False, "Le contact principal doit avoir un nom et un téléphone.", None

            for email_key in ("EmailPere", "EmailMere", "EmailTuteur"):
                email = (data.get(email_key) or "").strip()
                if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                    return False, f"L'adresse e-mail « {email} » est invalide.", None

            famille = session.get(TFamille, eleve.IDFamille) if eleve.IDFamille else None
            if not famille and data.get("ExistingFamilyId"):
                famille = session.get(TFamille, int(data["ExistingFamilyId"]))
            if not famille:
                famille = session.query(TFamille).filter_by(
                    NomResponsable=nom_resp, CellulaireResponsable=tel_resp
                ).first()
            if not famille:
                famille = TFamille(
                    NomResponsable=nom_resp,
                    CellulaireResponsable=tel_resp,
                    QualiteResponsable=qualite,
                )
                session.add(famille)
                session.flush()

            famille.NomResponsable = nom_resp
            famille.CellulaireResponsable = tel_resp
            famille.QualiteResponsable = qualite
            famille.EmailResponsable = data.get({
                "PERE": "EmailPere", "MERE": "EmailMere", "TUTEUR": "EmailTuteur"
            }[principal]) or None
            for key in (
                "NomPere", "TelPere", "TelBureauPere", "EmailPere",
                "NomMere", "TelMere", "TelBureauMere", "EmailMere",
                "NomTuteur", "CelTuteur", "TelBureauTuteur", "EmailTuteur",
            ):
                setattr(famille, key, (data.get(key) or "").strip() or None)

            eleve.IDFamille = famille.IdTFamille
            session.commit()
            return True, "Contacts des parents enregistrés avec succès.", famille.IdTFamille
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement des contacts : {e}", None
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
                TelBureauResponsable=data.get("TelBureauResponsable"),
                TelDomicileResponsable=data.get("TelDomicileResponsable"),
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
                EmailPere=data.get("EmailPere"),
                EntreprisePere=data.get("EntreprisePere"),
                LieuResidencePere=data.get("LieuResidencePere"),
                TelBureauPere=data.get("TelBureauPere"),
                TelDomicilePere=data.get("TelDomicilePere"),
                AdressePostalePere=data.get("AdressePostalePere"),
                NomMere=data.get("NomMere"),
                ProfessionMere=data.get("ProfessionMere"),
                TelMere=data.get("TelMere"),
                EmailMere=data.get("EmailMere"),
                EntrepriseMere=data.get("EntrepriseMere"),
                LieuResidenceMere=data.get("LieuResidenceMere"),
                TelBureauMere=data.get("TelBureauMere"),
                TelDomicileMere=data.get("TelDomicileMere"),
                AdressePostaleMere=data.get("AdressePostaleMere"),
                NomTuteur=data.get("NomTuteur"),
                ProfessionTuteur=data.get("ProfessionTuteur"),
                EntrepriseTuteur=data.get("EntrepriseTuteur"),
                CelTuteur=data.get("CelTuteur"),
                EmailTuteur=data.get("EmailTuteur"),
                TelBureauTuteur=data.get("TelBureauTuteur"),
                TelDomicileTuteur=data.get("TelDomicileTuteur"),
                AdressePostaleTuteur=data.get("AdressePostaleTuteur"),
                MotivationChoixEcole=data.get("MotivationChoixEcole"),
                Observations=data.get("Observations"),
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
                return False, "Une autre famille possède déjà ce couple Responsable / Téléphone."

            # Mise à jour des valeurs
            famille.NomResponsable = nom_resp
            famille.QualiteResponsable = data.get("QualiteResponsable", 1)
            famille.ProfessionResponsable = data.get("ProfessionResponsable")
            famille.TypeResponsable = data.get("TypeResponsable")
            famille.NumeroPieceIdentite = data.get("NumeroPieceIdentite")
            famille.AdresseResponsable = data.get("AdresseResponsable")
            famille.CellulaireResponsable = tel_resp
            famille.EmailResponsable = email if email else None
            famille.TelBureauResponsable = data.get("TelBureauResponsable")
            famille.TelDomicileResponsable = data.get("TelDomicileResponsable")
            famille.SIMaitre = data.get("SIMaitre", False)
            # Le formulaire de saisie n'expose plus cette case a cocher ; on
            # preserve la valeur existante (reduction deja accordee) au lieu
            # de la reinitialiser silencieusement a False a chaque edition.
            famille.EbrieAbobote = data.get("EbrieAbobote", famille.EbrieAbobote)
            famille.NomUrgence = data.get("NomUrgence")
            famille.ContactUrgence = data.get("ContactUrgence")
            famille.HabitationUrgence = data.get("HabitationUrgence")
            famille.UrgenceMoimeme = data.get("UrgenceMoimeme", False)
            famille.HabitationParent = data.get("HabitationParent")
            famille.NomPere = data.get("NomPere")
            famille.ProfessionPere = data.get("ProfessionPere")
            famille.TelPere = data.get("TelPere")
            famille.EmailPere = data.get("EmailPere")
            famille.EntreprisePere = data.get("EntreprisePere")
            famille.LieuResidencePere = data.get("LieuResidencePere")
            famille.TelBureauPere = data.get("TelBureauPere")
            famille.TelDomicilePere = data.get("TelDomicilePere")
            famille.AdressePostalePere = data.get("AdressePostalePere")
            famille.NomMere = data.get("NomMere")
            famille.ProfessionMere = data.get("ProfessionMere")
            famille.TelMere = data.get("TelMere")
            famille.EmailMere = data.get("EmailMere")
            famille.EntrepriseMere = data.get("EntrepriseMere")
            famille.LieuResidenceMere = data.get("LieuResidenceMere")
            famille.TelBureauMere = data.get("TelBureauMere")
            famille.TelDomicileMere = data.get("TelDomicileMere")
            famille.AdressePostaleMere = data.get("AdressePostaleMere")
            famille.NomTuteur = data.get("NomTuteur")
            famille.ProfessionTuteur = data.get("ProfessionTuteur")
            famille.EntrepriseTuteur = data.get("EntrepriseTuteur")
            famille.CelTuteur = data.get("CelTuteur")
            famille.EmailTuteur = data.get("EmailTuteur")
            famille.TelBureauTuteur = data.get("TelBureauTuteur")
            famille.TelDomicileTuteur = data.get("TelDomicileTuteur")
            famille.AdressePostaleTuteur = data.get("AdressePostaleTuteur")
            famille.MotivationChoixEcole = data.get("MotivationChoixEcole")
            famille.Observations = data.get("Observations")

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
