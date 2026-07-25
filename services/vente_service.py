import datetime
import uuid
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.orm import joinedload
from models.article import Article
from models.kit_article import KitArticle
from models.stock_cour import StockCour
from models.vente import Vente, VenteLigne
from app.database import get_session
from services.authorization import permission_denied
import logging
logger = logging.getLogger(__name__)


class VenteService:
    @staticmethod
    def process_sale(cart: dict, id_annee: int, login: str, mode_paiement: str = "Espèce") -> Tuple[bool, str, Optional[dict]]:
        """
        Enregistre une vente multi-articles en une seule transaction : verrouille
        (SELECT ... FOR UPDATE) les lignes de stock concernees, verifie toutes les
        quantites, puis debite tous les stocks et cree la Vente (entete) + une
        VenteLigne par article/KIT en un seul commit. Aucune ecriture partielle
        en cas d'echec, et le verrouillage empeche deux ventes concurrentes de
        survendre le meme stock (comportement herite de l'ancien
        StockService.process_sale, garanties B2/B3 preservees).

        Un KIT (D3) n'a plus sa propre ligne de stock : sa vente decompte le
        stock de ses composants (KitArticle), multiplie par la quantite de
        KITs vendus. Les besoins de tous les KITs et articles simples du
        panier sont fusionnes en un seul total par composant reellement
        stocke avant verrouillage, pour que le meme composant vendu a la
        fois seul et via un ou plusieurs KITs ne soit decompte qu'une fois.

        cart : {id_article: {"qte": int, "pu": float, "nom": str (optionnel, pour les messages)}}

        Retourne (ok, message, recu). recu est un dict pret pour l'impression
        (numero_recu, id_vente, total, date, heure, mode_paiement, lignes) si
        ok, sinon None.
        """
        if not cart:
            return False, "Le panier est vide.", None
        if not id_annee:
            return False, "Aucune annee scolaire active n'est configuree.", None

        session = get_session()
        try:
            erreurs_qte = []
            for id_art, info in cart.items():
                if info["qte"] <= 0:
                    nom = info.get("nom", f"Article #{id_art}")
                    erreurs_qte.append(f"- {nom} : quantite invalide.")
            if erreurs_qte:
                session.rollback()
                return False, "Vente annulee, stock insuffisant :\n" + "\n".join(erreurs_qte), None

            articles = session.query(Article).filter(Article.IDTArticle.in_(cart.keys())).all()
            articles_par_id = {a.IDTArticle: a for a in articles}

            # Fusionne les besoins reels (composants de KITs + articles simples
            # vendus tels quels) en un seul total par article reellement stocke.
            besoins: dict[int, dict] = {}
            for id_art, info in cart.items():
                art = articles_par_id.get(id_art)
                if art and art.KIT:
                    lignes_kit = session.query(KitArticle).options(
                        joinedload(KitArticle.composant)
                    ).filter_by(IDKit=id_art).all()
                    for ligne in lignes_kit:
                        besoin = besoins.setdefault(ligne.IDArticleComposant, {"qte": 0, "libelles": set()})
                        besoin["qte"] += ligne.Quantite * info["qte"]
                        besoin["libelles"].add(ligne.composant.Libelle if ligne.composant else f"Article #{ligne.IDArticleComposant}")
                else:
                    besoin = besoins.setdefault(id_art, {"qte": 0, "libelles": set()})
                    besoin["qte"] += info["qte"]
                    besoin["libelles"].add(info.get("nom", f"Article #{id_art}"))

            stocks = (
                session.query(StockCour)
                .filter(StockCour.IDTArticle.in_(besoins.keys()))
                .with_for_update()
                .all()
            )
            stock_par_article = {s.IDTArticle: s for s in stocks}

            erreurs = []
            for id_composant, besoin in besoins.items():
                sc = stock_par_article.get(id_composant)
                dispo = sc.QuantiteCour if sc else 0
                if besoin["qte"] > dispo:
                    nom = " / ".join(sorted(besoin["libelles"]))
                    erreurs.append(f"- {nom} : demande {besoin['qte']}, disponible {dispo}.")

            if erreurs:
                session.rollback()
                return False, "Vente annulee, stock insuffisant :\n" + "\n".join(erreurs), None

            now_time = datetime.datetime.now().time()
            today = datetime.date.today()
            montant_total = sum(Decimal(str(info["pu"])) * info["qte"] for info in cart.values())

            # NumeroRecu depend du IDVente reellement attribue (auto-increment) :
            # placeholder unique le temps du flush, remplace juste apres.
            vente = Vente(
                IDTAnneeScolaire=id_annee,
                NumeroRecu=f"T{uuid.uuid4().hex[:18]}",  # placeholder <= 20 car., remplace juste apres le flush
                DateVente=today,
                HeureVente=now_time,
                ModePaiement=mode_paiement or "Espèce",
                MontantTotal=montant_total,
                Login=login,
            )
            session.add(vente)
            session.flush()
            vente.NumeroRecu = f"V-{vente.IDVente:06d}"

            # Debit des composants reellement stockes.
            for id_composant, besoin in besoins.items():
                stock_par_article[id_composant].QuantiteCour -= besoin["qte"]

            # Une VenteLigne par entree du panier d'origine (KIT ou article
            # simple), jamais une ligne par composant : le recu montre
            # "1 x Kit Rentree", pas le detail interne de ses composants.
            lignes_recu = []
            for id_art, info in cart.items():
                pu = Decimal(str(info["pu"]))
                qte = info["qte"]
                ligne_total = pu * qte
                session.add(VenteLigne(
                    IDVente=vente.IDVente,
                    IDTArticle=id_art,
                    Quantite=qte,
                    PrixUnitaire=pu,
                    Total=ligne_total,
                ))
                lignes_recu.append({
                    "nom": info.get("nom", f"Article #{id_art}"),
                    "qte": qte,
                    "pu": float(pu),
                    "total": float(ligne_total),
                })

            session.commit()
            recu = {
                "id_vente": vente.IDVente,
                "numero_recu": vente.NumeroRecu,
                "total": float(montant_total),
                "date": today,
                "heure": now_time,
                "mode_paiement": vente.ModePaiement,
                "login": login,
                "lignes": lignes_recu,
            }
            return True, f"Vente finalisee avec succes ! {len(cart)} article(s)/KIT(s) debite(s) des stocks.", recu
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement de la vente : {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def annuler_vente(
        id_vente: int, motif: str, login: str = "ADMIN", id_utilisateur: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Annule une vente (piste d'audit conservee) au lieu de la supprimer
        physiquement. Une vente annulee reste visible dans l'historique mais
        est exclue des agregations financieres (dashboard, comptabilite).

        Ne restitue PAS automatiquement le stock decompte au moment de la
        vente : meme choix que B7 pour les versements/mouvements, l'annulation
        tracee suffit a la traçabilite ; une restitution de stock est une
        decision metier distincte (rebus, casse... pas systematique), hors
        perimetre ici."""
        denied = permission_denied("KIOSQUE_VENTES", "annuler une vente")
        if denied:
            return denied
        if not motif or not motif.strip():
            return False, "Le motif d'annulation est obligatoire."

        session = get_session()
        try:
            v = session.get(Vente, id_vente)
            if not v:
                return False, "Vente introuvable."
            if v.Annule:
                return False, "Cette vente est deja annulee."

            ancien_montant = str(v.MontantTotal)
            v.Annule = True
            v.AnnulePar = login
            v.DateAnnulation = datetime.datetime.now()
            v.MotifAnnulation = motif.strip()
            session.commit()

            from services.audit_log_service import AuditLogService
            AuditLogService.log(
                action="ANNULER_VENTE", table_cible="Vente", id_cible=id_vente,
                id_utilisateur=id_utilisateur, ancienne_valeur=f"MontantTotal={ancien_montant}",
                nouvelle_valeur="Annule=True", motif=motif.strip(),
            )
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {e}"
        finally:
            session.close()

        return True, "Vente annulée avec succès !"
