import datetime
from typing import List, Optional, Tuple, Any
from decimal import Decimal
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
from app.database import get_session
from app.session import AppSession
from models.compte import Compte
from models.type_sortie import TypeSortie
from models.sortie_fin import SortieFin
from models.annee_scolaire import TAnneeScolaire
from models.versement_scol import VersementScol
from models.stock_sortie import StockSortie
from services.compte_service import SYSCOA_INCOME_ACCOUNTS

# Correspondance NumCompte SYSCOA → clé rubrique dans get_totaux_entrees_rubriques
_SYSCOA_RUBRIQUE = {
    "7041": "scolarite",
    "7042": "transport",
    "7043": "cantine",
    "7044": "vente",
    "7045": "autres",
}

class ComptabiliteService:
    @staticmethod
    def generate_code_sortie(session, id_annee: int) -> str:
        """Génère un code séquentiel simple : SF-AAAA-0001."""
        annee = session.query(TAnneeScolaire).filter_by(IDTAnneeScolaire=id_annee).first()
        year_str = "YYYY"
        if annee and annee.Libelle:
            # Ex: "2026-2027" -> "2026"
            parts = annee.Libelle.split("-")
            if parts and len(parts[0]) == 4:
                year_str = parts[0]
            else:
                year_str = annee.Libelle[:4]
        else:
            year_str = str(datetime.date.today().year)
            
        prefix = f"SF-{year_str}-"
        
        # Trouver tous les codes pour ce préfixe de cette année
        max_num = 0
        mouvements = session.query(SortieFin).filter(SortieFin.CodeSortie.like(f"{prefix}%")).all()
        for m in mouvements:
            if m.CodeSortie and len(m.CodeSortie) > len(prefix):
                suffix = m.CodeSortie[len(prefix):]
                try:
                    num = int(suffix)
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
        new_num = max_num + 1
        return f"{prefix}{new_num:04d}"

    @staticmethod
    def create_mouvement(benef: str, montant: float, date_sortie: datetime.date, 
                         id_compte: int, debit_credit: str, detail: Optional[str] = None, 
                         num_benef: Optional[str] = None) -> Tuple[bool, str]:
        """Crée un nouveau mouvement financier dans SortieFin."""
        # Validation des paramètres obligatoires
        if not benef or not benef.strip():
            return False, "Le beneficiaire est obligatoire."
        if not montant or montant <= 0:
            return False, "Le montant doit être strictement positif."
        if not date_sortie:
            return False, "La date de mouvement est obligatoire."
        if not id_compte:
            return False, "Le compte est obligatoire."
        if debit_credit not in ["Debit", "Credit"]:
            return False, "Le mouvement doit être 'Debit' ou 'Credit'."

        # Récupération de la session et de l'année scolaire active du Kiosque / AppSession
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return False, "Aucune année scolaire active n'est selectionnée."

        login_util = AppSession.get_logged_in_username() or "admin"

        session = get_session()
        try:
            # Vérifier si l'année est clôturée
            annee = session.query(TAnneeScolaire).filter_by(IDTAnneeScolaire=active_annee_id).first()
            if not annee:
                return False, "L'année scolaire active n'existe pas en base."
            if annee.Cloturer:
                return False, "Impossible d'enregistrer un mouvement : cette année scolaire est clôturée."

            # Vérifier que le compte existe
            compte = session.query(Compte).filter_by(IDCompte=id_compte).first()
            if not compte:
                return False, "Le compte spécifié n'existe pas."

            # Comptes de produits SYSCOA (7041-7045) : alimentes automatiquement par
            # get_totaux_entrees_rubriques depuis les versements/ventes. Un credit manuel
            # sur ces comptes s'ajouterait a ce calcul automatique et compterait la
            # recette deux fois dans la balance.
            if debit_credit == "Credit" and compte.NumCompte in _SYSCOA_RUBRIQUE:
                return False, (
                    f"Le compte {compte.NumCompte} ({compte.LibCompte}) est alimente "
                    "automatiquement par les versements et ventes : un credit manuel "
                    "compterait cette recette deux fois dans la balance."
                )

            # Génération automatique du CodeSortie
            code = ComptabiliteService.generate_code_sortie(session, active_annee_id)

            nouveau_mouvement = SortieFin(
                Benef=benef.strip(),
                Detail=detail.strip() if detail else None,
                Montant=Decimal(str(montant)),
                NumBenef=num_benef.strip() if num_benef else None,
                DateSortie=date_sortie,
                Login=login_util,
                CodeSortie=code,
                IDAnSco=active_annee_id,
                DebitCredit=debit_credit,
                IDCompte=id_compte
            )

            session.add(nouveau_mouvement)
            session.commit()
            return True, f"Mouvement {code} enregistré avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de données : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_mouvement(id_sortie_fin: int, benef: str, montant: float, date_sortie: datetime.date, 
                         id_compte: int, debit_credit: str, detail: Optional[str] = None, 
                         num_benef: Optional[str] = None) -> Tuple[bool, str]:
        """Met à jour un mouvement financier existant."""
        if not benef or not benef.strip():
            return False, "Le beneficiaire est obligatoire."
        if not montant or montant <= 0:
            return False, "Le montant doit être strictement positif."
        if not date_sortie:
            return False, "La date de mouvement est obligatoire."
        if not id_compte:
            return False, "Le compte est obligatoire."
        if debit_credit not in ["Debit", "Credit"]:
            return False, "Le mouvement doit être 'Debit' ou 'Credit'."

        session = get_session()
        try:
            mouvement = session.query(SortieFin).filter_by(IDSortieFin=id_sortie_fin).first()
            if not mouvement:
                return False, "Mouvement inexistant."

            # Vérifier si l'année est clôturée
            annee = session.query(TAnneeScolaire).filter_by(IDTAnneeScolaire=mouvement.IDAnSco).first()
            if annee and annee.Cloturer:
                return False, "Modification impossible: l'année pour ce mouvement est clôturée."

            # Comptes de produits SYSCOA (7041-7045) : voir create_mouvement, meme raison.
            compte = session.query(Compte).filter_by(IDCompte=id_compte).first()
            if compte and debit_credit == "Credit" and compte.NumCompte in _SYSCOA_RUBRIQUE:
                return False, (
                    f"Le compte {compte.NumCompte} ({compte.LibCompte}) est alimente "
                    "automatiquement par les versements et ventes : un credit manuel "
                    "compterait cette recette deux fois dans la balance."
                )

            mouvement.Benef = benef.strip()
            mouvement.Detail = detail.strip() if detail else None
            mouvement.Montant = Decimal(str(montant))
            mouvement.NumBenef = num_benef.strip() if num_benef else None
            mouvement.DateSortie = date_sortie
            mouvement.DebitCredit = debit_credit
            mouvement.IDCompte = id_compte

            session.commit()
            return True, "Mouvement mis à jour avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de données : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def annuler_mouvement(
        id_sortie_fin: int, motif: str, login: Optional[str] = None, id_utilisateur: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Annule un mouvement financier (piste d'audit conservee) au lieu de le supprimer
        physiquement. Un mouvement annule reste visible dans les listes mais est exclu
        des agregations de la balance."""
        if not motif or not motif.strip():
            return False, "Le motif d'annulation est obligatoire."

        session = get_session()
        try:
            mouvement = session.query(SortieFin).filter_by(IDSortieFin=id_sortie_fin).first()
            if not mouvement:
                return False, "Mouvement inexistant."
            if mouvement.Annule:
                return False, "Ce mouvement est deja annule."

            # Vérifier si l'année est clôturée
            annee = session.query(TAnneeScolaire).filter_by(IDTAnneeScolaire=mouvement.IDAnSco).first()
            if annee and annee.Cloturer:
                return False, "Annulation impossible: l'année pour ce mouvement est clôturée."

            ancien_montant = str(mouvement.Montant)
            mouvement.Annule = True
            mouvement.AnnulePar = login or "admin"
            mouvement.DateAnnulation = datetime.datetime.now()
            mouvement.MotifAnnulation = motif.strip()
            session.commit()

            from services.audit_log_service import AuditLogService
            AuditLogService.log(
                action="ANNULER_MOUVEMENT", table_cible="SortieFin", id_cible=id_sortie_fin,
                id_utilisateur=id_utilisateur, ancienne_valeur=f"Montant={ancien_montant}",
                nouvelle_valeur="Annule=True", motif=motif.strip(),
            )
            return True, "Mouvement annulé avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de données : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_all_mouvements(id_annee: Optional[int] = None) -> List[SortieFin]:
        """Récupère l'ensemble des mouvements d'une année active."""
        if not id_annee:
            id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []

        session = get_session()
        try:
            return session.query(SortieFin).options(joinedload(SortieFin.compte))\
                .filter_by(IDAnSco=id_annee)\
                .order_by(SortieFin.DateSortie.desc(), SortieFin.IDSortieFin.desc()).all()
        except Exception as e:
            print(f"Erreur get_all_mouvements : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_mouvements_by_period(id_annee: int, date_debut: datetime.date, date_fin: datetime.date) -> List[SortieFin]:
        """Filtre les mouvements par année et par période."""
        session = get_session()
        try:
            return session.query(SortieFin).options(joinedload(SortieFin.compte))\
                .filter(
                    SortieFin.IDAnSco == id_annee,
                    SortieFin.DateSortie >= date_debut,
                    SortieFin.DateSortie <= date_fin
                ).order_by(SortieFin.DateSortie.desc(), SortieFin.IDSortieFin.desc()).all()
        except Exception as e:
            print(f"Erreur get_mouvements_by_period : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_etat_sorties(id_annee: int, id_compte: Optional[int] = None, 
                         date_debut: Optional[datetime.date] = None, 
                         date_fin: Optional[datetime.date] = None) -> List[SortieFin]:
        """
        Etat des sorties : affiche uniquement les mouvements de type 'Debit'.
        Permet de filtrer en option par compte et par période.
        """
        session = get_session()
        try:
            q = session.query(SortieFin).options(joinedload(SortieFin.compte))\
                .filter(SortieFin.DebitCredit == 'Debit', SortieFin.IDAnSco == id_annee)
            
            if id_compte:
                q = q.filter_by(IDCompte=id_compte)
            if date_debut:
                q = q.filter(SortieFin.DateSortie >= date_debut)
            if date_fin:
                q = q.filter(SortieFin.DateSortie <= date_fin)
                
            return q.order_by(SortieFin.DateSortie.desc(), SortieFin.IDSortieFin.desc()).all()
        except Exception as e:
            print(f"Erreur get_etat_sorties : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_balance_comptes(id_annee: int, date_debut: Optional[datetime.date] = None, 
                            date_fin: Optional[datetime.date] = None) -> List[dict]:
        """
        Calcule la balance des comptes (debit, credit, solde = credit - debit)
        pour une annee scolaire donnee et une periode optionnelle.
        Conserve TOUS les comptes même s'ils n'ont aucun mouvement.
        """
        session = get_session()
        try:
            # Sous-requête pour agréger les mouvements filtrés de SortieFin par IDCompte
            sf_sub_q = session.query(
                SortieFin.IDCompte.label("IDCompte"),
                func.coalesce(func.sum(case((SortieFin.DebitCredit == 'Debit', SortieFin.Montant), else_=0)), 0).label("debit"),
                func.coalesce(func.sum(case((SortieFin.DebitCredit == 'Credit', SortieFin.Montant), else_=0)), 0).label("credit")
            ).filter(SortieFin.IDAnSco == id_annee, SortieFin.Annule == False)

            if date_debut:
                sf_sub_q = sf_sub_q.filter(SortieFin.DateSortie >= date_debut)
            if date_fin:
                sf_sub_q = sf_sub_q.filter(SortieFin.DateSortie <= date_fin)

            sf_sub = sf_sub_q.group_by(SortieFin.IDCompte).subquery()

            # Jointure externe pour récupérer TOUS les comptes avec leurs débits/crédits
            results = session.query(
                Compte.NumCompte,
                Compte.LibCompte,
                func.coalesce(sf_sub.c.debit, 0).label("debit"),
                func.coalesce(sf_sub.c.credit, 0).label("credit")
            ).outerjoin(
                sf_sub, Compte.IDCompte == sf_sub.c.IDCompte
            ).order_by(Compte.NumCompte.asc()).all()

            balance_list = []
            for num, lib, deb, cred in results:
                balance_list.append({
                    "NumCompte": num,
                    "LibCompte": lib,
                    "Debit": float(deb),
                    "Credit": float(cred),
                    "Solde": float(cred - deb)
                })

            # Injecter les entrées (VersementScol + StockSortie) dans les comptes SYSCOA 7041-7044
            entrees = ComptabiliteService.get_totaux_entrees_rubriques(id_annee, date_debut, date_fin)
            for item in balance_list:
                rubrique = _SYSCOA_RUBRIQUE.get(item["NumCompte"])
                if rubrique:
                    income = entrees.get(rubrique, 0.0)
                    item["Credit"] += income
                    item["Solde"] = item["Credit"] - item["Debit"]

            return balance_list
        except Exception as e:
            print(f"Erreur get_balance_comptes : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_totaux_entrees_rubriques(id_annee: int, date_debut=None, date_fin=None) -> dict:
        """Retourne le total des encaissements par rubrique pour une période donnée."""
        session = get_session()
        try:
            q_vers = session.query(
                func.coalesce(func.sum(VersementScol.MontantVersSco), 0),
                func.coalesce(func.sum(VersementScol.MontantVersTrans), 0),
                func.coalesce(func.sum(VersementScol.MontantCantine), 0),
                func.coalesce(func.sum(VersementScol.MontantVersAutres), 0),
            ).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
                VersementScol.Annule == False
            )
            if date_debut:
                q_vers = q_vers.filter(VersementScol.DateVers >= date_debut)
            if date_fin:
                q_vers = q_vers.filter(VersementScol.DateVers <= date_fin)
            row = q_vers.first()
            scol   = float(row[0]) if row else 0.0
            trans  = float(row[1]) if row else 0.0
            cant   = float(row[2]) if row else 0.0
            autres = float(row[3]) if row else 0.0

            q_vente = session.query(
                func.coalesce(func.sum(StockSortie.QuantiteSort * StockSortie.Prix_vente), 0)
            ).filter(StockSortie.IDTAnneeScolaire == id_annee)
            if date_debut:
                q_vente = q_vente.filter(StockSortie.DateSort >= date_debut)
            if date_fin:
                q_vente = q_vente.filter(StockSortie.DateSort <= date_fin)
            vente_row = q_vente.first()
            vente = float(vente_row[0]) if vente_row else 0.0

            return {"scolarite": scol, "transport": trans, "cantine": cant, "vente": vente, "autres": autres}
        except Exception as e:
            print(f"Erreur get_totaux_entrees_rubriques : {e}")
            return {"scolarite": 0.0, "transport": 0.0, "cantine": 0.0, "vente": 0.0, "autres": 0.0}
        finally:
            session.close()
