import datetime
from typing import List, Optional, Any
from sqlalchemy import func
from app.database import get_session
from app.session import AppSession

class StatistiquesService:
    @staticmethod
    def get_inscrits(id_niveau: Optional[int] = None, id_classe: Optional[int] = None) -> List[dict]:
        """Retourne la liste des élèves inscrits dans l'année active."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse
            from models.niveau import TNiveau

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .join(TNiveau, TInscription.IDNiveau == TNiveau.IDT_Niveau)\
                                          .options(joinedload(TInscription.eleve), joinedload(TInscription.classe), joinedload(TInscription.niveau))\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms)
            results = q.all()

            lst = []
            for ins in results:
                lst.append({
                    "DateInscription": ins.DateInscription,
                    "Matricule": ins.eleve.MatriculeNational or ins.eleve.Matricule,
                    "Nom": ins.eleve.Nom,
                    "Prenoms": ins.eleve.Prenoms,
                    "DateNaissance": ins.eleve.DateNaissance,
                    "LibClasse": ins.classe.LibClasse,
                    "LibNiveau": ins.niveau.Libelle,
                })
            return lst
        except Exception as e:
            print(f"Error in get_inscrits: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_nouveaux_inscrits(id_utilisateur: Optional[str] = None, id_niveau: Optional[int] = None, id_classe: Optional[int] = None) -> List[dict]:
        """Retourne les inscriptions avec Nouveau = True dans l'année active."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .options(joinedload(TInscription.eleve), joinedload(TInscription.classe))\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee, TInscription.Nouveau == True)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)
            if id_utilisateur:
                q = q.filter(TInscription.Login == id_utilisateur)

            q = q.order_by(TInscription.DateInscription.desc(), Eleve.Nom, Eleve.Prenoms)
            results = q.all()

            lst = []
            for ins in results:
                lst.append({
                    "DateInscription": ins.DateInscription,
                    "Matricule": ins.eleve.MatriculeNational or ins.eleve.Matricule,
                    "Nom": ins.eleve.Nom,
                    "Prenoms": ins.eleve.Prenoms,
                    "DateNaissance": ins.eleve.DateNaissance,
                    "LibClasse": ins.classe.LibClasse,
                    "Login": ins.Login
                })
            return lst
        except Exception as e:
            print(f"Error in get_nouveaux_inscrits: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_versements_scolarite(id_niveau: Optional[int] = None, id_classe: Optional[int] = None) -> List[dict]:
        """Retourne l'état des paiements de scolarité par élève."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse
            from models.montant_scol import MontantScol
            from models.versement_scol import VersementScol
            from services.tarification_service import TarificationService

            # Enseignant/famille categorisation possible
            # 1. Recuperer tous les tarifs de cette annee
            montants = session.query(MontantScol).filter(MontantScol.IDTAnneeScolaire == id_annee).all()
            montants_map = {m.IDNiveau: m for m in montants}

            # 2a. Cumul des vrais versements (Reduction=False)
            versements_sums = session.query(
                VersementScol.IDEleve,
                func.sum(VersementScol.MontantVersSco).label("vers_sum"),
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False,
            ).group_by(VersementScol.IDEleve).all()

            versements_map = {v[0]: float(v[1]) if v[1] is not None else 0.0 for v in versements_sums}

            # 2b. Cumul des reductions accordees (Reduction=True)
            reductions_sums = session.query(
                VersementScol.IDEleve,
                func.sum(VersementScol.MontantVersSco).label("reduc_sum"),
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == True,
                VersementScol.Annule == False,
            ).group_by(VersementScol.IDEleve).all()

            reductions_map = {v[0]: float(v[1]) if v[1] is not None else 0.0 for v in reductions_sums}

            # 3. Récupérer les inscriptions
            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .options(joinedload(TInscription.eleve), joinedload(TInscription.classe), joinedload(TInscription.famille))\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms)
            inscriptions = q.all()

            lst = []
            for ins in inscriptions:
                # Calcul montant du (regles centralisees : TarificationService)
                scol_due = 0.0
                if ins.Scolarite:
                    m_scol = montants_map.get(ins.IDNiveau)
                    scol_due = float(ins.MontantScolariteApplique) if ins.MontantScolariteApplique is not None else (
                        TarificationService.calculer_scolarite_due(
                            montant_affecte=m_scol.MontantAffecte if m_scol else 0,
                            montant_non_affecte=m_scol.MontantNonAffecte if m_scol else 0,
                            statut_affectation=ins.StatutAffectation,
                        )
                    )

                scol_vers  = versements_map.get(ins.IDEleve, 0.0)
                scol_reduc = reductions_map.get(ins.IDEleve, 0.0)
                reste = max(0.0, scol_due - scol_vers - scol_reduc)

                total_couvert = scol_vers + scol_reduc
                if total_couvert >= scol_due and scol_due > 0:
                    etat = "Payé"
                elif total_couvert > 0:
                    etat = "Partiel"
                else:
                    etat = "Impayé"

                lst.append({
                    "Matricule": ins.eleve.MatriculeNational or ins.eleve.Matricule,
                    "Nom": f"{ins.eleve.Nom} {ins.eleve.Prenoms}",
                    "LibClasse": ins.classe.LibClasse,
                    "MontantDu": scol_due,
                    "MontantVerse": scol_vers,
                    "Reduction": scol_reduc,
                    "Reste": reste,
                    "Etat": etat
                })
            return lst
        except Exception as e:
            print(f"Error in get_etat_versements_scolarite: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_versements_cantine(id_niveau: Optional[int] = None, id_classe: Optional[int] = None) -> List[dict]:
        """Retourne l'état des paiements de cantine par élève."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse
            from models.montant_cantine import MontantCantine
            from models.versement_scol import VersementScol

            montants_cantine = session.query(MontantCantine).filter(MontantCantine.IDTAnneeScolaire == id_annee).all()
            cantine_map = {m.IDNiveau: m for m in montants_cantine}

            payments_sums = session.query(
                VersementScol.IDEleve,
                func.sum(VersementScol.MontantCantine).label("cant_sum")
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Annule == False,
            ).group_by(VersementScol.IDEleve).all()

            payments_map = {p[0]: float(p[1]) if p[1] is not None else 0.0 for p in payments_sums}

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .options(joinedload(TInscription.eleve), joinedload(TInscription.classe))\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee, TInscription.Cantine == True)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms)
            inscriptions = q.all()

            lst = []
            for ins in inscriptions:
                m_cant = cantine_map.get(ins.IDNiveau)
                cant_due = float(m_cant.Montant) if m_cant else 0.0
                cant_vers = payments_map.get(ins.IDEleve, 0.0)
                reste = max(0.0, cant_due - cant_vers)

                if cant_vers >= cant_due and cant_due > 0:
                    etat = "Payé"
                elif cant_vers > 0:
                    etat = "Partiel"
                else:
                    etat = "Impayé"

                lst.append({
                    "Matricule": ins.eleve.MatriculeNational or ins.eleve.Matricule,
                    "Nom": f"{ins.eleve.Nom} {ins.eleve.Prenoms}",
                    "LibClasse": ins.classe.LibClasse,
                    "MontantDu": cant_due,
                    "MontantVerse": cant_vers,
                    "Reste": reste,
                    "Etat": etat
                })
            return lst
        except Exception as e:
            print(f"Error in get_etat_versements_cantine: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_versements_transport(id_niveau: Optional[int] = None, id_classe: Optional[int] = None) -> List[dict]:
        """Retourne l'état des paiements de transport par élève."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse
            from models.montant_transport import MontantTransport
            from models.versement_scol import VersementScol

            montants_trans = session.query(MontantTransport).filter(MontantTransport.IDTAnneeScolaire == id_annee).all()
            trans_map = {m.IDNiveau: m for m in montants_trans}

            payments_sums = session.query(
                VersementScol.IDEleve,
                func.sum(VersementScol.MontantVersTrans).label("trans_sum")
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Annule == False,
            ).group_by(VersementScol.IDEleve).all()

            payments_map = {p[0]: float(p[1]) if p[1] is not None else 0.0 for p in payments_sums}

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .options(joinedload(TInscription.eleve), joinedload(TInscription.classe))\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee, TInscription.Transport == True)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms)
            inscriptions = q.all()

            lst = []
            for ins in inscriptions:
                m_trans = trans_map.get(ins.IDNiveau)
                trans_due = float(m_trans.Montant) if m_trans else 0.0
                trans_vers = payments_map.get(ins.IDEleve, 0.0)
                reste = max(0.0, trans_due - trans_vers)

                if trans_vers >= trans_due and trans_due > 0:
                    etat = "Payé"
                elif trans_vers > 0:
                    etat = "Partiel"
                else:
                    etat = "Impayé"

                lst.append({
                    "Matricule": ins.eleve.MatriculeNational or ins.eleve.Matricule,
                    "Nom": f"{ins.eleve.Nom} {ins.eleve.Prenoms}",
                    "LibClasse": ins.classe.LibClasse,
                    "MontantDu": trans_due,
                    "MontantVerse": trans_vers,
                    "Reste": reste,
                    "Etat": etat
                })
            return lst
        except Exception as e:
            print(f"Error in get_etat_versements_transport: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_ventes(date_debut: Optional[datetime.date] = None, date_fin: Optional[datetime.date] = None) -> List[dict]:
        """Retourne les ventes kiosque sur une période."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.vente import Vente, VenteLigne

            q = session.query(VenteLigne).options(
                joinedload(VenteLigne.vente), joinedload(VenteLigne.article)
            ).join(Vente, VenteLigne.IDVente == Vente.IDVente).filter(
                Vente.IDTAnneeScolaire == id_annee
            )
            if date_debut:
                q = q.filter(Vente.DateVente >= date_debut)
            if date_fin:
                q = q.filter(Vente.DateVente <= date_fin)

            q = q.order_by(Vente.DateVente.desc(), Vente.HeureVente.desc(), VenteLigne.IDVenteLigne.desc())
            results = q.all()

            lst = []
            for ligne in results:
                lst.append({
                    "DateSort": ligne.vente.DateVente,
                    "HeureSortie": ligne.vente.HeureVente,
                    "Article": ligne.article.Libelle,
                    "QuantiteSort": ligne.Quantite,
                    "Prix_vente": float(ligne.PrixUnitaire),
                    "Total": float(ligne.Total),
                    "Login": ligne.vente.Login,
                    # Champs additionnels (D2), utilises par stat_vente_view.py
                    # pour l'annulation et l'affichage du recu :
                    "IDVente": ligne.IDVente,
                    "NumeroRecu": ligne.vente.NumeroRecu,
                    "ModePaiement": ligne.vente.ModePaiement,
                    "Annule": ligne.vente.Annule,
                })
            return lst
        except Exception as e:
            print(f"Error in get_etat_ventes: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_stock() -> List[dict]:
        """Retourne l'état du stock courant."""
        session = get_session()
        try:
            from models.article import Article
            from models.kit_article import KitArticle
            from models.stock_cour import StockCour

            articles = session.query(Article).order_by(Article.Libelle.asc()).all()
            stocks_simples = {s.IDTArticle: s.QuantiteCour for s in session.query(StockCour).all()}

            lst = []
            for art in articles:
                if art.KIT:
                    # Un KIT n'a plus de ligne de stock propre depuis D3 : sa
                    # quantite vendable est deduite du stock de ses composants.
                    lignes = session.query(KitArticle).filter_by(IDKit=art.IDTArticle).all()
                    if not lignes:
                        qty = 0
                    else:
                        qty = max(0, min(
                            stocks_simples.get(ligne.IDArticleComposant, 0) // ligne.Quantite
                            for ligne in lignes
                        ))
                else:
                    qty = stocks_simples.get(art.IDTArticle, 0)
                pu = float(art.PU)
                seuil = int(art.QTESeuil) if art.QTESeuil is not None else 0
                val_stock = qty * pu

                if qty == 0:
                    etat = "Rupture"
                elif qty <= seuil:
                    etat = "Alerte"
                else:
                    etat = "OK"

                lst.append({
                    "Libelle": art.Libelle,
                    "PU": pu,
                    "QTESeuil": seuil,
                    "KIT": bool(art.KIT),
                    "QuantiteCour": qty,
                    "ValeurStock": val_stock,
                    "Etat": etat
                })
            return lst
        except Exception as e:
            print(f"Error in get_etat_stock: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_liste_alphabetique(id_niveau: Optional[int] = None, id_classe: Optional[int] = None) -> List[dict]:
        """Retourne la liste alphabétique des élèves inscrits (classe/niveau), avec contact du responsable légal."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .options(joinedload(TInscription.eleve), joinedload(TInscription.classe), joinedload(TInscription.famille))\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms)
            results = q.all()

            lst = []
            for ins in results:
                famille = ins.famille
                lst.append({
                    "Matricule": ins.eleve.MatriculeNational or ins.eleve.Matricule,
                    "Nom": ins.eleve.Nom,
                    "Prenoms": ins.eleve.Prenoms,
                    "DateNaissance": ins.eleve.DateNaissance,
                    "Sexe": ins.eleve.Sexe,
                    "LibClasse": ins.classe.LibClasse,
                    "Profession": famille.ProfessionResponsable if famille else "",
                    "Telephone": famille.CellulaireResponsable if famille else "",
                })
            return lst
        except Exception as e:
            print(f"Error in get_liste_alphabetique: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_niveaux() -> List[dict]:
        """Retourne les niveaux disponibles."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from models.niveau import TNiveau
            results = session.query(TNiveau).filter(TNiveau.IDAnneeScolaire == id_annee).order_by(TNiveau.Libelle.asc()).all()
            return [{"IDT_Niveau": n.IDT_Niveau, "Libelle": n.Libelle} for n in results]
        except Exception as e:
            print(f"Error in get_niveaux: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_classes_by_niveau(id_niveau: Optional[int] = None) -> List[dict]:
        """Retourne les classes filtrées par niveau."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from models.classe import TClasse
            q = session.query(TClasse).filter(TClasse.IDAnneeScolaire == id_annee)
            if id_niveau:
                q = q.filter(TClasse.IDT_Niveau == id_niveau)
            results = q.order_by(TClasse.LibClasse.asc()).all()
            return [{"IDTClasse": c.IDTClasse, "LibClasse": c.LibClasse} for c in results]
        except Exception as e:
            print(f"Error in get_classes_by_niveau: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_utilisateurs_inscriptions() -> List[str]:
        """Retourne la liste des logins uniques ayant enregistré des inscriptions."""
        session = get_session()
        try:
            from models.inscription import TInscription
            results = session.query(TInscription.Login).distinct().filter(TInscription.Login != None).all()
            return [r[0] for r in results if r[0]]
        except Exception as e:
            print(f"Error in get_utilisateurs_inscriptions: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_versements_internat() -> List[dict]:
        """Retourne l'état financier de chaque pensionnaire de l'année active."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            from models.classe import TClasse
            from models.eleve import Eleve
            from models.inscription import TInscription
            from models.internat import InscriptionInternat, VersementInternat

            versements = session.query(
                VersementInternat.IDInscriptionInternat.label("id_internat"),
                func.sum(VersementInternat.Montant).label("total_verse"),
            ).filter(
                VersementInternat.Annule.is_(False)
            ).group_by(VersementInternat.IDInscriptionInternat).subquery()

            rows = session.query(
                InscriptionInternat,
                Eleve,
                TClasse.LibClasse,
                func.coalesce(versements.c.total_verse, 0),
            ).join(
                Eleve, InscriptionInternat.IDEleve == Eleve.IDEleve
            ).outerjoin(
                TInscription,
                InscriptionInternat.IDTInscription == TInscription.IDTInscription,
            ).outerjoin(
                TClasse, TInscription.IDClasse == TClasse.IDTClasse,
            ).outerjoin(
                versements,
                versements.c.id_internat == InscriptionInternat.IDInscriptionInternat,
            ).filter(
                InscriptionInternat.IDTAnneeScolaire == id_annee
            ).order_by(Eleve.Nom, Eleve.Prenoms).all()

            result = []
            for internat, eleve, classe, total_verse in rows:
                montant_du = float(internat.MontantAnnuel or 0)
                montant_verse = float(total_verse or 0)
                reste = max(0.0, montant_du - montant_verse)
                etat = "Payé" if montant_du > 0 and reste <= 0 else (
                    "Partiel" if montant_verse > 0 else "Impayé"
                )
                origine = "Collège" if internat.OrigineScolaire == "COLLEGE" else "Externe"
                lib_classe = classe or internat.ClasseFrequentee or origine
                result.append({
                    "Matricule": eleve.Matricule,
                    "Nom": f"{eleve.Nom} {eleve.Prenoms}",
                    "LibClasse": lib_classe,
                    "Origine": origine,
                    "Type": "Nouvelle" if internat.TypePensionnaire == "NOUVELLE" else "Renouvellement",
                    "MontantDu": montant_du,
                    "MontantVerse": montant_verse,
                    "Reste": reste,
                    "Etat": etat,
                })
            return result
        except Exception as e:
            print(f"Error in get_etat_versements_internat: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_periodique(date_debut: Optional[datetime.date] = None, date_fin: Optional[datetime.date] = None) -> List[dict]:
        """Retourne le récapitulatif des encaissements par rubrique sur une période donnée."""
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        try:
            from app.config import Config
            from services.comptabilite_service import ComptabiliteService

            totaux = ComptabiliteService.get_totaux_entrees_rubriques(id_annee, date_debut, date_fin)

            lignes = [("Scolarité", totaux.get("scolarite", 0.0))]
            if Config.ENABLE_CANTINE:
                lignes.append(("Cantine", totaux.get("cantine", 0.0)))
            if Config.ENABLE_TRANSPORT:
                lignes.append(("Transport", totaux.get("transport", 0.0)))
            lignes.append(("Autres frais annexes", totaux.get("autres", 0.0)))
            lignes.append(("Internat", totaux.get("internat", 0.0)))
            lignes.append(("Vente Kiosque", totaux.get("vente", 0.0)))

            return [{"Rubrique": lib, "Montant": montant} for lib, montant in lignes]
        except Exception as e:
            print(f"Error in get_etat_periodique: {e}")
            return []

    @staticmethod
    def format_fcfa(montant: Any) -> str:
        """Formate un montant numérique en FCFA (Ex: 100 000 FCFA)."""
        try:
            val = int(float(montant))
            return f"{val:,}".replace(",", " ") + " FCFA"
        except Exception:
            return f"{montant} FCFA"
