"""creer tables Vente et VenteLigne

Introduit des entites de vente structurees (audit D2) : la table StockSortie
ne stockait qu'une ligne d'article par vente, sans entete, sans total,
sans numero de recu, sans mode de paiement et sans possibilite d'annulation
tracee (contrairement a VersementScol/SortieFin, cf. B7).

Vente = entete (numero de recu, total, mode de paiement, annulation tracee).
VenteLigne = une ligne par article/KIT du panier (remplace StockSortie comme
registre des ventes a compter de cette revision).

StockSortie n'est PAS supprimee ici : elle reste en base, gelee (plus
alimentee par StockService/VenteService a partir de cette revision), pour
ne perdre aucun historique et eviter une suppression de table sur la base
reelle CJGA dont l'etat exact n'est pas connu depuis cette session (meme
prudence que C1 pour les blocs ad hoc geles).

Backfill : chaque ligne StockSortie existante devient une Vente a une seule
ligne (VenteLigne), decision actee avec l'utilisateur plutot que de tenter
de regrouper les lignes par vendeur+horodatage (heuristique non fiable, deux
paniers distincts vendus a la meme seconde par le meme caissier auraient ete
fusionnes a tort). Numerotation historique distincte ('V-HIST-<IDStockSort>')
pour ne jamais entrer en collision avec la numerotation des ventes futures
('V-<IDVente zero-pad>', generee par VenteService.process_sale a partir du
IDVente reellement attribue).

CREATE TABLE IF NOT EXISTS (verification via inspecteur) : comme pour
71dbc5eb1292/6f2b3468174e, une base neuve creee via create_tables()
(Base.metadata.create_all, le modele Vente/VenteLigne est deja declare) a
deja ces tables au moment ou cette revision est rejouee (bug decouvert par
la CI, chantier C2) — sur une base neuve, StockSortie est vide, le backfill
n'insere donc simplement rien.

Revision ID: 4736fb8c1846
Revises: c4f81d9e2a10
Create Date: 2026-07-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4736fb8c1846'
down_revision: Union[str, Sequence[str], None] = 'c4f81d9e2a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "Vente" not in existing_tables:
        op.create_table(
            "Vente",
            sa.Column("IDVente", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDTAnneeScolaire", sa.Integer(),
                      sa.ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False),
            sa.Column("NumeroRecu", sa.String(20), nullable=False),
            sa.Column("DateVente", sa.Date(), nullable=False),
            sa.Column("HeureVente", sa.Time(), nullable=False),
            sa.Column("ModePaiement", sa.String(30), nullable=False),
            sa.Column("MontantTotal", sa.Numeric(12, 2), nullable=False),
            sa.Column("Login", sa.String(50), nullable=True),
            sa.Column("Annule", sa.Boolean(), nullable=False),
            sa.Column("AnnulePar", sa.String(50), nullable=True),
            sa.Column("DateAnnulation", sa.DateTime(), nullable=True),
            sa.Column("MotifAnnulation", sa.Text(), nullable=True),
            sa.CheckConstraint('"MontantTotal" >= 0', name="ck_vente_montant_total_positif"),
            sa.UniqueConstraint("NumeroRecu", name="uq_vente_numero_recu"),
        )

    if "VenteLigne" not in existing_tables:
        op.create_table(
            "VenteLigne",
            sa.Column("IDVenteLigne", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDVente", sa.Integer(),
                      sa.ForeignKey("Vente.IDVente", ondelete="RESTRICT"), nullable=False),
            sa.Column("IDTArticle", sa.Integer(),
                      sa.ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False),
            sa.Column("Quantite", sa.Integer(), nullable=False),
            sa.Column("PrixUnitaire", sa.Numeric(12, 2), nullable=False),
            sa.Column("Total", sa.Numeric(12, 2), nullable=False),
            sa.CheckConstraint('"Quantite" > 0', name="ck_vente_ligne_quantite_positive"),
        )

    # Backfill : chaque StockSortie existante -> une Vente a une ligne unique.
    # No-op sur une base neuve (StockSortie vide). Idempotent par construction
    # de toute facon : cette revision ne s'applique qu'une seule fois par base
    # (suivie par alembic_version), donc pas besoin de garde-fou supplementaire
    # ici contrairement aux CREATE TABLE ci-dessus.
    op.execute(sa.text(
        """
        WITH ventes_inserees AS (
            INSERT INTO "Vente" (
                "IDTAnneeScolaire", "NumeroRecu", "DateVente", "HeureVente",
                "ModePaiement", "MontantTotal", "Login", "Annule"
            )
            SELECT
                s."IDTAnneeScolaire",
                'V-HIST-' || s."IDStockSort",
                s."DateSort",
                s."HeureSortie",
                'Espèce',
                s."QuantiteSort" * s."Prix_vente",
                s."Login",
                false
            FROM "StockSortie" s
            RETURNING "IDVente", "NumeroRecu"
        )
        INSERT INTO "VenteLigne" ("IDVente", "IDTArticle", "Quantite", "PrixUnitaire", "Total")
        SELECT vi."IDVente", s."IDTArticle", s."QuantiteSort", s."Prix_vente", s."QuantiteSort" * s."Prix_vente"
        FROM "StockSortie" s
        JOIN ventes_inserees vi ON vi."NumeroRecu" = 'V-HIST-' || s."IDStockSort"
        """
    ))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("VenteLigne")
    op.drop_table("Vente")
