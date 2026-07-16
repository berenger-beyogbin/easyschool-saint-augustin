"""baseline etat actuel du schema

Revision vide intentionnellement : le schema existant a ete cree/mis a jour
jusqu'ici par app.database.create_tables() (Base.metadata.create_all() +
blocs ALTER TABLE ad hoc). Cette revision sert uniquement de point de depart
pour Alembic. Sur toute base deja a jour (dev, test, prod existante), marquer
directement cette revision comme appliquee, sans rien executer :

    alembic stamp head

Les prochains changements de schema doivent etre ajoutes via de nouvelles
revisions (`alembic revision --autogenerate -m "..."`) plutot que via de
nouveaux blocs dans create_tables().

Revision ID: f0e0bbadf6a8
Revises:
Create Date: 2026-07-16 20:13:19.878823

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0e0bbadf6a8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
