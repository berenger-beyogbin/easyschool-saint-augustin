from .etablissement import EtablissementEcole
from .annee_scolaire import TAnneeScolaire
from .cycle import TCycle
from .niveau import TNiveau
from .classe import TClasse
from .nationalite import TNationalite
from .religion import TReligion
from .famille import TFamille
from .eleve import Eleve
from .inscription import TInscription
from .prestation_tarif_niveau import PrestationTarifNiveau
from .montant_scol import MontantScol
from .montant_cantine import MontantCantine
from .montant_transport import MontantTransport
from .versement_scol import VersementScol
from .echeance_paiement import EcheancePaiement
from .echeance_paiement import EcheancePaiement
from .article import Article
from .stock_cour import StockCour
from .stock_entree import StockEntree
from .stock_sortie import StockSortie
from .kit_composant import KitComposant
from .kit_assemblage import KitAssemblage
from .compte import Compte
from .type_sortie import TypeSortie
from .sortie_fin import SortieFin

# Utile pour que Base.metadata connaisse tous nos modeles
__all__ = [
    "EtablissementEcole",
    "TAnneeScolaire",
    "TCycle",
    "TNiveau",
    "TClasse",
    "TNationalite",
    "TReligion",
    "TFamille",
    "Eleve",
    "TInscription",
    "PrestationTarifNiveau",
    "MontantScol",
    "MontantCantine",
    "MontantTransport",
    "VersementScol",
    "EcheancePaiement",
    "EcheancePaiement",
    "Article",
    "StockCour",
    "StockEntree",
    "StockSortie",
    "KitComposant",
    "KitAssemblage",
    "Compte",
    "TypeSortie",
    "SortieFin"
]
