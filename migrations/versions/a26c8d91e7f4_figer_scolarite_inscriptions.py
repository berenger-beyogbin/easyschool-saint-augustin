"""Figer la scolarite appliquee sur chaque inscription.

Revision ID: a26c8d91e7f4
Revises: f19c4d72a8b1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "a26c8d91e7f4"
down_revision = "f19c4d72a8b1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    colonnes = {c["name"] for c in inspect(bind).get_columns("TInscription")}
    if "MontantScolariteApplique" not in colonnes:
        op.add_column(
            "TInscription",
            sa.Column("MontantScolariteApplique", sa.Numeric(12, 2), nullable=True),
        )

    # Fige exactement l'ancien calcul avant sa suppression : reduction Ebrie,
    # surcharge nouvel affecte, puis reduction du 3e enfant et suivants.
    op.execute(sa.text('''
        WITH inscriptions_ordonnees AS (
            SELECT i."IDTInscription",
                   i."Nouveau",
                   i."StatutAffectation",
                   COALESCE(f."EbrieAbobote", FALSE) AS ebrie,
                   ROW_NUMBER() OVER (
                       PARTITION BY i."IDTAnneeScolaire", i."IDFamille"
                       ORDER BY i."IDTInscription"
                   ) AS rang_famille,
                   COUNT(*) OVER (
                       PARTITION BY i."IDTAnneeScolaire", i."IDFamille"
                   ) AS nb_famille,
                   CASE WHEN i."StatutAffectation" = 'NON_AFFECTE_ETAT'
                        THEN COALESCE(ms."MontantNonAffecte", 0)
                        ELSE COALESCE(ms."MontantAffecte", 0)
                   END AS base
            FROM "TInscription" i
            LEFT JOIN "TFamille" f ON f."IdTFamille" = i."IDFamille"
            LEFT JOIN "MontantScol" ms
              ON ms."IDTAnneeScolaire" = i."IDTAnneeScolaire"
             AND ms."IDNiveau" = i."IDNiveau"
        ), anciens_calculs AS (
            SELECT "IDTInscription",
                   GREATEST(
                       0,
                       GREATEST(0, base - CASE WHEN ebrie THEN 10000 ELSE 0 END)
                       + CASE WHEN "Nouveau" AND "StatutAffectation" = 'AFFECTE_ETAT'
                              THEN 15000 ELSE 0 END
                       - CASE WHEN nb_famille >= 3 AND rang_famille >= 3
                              THEN 10000 ELSE 0 END
                   ) AS montant
            FROM inscriptions_ordonnees
        )
        UPDATE "TInscription" i
           SET "MontantScolariteApplique" = c.montant
          FROM anciens_calculs c
         WHERE c."IDTInscription" = i."IDTInscription"
    '''))

    # Grille CJGA 2026-2027. Les niveaux sont propres a l'annee scolaire ;
    # le premier chiffre du libelle identifie 6e/5e/4e/3e sans imposer une
    # orthographe particuliere (6e, 6eme, 6ieme...).
    op.execute(sa.text('''
        INSERT INTO "MontantScol"
            ("IDTAnneeScolaire", "IDNiveau", "MontantAffecte", "MontantNonAffecte")
        SELECT a."IDTAnneeScolaire", n."IDT_Niveau", 120000,
               CASE LEFT(TRIM(n."Libelle"), 1)
                   WHEN '6' THEN 190000
                   WHEN '5' THEN 195000
                   WHEN '4' THEN 200000
                   WHEN '3' THEN 215000
               END
          FROM "TAnneeScolaire" a
          JOIN "TNiveau" n ON n."IDAnneeScolaire" = a."IDTAnneeScolaire"
         WHERE a."Libelle" = '2026-2027'
           AND LEFT(TRIM(n."Libelle"), 1) IN ('6', '5', '4', '3')
        ON CONFLICT ("IDTAnneeScolaire", "IDNiveau") DO UPDATE
            SET "MontantAffecte" = EXCLUDED."MontantAffecte",
                "MontantNonAffecte" = EXCLUDED."MontantNonAffecte"
    '''))

    # Contrairement aux annees historiques, les inscriptions 2026-2027
    # doivent adopter la nouvelle grille qui vient d'etre validee. Les
    # versements existants ne sont jamais modifies ni supprimes.
    op.execute(sa.text('''
        UPDATE "TInscription" i
           SET "MontantScolariteApplique" =
               CASE WHEN i."StatutAffectation" = 'NON_AFFECTE_ETAT'
                    THEN ms."MontantNonAffecte"
                    ELSE ms."MontantAffecte"
               END
          FROM "TAnneeScolaire" a, "MontantScol" ms
         WHERE a."IDTAnneeScolaire" = i."IDTAnneeScolaire"
           AND a."Libelle" = '2026-2027'
           AND ms."IDTAnneeScolaire" = i."IDTAnneeScolaire"
           AND ms."IDNiveau" = i."IDNiveau"
    '''))

    op.execute(sa.text('''
        INSERT INTO "Autres_Frais" ("CodeFrais", "LibelleFrais") VALUES
            ('POLOS2', '2 polos'),
            ('TENUE_F2', '2 polos et 2 jupes'),
            ('FOUR_NOUV', 'Feuilles et classeur'),
            ('FEUIL_ANC', 'Feuilles')
        ON CONFLICT ("CodeFrais") DO UPDATE
            SET "LibelleFrais" = EXCLUDED."LibelleFrais"
    '''))

    # Migration prudente : seules les inscriptions 2026-2027 qui n'ont
    # encore aucune ligne de frais sont completees automatiquement. Les cas
    # possedant deja des frais restent intacts pour eviter une double facture.
    op.execute(sa.text('''
        INSERT INTO "InscriptionAutresFrais"
            ("IDTInscription", "IDAutres_Frais", "MontantApplique", "Obligatoire",
             "DateCreation", "Login", "LibelleSnapshot", "CodeFraisSnapshot")
        SELECT i."IDTInscription", f."IDAutres_Frais",
               CASE f."CodeFrais"
                   WHEN 'POLOS2' THEN 12000
                   WHEN 'TENUE_F2' THEN 24000
                   WHEN 'FOUR_NOUV' THEN 13000
                   WHEN 'FEUIL_ANC' THEN 10000
               END,
               TRUE, CURRENT_DATE, 'MIGRATION-2026-2027', f."LibelleFrais", f."CodeFrais"
          FROM "TInscription" i
          JOIN "TAnneeScolaire" a ON a."IDTAnneeScolaire" = i."IDTAnneeScolaire"
          JOIN "Eleve" e ON e."IDEleve" = i."IDEleve"
          JOIN "Autres_Frais" f ON f."CodeFrais" IN (
              CASE WHEN i."Nouveau" THEN CASE WHEN e."Sexe" = 2 THEN 'TENUE_F2' ELSE 'POLOS2' END
                   ELSE 'FEUIL_ANC' END,
              CASE WHEN i."Nouveau" THEN 'FOUR_NOUV' ELSE 'FEUIL_ANC' END
          )
         WHERE a."Libelle" = '2026-2027'
           AND NOT EXISTS (
               SELECT 1 FROM "InscriptionAutresFrais" iaf
                WHERE iaf."IDTInscription" = i."IDTInscription"
           )
        ON CONFLICT ("IDTInscription", "IDAutres_Frais") DO NOTHING
    '''))

    op.execute(sa.text('''
        UPDATE "TInscription" i SET "AutresFrais" = TRUE
         FROM "TAnneeScolaire" a
         WHERE a."IDTAnneeScolaire" = i."IDTAnneeScolaire"
           AND a."Libelle" = '2026-2027'
           AND EXISTS (
               SELECT 1 FROM "InscriptionAutresFrais" iaf
                WHERE iaf."IDTInscription" = i."IDTInscription"
                  AND iaf."Obligatoire" = TRUE
           )
    '''))


def downgrade():
    op.drop_column("TInscription", "MontantScolariteApplique")
