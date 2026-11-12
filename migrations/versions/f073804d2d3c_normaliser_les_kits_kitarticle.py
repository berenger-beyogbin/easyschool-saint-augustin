"""normaliser les kits (KitArticle relationnel)

Introduit une table relationnelle pour la composition des KITs (audit D3) :
Article.ContenuKit/QteKit ("1;4;7" / "2;1;3", texte libre sans FK, sans
garantie de longueur egale entre les deux, sans validation d'existence des
IDs) sont remplaces par KitArticle (IDKit, IDArticleComposant, Quantite),
avec vraies contraintes : FK vers TArticle, CHECK Quantite > 0, unicite
(IDKit, IDArticleComposant).

Comportement metier egalement change (decide avec l'utilisateur) : un KIT
n'a plus sa propre ligne de stock (StockCour) alimentee manuellement au
reapprovisionnement. Sa quantite vendable est desormais deduite en temps
reel du stock de ses composants (services/stock_service.py::
get_stock_disponible), et sa vente decompte directement le stock des
composants (services/vente_service.py::process_sale). Les StockCour
existantes d'anciens KITs ne sont pas supprimees ici (juste devenues
inertes, plus jamais lues ni ecrites) : meme prudence que pour StockSortie
en D2, aucune suppression de donnees sur la base reelle CJGA sans confirmation.

Backfill : chaque paire (ContenuKit, QteKit) existante est parsee en Python
(pas en SQL brut - la logique de tolerance aux erreurs, deja implicitement
definie par l'ancien formulaire KitFormView qui ignorait silencieusement les
entrees non numeriques ou desequilibrees, est plus sure a exprimer ainsi) :
- jetons non numeriques ignores (memes garanties que l'ancien formulaire) ;
- les deux listes sont appariees comme zip() le faisait deja (troncature a
  la plus courte si elles n'ont jamais ete de meme longueur) ;
- IDs ne correspondant a aucun article existant ignores ;
- IDs pointant vers un autre KIT ignores (l'ancien formulaire ne permettait
  deja pas de choisir un KIT comme composant) ;
- quantites <= 0 ignorees ;
- doublons de composant au sein d'un meme KIT fusionnes (quantites sommees)
  plutot que rejetes, pour ne perdre aucune donnee historique meme improbable.

ContenuKit/QteKit sont supprimees a la fin de cette meme revision, une fois
le backfill effectue (decide avec l'utilisateur : contrairement a
StockSortie, ce ne sont pas des donnees historiques mais seulement l'etat
courant d'un KIT, integralement repris dans KitArticle - les garder crEerait
un risque de desynchronisation permanente, aucune valeur a preserver).

CREATE TABLE IF NOT EXISTS (verification via inspecteur) et backfill/DROP
COLUMN gardes par verification d'existence prealable : meme piege que
71dbc5eb1292/6f2b3468174e/4736fb8c1846 - une base neuve creee via
create_tables() (le modele Article ne declare deja plus ContenuKit/QteKit)
n'a jamais eu ces colonnes, le backfill doit donc etre un no-op silencieux
dans ce cas plutot qu'une erreur "colonne introuvable".

Revision ID: f073804d2d3c
Revises: 4736fb8c1846
Create Date: 2026-07-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f073804d2d3c'
down_revision: Union[str, Sequence[str], None] = '4736fb8c1846'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "KitArticle" not in existing_tables:
        op.create_table(
            "KitArticle",
            sa.Column("IDKitArticle", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("IDKit", sa.Integer(),
                      sa.ForeignKey("TArticle.IDTArticle", ondelete="CASCADE"), nullable=False),
            sa.Column("IDArticleComposant", sa.Integer(),
                      sa.ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False),
            sa.Column("Quantite", sa.Integer(), nullable=False),
            sa.CheckConstraint('"Quantite" > 0', name="ck_kit_article_quantite_positive"),
            sa.UniqueConstraint("IDKit", "IDArticleComposant", name="uq_kit_article_kit_composant"),
        )

    # Backfill depuis ContenuKit/QteKit, uniquement si ces colonnes existent
    # encore (no-op sur une base neuve ou elles n'ont jamais ete creees).
    existing_columns = {c["name"] for c in inspector.get_columns("TArticle")}
    if "ContenuKit" in existing_columns and "QteKit" in existing_columns:
        kits = conn.execute(sa.text(
            'SELECT "IDTArticle", "ContenuKit", "QteKit" FROM "TArticle" WHERE "KIT" = true'
        )).fetchall()

        tous_les_ids = {
            row[0] for row in conn.execute(sa.text('SELECT "IDTArticle" FROM "TArticle"')).fetchall()
        }
        ids_kits = {row[0] for row in kits}

        for id_kit, contenu_kit, qte_kit in kits:
            if not contenu_kit or not qte_kit:
                continue
            ids_str = [x.strip() for x in contenu_kit.split(";")]
            qtes_str = [x.strip() for x in qte_kit.split(";")]

            composition: dict[int, int] = {}
            for id_str, qte_str in zip(ids_str, qtes_str):
                try:
                    id_composant = int(id_str)
                    qte = int(qte_str)
                except ValueError:
                    continue
                if qte <= 0:
                    continue
                if id_composant == id_kit:
                    continue
                if id_composant not in tous_les_ids or id_composant in ids_kits:
                    continue
                composition[id_composant] = composition.get(id_composant, 0) + qte

            for id_composant, qte in composition.items():
                conn.execute(sa.text(
                    'INSERT INTO "KitArticle" ("IDKit", "IDArticleComposant", "Quantite") '
                    'VALUES (:id_kit, :id_composant, :qte)'
                ), {"id_kit": id_kit, "id_composant": id_composant, "qte": qte})

        op.execute(sa.text('ALTER TABLE "TArticle" DROP COLUMN IF EXISTS "ContenuKit"'))
        op.execute(sa.text('ALTER TABLE "TArticle" DROP COLUMN IF EXISTS "QteKit"'))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text('ALTER TABLE "TArticle" ADD COLUMN IF NOT EXISTS "ContenuKit" TEXT'))
    op.execute(sa.text('ALTER TABLE "TArticle" ADD COLUMN IF NOT EXISTS "QteKit" TEXT'))

    conn = op.get_bind()
    kits = conn.execute(sa.text(
        'SELECT DISTINCT "IDKit" FROM "KitArticle" ORDER BY "IDKit"'
    )).fetchall()
    for (id_kit,) in kits:
        lignes = conn.execute(sa.text(
            'SELECT "IDArticleComposant", "Quantite" FROM "KitArticle" '
            'WHERE "IDKit" = :id_kit ORDER BY "IDKitArticle"'
        ), {"id_kit": id_kit}).fetchall()
        contenu_kit = ";".join(str(ligne[0]) for ligne in lignes)
        qte_kit = ";".join(str(ligne[1]) for ligne in lignes)
        conn.execute(sa.text(
            'UPDATE "TArticle" SET "ContenuKit" = :contenu, "QteKit" = :qte WHERE "IDTArticle" = :id_kit'
        ), {"contenu": contenu_kit, "qte": qte_kit, "id_kit": id_kit})

    op.drop_table("KitArticle")
