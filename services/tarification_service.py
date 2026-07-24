from collections import defaultdict
from typing import Dict, Tuple

from models.inscription import TInscription

# Regles de tarification de la scolarite CJGA (audit D1). Avant ce service,
# la meme formule (reduction Ebrie d'Abobo-te, surcharge nouvel eleve,
# reduction 3e enfant) etait dupliquee independamment dans
# versement_service.py, dashboard_service.py et statistiques_service.py,
# au risque de diverger silencieusement lors d'une future evolution des
# montants (ex: changer 10 000 F a un seul endroit sans y penser ailleurs).
REDUCTION_EBRIE_ABOBOTE = 10000.0
SURCHARGE_NOUVEL_ELEVE_AFFECTE = 15000.0
REDUCTION_TROISIEME_ENFANT = 10000.0
SEUIL_FAMILLE_NOMBREUSE = 3


class TarificationService:
    @staticmethod
    def calculer_scolarite_due(
        montant_affecte: float,
        montant_non_affecte: float,
        statut_affectation: str,
        ebrie_abobote: bool,
        nouveau: bool,
        rang_famille: int,
        nb_enfants_famille: int,
    ) -> float:
        """Calcule le montant de scolarite du pour une inscription, tarif de
        base + surcharge nouvel eleve - reductions (Ebrie d'Abobo-te, 3e enfant)."""
        montant = montant_non_affecte if statut_affectation == "NON_AFFECTE_ETAT" else montant_affecte
        montant = float(montant or 0)

        if ebrie_abobote:
            montant = max(0.0, montant - REDUCTION_EBRIE_ABOBOTE)

        if nouveau and statut_affectation == "AFFECTE_ETAT":
            montant += SURCHARGE_NOUVEL_ELEVE_AFFECTE

        if nb_enfants_famille >= SEUIL_FAMILLE_NOMBREUSE and rang_famille >= SEUIL_FAMILLE_NOMBREUSE:
            montant = max(0.0, montant - REDUCTION_TROISIEME_ENFANT)

        return montant

    @staticmethod
    def get_rang_famille_pour_inscription(session, ins: TInscription, id_annee: int) -> Tuple[int, int]:
        """Rang (1-indexe, ordre IDTInscription) de ins parmi les inscriptions
        de sa famille pour cette annee, et nombre total d'enfants inscrits."""
        if not ins.IDFamille:
            return 1, 1
        ids_famille = [
            r[0] for r in session.query(TInscription.IDTInscription).filter(
                TInscription.IDFamille == ins.IDFamille,
                TInscription.IDTAnneeScolaire == id_annee,
            ).order_by(TInscription.IDTInscription.asc()).all()
        ]
        if ins.IDTInscription not in ids_famille:
            return 1, len(ids_famille) or 1
        rang = ids_famille.index(ins.IDTInscription) + 1
        return rang, len(ids_famille)

    @staticmethod
    def get_rangs_famille_par_eleve(session, id_annee: int) -> Dict[int, Tuple[int, int]]:
        """Precalcule (rang, nb_enfants_famille) pour tous les eleves inscrits
        sur l'annee en une seule passe (usage bulk : dashboard, statistiques)."""
        fam_buckets = defaultdict(list)
        for row in session.query(
            TInscription.IDFamille, TInscription.IDEleve, TInscription.IDTInscription
        ).filter(
            TInscription.IDTAnneeScolaire == id_annee
        ).order_by(TInscription.IDFamille, TInscription.IDTInscription.asc()).all():
            fam_buckets[row.IDFamille].append(row.IDEleve)

        rang_par_eleve = {}
        for _id_fam, eleve_ids in fam_buckets.items():
            for idx, id_el in enumerate(eleve_ids):
                rang_par_eleve[id_el] = (idx + 1, len(eleve_ids))
        return rang_par_eleve
