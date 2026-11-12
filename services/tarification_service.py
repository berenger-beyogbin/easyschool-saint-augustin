"""Regles de tarification de la scolarite CJGA.

Depuis 2026-2027, la scolarite depend uniquement du niveau et du statut
d'affectation. Les anciennes reductions automatiques et la surcharge nouvel
eleve ne sont plus en vigueur. Le montant retenu est ensuite fige sur
TInscription.MontantScolariteApplique.
"""


class TarificationService:
    @staticmethod
    def calculer_scolarite_due(
        montant_affecte: float,
        montant_non_affecte: float,
        statut_affectation: str,
    ) -> float:
        """Retourne le tarif de base correspondant au statut d'affectation."""
        montant = montant_non_affecte if statut_affectation == "NON_AFFECTE_ETAT" else montant_affecte
        return max(0.0, float(montant or 0))
