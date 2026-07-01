-- ===========================================================
-- EASY SCHOOL 2.0 — SAFE_DB_CONSTRAINT_REVIEW.sql
-- SCRIPT D'INSPECTION DES CONTRAINTES POSTGRESQL
-- ===========================================================
-- ATTENTION : Ce script NE MODIFIE PAS la base de données.
-- Il contient uniquement des requêtes SELECT pour inspecter
-- les contraintes existantes et les risques de CASCADE.
-- À exécuter manuellement avec un outil PostgreSQL (pgAdmin, psql, DBeaver).
-- ===========================================================

-- ===========================================================
-- 1. LISTE DE TOUTES LES CONTRAINTES DE CLÉ ÉTRANGÈRE
--    Permet d'identifier les ON DELETE CASCADE en base
-- ===========================================================
SELECT
    tc.table_name            AS table_source,
    kcu.column_name          AS colonne_fk,
    ccu.table_name           AS table_cible,
    ccu.column_name          AS colonne_cible,
    rc.delete_rule           AS regle_suppression,
    rc.update_rule           AS regle_mise_a_jour,
    tc.constraint_name       AS nom_contrainte
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
    AND tc.table_schema = rc.constraint_schema
JOIN information_schema.key_column_usage ccu
    ON rc.unique_constraint_name = ccu.constraint_name
    AND rc.unique_constraint_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;


-- ===========================================================
-- 2. CONTRAINTES CASCADE IDENTIFIÉES COMME RISQUÉES
--    Ces FK ont ON DELETE CASCADE et concernent des données métier
-- ===========================================================
-- Tables à risque détectées lors du diagnostic :
--
--   VersementScol.IDFamille  → TFamille    (CASCADE) ⚠️
--   VersementScol.IDEleve    → Eleve       (CASCADE) ⚠️
--   TInscription.IDEleve     → Eleve       (CASCADE) ⚠️
--   TInscription.IDFamille   → TFamille    (CASCADE) ⚠️
--
-- Vérification ciblée :
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS references_table,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
JOIN information_schema.key_column_usage ccu
    ON rc.unique_constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND rc.delete_rule = 'CASCADE'
  AND tc.table_name IN ('VersementScol', 'TInscription')
ORDER BY tc.table_name;


-- ===========================================================
-- 3. COMPTER LES ENREGISTREMENTS POTENTIELLEMENT PERDUS
--    En cas de suppression d'un élève ou d'une famille
-- ===========================================================

-- Versements par élève (combien de versements seraient supprimés si l'élève était supprimé)
SELECT
    e."IDEleve",
    e."Matricule",
    e."Nom" || ' ' || e."Prenoms" AS eleve,
    COUNT(v."IDVersementScol") AS nb_versements
FROM "Eleve" e
LEFT JOIN "VersementScol" v ON v."IDEleve" = e."IDEleve"
GROUP BY e."IDEleve", e."Matricule", e."Nom", e."Prenoms"
HAVING COUNT(v."IDVersementScol") > 0
ORDER BY nb_versements DESC;

-- Versements par famille (combien de versements seraient supprimés si la famille était supprimée)
SELECT
    f."IdTFamille",
    f."NomResponsable",
    COUNT(v."IDVersementScol") AS nb_versements
FROM "TFamille" f
LEFT JOIN "VersementScol" v ON v."IDFamille" = f."IdTFamille"
GROUP BY f."IdTFamille", f."NomResponsable"
HAVING COUNT(v."IDVersementScol") > 0
ORDER BY nb_versements DESC;


-- ===========================================================
-- 4. ÉLÈVES AVEC INSCRIPTIONS ET VERSEMENTS
--    Détecte les élèves qui ont des données imbriquées critiques
-- ===========================================================
SELECT
    e."IDEleve",
    e."Matricule",
    e."Nom" || ' ' || e."Prenoms" AS eleve,
    COUNT(DISTINCT i."IDTInscription") AS nb_inscriptions,
    COUNT(DISTINCT v."IDVersementScol") AS nb_versements,
    COALESCE(SUM(v."MontantVersSco"), 0) AS total_scol_verse
FROM "Eleve" e
LEFT JOIN "TInscription" i ON i."IDEleve" = e."IDEleve"
LEFT JOIN "VersementScol" v ON v."IDEleve" = e."IDEleve"
GROUP BY e."IDEleve", e."Matricule", e."Nom", e."Prenoms"
ORDER BY nb_versements DESC, nb_inscriptions DESC;


-- ===========================================================
-- 5. FAMILLES AVEC ÉLÈVES — Nombre d'élèves par famille
-- ===========================================================
SELECT
    f."IdTFamille",
    f."NomResponsable",
    f."CellulaireResponsable",
    COUNT(e."IDEleve") AS nb_eleves
FROM "TFamille" f
LEFT JOIN "Eleve" e ON e."IDFamille" = f."IdTFamille"
GROUP BY f."IdTFamille", f."NomResponsable", f."CellulaireResponsable"
ORDER BY nb_eleves DESC;


-- ===========================================================
-- 6. RECOMMANDATION (NON EXÉCUTÉ — DOCUMENTATION UNIQUEMENT)
-- ===========================================================
-- Pour sécuriser les FK en production, remplacer ON DELETE CASCADE
-- par ON DELETE RESTRICT sur les tables métier sensibles.
-- Ces instructions MODIFIENT le schéma — ne pas exécuter sans sauvegarde.
--
-- EXEMPLE (À NE PAS EXÉCUTER SANS VALIDATION) :
--
-- ALTER TABLE "VersementScol"
--     DROP CONSTRAINT IF EXISTS "versementscol_idfamille_fkey",
--     ADD CONSTRAINT "versementscol_idfamille_fkey"
--         FOREIGN KEY ("IDFamille") REFERENCES "TFamille"("IdTFamille")
--         ON DELETE RESTRICT;
--
-- ALTER TABLE "VersementScol"
--     DROP CONSTRAINT IF EXISTS "versementscol_ideleve_fkey",
--     ADD CONSTRAINT "versementscol_ideleve_fkey"
--         FOREIGN KEY ("IDEleve") REFERENCES "Eleve"("IDEleve")
--         ON DELETE RESTRICT;
--
-- NOTE : Avant d'exécuter, faire une sauvegarde complète de la base :
--   pg_dump -U postgres -h localhost easy_school_db > backup_avant_migration_$(date +%Y%m%d).sql
-- ===========================================================
