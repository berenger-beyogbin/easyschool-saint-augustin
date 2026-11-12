"""Ajouter le mode de paiement (especes/cheque) sur les versements scolarite.

Revision ID: 9f2e6b4c1a83
Revises: 7d3f9c1e4b82
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "9f2e6b4c1a83"
down_revision: Union[str, Sequence[str], None] = "7d3f9c1e4b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "VersementScol",
        sa.Column("ModePaiement", sa.String(length=30), nullable=False, server_default="ESPECES"),
    )
    op.add_column(
        "VersementScol",
        sa.Column("ReferencePaiement", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("VersementScol", "ReferencePaiement")
    op.drop_column("VersementScol", "ModePaiement")
