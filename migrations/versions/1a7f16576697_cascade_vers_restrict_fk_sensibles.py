"""cascade vers restrict fk sensibles

Remplace ON DELETE CASCADE par ON DELETE RESTRICT sur les cles etrangeres
scolaires/financieres sensibles (audit P0-02) : une inscription, un
versement, un mouvement de stock ou un tarif configure ne doivent jamais
disparaitre en silence comme effet de bord de la suppression d'une annee,
d'une famille, d'un eleve, d'un niveau, d'une classe ou d'un article.

Couvre TInscription (5 FK), VersementScol (3 FK), MontantScol (2 FK),
StockEnt (2 FK), StockSortie (2 FK).

Note : sur la base de test locale utilisee pour generer cette revision,
TInscription et VersementScol etaient deja en RESTRICT (derive anterieure
non expliquee), seuls MontantScol/StockEnt/StockSortie apparaissaient dans
le diff autogenere. Les operations sur TInscription/VersementScol ont ete
ajoutees a la main pour que cette revision soit correcte sur toute base
(dont la base reelle CJGA) qui a encore CASCADE sur ces 5 tables comme le
prevoyait le code jusqu'ici. Rejouer cette revision sur une base deja en
RESTRICT est un no-op fonctionnel (memes contraintes recreees a l'identique).

ATTENTION avant application sur une base contenant des donnees reelles :
une fois RESTRICT en place, toute tentative de suppression d'une annee,
famille, eleve, niveau, classe ou article encore reference echouera. C'est
le but recherche, mais verifier qu'aucun outil externe ne compte sur
l'ancien comportement CASCADE avant d'appliquer.

Revision ID: 1a7f16576697
Revises: 057c2c9d281a
Create Date: 2026-07-16 21:59:00.837792

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '1a7f16576697'
down_revision: Union[str, Sequence[str], None] = '057c2c9d281a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, colonne, table_cible, colonne_cible)
_RESTRICTED_FKS = [
    ("TInscription", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
    ("TInscription", "IDFamille", "TFamille", "IdTFamille"),
    ("TInscription", "IDEleve", "Eleve", "IDEleve"),
    ("TInscription", "IDNiveau", "TNiveau", "IDT_Niveau"),
    ("TInscription", "IDClasse", "TClasse", "IDTClasse"),
    ("VersementScol", "IDFamille", "TFamille", "IdTFamille"),
    ("VersementScol", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
    ("VersementScol", "IDEleve", "Eleve", "IDEleve"),
    ("MontantScol", "IDNiveau", "TNiveau", "IDT_Niveau"),
    ("MontantScol", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
    ("StockEnt", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
    ("StockEnt", "IDTArticle", "TArticle", "IDTArticle"),
    ("StockSortie", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
    ("StockSortie", "IDTArticle", "TArticle", "IDTArticle"),
]


def _constraint_name(table: str, column: str) -> str:
    return f"{table}_{column}_fkey"


def upgrade() -> None:
    """Upgrade schema."""
    for table, column, ref_table, ref_column in _RESTRICTED_FKS:
        name = _constraint_name(table, column)
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(name, table, ref_table, [column], [ref_column], ondelete='RESTRICT')


def downgrade() -> None:
    """Downgrade schema."""
    for table, column, ref_table, ref_column in reversed(_RESTRICTED_FKS):
        name = _constraint_name(table, column)
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(name, table, ref_table, [column], [ref_column], ondelete='CASCADE')
