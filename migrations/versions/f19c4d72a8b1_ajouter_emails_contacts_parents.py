"""Ajouter les emails propres au pere, a la mere et au tuteur.

Revision ID: f19c4d72a8b1
Revises: e42b8a71c6d9
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f19c4d72a8b1"
down_revision: Union[str, Sequence[str], None] = "e42b8a71c6d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("TFamille", sa.Column("EmailPere", sa.String(length=80), nullable=True))
    op.add_column("TFamille", sa.Column("EmailMere", sa.String(length=80), nullable=True))
    op.add_column("TFamille", sa.Column("EmailTuteur", sa.String(length=80), nullable=True))


def downgrade() -> None:
    op.drop_column("TFamille", "EmailTuteur")
    op.drop_column("TFamille", "EmailMere")
    op.drop_column("TFamille", "EmailPere")
