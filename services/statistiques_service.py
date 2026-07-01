import datetime
from typing import List, Optional, Any
from sqlalchemy import func, case
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
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse
            from models.niveau import TNiveau

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .join(TNiveau, TInscription.IDNiveau == TNiveau.IDT_Niveau)\
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
                    "Matricule": ins.eleve.Matricule,
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
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
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
                    "Matricule": ins.eleve.Matricule,
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
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse
            from models.montant_scol import MontantScol
            from models.versement_scol import VersementScol

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
                VersementScol.Reduction == False
            ).group_by(VersementScol.IDEleve).all()

            versements_map = {v[0]: float(v[1]) if v[1] is not None else 0.0 for v in versements_sums}

            # 2b. Cumul des reductions accordees (Reduction=True)
            reductions_sums = session.query(
                VersementScol.IDEleve,
                func.sum(VersementScol.MontantVersSco).label("reduc_sum"),
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == True
            ).group_by(VersementScol.IDEleve).all()

            reductions_map = {v[0]: float(v[1]) if v[1] is not None else 0.0 for v in reductions_sums}

            # 3. Récupérer les inscriptions
            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
                                          .filter(TInscription.IDTAnneeScolaire == id_annee)
            if id_niveau:
                q = q.filter(TInscription.IDNiveau == id_niveau)
            if id_classe:
                q = q.filter(TInscription.IDClasse == id_classe)

            q = q.order_by(TClasse.LibClasse, Eleve.Nom, Eleve.Prenoms)
            inscriptions = q.all()

            # Pré-calcul des rangs par famille (ordre IDTInscription) pour la règle 3e enfant
            from collections import defaultdict
            fam_buckets = defaultdict(list)
            for row in session.query(
                TInscription.IDFamille, TInscription.IDEleve, TInscription.IDTInscription
            ).filter(TInscription.IDTAnneeScolaire == id_annee
            ).order_by(TInscription.IDFamille, TInscription.IDTInscription.asc()).all():
                fam_buckets[row.IDFamille].append(row.IDEleve)
            rang_par_eleve = {}
            for id_fam, eleve_ids in fam_buckets.items():
                for idx, id_el in enumerate(eleve_ids):
                    rang_par_eleve[id_el] = (idx + 1, len(eleve_ids))

            lst = []
            for ins in inscriptions:
                # Calcul montant du
                scol_due = 0.0
                if ins.Scolarite:
                    m_scol = montants_map.get(ins.IDNiveau)
                    if m_scol:
                        if ins.famille and ins.famille.EnsCatPrimaire:
                            scol_due = float(m_scol.MontantEnsPri)
                        elif ins.famille and ins.famille.EnsCatSecondaire:
                            scol_due = float(m_scol.MontantEnsSecondaire)
                        else:
                            scol_due = float(m_scol.Montant)

                    if ins.famille and ins.famille.EbrieAbobote:
                        scol_due = max(0.0, scol_due - 10000.0)
                    if ins.Nouveau:
                        scol_due += 10000.0
                    rang, nb_famille = rang_par_eleve.get(ins.IDEleve, (1, 1))
                    if nb_famille >= 3 and rang >= 3:
                        scol_due = max(0.0, scol_due - 10000.0)

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
                    "Matricule": ins.eleve.Matricule,
                    "Nom": f"{ins.eleve.Nom} {ins.eleve.Prenoms}",
                    "LibClasse": ins.classe.LibClasse,
                    "SoldeAnt": 0.0,
                    "Impaye": 0.0,
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
            ).filter(VersementScol.IDTAnneeScolaire == id_annee).group_by(VersementScol.IDEleve).all()

            payments_map = {p[0]: float(p[1]) if p[1] is not None else 0.0 for p in payments_sums}

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
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
                    "Matricule": ins.eleve.Matricule,
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
            ).filter(VersementScol.IDTAnneeScolaire == id_annee).group_by(VersementScol.IDEleve).all()

            payments_map = {p[0]: float(p[1]) if p[1] is not None else 0.0 for p in payments_sums}

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
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
                    "Matricule": ins.eleve.Matricule,
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
            from models.stock_sortie import StockSortie
            from models.article import Article

            q = session.query(StockSortie).join(Article, StockSortie.IDTArticle == Article.IDTArticle)\
                                          .filter(StockSortie.IDTAnneeScolaire == id_annee)
            if date_debut:
                q = q.filter(StockSortie.DateSort >= date_debut)
            if date_fin:
                q = q.filter(StockSortie.DateSort <= date_fin)

            q = q.order_by(StockSortie.DateSort.desc(), StockSortie.HeureSortie.desc())
            results = q.all()

            lst = []
            for item in results:
                total_val = float(item.QuantiteSort) * float(item.Prix_vente)
                lst.append({
                    "DateSort": item.DateSort,
                    "HeureSortie": item.HeureSortie,
                    "Article": item.article.Libelle,
                    "QuantiteSort": item.QuantiteSort,
                    "Prix_vente": float(item.Prix_vente),
                    "Total": total_val,
                    "Login": item.Login
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
            from models.stock_cour import StockCour

            results = session.query(Article, StockCour.QuantiteCour).outerjoin(
                StockCour, Article.IDTArticle == StockCour.IDTArticle
            ).order_by(Article.Libelle.asc()).all()

            lst = []
            for art, qte_cour in results:
                qty = qte_cour if qte_cour is not None else 0
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
            from models.inscription import TInscription
            from models.eleve import Eleve
            from models.classe import TClasse

            q = session.query(TInscription).join(Eleve, TInscription.IDEleve == Eleve.IDEleve)\
                                          .join(TClasse, TInscription.IDClasse == TClasse.IDTClasse)\
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
                    "Matricule": ins.eleve.Matricule,
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
    def format_fcfa(montant: Any) -> str:
        """Formate un montant numérique en FCFA (Ex: 100 000 FCFA)."""
        try:
            val = int(float(montant))
            return f"{val:,}".replace(",", " ") + " FCFA"
        except Exception:
            return f"{montant} FCFA"
