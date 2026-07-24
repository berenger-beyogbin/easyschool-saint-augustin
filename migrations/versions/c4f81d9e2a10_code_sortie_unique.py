"""Rendre CodeSortie unique pour eviter les doublons concurrents.

Revision ID: c4f81d9e2a10
Revises: a369634edd2b
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c4f81d9e2a10"
down_revision: Union[str, Sequence[str], None] = "a369634edd2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM "SortieFin"
                WHERE "CodeSortie" IS NOT NULL
                GROUP BY "CodeSortie"
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Des CodeSortie dupliques existent. Les corriger avant de relancer la migration.';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_sortie_fin_code_sortie'
            ) THEN
                ALTER TABLE "SortieFin"
                ADD CONSTRAINT uq_sortie_fin_code_sortie UNIQUE ("CodeSortie");
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        'ALTER TABLE "SortieFin" DROP CONSTRAINT IF EXISTS uq_sortie_fin_code_sortie'
    )
