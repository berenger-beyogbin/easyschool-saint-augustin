"""supprimer tables mortes prestations ventilation

Supprime les tables Prestataire / PrestationAnnexe / VentilationPrestation :
leurs modeles ont ete retires du code lors du refactor CJGA (commit 12b659d,
remplaces par InscriptionAutresFrais / VersementAutresFrais), mais
create_tables() ne fait que creer des tables, jamais en supprimer. Ces tables
sont donc restees orphelines sur toute base ayant tourne avec l'ancien schema.

ATTENTION : irreversible pour les donnees qu'elles contiennent (le downgrade
recree les tables et contraintes, pas les lignes). Sauvegarder la base avant
d'appliquer cette revision sur toute installation contenant des donnees
reelles.

Fichier nettoye a la main par rapport a l'autogenerate brut : les operations
de drop/recreate de cles etrangeres sur TInscription et VersementScol,
generees uniquement a cause de contraintes non nommees explicitement dans
les modeles (bruit de reflection, aucun changement fonctionnel), ont ete
retirees pour ne garder que la suppression des 3 tables mortes.

Correctif (decouvert par la CI, chantier C2) : les DROP INDEX/DROP TABLE
utilisent IF EXISTS. Sur une base entierement neuve creee avec le code
actuel, ces objets n'ont jamais existe (le modele VentilationPrestation et
le bloc ad hoc qui creait son index ont ete retires du code en meme temps
que ce refactor) : un DROP sans garde y echouerait, alors que cette
revision ne doit rien faire de plus qu'un no-op dans ce cas precis.

Revision ID: 057c2c9d281a
Revises: f0e0bbadf6a8
Create Date: 2026-07-16 20:47:21.638500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '057c2c9d281a'
down_revision: Union[str, Sequence[str], None] = 'f0e0bbadf6a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text('DROP INDEX IF EXISTS idx_ventilation_eleve_annee'))
    op.execute(sa.text('DROP TABLE IF EXISTS "VentilationPrestation"'))
    op.execute(sa.text('DROP TABLE IF EXISTS "PrestationAnnexe"'))
    op.execute(sa.text('DROP TABLE IF EXISTS "Prestataire"'))


def downgrade() -> None:
    """Downgrade schema.

    Recree la structure des 3 tables (colonnes, contraintes, index) telle
    qu'elle etait avant suppression. Ne restaure PAS les donnees qu'elles
    contenaient : ce downgrade sert a annuler un deploiement errone de cette
    revision, pas a recuperer des donnees perdues.
    """
    op.create_table(
        'Prestataire',
        sa.Column('IDPrestataire', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('Nom', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
        sa.Column('Contact', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column('Telephone', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.Column('Email', sa.VARCHAR(length=150), autoincrement=False, nullable=True),
        sa.Column('IsActive', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('CreatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('UpdatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('IDPrestataire', name=op.f('Prestataire_pkey')),
    )
    op.create_table(
        'PrestationAnnexe',
        sa.Column('IDPrestation', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('Code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
        sa.Column('Libelle', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
        sa.Column('MontantAnnuel', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
        sa.Column('IDPrestataire', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('IsActive', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('CreatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('UpdatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['IDPrestataire'], ['Prestataire.IDPrestataire'], name=op.f('PrestationAnnexe_IDPrestataire_fkey'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('IDPrestation', name=op.f('PrestationAnnexe_pkey')),
        sa.UniqueConstraint('Code', name=op.f('PrestationAnnexe_Code_key')),
    )
    op.create_table(
        'VentilationPrestation',
        sa.Column('IDVentilation', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('IDEleve', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('IDPrestation', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('IDAnneeScolaire', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('MontantVentile', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
        sa.Column('MontantTheorique', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
        sa.Column('TauxPaiement', sa.NUMERIC(precision=6, scale=4), autoincrement=False, nullable=False),
        sa.Column('ModeCalcul', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
        sa.Column('CalculeAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('CreatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('UpdatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['IDAnneeScolaire'], ['TAnneeScolaire.IDTAnneeScolaire'], name=op.f('VentilationPrestation_IDAnneeScolaire_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['IDEleve'], ['Eleve.IDEleve'], name=op.f('VentilationPrestation_IDEleve_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['IDPrestation'], ['PrestationAnnexe.IDPrestation'], name=op.f('VentilationPrestation_IDPrestation_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('IDVentilation', name=op.f('VentilationPrestation_pkey')),
        sa.UniqueConstraint('IDEleve', 'IDPrestation', 'IDAnneeScolaire', name=op.f('uq_ventilation_eleve_prestation_annee')),
    )
    op.create_index(op.f('idx_ventilation_eleve_annee'), 'VentilationPrestation', ['IDEleve', 'IDAnneeScolaire'], unique=False)
