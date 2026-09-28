from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.database import get_session
from app.session import AppSession
from models.inscription import TInscription
from models.famille import TFamille
from models.classe import TClasse
from models.versement_scol import VersementScol
from models.montant_scol import MontantScol
from models.vente import Vente, VenteLigne
from models.article import Article
from models.kit_article import KitArticle
from models.stock_cour import StockCour
from models.sortie_fin import SortieFin
from models.internat import InscriptionInternat, VersementInternat
from models.cantine_externe import InscriptionCantine, VersementCantine
from services.tarification_service import TarificationService
from models.etablissement import EtablissementEcole
import logging
logger = logging.getLogger(__name__)



class DashboardService:

    @staticmethod
    def format_fcfa(montant) -> str:
        if montant is None:
            return "0 F"
        try:
            val = int(float(montant))
            formatted = f"{val:,}".replace(",", " ")
            return f"{formatted} F"
        except (ValueError, TypeError):
            return "0 F"

    @staticmethod
    def get_active_school_year_label() -> str:
        try:
            return AppSession.get_active_annee_libelle() or "Aucune année active"
        except Exception:
            return "Aucune année active"

    @staticmethod
    def get_etablissement_info() -> dict:
        session = get_session()
        try:
            etab = session.query(EtablissementEcole).first()
            if not etab:
                return {"nom": "Établissement non configuré", "sigle": "", "localite": "", "telephone": ""}
            return {
                "nom": etab.RaisonSociale or "",
                "sigle": etab.Sigle or "",
                "localite": etab.Localite or "",
                "telephone": etab.Telephone or "",
            }
        except Exception:
            logger.exception("Erreur get_etablissement_info")
            return {"nom": "Erreur chargement", "sigle": "", "localite": "", "telephone": ""}
        finally:
            session.close()

    @staticmethod
    def get_dashboard_summary() -> dict:
        defaults = {
            "total_inscrits": 0,
            "total_nouveaux": 0,
            "total_classes": 0,
            "total_familles": 0,
            "total_pensionnaires": 0,
            "total_attendu_internat": Decimal("0"),
            "total_reste_internat": Decimal("0"),
            "total_versements_scolarite": Decimal("0"),
            "total_attendu_scolarite": Decimal("0"),
            "total_versements_cantine": Decimal("0"),
            "total_versements_transport": Decimal("0"),
            "total_versements_internat": Decimal("0"),
            "total_attendu_cantine_externe": Decimal("0"),
            "total_versements_cantine_externe": Decimal("0"),
            "total_reste_cantine_externe": Decimal("0"),
            "total_ventes_kiosque": Decimal("0"),
            "total_depenses": Decimal("0"),
            "total_recettes": Decimal("0"),
            "solde_net": Decimal("0"),
        }
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return defaults

        session = get_session()
        try:
            total_inscrits = session.query(
                func.count(TInscription.IDTInscription)
            ).filter(TInscription.IDTAnneeScolaire == id_annee).scalar() or 0

            total_nouveaux = session.query(
                func.count(TInscription.IDTInscription)
            ).filter(
                TInscription.IDTAnneeScolaire == id_annee,
                TInscription.Nouveau == True
            ).scalar() or 0

            total_classes = session.query(
                func.count(TClasse.IDTClasse)
            ).filter(TClasse.IDAnneeScolaire == id_annee).scalar() or 0

            total_familles = session.query(
                func.count(TFamille.IdTFamille)
            ).scalar() or 0

            total_pensionnaires = session.query(
                func.count(InscriptionInternat.IDInscriptionInternat)
            ).filter(
                InscriptionInternat.IDTAnneeScolaire == id_annee,
                InscriptionInternat.Statut != "SORTIE",
            ).scalar() or 0

            total_attendu_internat = session.query(
                func.sum(InscriptionInternat.MontantAnnuel)
            ).filter(
                InscriptionInternat.IDTAnneeScolaire == id_annee,
                InscriptionInternat.Statut != "SORTIE",
            ).scalar() or Decimal("0")

            total_versements_scolarite = session.query(
                func.sum(VersementScol.MontantVersSco)
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False,
            ).scalar() or Decimal("0")

            total_versements_cantine = session.query(
                func.sum(VersementScol.MontantCantine)
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False,
            ).scalar() or Decimal("0")

            total_versements_transport = session.query(
                func.sum(VersementScol.MontantVersTrans)
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False,
            ).scalar() or Decimal("0")

            montants_scolarite = {
                row.IDNiveau: row
                for row in session.query(MontantScol).filter(
                    MontantScol.IDTAnneeScolaire == id_annee
                ).all()
            }
            total_attendu_scolarite = Decimal("0")
            inscriptions_scolarite = session.query(TInscription).filter(
                TInscription.IDTAnneeScolaire == id_annee,
                TInscription.Scolarite == True,
            ).all()
            for inscription in inscriptions_scolarite:
                if inscription.MontantScolariteApplique is not None:
                    montant_du = inscription.MontantScolariteApplique
                else:
                    tarif = montants_scolarite.get(inscription.IDNiveau)
                    montant_du = Decimal(str(TarificationService.calculer_scolarite_due(
                        montant_affecte=tarif.MontantAffecte if tarif else 0,
                        montant_non_affecte=tarif.MontantNonAffecte if tarif else 0,
                        statut_affectation=inscription.StatutAffectation,
                    )))
                total_attendu_scolarite += Decimal(str(montant_du or 0))

            total_versements_internat = session.query(
                func.sum(VersementInternat.Montant)
            ).join(
                InscriptionInternat,
                VersementInternat.IDInscriptionInternat == InscriptionInternat.IDInscriptionInternat,
            ).filter(
                InscriptionInternat.IDTAnneeScolaire == id_annee,
                VersementInternat.Annule == False,
            ).scalar() or Decimal("0")

            total_attendu_cantine_externe = session.query(
                func.sum(InscriptionCantine.MontantTotal)
            ).filter(
                InscriptionCantine.IDTAnneeScolaire == id_annee,
                InscriptionCantine.Statut != "SORTIE",
            ).scalar() or Decimal("0")

            total_versements_cantine_externe = session.query(
                func.sum(VersementCantine.Montant)
            ).join(
                InscriptionCantine,
                VersementCantine.IDInscriptionCantine == InscriptionCantine.IDInscriptionCantine,
            ).filter(
                InscriptionCantine.IDTAnneeScolaire == id_annee,
                VersementCantine.Annule == False,
            ).scalar() or Decimal("0")

            total_versements_autres = session.query(
                func.sum(VersementScol.MontantVersAutres)
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False,
            ).scalar() or Decimal("0")

            total_ventes_kiosque = session.query(
                func.sum(Vente.MontantTotal)
            ).filter(
                Vente.IDTAnneeScolaire == id_annee,
                Vente.Annule == False,
            ).scalar() or Decimal("0")

            total_depenses = session.query(
                func.sum(SortieFin.Montant)
            ).filter(
                SortieFin.IDAnSco == id_annee,
                SortieFin.DebitCredit == "Debit",
                SortieFin.Annule == False,
            ).scalar() or Decimal("0")

            total_recettes = (
                total_versements_scolarite
                + total_versements_cantine
                + total_versements_transport
                + total_versements_autres
                + total_versements_internat
                + total_versements_cantine_externe
                + total_ventes_kiosque
            )
            total_reste_internat = max(Decimal("0"), total_attendu_internat - total_versements_internat)
            total_reste_cantine_externe = max(
                Decimal("0"), total_attendu_cantine_externe - total_versements_cantine_externe
            )
            solde_net = total_recettes - total_depenses

            return {
                "total_inscrits": total_inscrits,
                "total_nouveaux": total_nouveaux,
                "total_classes": total_classes,
                "total_familles": total_familles,
                "total_pensionnaires": total_pensionnaires,
                "total_attendu_internat": total_attendu_internat,
                "total_reste_internat": total_reste_internat,
                "total_versements_scolarite": total_versements_scolarite,
                "total_attendu_scolarite": total_attendu_scolarite,
                "total_versements_cantine": total_versements_cantine,
                "total_versements_transport": total_versements_transport,
                "total_versements_internat": total_versements_internat,
                "total_attendu_cantine_externe": total_attendu_cantine_externe,
                "total_versements_cantine_externe": total_versements_cantine_externe,
                "total_reste_cantine_externe": total_reste_cantine_externe,
                "total_ventes_kiosque": total_ventes_kiosque,
                "total_depenses": total_depenses,
                "total_recettes": total_recettes,
                "solde_net": solde_net,
            }
        except Exception:
            logger.exception("Erreur get_dashboard_summary")
            return defaults
        finally:
            session.close()

    @staticmethod
    def get_latest_inscriptions(limit=5) -> list:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []
        session = get_session()
        try:
            rows = session.query(TInscription).options(
                joinedload(TInscription.eleve),
                joinedload(TInscription.classe),
            ).filter(
                TInscription.IDTAnneeScolaire == id_annee
            ).order_by(
                TInscription.DateInscription.desc(),
                TInscription.IDTInscription.desc()
            ).limit(limit).all()

            result = []
            for ins in rows:
                date_str = ins.DateInscription.strftime("%d/%m/%Y") if ins.DateInscription else ""
                matricule = ins.eleve.Matricule if ins.eleve else ""
                nom_eleve = f"{ins.eleve.Nom} {ins.eleve.Prenoms}" if ins.eleve else ""
                classe = ins.classe.LibClasse if ins.classe else ""
                result.append({
                    "date": date_str,
                    "matricule": matricule,
                    "eleve": nom_eleve,
                    "classe": classe,
                })
            return result
        except Exception:
            logger.exception("Erreur get_latest_inscriptions")
            return []
        finally:
            session.close()

    @staticmethod
    def get_latest_versements(limit=5) -> list:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []
        session = get_session()
        try:
            rows = session.query(VersementScol).options(
                joinedload(VersementScol.eleve),
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee
            ).order_by(
                VersementScol.DateVers.desc(),
                VersementScol.IDVersementScol.desc()
            ).limit(limit).all()

            result = []
            for v in rows:
                date_str = v.DateVers.strftime("%d/%m/%Y") if v.DateVers else ""
                nom_eleve = f"{v.eleve.Nom} {v.eleve.Prenoms}" if v.eleve else ""
                matricule = v.eleve.Matricule if v.eleve else ""
                result.append({
                    "date": date_str,
                    "matricule": matricule,
                    "eleve": nom_eleve,
                    "scolarite": DashboardService.format_fcfa(v.MontantVersSco),
                    "cantine": DashboardService.format_fcfa(v.MontantCantine),
                    "transport": DashboardService.format_fcfa(v.MontantVersTrans),
                })
            return result
        except Exception:
            logger.exception("Erreur get_latest_versements")
            return []
        finally:
            session.close()

    @staticmethod
    def get_latest_ventes(limit=5) -> list:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []
        session = get_session()
        try:
            rows = session.query(VenteLigne).options(
                joinedload(VenteLigne.article),
                joinedload(VenteLigne.vente),
            ).join(Vente, VenteLigne.IDVente == Vente.IDVente).filter(
                Vente.IDTAnneeScolaire == id_annee
            ).order_by(
                Vente.DateVente.desc(),
                Vente.HeureVente.desc(),
                VenteLigne.IDVenteLigne.desc(),
            ).limit(limit).all()

            result = []
            for ligne in rows:
                date_str = ligne.vente.DateVente.strftime("%d/%m/%Y") if ligne.vente and ligne.vente.DateVente else ""
                article = ligne.article.Libelle if ligne.article else ""
                result.append({
                    "date": date_str,
                    "article": article,
                    "quantite": str(ligne.Quantite or 0),
                    "montant": DashboardService.format_fcfa(float(ligne.Total or 0)),
                })
            return result
        except Exception:
            logger.exception("Erreur get_latest_ventes")
            return []
        finally:
            session.close()

    @staticmethod
    def get_stock_alerts(limit=10) -> list:
        session = get_session()
        try:
            result = []

            rows = session.query(StockCour).options(
                joinedload(StockCour.article),
            ).join(StockCour.article).filter(
                Article.KIT == False,
                StockCour.QuantiteCour <= Article.QTESeuil,
            ).limit(limit).all()
            for sc in rows:
                article_nom = sc.article.Libelle if sc.article else ""
                seuil = sc.article.QTESeuil if sc.article else 0
                result.append({
                    "article": article_nom,
                    "stock": sc.QuantiteCour,
                    "seuil": seuil,
                })

            # Un KIT n'a plus de ligne de stock propre depuis D3 : son alerte
            # se calcule a partir du stock deduit de ses composants.
            if len(result) < limit:
                kits = session.query(Article).filter(Article.KIT == True).all()
                stocks_simples = {s.IDTArticle: s.QuantiteCour for s in session.query(StockCour).all()}
                for kit in kits:
                    lignes = session.query(KitArticle).filter_by(IDKit=kit.IDTArticle).all()
                    if not lignes:
                        continue
                    dispo = max(0, min(
                        stocks_simples.get(ligne.IDArticleComposant, 0) // ligne.Quantite
                        for ligne in lignes
                    ))
                    if dispo <= kit.QTESeuil:
                        result.append({"article": kit.Libelle, "stock": dispo, "seuil": kit.QTESeuil})
                        if len(result) >= limit:
                            break

            return result
        except Exception:
            logger.exception("Erreur get_stock_alerts")
            return []
        finally:
            session.close()

    @staticmethod
    def get_internat_alerts() -> dict:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return {"dossiers_incomplets": 0, "reste": 0}
        try:
            from services.internat_service import InternatService
            stats = InternatService.dashboard(id_annee)
            return {
                "dossiers_incomplets": stats.get("dossiers_incomplets", 0),
                "reste": stats.get("reste", 0),
            }
        except Exception:
            logger.exception("Erreur get_internat_alerts")
            return {"dossiers_incomplets": 0, "reste": 0}

    @staticmethod
    def get_classes_capacity_alerts(limit=10) -> list:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []
        session = get_session()
        try:
            effectifs_sq = session.query(
                TInscription.IDClasse,
                func.count(TInscription.IDTInscription).label("effectif")
            ).filter(
                TInscription.IDTAnneeScolaire == id_annee
            ).group_by(TInscription.IDClasse).subquery()

            rows = session.query(TClasse, effectifs_sq.c.effectif).outerjoin(
                effectifs_sq, TClasse.IDTClasse == effectifs_sq.c.IDClasse
            ).filter(
                TClasse.IDAnneeScolaire == id_annee
            ).all()

            result = []
            for classe, effectif in rows:
                effectif = effectif or 0
                capacite = classe.Capacite or 40
                if capacite > 0 and effectif >= (capacite * 0.9):
                    pct = int(effectif / capacite * 100)
                    result.append({
                        "classe": classe.LibClasse,
                        "effectif": effectif,
                        "capacite": capacite,
                        "pct": pct,
                    })

            result.sort(key=lambda x: x["pct"], reverse=True)
            return result[:limit]
        except Exception:
            logger.exception("Erreur get_classes_capacity_alerts")
            return []
        finally:
            session.close()

    @staticmethod
    def get_impayes_scolarite(limit=10) -> list:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []
        session = get_session()
        try:
            inscriptions = session.query(TInscription).options(
                joinedload(TInscription.eleve),
                joinedload(TInscription.classe),
                joinedload(TInscription.famille),
            ).filter(
                TInscription.IDTAnneeScolaire == id_annee,
                TInscription.Scolarite == True,
            ).all()

            if not inscriptions:
                return []

            montants_scol = session.query(MontantScol).filter(
                MontantScol.IDTAnneeScolaire == id_annee
            ).all()
            montants_par_niveau = {m.IDNiveau: m for m in montants_scol}

            versements = session.query(
                VersementScol.IDEleve,
                func.coalesce(func.sum(VersementScol.MontantVersSco), 0).label("total_verse")
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False,
            ).group_by(VersementScol.IDEleve).all()

            verses_par_eleve = {v.IDEleve: float(v.total_verse) for v in versements}

            result = []
            for ins in inscriptions:
                m_scol = montants_par_niveau.get(ins.IDNiveau)
                if ins.MontantScolariteApplique is None and not m_scol:
                    continue
                montant_du = float(ins.MontantScolariteApplique) if ins.MontantScolariteApplique is not None else (
                    TarificationService.calculer_scolarite_due(
                        montant_affecte=m_scol.MontantAffecte,
                        montant_non_affecte=m_scol.MontantNonAffecte,
                        statut_affectation=ins.StatutAffectation,
                    )
                )
                if montant_du == 0:
                    continue
                total_verse = verses_par_eleve.get(ins.IDEleve, 0)
                reste = montant_du - total_verse
                if reste > 0:
                    nom_eleve = f"{ins.eleve.Nom} {ins.eleve.Prenoms}" if ins.eleve else ""
                    classe = ins.classe.LibClasse if ins.classe else ""
                    result.append({
                        "eleve": nom_eleve,
                        "classe": classe,
                        "du": DashboardService.format_fcfa(montant_du),
                        "verse": DashboardService.format_fcfa(total_verse),
                        "reste": DashboardService.format_fcfa(reste),
                        "_reste_raw": reste,
                    })

            result.sort(key=lambda x: x["_reste_raw"], reverse=True)
            for r in result:
                r.pop("_reste_raw", None)
            return result[:limit]
        except Exception:
            logger.exception("Erreur get_impayes_scolarite")
            return []
        finally:
            session.close()
