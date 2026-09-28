"""prendre en charge les pensionnaires externes

Revision ID: d84f1a2c7b90
Revises: a26c8d91e7f4
Create Date: 2026-08-26
"""
from alembic import op
import sqlalchemy as sa


revision = "d84f1a2c7b90"
down_revision = "a26c8d91e7f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("InscriptionInternat", sa.Column("IDEleve", sa.Integer(), nullable=True))
    op.add_column("InscriptionInternat", sa.Column("IDTAnneeScolaire", sa.Integer(), nullable=True))
    op.add_column("InscriptionInternat", sa.Column("OrigineScolaire", sa.String(10), nullable=False, server_default="COLLEGE"))
    op.add_column("InscriptionInternat", sa.Column("EtablissementFrequente", sa.String(120), nullable=True))
    op.add_column("InscriptionInternat", sa.Column("ClasseFrequentee", sa.String(50), nullable=True))
    op.add_column("InscriptionInternat", sa.Column("ResponsableNom", sa.String(100), nullable=True))
    op.add_column("InscriptionInternat", sa.Column("ResponsableContact", sa.String(50), nullable=True))

    # Rattache les admissions historiques à la même élève et à la même année.
    op.execute(sa.text(
        'UPDATE "InscriptionInternat" SET "IDEleve" = i."IDEleve", '
        '"IDTAnneeScolaire" = i."IDTAnneeScolaire" '
        'FROM "TInscription" i '
        'WHERE "InscriptionInternat"."IDTInscription" = i."IDTInscription"'
    ))
    op.alter_column("InscriptionInternat", "IDEleve", existing_type=sa.Integer(), nullable=False)
    op.alter_column("InscriptionInternat", "IDTAnneeScolaire", existing_type=sa.Integer(), nullable=False)
    op.alter_column("InscriptionInternat", "IDTInscription", existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key("fk_internat_eleve", "InscriptionInternat", "Eleve", ["IDEleve"], ["IDEleve"], ondelete="RESTRICT")
    op.create_foreign_key("fk_internat_annee", "InscriptionInternat", "TAnneeScolaire", ["IDTAnneeScolaire"], ["IDTAnneeScolaire"], ondelete="RESTRICT")
    op.create_unique_constraint("uq_internat_eleve_annee", "InscriptionInternat", ["IDEleve", "IDTAnneeScolaire"])
    op.create_check_constraint("ck_internat_origine_scolaire", "InscriptionInternat", '"OrigineScolaire" IN (\'COLLEGE\',\'EXTERNE\')')
    op.alter_column("InscriptionInternat", "OrigineScolaire", server_default=None)


def downgrade() -> None:
    # Une admission externe ne possède pas de TInscription et ne peut donc pas
    # être représentée par l'ancien schéma.
    op.execute(sa.text(
        'DELETE FROM "VersementInternat" WHERE "IDInscriptionInternat" IN '
        '(SELECT "IDInscriptionInternat" FROM "InscriptionInternat" WHERE "IDTInscription" IS NULL)'
    ))
    op.execute(sa.text('DELETE FROM "InscriptionInternat" WHERE "IDTInscription" IS NULL'))
    op.drop_constraint("ck_internat_origine_scolaire", "InscriptionInternat", type_="check")
    op.drop_constraint("uq_internat_eleve_annee", "InscriptionInternat", type_="unique")
    op.drop_constraint("fk_internat_annee", "InscriptionInternat", type_="foreignkey")
    op.drop_constraint("fk_internat_eleve", "InscriptionInternat", type_="foreignkey")
    op.alter_column("InscriptionInternat", "IDTInscription", existing_type=sa.Integer(), nullable=False)
    for column in (
        "ResponsableContact", "ResponsableNom", "ClasseFrequentee",
        "EtablissementFrequente", "OrigineScolaire", "IDTAnneeScolaire", "IDEleve",
    ):
        op.drop_column("InscriptionInternat", column)
