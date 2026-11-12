"""Ajouter l'identifiant de l'ancien logiciel sur les eleves.

Revision ID: e42b8a71c6d9
Revises: d21a6c9f4e30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e42b8a71c6d9"
down_revision: Union[str, Sequence[str], None] = "d21a6c9f4e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("Eleve", sa.Column("CodeExterne", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_eleve_code_externe", "Eleve", ["CodeExterne"])


def downgrade() -> None:
    op.drop_constraint("uq_eleve_code_externe", "Eleve", type_="unique")
    op.drop_column("Eleve", "CodeExterne")
