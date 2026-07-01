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
from .autres_frais import AutresFrais
from .montant_autres_frais import MontantAutresFrais
from .montant_scol import MontantScol
from .montant_cantine import MontantCantine
from .montant_transport import MontantTransport
from .versement_scol import VersementScol
from .article import Article
from .stock_cour import StockCour
from .stock_entree import StockEntree
from .stock_sortie import StockSortie
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
    "AutresFrais",
    "MontantAutresFrais",
    "MontantScol",
    "MontantCantine",
    "MontantTransport",
    "VersementScol",
    "Article",
    "StockCour",
    "StockEntree",
    "StockSortie",
    "Compte",
    "TypeSortie",
    "SortieFin"
]
