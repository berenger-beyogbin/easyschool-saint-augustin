from app.database import get_session
from models.inscription import TInscription
from models.classe import TClasse
from models.eleve import Eleve
from models.famille import TFamille
from models.annee_scolaire import TAnneeScolaire
from app.session import AppSession
from datetime import date

STATUTS_AFFECTATION_VALIDES = ("AFFECTE_ETAT", "NON_AFFECTE_ETAT")

class InscriptionService:
    """
    Service d'inscription des élèves dans l'année scolaire active.
    """

    @staticmethod
    def get_inscriptions_by_annee(id_annee: int) -> list[TInscription]:
        """Récupère toutes les inscriptions d'une année donnée."""
        session = get_session()
        try:
            return session.query(TInscription).filter_by(IDTAnneeScolaire=id_annee).all()
        finally:
            session.close()

    @staticmethod
    def is_eleve_inscrit(id_eleve: int, id_annee: int) -> bool:
        """Indique si un élève est déjà inscrit pour cette année scolaire."""
        session = get_session()
        try:
            inscrip = session.query(TInscription).filter_by(
                IDEleve=id_eleve,
                IDTAnneeScolaire=id_annee
            ).first()
            return inscrip is not None
        finally:
            session.close()

    @staticmethod
    def get_effectif_classe(id_classe: int, id_annee: int) -> int:
        """Compte les élèves inscrits dans une classe pour une année scolaire donnée."""
        session = get_session()
        try:
            return session.query(TInscription).filter_by(
                IDClasse=id_classe,
                IDTAnneeScolaire=id_annee
            ).count()
        finally:
            session.close()

    @staticmethod
    def validate_classe_capacity(id_classe: int, id_annee: int) -> tuple[bool, str]:
        """
        Vérifie si la classe sélectionnée dispose de places disponibles
        par rapport à sa capacité maximale programmée.
        """
        session = get_session()
        try:
            classe = session.get(TClasse, id_classe)
            if not classe:
                return False, "La classe spécifiée n'existe pas."
                
            effectif = session.query(TInscription).filter_by(
                IDClasse=id_classe,
                IDTAnneeScolaire=id_annee
            ).count()
            
            capacity = classe.Capacite if classe.Capacite else 40
            
            if effectif >= capacity:
                return False, f"La capacité maximale de cette classe ({capacity} élèves) est déjà atteinte."
            return True, "Capacité suffisante."
        finally:
            session.close()

    @staticmethod
    def create_inscription(data: dict) -> tuple[bool, str]:
        """
        Inscrit un élève dans une classe pour l'année scolaire active.
        """
        # Obtenir l'année active
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return False, "Aucune session d'année scolaire active."

        session = get_session()
        try:
            # 1. Vérifier si l'année est clôturée
            annee = session.get(TAnneeScolaire, id_annee)
            if not annee or annee.Cloturer:
                return False, "L'année active est clôturée. Impossible d'y inscrire des élèves."

            # Extraction
            id_eleve = data.get("IDEleve")
            id_famille = data.get("IDFamille")
            id_niveau = data.get("IDNiveau")
            id_classe = data.get("IDClasse")

            if not id_eleve:
                return False, "Veuillez sélectionner un élève."
            if not id_famille:
                return False, "Aucune famille / parent n'est associé à cette opération."
            if not id_niveau:
                return False, "Veuillez sélectionner un niveau scolaire."
            if not id_classe:
                return False, "Veuillez sélectionner une classe."

            statut_affectation = data.get("StatutAffectation") or "AFFECTE_ETAT"
            if statut_affectation not in STATUTS_AFFECTATION_VALIDES:
                return False, "Statut d'affectation invalide."

            # 2. Vérifier si l'élève est déjà inscrit pour cette année scolaire
            doublon = session.query(TInscription).filter_by(
                IDEleve=id_eleve,
                IDTAnneeScolaire=id_annee
            ).first()
            if doublon:
                return False, "Cet élève possède déjà une inscription pour cette année scolaire."

            # 3. Vérifier la capacité de la classe
            classe = session.get(TClasse, id_classe)
            if not classe:
                return False, "La classe sélectionnée est inconnue."
                
            effectif = session.query(TInscription).filter_by(
                IDClasse=id_classe,
                IDTAnneeScolaire=id_annee
            ).count()
            
            capacite = classe.Capacite if classe.Capacite else 40
            if effectif >= capacite:
                return False, f"Impossible d'inscrire l'élève : l'effectif actuel ({effectif}) a atteint la capacité maximale ({capacite}) de cette classe."

            # 4. Enregistrement de l'inscription
            # TODO: remplacer par l'utilisateur authentifié lorsque le module de connexion sera finalisé.
            nouvelle_inscription = TInscription(
                IDTAnneeScolaire=id_annee,
                IDFamille=id_famille,
                IDEleve=id_eleve,
                IDNiveau=id_niveau,
                IDClasse=id_classe,
                Nouveau=data.get("Nouveau", True),
                Scolarite=data.get("Scolarite", True),
                Transport=data.get("Transport", False),
                Cantine=data.get("Cantine", False),
                AutresFrais=data.get("AutresFrais", False),
                StatutAffectation=statut_affectation,
                Login=AppSession.get_logged_in_username(),
                DateInscription=date.today()
            )
            
            # Si l'élève n'était pas associé à cette famille, on met à jour sa fiche
            eleve = session.get(Eleve, id_eleve)
            if eleve and eleve.IDFamille != id_famille:
                eleve.IDFamille = id_famille

            session.add(nouvelle_inscription)
            session.commit()
            return True, "L'élève a été inscrit avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'inscription : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_inscription_by_eleve_annee(id_eleve: int, id_annee: int):
        """Retourne l'inscription d'un élève pour une année scolaire donnée, ou None."""
        session = get_session()
        try:
            return session.query(TInscription).filter_by(
                IDEleve=id_eleve,
                IDTAnneeScolaire=id_annee
            ).first()
        finally:
            session.close()

    @staticmethod
    def get_inscriptions_by_eleves(eleve_ids: list, id_annee: int) -> dict:
        """Retourne {id_eleve: TInscription} pour une liste d'élèves et une année."""
        if not eleve_ids:
            return {}
        session = get_session()
        try:
            inscrips = session.query(TInscription).filter(
                TInscription.IDEleve.in_(eleve_ids),
                TInscription.IDTAnneeScolaire == id_annee
            ).all()
            result = {}
            for insc in inscrips:
                # Force-load des attributs colonnes avant fermeture de session
                _ = (insc.IDTInscription, insc.IDNiveau, insc.IDClasse,
                     insc.Nouveau, insc.Scolarite, insc.Transport,
                     insc.Cantine, insc.AutresFrais)
                result[insc.IDEleve] = insc
            return result
        finally:
            session.close()

    @staticmethod
    def update_inscription(id_inscription: int, data: dict) -> tuple[bool, str]:
        """Modifie une inscription existante (niveau, classe et options)."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return False, "Aucune session d'année scolaire active."

        session = get_session()
        try:
            annee = session.get(TAnneeScolaire, id_annee)
            if not annee or annee.Cloturer:
                return False, "L'année active est clôturée. Impossible de modifier l'inscription."

            inscription = session.get(TInscription, id_inscription)
            if not inscription:
                return False, "L'inscription à modifier est introuvable."

            id_niveau = data.get("IDNiveau")
            id_classe = data.get("IDClasse")
            if not id_niveau:
                return False, "Veuillez sélectionner un niveau scolaire."
            if not id_classe:
                return False, "Veuillez sélectionner une classe."

            statut_affectation = data.get("StatutAffectation", inscription.StatutAffectation)
            if statut_affectation not in STATUTS_AFFECTATION_VALIDES:
                return False, "Statut d'affectation invalide."

            # Vérifier la capacité uniquement si la classe change
            if id_classe != inscription.IDClasse:
                classe = session.get(TClasse, id_classe)
                if not classe:
                    return False, "La classe sélectionnée est inconnue."
                effectif = session.query(TInscription).filter_by(
                    IDClasse=id_classe,
                    IDTAnneeScolaire=id_annee
                ).count()
                capacite = classe.Capacite if classe.Capacite else 40
                if effectif >= capacite:
                    return False, (
                        f"Impossible de modifier : l'effectif actuel ({effectif}) a atteint "
                        f"la capacité maximale ({capacite}) de cette classe."
                    )

            inscription.IDNiveau = id_niveau
            inscription.IDClasse = id_classe
            inscription.Nouveau = data.get("Nouveau", inscription.Nouveau)
            inscription.Scolarite = data.get("Scolarite", inscription.Scolarite)
            inscription.Transport = data.get("Transport", inscription.Transport)
            inscription.Cantine = data.get("Cantine", inscription.Cantine)
            inscription.AutresFrais = data.get("AutresFrais", inscription.AutresFrais)
            inscription.StatutAffectation = statut_affectation

            session.commit()
            return True, "L'inscription a été modifiée avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la modification : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_familles_for_inscription() -> list[TFamille]:
        """Récupère les familles triées, destinées au tableau d'inscription (gauche)."""
        session = get_session()
        try:
            return session.query(TFamille).order_by(TFamille.NomResponsable.asc()).all()
        finally:
            session.close()
