from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from models.inscription import TInscription
from models.eleve import Eleve
from models.annee_scolaire import TAnneeScolaire
from models.montant_scol import MontantScol
from models.montant_transport import MontantTransport
from models.montant_cantine import MontantCantine
from models.montant_autres_frais import MontantAutresFrais
from models.inscription_autres_frais import InscriptionAutresFrais
from models.versement_scol import VersementScol
from models.versement_autres_frais import VersementAutresFrais
from app.database import get_session
from services.tarification_service import TarificationService
import logging
logger = logging.getLogger(__name__)


class VersementService:
    @staticmethod
    def get_eleves_inscrits(id_annee: int) -> List[TInscription]:
        """Recupere les inscriptions actives pour une annee scolaire."""
        if not id_annee:
            return []
        session = get_session()
        try:
            return session.query(TInscription).options(
                joinedload(TInscription.eleve),
                joinedload(TInscription.famille),
                joinedload(TInscription.classe),
                joinedload(TInscription.niveau)
            ).filter(TInscription.IDTAnneeScolaire == id_annee).all()
        except Exception:
            logger.exception("Erreur get_eleves_inscrits")
            return []
        finally:
            session.close()

    @staticmethod
    def search_eleves_inscrits(id_annee: int, query: str) -> List[TInscription]:
        """Filtre les inscriptions de l'annee selon le nom, prenom ou matricule de l'eleve."""
        if not id_annee:
            return []
        if not query or not query.strip():
            return VersementService.get_eleves_inscrits(id_annee)
        
        q_clean = f"%{query.strip().lower()}%"
        session = get_session()
        try:
            return session.query(TInscription).join(TInscription.eleve).options(
                joinedload(TInscription.eleve),
                joinedload(TInscription.famille),
                joinedload(TInscription.classe),
                joinedload(TInscription.niveau)
            ).filter(
                (TInscription.IDTAnneeScolaire == id_annee) & (
                    (Eleve.Nom.ilike(q_clean)) |
                    (Eleve.Prenoms.ilike(q_clean)) |
                    (Eleve.Matricule.ilike(q_clean))
                )
            ).all()
        except Exception:
            logger.exception("Erreur search_eleves_inscrits")
            return []
        finally:
            session.close()

    @staticmethod
    def get_versements_eleve(id_annee: int, id_eleve: int) -> List[VersementScol]:
        """Recupere tous les paiements effectues par un eleve durant une annee scolaire."""
        session = get_session()
        try:
            return session.query(VersementScol).filter(
                (VersementScol.IDTAnneeScolaire == id_annee) & (VersementScol.IDEleve == id_eleve)
            ).order_by(VersementScol.DateVers.desc(), VersementScol.IDVersementScol.desc()).all()
        except Exception:
            logger.exception("Erreur get_versements_eleve")
            return []
        finally:
            session.close()

    @staticmethod
    def get_infos_financieres_eleve(id_annee: int, id_eleve: int) -> Dict[str, Any]:
        """Calcule la situation financiere detaillee de l'eleve (Montants dus, Deja verses et Reste)."""
        res = {
            "scol_due": 0.0, "scol_paye": 0.0, "scol_reduc": 0.0, "scol_reste": 0.0,
            "trans_due": 0.0, "trans_paye": 0.0, "trans_reste": 0.0,
            "cant_due": 0.0, "cant_paye": 0.0, "cant_reste": 0.0,
            "autres_due": 0.0, "autres_paye": 0.0, "autres_reste": 0.0,
            "total_due": 0.0, "total_paye": 0.0, "total_reduc": 0.0, "total_reste": 0.0,
            "options": {"scolarite": False, "transport": False, "cantine": False, "autres": False},
            "id_inscription": None
        }

        if not id_annee or not id_eleve:
            return res

        session = get_session()
        try:
            # 1. Recuperer l'inscription active
            ins = session.query(TInscription).options(
                joinedload(TInscription.famille)
            ).filter(
                (TInscription.IDTAnneeScolaire == id_annee) & (TInscription.IDEleve == id_eleve)
            ).first()

            if not ins:
                return res

            res["id_inscription"] = ins.IDTInscription
            res["options"] = {
                "scolarite": bool(ins.Scolarite),
                "transport": bool(ins.Transport),
                "cantine": bool(ins.Cantine),
                "autres": bool(ins.AutresFrais)
            }

            # 2. Calculer le montant du de Scolarite (regles centralisees : TarificationService)
            if ins.Scolarite:
                m_scol = session.query(MontantScol).filter(
                    (MontantScol.IDTAnneeScolaire == id_annee) & (MontantScol.IDNiveau == ins.IDNiveau)
                ).first()
                rang, nb_famille = TarificationService.get_rang_famille_pour_inscription(session, ins, id_annee)
                res["scol_due"] = TarificationService.calculer_scolarite_due(
                    montant_affecte=m_scol.MontantAffecte if m_scol else 0,
                    montant_non_affecte=m_scol.MontantNonAffecte if m_scol else 0,
                    statut_affectation=ins.StatutAffectation,
                    ebrie_abobote=bool(ins.famille and ins.famille.EbrieAbobote),
                    nouveau=bool(ins.Nouveau),
                    rang_famille=rang,
                    nb_enfants_famille=nb_famille,
                )

            # 3. Calculer le montant du de Transport
            if ins.Transport:
                m_trans = session.query(MontantTransport).filter(
                    (MontantTransport.IDTAnneeScolaire == id_annee) & (MontantTransport.IDNiveau == ins.IDNiveau)
                ).first()
                if m_trans:
                    res["trans_due"] = float(m_trans.Montant)

            # 4. Calculer le montant du de Cantine
            if ins.Cantine:
                m_cant = session.query(MontantCantine).filter(
                    (MontantCantine.IDTAnneeScolaire == id_annee) & (MontantCantine.IDNiveau == ins.IDNiveau)
                ).first()
                if m_cant:
                    res["cant_due"] = float(m_cant.Montant)

            # 5. Calculer le montant du des Autres Frais Annexes
            lignes_autres = session.query(InscriptionAutresFrais).filter(
                InscriptionAutresFrais.IDTInscription == ins.IDTInscription
            ).all()
            if lignes_autres:
                # Frais annexes coches individuellement a l'inscription : montants figes
                res["autres_due"] = sum(float(ligne.MontantApplique) for ligne in lignes_autres)
            elif ins.AutresFrais:
                # Fallback legacy (anciennes inscriptions sans lignes InscriptionAutresFrais) :
                # somme de tous les autres frais configures pour ce niveau
                frais_items = session.query(MontantAutresFrais).filter(
                    (MontantAutresFrais.IDAnneeScolaire == id_annee) & (MontantAutresFrais.IDT_Niveau == ins.IDNiveau)
                ).all()
                res["autres_due"] = sum(float(item.MontantFrais) for item in frais_items)

            # 6. Recuperer les vrais versements (hors reductions)
            totals = session.query(
                func.sum(VersementScol.MontantVersSco),
                func.sum(VersementScol.MontantVersTrans),
                func.sum(VersementScol.MontantCantine),
                func.sum(VersementScol.MontantVersAutres)
            ).filter(
                (VersementScol.IDTAnneeScolaire == id_annee) &
                (VersementScol.IDEleve == id_eleve) &
                (VersementScol.Reduction == False) &
                (VersementScol.Annule == False)
            ).first()

            if totals:
                res["scol_paye"] = float(totals[0]) if totals[0] is not None else 0.0
                res["trans_paye"] = float(totals[1]) if totals[1] is not None else 0.0
                res["cant_paye"] = float(totals[2]) if totals[2] is not None else 0.0
                res["autres_paye"] = float(totals[3]) if totals[3] is not None else 0.0

            # 6b. Recuperer les reductions accordees (diminuent le reste sans etre des versements)
            reductions = session.query(
                func.sum(VersementScol.MontantVersSco),
                func.sum(VersementScol.MontantVersTrans),
                func.sum(VersementScol.MontantCantine),
                func.sum(VersementScol.MontantVersAutres)
            ).filter(
                (VersementScol.IDTAnneeScolaire == id_annee) &
                (VersementScol.IDEleve == id_eleve) &
                (VersementScol.Reduction == True) &
                (VersementScol.Annule == False)
            ).first()

            scol_reduc   = float(reductions[0]) if reductions and reductions[0] is not None else 0.0
            trans_reduc  = float(reductions[1]) if reductions and reductions[1] is not None else 0.0
            cant_reduc   = float(reductions[2]) if reductions and reductions[2] is not None else 0.0
            autres_reduc = float(reductions[3]) if reductions and reductions[3] is not None else 0.0

            res["scol_reduc"]  = scol_reduc
            res["total_reduc"] = scol_reduc + trans_reduc + cant_reduc + autres_reduc

            # 7. Formuler les totaux et restants (reductions deduites du reste, pas des verses)
            res["scol_reste"]   = max(0.0, res["scol_due"]   - res["scol_paye"]   - scol_reduc)
            res["trans_reste"]  = max(0.0, res["trans_due"]  - res["trans_paye"]  - trans_reduc)
            res["cant_reste"]   = max(0.0, res["cant_due"]   - res["cant_paye"]   - cant_reduc)
            res["autres_reste"] = max(0.0, res["autres_due"] - res["autres_paye"] - autres_reduc)

            res["total_due"]   = res["scol_due"]   + res["trans_due"]   + res["cant_due"]   + res["autres_due"]
            res["total_paye"]  = res["scol_paye"]  + res["trans_paye"]  + res["cant_paye"]  + res["autres_paye"]
            res["total_reste"] = res["scol_reste"] + res["trans_reste"] + res["cant_reste"] + res["autres_reste"]

        except Exception:
            logger.exception("Erreur get_infos_financieres_eleve")
        finally:
            session.close()

        return res

    @staticmethod
    def create_versement(
        id_annee: int,
        id_eleve: int,
        id_famille: int,
        date_v: date,
        m_scol: float,
        m_trans: float,
        m_cant: float,
        m_autres: float,
        reduction: bool = False,
        impaye: bool = False,
        restitution: bool = False,
        login: str = "ADMIN",
        ids_autres_frais: Optional[List[int]] = None,
    ) -> tuple[bool, str, Optional[int]]:
        """Enregistre un versement dans la table VersementScol après validations métier.

        ids_autres_frais : IDInscriptionAutresFrais des frais annexes que ce versement solde.
        Chacun est lie au versement via VersementAutresFrais, ce qui le retire ensuite de la
        liste des frais encore a verser proposee a la caisse.
        """
        if not id_annee:
            return False, "Aucune annee scolaire active.", None
        if not id_eleve or not id_famille:
            return False, "Eleve et famille responsables sont obligatoires.", None
        if m_scol < 0 or m_trans < 0 or m_cant < 0 or m_autres < 0:
            return False, "Les montants verses ne peuvent pas être negatifs.", None
        if m_scol + m_trans + m_cant + m_autres == 0:
            return False, "Le total du versement doit être superieur a 0 FCFA.", None

        ids_autres_frais = list({i for i in (ids_autres_frais or []) if i})

        session = get_session()
        try:
            # Verifier si l'annee est cloturee
            annee = session.get(TAnneeScolaire, id_annee)
            if not annee:
                return False, "Annee scolaire introuvable.", None
            if annee.Cloturer:
                return False, "Impossible de versement : L'annee scolaire active est cloturee.", None

            # Verrouille l'inscription de cet eleve pour cette annee : serialise les
            # versements concurrents sur le meme eleve (deux caisses simultanees), pour
            # qu'aucune des deux ne lise un "reste a payer" perime avant l'autre.
            ins_lock = session.query(TInscription).filter(
                TInscription.IDTAnneeScolaire == id_annee,
                TInscription.IDEleve == id_eleve,
            ).with_for_update().first()
            if not ins_lock:
                return False, "Inscription introuvable pour cet eleve sur cette annee.", None

            # Valider les plafonds de paiement par rapport aux restes a payer (sauf si restitution est coché)
            if not restitution:
                fin = VersementService.get_infos_financieres_eleve(id_annee, id_eleve)
                if m_scol > fin["scol_reste"]:
                    return False, f"Le versement scolarite ({m_scol} F) depasse le reste a payer ({fin['scol_reste']} F).", None
                if m_trans > fin["trans_reste"]:
                    return False, f"Le versement transport ({m_trans} F) depasse le reste a payer ({fin['trans_reste']} F).", None
                if m_cant > fin["cant_reste"]:
                    return False, f"Le versement cantine ({m_cant} F) depasse le reste a payer ({fin['cant_reste']} F).", None
                if m_autres > fin["autres_reste"]:
                    return False, f"Le versement autres frais ({m_autres} F) depasse le reste a payer ({fin['autres_reste']} F).", None

            # Validation des frais annexes selectionnes : existent, non deja regles, et
            # leur somme correspond bien au montant "autres frais" du versement.
            lignes_autres_frais = []
            if ids_autres_frais:
                lignes_autres_frais = session.query(InscriptionAutresFrais).filter(
                    InscriptionAutresFrais.IDInscriptionAutresFrais.in_(ids_autres_frais)
                ).all()
                ids_trouves = {ligne.IDInscriptionAutresFrais for ligne in lignes_autres_frais}
                ids_invalides = set(ids_autres_frais) - ids_trouves
                if ids_invalides:
                    return False, f"Frais annexe(s) introuvable(s) : {sorted(ids_invalides)}.", None

                deja_regles = session.query(VersementAutresFrais.IDInscriptionAutresFrais).filter(
                    VersementAutresFrais.IDInscriptionAutresFrais.in_(ids_autres_frais)
                ).all()
                if deja_regles:
                    return False, "Un ou plusieurs frais annexes selectionnes ont deja ete regles par un autre versement.", None

                total_frais = sum(float(ligne.MontantApplique) for ligne in lignes_autres_frais)
                if abs(total_frais - m_autres) > 0.01:
                    return False, "Le montant des autres frais ne correspond pas aux frais annexes selectionnes.", None

            # Enregistrement
            n_vers = VersementScol(
                IDTAnneeScolaire=id_annee,
                IDEleve=id_eleve,
                IDFamille=id_famille,
                DateVers=date_v,
                MontantVersSco=m_scol,
                MontantVersTrans=m_trans,
                MontantCantine=m_cant,
                MontantVersAutres=m_autres,
                Reduction=reduction,
                Impaye=impaye,
                Restitution=restitution,
                Login=login
            )

            session.add(n_vers)
            session.flush()  # attribue IDVersementScol avant de lier les frais annexes

            for ligne in lignes_autres_frais:
                session.add(VersementAutresFrais(
                    IDVersementScol=n_vers.IDVersementScol,
                    IDInscriptionAutresFrais=ligne.IDInscriptionAutresFrais,
                ))

            session.commit()
            new_id = n_vers.IDVersementScol

        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement de versement : {str(e)}", None
        finally:
            session.close()

        return True, "Versement enregistre avec succes !", new_id

    @staticmethod
    def annuler_versement(
        id_versement: int, motif: str, login: str = "ADMIN", id_utilisateur: Optional[int] = None
    ) -> tuple[bool, str]:
        """Annule un versement (piste d'audit conservee) au lieu de le supprimer
        physiquement. Un versement annule reste visible dans l'historique mais est
        exclu du calcul du reste a payer et des agregations comptables."""
        if not motif or not motif.strip():
            return False, "Le motif d'annulation est obligatoire."

        session = get_session()
        try:
            v = session.get(VersementScol, id_versement)
            if not v:
                return False, "Versement introuvable."
            if v.Annule:
                return False, "Ce versement est deja annule."

            # Verifier si l'annee est cloturee
            annee = session.get(TAnneeScolaire, v.IDTAnneeScolaire)
            if annee and annee.Cloturer:
                return False, "Impossible d'annuler un versement appartenant a une annee cloturee."

            ancien_montant_scol = str(v.MontantVersSco)
            v.Annule = True
            v.AnnulePar = login
            v.DateAnnulation = datetime.now()
            v.MotifAnnulation = motif.strip()
            session.commit()

            from services.audit_log_service import AuditLogService
            AuditLogService.log(
                action="ANNULER_VERSEMENT", table_cible="VersementScol", id_cible=id_versement,
                id_utilisateur=id_utilisateur, ancienne_valeur=f"MontantVersSco={ancien_montant_scol}",
                nouvelle_valeur="Annule=True", motif=motif.strip(),
            )

        except Exception as e:
            session.rollback()
            return False, f"Erreur : {e}"
        finally:
            session.close()

        return True, "Versement annulé avec succès !"
