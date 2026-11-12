"""Remplacer les suffixes alphabetiques des classes par des numeros.

Revision ID: d21a6c9f4e30
Revises: c7e2b4a891f5
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d21a6c9f4e30"
down_revision: Union[str, Sequence[str], None] = "c7e2b4a891f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Le suffixe final seul est converti : A=1, B=2, ..., Z=26.
    op.execute(
        r'''
        UPDATE "TClasse"
        SET "LibClasse" = regexp_replace(
                upper(trim("LibClasse")),
                '[[:space:]-]+([A-Z])$',
                ' ' || (ascii(substring(upper(trim("LibClasse")) from '([A-Z])$')) - 64)::text
            ),
            "Sigle" = replace(
                regexp_replace(
                    upper(trim("LibClasse")),
                    '[[:space:]-]+([A-Z])$',
                    ' ' || (ascii(substring(upper(trim("LibClasse")) from '([A-Z])$')) - 64)::text
                ),
                ' ',
                ''
            )
        WHERE upper(trim("LibClasse")) ~ '[[:space:]-]+[A-Z]$';
        '''
    )


def downgrade() -> None:
    # Correction de données volontairement irréversible : un suffixe numérique
    # peut aussi avoir été saisi directement et ne doit pas redevenir une lettre.
    pass
