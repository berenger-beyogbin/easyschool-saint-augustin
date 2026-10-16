from typing import Optional
from sqlalchemy.orm import joinedload
from app.database import get_session
from models.inscription import TInscription
from models.classe import TClasse
from models.eleve import Eleve
from models.famille import TFamille
from models.annee_scolaire import TAnneeScolaire
from models.montant_scol import MontantScol
from models.versement_scol import VersementScol
from services.tarification_service import TarificationService
from app.session import AppSession
from datetime import date

STATUTS_AFFECTATION_VALIDES = ("AFFECTE_ETAT", "NON_AFFECTE_ETAT")

MSG_BLOQUE_PAR_PAIEMENT = (
    "Le niveau ou le statut d'affectation ne peut plus etre modifie "
    "apres un paiement de scolarite."
)

class InscriptionService:
    """
    Service d'inscription des élèves dans l'année scolaire active.
    """
    MSG_BLOQUE_PAR_PAIEMENT = MSG_BLOQUE_PAR_PAIEMENT

    @staticmethod
    def _get_classe_for_capacity_update(session, id_classe: int):
        """Verrouille la classe cible jusqu'a la fin de la transaction.

        Les inscriptions concurrentes visant la meme classe calculent ainsi
        leur effectif l'une apres l'autre, apres le commit precedent.
        """
        return session.query(TClasse).filter_by(IDTClasse=id_classe).with_for_update().first()

    @staticmethod
    def _calculer_montant_scolarite(session, id_annee: int, id_niveau: int, statut: str) -> float:
        tarif = session.query(MontantScol).filter_by(
            IDTAnneeScolaire=id_annee,
            IDNiveau=id_niveau,
        ).first()
        return TarificationService.calculer_scolarite_due(
            montant_affecte=tarif.MontantAffecte if tarif else 0,
            montant_non_affecte=tarif.MontantNonAffecte if tarif else 0,
            statut_affectation=statut,
        )

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
            id_niveau = data.get("IDNiveau")
            id_classe = data.get("IDClasse")

            if not id_eleve:
                return False, "Veuillez sélectionner un élève."
            if not id_niveau:
                return False, "Veuillez sélectionner un niveau scolaire."
            if not id_classe:
                return False, "Veuillez sélectionner une classe."

            # La famille de l'inscription est TOUJOURS derivee de la fiche
            # elève (Eleve.IDFamille), jamais acceptee telle quelle depuis
            # l'UI : un IDFamille arbitraire transmis dans le payload ne peut
            # que servir de verification de coherence, pas de source de
            # verite (audit parcours "eleve d'abord").
            eleve = session.get(Eleve, id_eleve)
            if not eleve:
                return False, "Élève introuvable."
            if not eleve.IDFamille:
                return False, "Cet élève n'a pas de famille associée. Veuillez associer une famille avant l'inscription."
            id_famille = eleve.IDFamille

            payload_id_famille = data.get("IDFamille")
            if payload_id_famille is not None and payload_id_famille != id_famille:
                return False, "La famille transmise ne correspond pas à la famille associée à l'élève."

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
            classe = InscriptionService._get_classe_for_capacity_update(session, id_classe)
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
                MontantScolariteApplique=InscriptionService._calculer_montant_scolarite(
                    session, id_annee, id_niveau, statut_affectation
                ),
                Login=AppSession.get_logged_in_username(),
                DateInscription=date.today()
            )

            session.add(nouvelle_inscription)
            session.flush()
            from services.inscription_autres_frais_service import InscriptionAutresFraisService
            InscriptionAutresFraisService.synchroniser_frais_obligatoires_session(
                session, nouvelle_inscription, AppSession.get_logged_in_username()
            )
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
    def get_situation_scolaire_active(id_eleve: int, id_annee: int) -> dict | None:
        """Situation scolaire d'un élève pour une année donnée, prête pour l'UI
        (parcours "élève d'abord" — préremplissage du bloc affectation).

        Retourne un dict simple (jamais un objet SQLAlchemy détaché) ou None
        si l'élève n'a pas d'inscription cette année-là. Charge lui-même
        l'effectif/capacité de la classe pour éviter un aller-retour
        supplémentaire depuis la vue.
        """
        if not id_eleve or not id_annee:
            return None
        session = get_session()
        try:
            ins = session.query(TInscription).options(
                joinedload(TInscription.niveau),
                joinedload(TInscription.classe),
            ).filter_by(IDEleve=id_eleve, IDTAnneeScolaire=id_annee).first()
            if not ins:
                return None

            effectif = session.query(TInscription).filter_by(
                IDClasse=ins.IDClasse, IDTAnneeScolaire=id_annee
            ).count()
            capacite = ins.classe.Capacite if ins.classe and ins.classe.Capacite else 40

            return {
                "id_inscription": ins.IDTInscription,
                "id_niveau": ins.IDNiveau,
                "id_classe": ins.IDClasse,
                "niveau_libelle": ins.niveau.Libelle if ins.niveau else "",
                "classe_libelle": ins.classe.LibClasse if ins.classe else "",
                "statut_affectation": ins.StatutAffectation,
                "nouveau": bool(ins.Nouveau),
                "scolarite": bool(ins.Scolarite),
                "transport": bool(ins.Transport),
                "cantine": bool(ins.Cantine),
                "autres_frais": bool(ins.AutresFrais),
                "date_inscription": ins.DateInscription,
                "id_famille": ins.IDFamille,
                "effectif": effectif,
                "capacite": capacite,
            }
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

            tarif_change = (
                id_niveau != inscription.IDNiveau
                or statut_affectation != inscription.StatutAffectation
            )
            if tarif_change:
                paiement_scolarite = session.query(VersementScol.IDVersementScol).filter(
                    VersementScol.IDTAnneeScolaire == inscription.IDTAnneeScolaire,
                    VersementScol.IDEleve == inscription.IDEleve,
                    VersementScol.MontantVersSco > 0,
                    VersementScol.Annule == False,
                ).first()
                if paiement_scolarite:
                    return False, MSG_BLOQUE_PAR_PAIEMENT

            # Vérifier la capacité uniquement si la classe change
            if id_classe != inscription.IDClasse:
                classe = InscriptionService._get_classe_for_capacity_update(session, id_classe)
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
            if tarif_change or inscription.MontantScolariteApplique is None:
                inscription.MontantScolariteApplique = InscriptionService._calculer_montant_scolarite(
                    session, inscription.IDTAnneeScolaire, id_niveau, statut_affectation
                )

            from services.inscription_autres_frais_service import InscriptionAutresFraisService
            InscriptionAutresFraisService.synchroniser_frais_obligatoires_session(
                session, inscription, AppSession.get_logged_in_username()
            )

            session.commit()
            return True, "L'inscription a été modifiée avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la modification : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_obstacles_suppression(id_inscription: int) -> list[str]:
        """Raisons qui empechent de supprimer une inscription (liste vide =
        suppression possible). Versements non annules (scolarite, cantine,
        frais annexes) et dossier d'internat lie bloquent : l'utilisateur doit
        d'abord les annuler de facon tracee."""
        from models.internat import InscriptionInternat
        session = get_session()
        try:
            ins = session.get(TInscription, id_inscription)
            if not ins:
                return ["Inscription introuvable."]
            obstacles = []
            nb_versements = session.query(VersementScol).filter(
                VersementScol.IDTAnneeScolaire == ins.IDTAnneeScolaire,
                VersementScol.IDEleve == ins.IDEleve,
                VersementScol.Annule == False,
            ).count()
            if nb_versements:
                obstacles.append(
                    f"{nb_versements} versement(s) actif(s) existent pour cet eleve : "
                    "annulez-les d'abord depuis l'onglet Versements."
                )
            if session.query(InscriptionInternat.IDInscriptionInternat).filter_by(
                IDTInscription=id_inscription
            ).first():
                obstacles.append("Un dossier d'internat est lie a cette inscription.")
            return obstacles
        finally:
            session.close()

    @staticmethod
    def supprimer_inscription(
        id_inscription: int, motif: str, id_utilisateur: Optional[int] = None
    ) -> tuple[bool, str]:
        """Supprime definitivement une inscription (erreur de saisie) avec
        piste d'audit. Refuse si des versements actifs ou un dossier
        d'internat y sont rattaches, ou si l'annee est cloturee."""
        from services.authorization import permission_denied
        denied = permission_denied("SCOLARITE_INSCRIPTIONS", "supprimer une inscription")
        if denied:
            return denied
        if not motif or not motif.strip():
            return False, "Le motif de la suppression est obligatoire."

        obstacles = InscriptionService.get_obstacles_suppression(id_inscription)
        if obstacles:
            return False, "Suppression impossible :\n- " + "\n- ".join(obstacles)

        session = get_session()
        try:
            ins = session.get(TInscription, id_inscription)
            if not ins:
                return False, "Inscription introuvable."
            annee = session.get(TAnneeScolaire, ins.IDTAnneeScolaire)
            if not annee or annee.Cloturer:
                return False, "Impossible de supprimer une inscription d'une annee cloturee."

            ancienne = (
                f"IDEleve={ins.IDEleve}; IDClasse={ins.IDClasse}; IDNiveau={ins.IDNiveau}; "
                f"Annee={ins.IDTAnneeScolaire}; Statut={ins.StatutAffectation}; "
                f"MontantScolarite={ins.MontantScolariteApplique}"
            )
            # InscriptionAutresFrais (et ses liens) partent en cascade FK.
            session.delete(ins)
            session.commit()
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la suppression : {e}"
        finally:
            session.close()

        from services.audit_log_service import AuditLogService
        AuditLogService.log(
            action="SUPPRIMER_INSCRIPTION", table_cible="TInscription", id_cible=id_inscription,
            id_utilisateur=id_utilisateur, ancienne_valeur=ancienne, motif=motif.strip(),
        )
        return True, "L'inscription a ete supprimee."

    @staticmethod
    def get_versements_scolarite_bloquants(id_inscription: int) -> list:
        """Versements de scolarité actifs (non annulés) qui bloquent un
        changement de niveau/statut d'affectation pour cette inscription
        (même filtre que le contrôle dans update_inscription, mais renvoie
        tous les versements concernés au lieu de s'arrêter au premier)."""
        session = get_session()
        try:
            inscription = session.get(TInscription, id_inscription)
            if not inscription:
                return []
            return session.query(VersementScol).filter(
                VersementScol.IDTAnneeScolaire == inscription.IDTAnneeScolaire,
                VersementScol.IDEleve == inscription.IDEleve,
                VersementScol.MontantVersSco > 0,
                VersementScol.Annule == False,
            ).all()
        finally:
            session.close()

    @staticmethod
    def corriger_inscription_avec_annulation(
        id_inscription: int, data: dict, motif: str, login: str, id_utilisateur: Optional[int] = None
    ) -> tuple[bool, str]:
        """Corrige une inscription bloquée par un paiement en annulant
        d'abord, de façon tracée, les versements de scolarité concernés
        (réutilise VersementService.annuler_versement : permission
        SCOLARITE_VERSEMENTS, blocage année clôturée, piste d'audit), puis
        applique la correction via update_inscription."""
        if not motif or not motif.strip():
            return False, "Le motif de la correction est obligatoire."

        versements = InscriptionService.get_versements_scolarite_bloquants(id_inscription)
        if not versements:
            return InscriptionService.update_inscription(id_inscription, data)

        from services.versement_service import VersementService

        annules = []
        for v in versements:
            ok, msg = VersementService.annuler_versement(
                v.IDVersementScol, motif, login=login, id_utilisateur=id_utilisateur
            )
            if not ok:
                return False, (
                    f"Correction interrompue après annulation de {len(annules)} versement(s) : {msg}\n"
                    "Vérifiez l'état des versements avant de réessayer."
                )
            annules.append(v.IDVersementScol)

        ok, msg = InscriptionService.update_inscription(id_inscription, data)
        if not ok:
            return False, (
                f"{len(annules)} versement(s) annulé(s) mais la correction de l'inscription a échoué : {msg}\n"
                "Les versements annulés restent annulés (piste d'audit) ; contactez un administrateur."
            )
        return True, (
            f"Inscription corrigée avec succès. {len(annules)} versement(s) de scolarité "
            "ont été annulés (motif enregistré) — pensez à ressaisir le ou les paiements corrects."
        )

    @staticmethod
    def synchroniser_famille_inscription_active(id_inscription: int, id_famille: int) -> tuple[bool, str]:
        """Met à jour IDFamille sur UNE inscription précise (l'inscription
        active de l'année en cours), uniquement à la demande explicite de
        l'utilisateur après confirmation dans l'UI (voir EleveService.
        associer_famille).

        Règle documentée (audit parcours "élève d'abord") : n'affecte jamais
        les inscriptions d'années antérieures, ni les versements déjà
        enregistrés — VersementScol.IDFamille garde la valeur historique au
        moment du paiement, jamais réécrite rétroactivement.
        """
        if not id_inscription or not id_famille:
            return False, "Inscription et famille sont obligatoires."
        session = get_session()
        try:
            ins = session.get(TInscription, id_inscription)
            if not ins:
                return False, "Inscription introuvable."
            famille = session.get(TFamille, id_famille)
            if not famille:
                return False, "Famille introuvable."
            ins.IDFamille = id_famille
            session.commit()
            return True, "Famille de l'inscription active mise à jour."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {e}"
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
