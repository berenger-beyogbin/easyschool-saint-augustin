"""ajouter module cantine externe

Revision ID: 7d3f9c1e4b82
Revises: d84f1a2c7b90
Create Date: 2026-09-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d3f9c1e4b82"
down_revision: Union[str, Sequence[str], None] = "d84f1a2c7b90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = inspector.get_table_names()
    if "CantineTarif" not in existing:
        op.create_table(
            "CantineTarif",
            sa.Column("IDTarifCantine", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDTAnneeScolaire", sa.Integer(), sa.ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False),
            sa.Column("Montant", sa.Numeric(12, 2), nullable=False, server_default="50000"),
            sa.Column("Actif", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("IDTAnneeScolaire", name="uq_cantine_tarif_annee"),
            sa.CheckConstraint('"Montant" >= 0', name="ck_cantine_tarif_positif"),
        )
    if "InscriptionCantine" not in existing:
        op.create_table(
            "InscriptionCantine",
            sa.Column("IDInscriptionCantine", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDEleve", sa.Integer(), sa.ForeignKey("Eleve.IDEleve", ondelete="RESTRICT"), nullable=False),
            sa.Column("IDTAnneeScolaire", sa.Integer(), sa.ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False),
            sa.Column("MontantTotal", sa.Numeric(12, 2), nullable=False),
            sa.Column("DateInscription", sa.Date(), nullable=False),
            sa.Column("ResponsableNom", sa.String(150), nullable=True),
            sa.Column("ResponsableContact", sa.String(50), nullable=True),
            sa.Column("Statut", sa.String(15), nullable=False, server_default="EN_COURS"),
            sa.Column("DateSortie", sa.Date(), nullable=True),
            sa.Column("MotifSortie", sa.Text(), nullable=True),
            sa.Column("Login", sa.String(50), nullable=True),
            sa.UniqueConstraint("IDEleve", "IDTAnneeScolaire", name="uq_cantine_eleve_annee"),
            sa.CheckConstraint("\"Statut\" IN ('EN_COURS','SOLDE','SUSPENDU','SORTIE')", name="ck_cantine_statut"),
            sa.CheckConstraint('"MontantTotal" >= 0', name="ck_cantine_montant_total_positif"),
        )
    if "VersementCantine" not in existing:
        op.create_table(
            "VersementCantine",
            sa.Column("IDVersementCantine", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDInscriptionCantine", sa.Integer(), sa.ForeignKey("InscriptionCantine.IDInscriptionCantine", ondelete="RESTRICT"), nullable=False),
            sa.Column("NumeroRecu", sa.String(40), nullable=False),
            sa.Column("DateVersement", sa.Date(), nullable=False),
            sa.Column("Montant", sa.Numeric(12, 2), nullable=False),
            sa.Column("ModePaiement", sa.String(30), nullable=False, server_default="ESPECES"),
            sa.Column("ReferencePaiement", sa.String(80), nullable=True),
            sa.Column("Login", sa.String(50), nullable=True),
            sa.Column("Annule", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("AnnulePar", sa.String(50), nullable=True),
            sa.Column("DateAnnulation", sa.DateTime(), nullable=True),
            sa.Column("MotifAnnulation", sa.Text(), nullable=True),
            sa.UniqueConstraint("NumeroRecu", name="uq_versement_cantine_numero_recu"),
            sa.CheckConstraint('"Montant" > 0', name="ck_versement_cantine_montant_positif"),
        )


def downgrade() -> None:
    op.drop_table("VersementCantine")
    op.drop_table("InscriptionCantine")
    op.drop_table("CantineTarif")
