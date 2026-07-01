"""
Moteur de calcul de ventilation analytique des prestations annexes.

Règle métier : Affectation en cascade par ordre de priorité (ordre de création
des prestations, IDPrestation croissant). Chaque franc payé par l'élève sert
d'abord à couvrir intégralement la première prestation de la liste, puis la
suivante, etc. Le reliquat éventuel après couverture de toutes les prestations
actives est considéré comme de la scolarité pure.
  montant_restant = total_scol_payé
  pour chaque prestation (ordre de création) :
      montant_ventilé = min(montant_restant, montant_annuel_prestation)
      montant_restant -= montant_ventilé

Le calcul s'appuie sur VersementService.get_infos_financieres_eleve() pour rester
cohérent avec la situation financière affichée à l'utilisateur. Le taux de
paiement global de la scolarité (scol_payé / scol_due) reste calculé et renvoyé
à titre informatif uniquement — il ne sert plus au calcul des montants ventilés.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import and_

from app.database import get_session
from models.ventilation_prestation import VentilationPrestation
from models.prestation_annexe import PrestationAnnexe
from models.inscription import TInscription
from models.eleve import Eleve
from models.classe import TClasse


class VentilationService:

    # ─── Calcul / Recalcul ────────────────────────────────────────────────────

    @staticmethod
    def recalculate_student_ventilation(id_eleve: int, id_annee: int) -> Dict[str, Any]:
        """
        Recalcule et persiste la ventilation analytique des prestations pour un élève.

        Scénarios couverts :
        - 0 paiement          → ventilation = 0 pour toutes prestations
        - Paiement partiel    → couvre les prestations dans l'ordre de création,
                                 la première non couverte reçoit le reliquat,
                                 les suivantes restent à 0
        - Paiement complet    → toutes les prestations sont couvertes à 100 %
        - Sur-paiement        → le surplus au-delà de la dernière prestation
                                 est ignoré (scolarité pure)
        - Scolarité non due   → ventilation = 0 (warning retourné)
        - Prestation inactive → ignorée

        Retourne un dict avec les clés :
          success, montant_scol_due, total_paye, taux_paiement, prestations, [error], [warning]
        """
        from services.versement_service import VersementService

        if not id_eleve or not id_annee:
            return {"success": False, "error": "Identifiants élève / année manquants."}

        # 1. Récupérer la situation financière via le service existant (source unique de vérité)
        fin = VersementService.get_infos_financieres_eleve(id_annee, id_eleve)
        scol_due = fin.get("scol_due", 0.0)
        scol_paye = fin.get("scol_paye", 0.0)  # encaissements réels (hors réductions)

        # 2. Garde-fou division par zéro
        if scol_due <= 0:
            VentilationService._purge_ventilations(id_eleve, id_annee)
            return {
                "success": True,
                "montant_scol_due": 0.0,
                "total_paye": scol_paye,
                "taux_paiement": 0.0,
                "prestations": [],
                "warning": "Montant de scolarité nul ou non configuré — ventilations remises à zéro.",
            }

        # 3. Taux de paiement global de la scolarité — informatif uniquement,
        #    ne sert plus au calcul des montants ventilés (voir cascade ci-dessous)
        taux = min(scol_paye / scol_due, 1.0)

        session = get_session()
        try:
            # 4. Récupérer les prestations actives, ordre de création = ordre de priorité
            prestations = session.query(PrestationAnnexe).filter(
                PrestationAnnexe.IsActive == True
            ).order_by(PrestationAnnexe.IDPrestation.asc()).all()

            # 5. Supprimer les anciennes ventilations de l'élève pour cette année
            session.query(VentilationPrestation).filter(
                VentilationPrestation.IDEleve == id_eleve,
                VentilationPrestation.IDAnneeScolaire == id_annee,
            ).delete(synchronize_session="fetch")

            # 6. Recréer les ventilations actualisées — affectation en cascade :
            #    chaque prestation est couverte intégralement avant de passer à la
            #    suivante, dans l'ordre de création des prestations.
            results = []
            now = datetime.utcnow()
            montant_restant = max(scol_paye, 0.0)
            for p in prestations:
                montant_theorique = float(p.MontantAnnuel)
                montant_ventile = round(min(montant_restant, montant_theorique), 2)
                montant_restant = round(montant_restant - montant_ventile, 2)
                taux_prestation = round(montant_ventile / montant_theorique, 4) if montant_theorique > 0 else 0.0

                session.add(VentilationPrestation(
                    IDEleve=id_eleve,
                    IDPrestation=p.IDPrestation,
                    IDAnneeScolaire=id_annee,
                    MontantVentile=montant_ventile,
                    MontantTheorique=montant_theorique,
                    TauxPaiement=taux_prestation,
                    ModeCalcul="CASCADE",
                    CalculeAt=now,
                ))
                results.append({
                    "prestation_id": p.IDPrestation,
                    "code": p.Code,
                    "prestation": p.Libelle,
                    "montant_theorique": montant_theorique,
                    "montant_ventile": montant_ventile,
                    "taux": taux_prestation,
                })

            session.commit()
            return {
                "success": True,
                "montant_scol_due": scol_due,
                "total_paye": scol_paye,
                "taux_paiement": taux,
                "prestations": results,
            }

        except Exception as e:
            session.rollback()
            print(f"Erreur recalculate_student_ventilation ({id_eleve}/{id_annee}) : {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    @staticmethod
    def _purge_ventilations(id_eleve: int, id_annee: int) -> None:
        """Supprime toutes les ventilations d'un élève pour une année donnée."""
        session = get_session()
        try:
            session.query(VentilationPrestation).filter(
                VentilationPrestation.IDEleve == id_eleve,
                VentilationPrestation.IDAnneeScolaire == id_annee,
            ).delete(synchronize_session="fetch")
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur _purge_ventilations : {e}")
        finally:
            session.close()

    # ─── Consultation ─────────────────────────────────────────────────────────

    @staticmethod
    def get_student_ventilations(id_eleve: int, id_annee: int) -> List[Dict[str, Any]]:
        """Retourne les ventilations actuelles d'un élève pour l'année donnée."""
        session = get_session()
        try:
            rows = (
                session.query(VentilationPrestation, PrestationAnnexe)
                .join(PrestationAnnexe, VentilationPrestation.IDPrestation == PrestationAnnexe.IDPrestation)
                .filter(
                    VentilationPrestation.IDEleve == id_eleve,
                    VentilationPrestation.IDAnneeScolaire == id_annee,
                )
                .order_by(PrestationAnnexe.IDPrestation.asc())
                .all()
            )
            return [
                {
                    "prestation": row.PrestationAnnexe.Libelle,
                    "code": row.PrestationAnnexe.Code,
                    "montant_theorique": float(row.VentilationPrestation.MontantTheorique),
                    "montant_ventile": float(row.VentilationPrestation.MontantVentile),
                    "taux": float(row.VentilationPrestation.TauxPaiement),
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Erreur get_student_ventilations : {e}")
            return []
        finally:
            session.close()

    # ─── Rapport prestataire ──────────────────────────────────────────────────

    @staticmethod
    def get_provider_report(
        id_annee: int,
        id_prestation: Optional[int] = None,
        id_classe: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rapport synthétique par classe et prestation :
        Classe | Prestation | Nb élèves | Montant théorique | Montant ventilé | Reste
        """
        from sqlalchemy import func
        session = get_session()
        try:
            q = (
                session.query(
                    TClasse.LibClasse,
                    PrestationAnnexe.Libelle.label("prestation"),
                    PrestationAnnexe.MontantAnnuel.label("montant_annuel"),
                    func.count(VentilationPrestation.IDEleve.distinct()).label("nb_eleves"),
                    func.sum(VentilationPrestation.MontantTheorique).label("total_theorique"),
                    func.sum(VentilationPrestation.MontantVentile).label("total_ventile"),
                )
                .join(PrestationAnnexe, VentilationPrestation.IDPrestation == PrestationAnnexe.IDPrestation)
                .join(
                    TInscription,
                    and_(
                        TInscription.IDEleve == VentilationPrestation.IDEleve,
                        TInscription.IDTAnneeScolaire == VentilationPrestation.IDAnneeScolaire,
                    ),
                )
                .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)
                .filter(VentilationPrestation.IDAnneeScolaire == id_annee)
            )

            if id_prestation:
                q = q.filter(VentilationPrestation.IDPrestation == id_prestation)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.group_by(TClasse.LibClasse, PrestationAnnexe.Libelle, PrestationAnnexe.MontantAnnuel)
            q = q.order_by(TClasse.LibClasse, PrestationAnnexe.Libelle)

            return [
                {
                    "classe": row.LibClasse,
                    "prestation": row.prestation,
                    "montant_annuel": float(row.montant_annuel),
                    "nb_eleves": row.nb_eleves,
                    "total_theorique": float(row.total_theorique or 0),
                    "total_ventile": float(row.total_ventile or 0),
                    "reste": float(row.total_theorique or 0) - float(row.total_ventile or 0),
                }
                for row in q.all()
            ]
        except Exception as e:
            print(f"Erreur get_provider_report : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_detail_eleves_report(
        id_annee: int,
        id_prestation: Optional[int] = None,
        id_classe: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rapport détaillé élève × prestation :
        Matricule | Nom | Classe | Prestation | Scol due | Total payé | Taux | Montant ventilé | Reste
        """
        from services.versement_service import VersementService
        session = get_session()
        try:
            q = (
                session.query(
                    Eleve.IDEleve,
                    Eleve.Matricule,
                    Eleve.Nom,
                    Eleve.Prenoms,
                    TClasse.LibClasse,
                    PrestationAnnexe.Libelle.label("prestation"),
                    VentilationPrestation.MontantTheorique,
                    VentilationPrestation.MontantVentile,
                    VentilationPrestation.TauxPaiement,
                )
                .join(Eleve, VentilationPrestation.IDEleve == Eleve.IDEleve)
                .join(PrestationAnnexe, VentilationPrestation.IDPrestation == PrestationAnnexe.IDPrestation)
                .join(
                    TInscription,
                    and_(
                        TInscription.IDEleve == VentilationPrestation.IDEleve,
                        TInscription.IDTAnneeScolaire == VentilationPrestation.IDAnneeScolaire,
                    ),
                )
                .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)
                .filter(VentilationPrestation.IDAnneeScolaire == id_annee)
            )

            if id_prestation:
                q = q.filter(VentilationPrestation.IDPrestation == id_prestation)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms, PrestationAnnexe.IDPrestation)

            return [
                {
                    "matricule": row.Matricule,
                    "nom": f"{row.Nom} {row.Prenoms}".strip(),
                    "classe": row.LibClasse,
                    "prestation": row.prestation,
                    "montant_theorique": float(row.MontantTheorique or 0),
                    "montant_ventile": float(row.MontantVentile or 0),
                    "taux": float(row.TauxPaiement or 0),
                    "reste": float(row.MontantTheorique or 0) - float(row.MontantVentile or 0),
                }
                for row in q.all()
            ]
        except Exception as e:
            print(f"Erreur get_detail_eleves_report : {e}")
            return []
        finally:
            session.close()

    # ─── Recalcul global ──────────────────────────────────────────────────────

    @staticmethod
    def recalculate_all_for_annee(id_annee: int) -> Dict[str, Any]:
        """
        Recalcule les ventilations de TOUS les élèves inscrits pour une année scolaire.
        Utile après modification d'une prestation ou d'un tarif de scolarité.
        Retourne un résumé (nb traités, erreurs).
        """
        from services.versement_service import VersementService
        session = get_session()
        try:
            inscriptions = session.query(TInscription).filter(
                TInscription.IDTAnneeScolaire == id_annee
            ).all()
            ids = [(ins.IDEleve, id_annee) for ins in inscriptions]
        finally:
            session.close()

        ok, errors = 0, []
        for id_eleve, id_ann in ids:
            result = VentilationService.recalculate_student_ventilation(id_eleve, id_ann)
            if result.get("success"):
                ok += 1
            else:
                errors.append(f"Élève {id_eleve} : {result.get('error', '?')}")

        return {"traites": ok, "erreurs": len(errors), "detail_erreurs": errors}
