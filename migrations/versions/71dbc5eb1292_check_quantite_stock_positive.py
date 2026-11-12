"""check quantite stock positive

Ajoute CHECK ("QuantiteCour" >= 0) sur StockCour (audit P0-04/B3) : defense
en profondeur en complement du verrouillage applicatif de
StockService.process_sale, au cas ou une autre voie de code modifierait
la quantite sans passer par ce verrouillage.

Alembic n'autogenere pas les CHECK CONSTRAINT (non compare par defaut par
le comparateur d'autogenerate) : ecrite a la main, meme motif que les
UNIQUE/CHECK deja ajoutes via app/database.py::create_tables().

Idempotent (verification pg_constraint avant l'ajout) : le modele StockCour
declare deja cette contrainte dans son __table_args__, donc une base neuve
creee via create_tables() (Base.metadata.create_all) l'a deja au moment ou
cette revision est rejouee (bug decouvert par la CI, chantier C2).

Revision ID: 71dbc5eb1292
Revises: 1a7f16576697
Create Date: 2026-07-16 22:07:14.004463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71dbc5eb1292'
down_revision: Union[str, Sequence[str], None] = '1a7f16576697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSTRAINT_NAME = "ck_stock_cour_quantite_positive"


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM pg_constraint WHERE conname = :name"),
        {"name": _CONSTRAINT_NAME},
    ).first()
    if not exists:
        op.create_check_constraint(_CONSTRAINT_NAME, "StockCour", '"QuantiteCour" >= 0')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_CONSTRAINT_NAME, "StockCour", type_="check")
