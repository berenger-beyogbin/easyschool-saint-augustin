"""ajouter champs parents (pere/mere/tuteur/responsable) sur TFamille

Revision ID: b3f6a1c9d0e2
Revises: 8c9e1a7b2d44
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3f6a1c9d0e2"
down_revision: Union[str, Sequence[str], None] = "8c9e1a7b2d44"
branch_labels = None
depends_on = None


# Colonnes texte ajoutees a TFamille pour se conformer a la fiche d'inscription
# papier CJGA (dossier d'inscription, section "2- Renseignements d'ordre
# familial") : coordonnees completes Pere/Mere, bloc Tuteur independant,
# telephones bureau/domicile du responsable legal, notes du dossier. Toutes
# nullable : aucune n'est obligatoire sur la fiche papier.
_NEW_COLUMNS = [
    ("TelBureauResponsable", "VARCHAR(25)"),
    ("TelDomicileResponsable", "VARCHAR(25)"),
    ("EntreprisePere", "VARCHAR(40)"),
    ("LieuResidencePere", "VARCHAR(50)"),
    ("TelBureauPere", "VARCHAR(25)"),
    ("TelDomicilePere", "VARCHAR(25)"),
    ("AdressePostalePere", "VARCHAR(50)"),
    ("EntrepriseMere", "VARCHAR(40)"),
    ("LieuResidenceMere", "VARCHAR(50)"),
    ("TelBureauMere", "VARCHAR(25)"),
    ("TelDomicileMere", "VARCHAR(25)"),
    ("AdressePostaleMere", "VARCHAR(50)"),
    ("NomTuteur", "VARCHAR(50)"),
    ("ProfessionTuteur", "VARCHAR(25)"),
    ("EntrepriseTuteur", "VARCHAR(40)"),
    ("CelTuteur", "VARCHAR(25)"),
    ("TelBureauTuteur", "VARCHAR(25)"),
    ("TelDomicileTuteur", "VARCHAR(25)"),
    ("AdressePostaleTuteur", "VARCHAR(50)"),
    ("MotivationChoixEcole", "VARCHAR(255)"),
    ("Observations", "VARCHAR(500)"),
]


def upgrade() -> None:
    bind = op.get_bind()
    for name, coltype in _NEW_COLUMNS:
        bind.execute(sa.text(
            f'ALTER TABLE "TFamille" ADD COLUMN IF NOT EXISTS "{name}" {coltype};'
        ))


def downgrade() -> None:
    bind = op.get_bind()
    for name, _ in _NEW_COLUMNS:
        bind.execute(sa.text(f'ALTER TABLE "TFamille" DROP COLUMN IF EXISTS "{name}";'))
