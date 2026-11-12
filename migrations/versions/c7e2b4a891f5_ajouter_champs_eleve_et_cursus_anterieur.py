"""ajouter champs eleve (dossier CJGA) et table CursusAnterieur

Revision ID: c7e2b4a891f5
Revises: b3f6a1c9d0e2
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e2b4a891f5"
down_revision: Union[str, Sequence[str], None] = "b3f6a1c9d0e2"
branch_labels = None
depends_on = None


# Colonnes ajoutees a Eleve pour se conformer a la fiche d'inscription papier
# CJGA (page 1 : identification, cursus, religion, cadre direction ; page 3 :
# documents a fournir ; page 4 : renseignements medicaux). Toutes nullable
# (ou par defaut False pour les checklists), aucune n'est obligatoire sur la
# fiche papier.
_NEW_TEXT_COLUMNS = [
    ("MatriculeNational", "VARCHAR(30)"),
    ("EtablissementOrigine", "VARCHAR(100)"),
    ("ClasseSuivieOrigine", "VARCHAR(30)"),
    ("DeuxiemeLangue", "VARCHAR(30)"),
    ("VitChezQui", "VARCHAR(20)"),
    ("ParoisseActuelle", "VARCHAR(60)"),
    ("ActiviteParoisse", "VARCHAR(100)"),
    ("PreciserEglise", "VARCHAR(60)"),
    ("NDossier", "VARCHAR(20)"),
    ("AccidentNom1", "VARCHAR(50)"),
    ("AccidentTel1", "VARCHAR(25)"),
    ("AccidentCel1", "VARCHAR(25)"),
    ("AccidentBureau1", "VARCHAR(25)"),
    ("AccidentNom2", "VARCHAR(50)"),
    ("AccidentTel2", "VARCHAR(25)"),
    ("AccidentCel2", "VARCHAR(25)"),
    ("AccidentBureau2", "VARCHAR(25)"),
    ("AccidentAdresse", "VARCHAR(100)"),
    ("ConduireHopitalPrecision", "VARCHAR(100)"),
    ("ConduireCliniquePrecision", "VARCHAR(100)"),
    ("MedecinNom", "VARCHAR(50)"),
    ("MedecinTel", "VARCHAR(25)"),
    ("MedecinCel", "VARCHAR(25)"),
    ("MedecinBureau", "VARCHAR(25)"),
    ("MedecinAdresse", "VARCHAR(100)"),
    ("Maladie", "VARCHAR(200)"),
    ("ContreIndications", "VARCHAR(200)"),
]

_NEW_DATE_COLUMNS = [
    ("DateAdmission", "DATE"),
]

_NEW_BOOL_NULLABLE_COLUMNS = [
    "Baptise", "Confirme", "AutorisationCourrier",
    "ConduireHopital", "ConduireClinique",
]

_NEW_BOOL_DEFAULT_FALSE_COLUMNS = [
    "DocExtraitNaissance", "DocCertifScolarite", "DocBulletins", "DocPhotos",
    "DocCarnetVaccination", "DocCarnetSante", "DocDispenseEPS",
    "DocDispenseEPSCertificat", "DocCarteSejour", "DocLivretScolaire",
]


def upgrade() -> None:
    bind = op.get_bind()
    for name, coltype in _NEW_TEXT_COLUMNS:
        bind.execute(sa.text(f'ALTER TABLE "Eleve" ADD COLUMN IF NOT EXISTS "{name}" {coltype};'))
    for name, coltype in _NEW_DATE_COLUMNS:
        bind.execute(sa.text(f'ALTER TABLE "Eleve" ADD COLUMN IF NOT EXISTS "{name}" {coltype};'))
    for name in _NEW_BOOL_NULLABLE_COLUMNS:
        bind.execute(sa.text(f'ALTER TABLE "Eleve" ADD COLUMN IF NOT EXISTS "{name}" BOOLEAN;'))
    for name in _NEW_BOOL_DEFAULT_FALSE_COLUMNS:
        bind.execute(sa.text(
            f'ALTER TABLE "Eleve" ADD COLUMN IF NOT EXISTS "{name}" BOOLEAN NOT NULL DEFAULT FALSE;'
        ))

    inspector = sa.inspect(bind)
    if "CursusAnterieur" not in inspector.get_table_names():
        op.create_table(
            "CursusAnterieur",
            sa.Column("IDCursusAnterieur", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDEleve", sa.Integer(), sa.ForeignKey("Eleve.IDEleve", ondelete="CASCADE"), nullable=False),
            sa.Column("AnneeScolaire", sa.String(20), nullable=True),
            sa.Column("Classe", sa.String(30), nullable=True),
            sa.Column("MoyenneAnnuelle", sa.Numeric(5, 2), nullable=True),
            sa.Column("Etablissement", sa.String(100), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("CursusAnterieur")
    bind = op.get_bind()
    all_cols = (
        [n for n, _ in _NEW_TEXT_COLUMNS]
        + [n for n, _ in _NEW_DATE_COLUMNS]
        + _NEW_BOOL_NULLABLE_COLUMNS
        + _NEW_BOOL_DEFAULT_FALSE_COLUMNS
    )
    for name in all_cols:
        bind.execute(sa.text(f'ALTER TABLE "Eleve" DROP COLUMN IF EXISTS "{name}";'))
