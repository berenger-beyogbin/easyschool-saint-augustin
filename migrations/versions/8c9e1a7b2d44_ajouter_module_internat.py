"""ajouter module internat

Revision ID: 8c9e1a7b2d44
Revises: f073804d2d3c
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c9e1a7b2d44"
down_revision: Union[str, Sequence[str], None] = "f073804d2d3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = inspector.get_table_names()
    if "InternatEcheance" not in existing:
        op.create_table(
            "InternatEcheance",
            sa.Column("IDEcheance", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDTAnneeScolaire", sa.Integer(), sa.ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False),
            sa.Column("Code", sa.String(30), nullable=False),
            sa.Column("Libelle", sa.String(80), nullable=False),
            sa.Column("Ordre", sa.Integer(), nullable=False),
            sa.Column("DateLimite", sa.Date(), nullable=True),
            sa.Column("MontantNouvelle", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("MontantAncienne", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("Actif", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("IDTAnneeScolaire", "Code", name="uq_internat_echeance_annee_code"),
            sa.CheckConstraint('"MontantNouvelle" >= 0', name="ck_internat_echeance_nouvelle_positif"),
            sa.CheckConstraint('"MontantAncienne" >= 0', name="ck_internat_echeance_ancienne_positif"),
        )
    if "InscriptionInternat" not in existing:
        op.create_table(
            "InscriptionInternat",
            sa.Column("IDInscriptionInternat", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDTInscription", sa.Integer(), sa.ForeignKey("TInscription.IDTInscription", ondelete="RESTRICT"), nullable=False),
            sa.Column("TypePensionnaire", sa.String(10), nullable=False),
            sa.Column("DateAdmission", sa.Date(), nullable=False),
            sa.Column("DateDebutPension", sa.Date(), nullable=False),
            sa.Column("MontantAnnuel", sa.Numeric(12, 2), nullable=False),
            sa.Column("Statut", sa.String(25), nullable=False, server_default="DOSSIER_INCOMPLET"),
            sa.Column("DateSortie", sa.Date(), nullable=True),
            sa.Column("MotifSortie", sa.Text(), nullable=True),
            sa.Column("Login", sa.String(50), nullable=True),
            sa.UniqueConstraint("IDTInscription", name="uq_internat_inscription_scolaire"),
            sa.CheckConstraint("\"TypePensionnaire\" IN ('NOUVELLE','ANCIENNE')", name="ck_internat_type_pensionnaire"),
            sa.CheckConstraint("\"Statut\" IN ('DOSSIER_INCOMPLET','EN_ATTENTE_PAIEMENT','ADMISE','SUSPENDUE','SORTIE')", name="ck_internat_statut"),
            sa.CheckConstraint('"MontantAnnuel" >= 0', name="ck_internat_montant_annuel_positif"),
        )
    if "InternatPieceDossier" not in existing:
        op.create_table(
            "InternatPieceDossier",
            sa.Column("IDPieceDossier", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDInscriptionInternat", sa.Integer(), sa.ForeignKey("InscriptionInternat.IDInscriptionInternat", ondelete="CASCADE"), nullable=False),
            sa.Column("CodePiece", sa.String(40), nullable=False),
            sa.Column("Libelle", sa.String(160), nullable=False),
            sa.Column("Obligatoire", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("QuantiteDemandee", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("QuantiteRecue", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("DateReception", sa.Date(), nullable=True),
            sa.Column("Observation", sa.Text(), nullable=True),
            sa.Column("VerifiePar", sa.String(50), nullable=True),
            sa.UniqueConstraint("IDInscriptionInternat", "CodePiece", name="uq_internat_dossier_piece"),
            sa.CheckConstraint('"QuantiteDemandee" > 0', name="ck_internat_piece_qte_demandee"),
            sa.CheckConstraint('"QuantiteRecue" >= 0', name="ck_internat_piece_qte_recue"),
        )
    if "VersementInternat" not in existing:
        op.create_table(
            "VersementInternat",
            sa.Column("IDVersementInternat", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDInscriptionInternat", sa.Integer(), sa.ForeignKey("InscriptionInternat.IDInscriptionInternat", ondelete="RESTRICT"), nullable=False),
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
            sa.UniqueConstraint("NumeroRecu", name="uq_versement_internat_numero_recu"),
            sa.CheckConstraint('"Montant" > 0', name="ck_versement_internat_montant_positif"),
        )


def downgrade() -> None:
    op.drop_table("VersementInternat")
    op.drop_table("InternatPieceDossier")
    op.drop_table("InscriptionInternat")
    op.drop_table("InternatEcheance")
