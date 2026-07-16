# Plan de stabilisation — Easy School 2.0 CJGA

Base : audit complet du 2026-07-16 (révision auditée `47951ef`), constats
vérifiés manuellement dans le code avant integration ici (cascades, vente
non atomique, agregation comptable, import `QFont`, décompte Ruff — tous
confirmés exacts).

Statut de chaque item : `[ ]` a faire, `[~]` en cours, `[x]` fait.

---

## Phase A — Sécurisation immédiate (avant toute nouvelle diffusion)

- [ ] **A1** — Changer le mot de passe PostgreSQL utilisé par l'application ; créer un rôle dédié non-superuser. *(opérationnel, hors code)*
- [ ] **A2** — Produire une archive source propre (sans `.env`, `venv`, `build`, `dist`, `.git`).
- [ ] **A3** — Sauvegarde complète de la base réelle avant toute autre action. *(opérationnel)*
- [x] **A4** — Corriger l'import manquant `QFont` dans [views/stat_stock_view.py:6](views/stat_stock_view.py:6) (plante en rupture/alerte stock, lignes 134/137).
- [x] **A5** — Garde-fou immédiat côté service : refuser la suppression de classe/niveau dès qu'une inscription existe. `élève`, `famille` et `article` avaient déjà cette protection ; `année` n'a pas de méthode de suppression exposée (aucun risque). Tests ajoutés : [tests/test_classe_service.py](tests/test_classe_service.py), [tests/test_niveau_service.py](tests/test_niveau_service.py).
  - `versement` reste supprimable sans garde complète (seule l'année clôturée est vérifiée) : remplacer la suppression par une annulation tracée est le sujet propre de **B7**, pas un simple garde-fou — non traité ici pour éviter un changement de comportement non abouti.
- [x] **A6** — Corriger [MIGRATIONS.md](MIGRATIONS.md) : recommander `alembic stamp` sur la révision **baseline** (`f0e0bbadf6a8`), pas `head`, tant que la migration `057c2c9d281a` (suppression Prestataire/PrestationAnnexe/VentilationPrestation) n'a pas été volontairement appliquée sur la base concernée. Sinon Alembic marque une suppression comme faite alors qu'elle ne l'est pas.

## Phase B — Stabilisation critique des données

- [x] **B1** — CASCADE → RESTRICT sur les FK sensibles + migration Alembic dédiée + tests de non-suppression.
  Références : [models/inscription.py](models/inscription.py), [models/versement_scol.py](models/versement_scol.py), [models/stock_entree.py](models/stock_entree.py), [models/stock_sortie.py](models/stock_sortie.py), [models/montant_scol.py](models/montant_scol.py), migration [migrations/versions/1a7f16576697_cascade_vers_restrict_fk_sensibles.py](migrations/versions/1a7f16576697_cascade_vers_restrict_fk_sensibles.py).
  Vérifié réellement (SQL brut hors application) : suppression d'une classe/famille/année référencée par une inscription → bloquée par la contrainte DB. Tests : [tests/test_db_restrict_constraints.py](tests/test_db_restrict_constraints.py).
  **Non appliquée sur la base réelle CJGA** — seulement vérifiée sur la base de test jetable. À appliquer après sauvegarde (A3).
- [x] **B2** — Vente atomique : [StockService.process_sale](services/stock_service.py) en une seule transaction (verrouillage des lignes de stock, verification puis debit de tous les articles, un seul commit, aucune ecriture si un seul article manque). `views/vente_view.py::on_valider_vente` mis a jour pour l'utiliser. Testé : panier a 2 articles échouant sur le 2e → aucun stock modifié, aucune ligne de vente créée ([tests/test_stock_service.py](tests/test_stock_service.py)).
- [x] **B3** — Verrouillage concurrent du stock : `SELECT ... FOR UPDATE` dans `process_sale` (implémenté avec B2, même méthode) + `CHECK (QuantiteCour >= 0)` sur `StockCour` (migration [71dbc5eb1292](migrations/versions/71dbc5eb1292_check_quantite_stock_positive.py)). Testé réellement avec 2 threads concurrents sur un stock de 5 unités demandant 4 chacun : exactement une vente passe, l'autre échoue, stock final = 1 (jamais négatif).
- [x] **B4** — Verrouillage concurrent des encaissements : `create_versement` verrouille désormais la ligne `TInscription` (`SELECT ... FOR UPDATE`) de l'élève avant de calculer le reste à payer, serialisant deux versements concurrents sur le même élève.
  Référence : [services/versement_service.py](services/versement_service.py). Testé réellement avec 2 threads concurrents payant 60 000 F chacun sur une scolarité due à 100 000 F : une seule des deux réussit, reste final = 40 000 F (jamais dépassé). Test : [tests/test_versement_service.py](tests/test_versement_service.py).
- [ ] **B5** — Intégrer `MontantVersAutres` dans la balance comptable (compte SYSCOA à définir avec le comptable, ex. `7045`).
  Référence : [services/comptabilite_service.py:296-344](services/comptabilite_service.py:296) (`get_totaux_entrees_rubriques` n'agrège que scolarité/transport/cantine/vente).
- [ ] **B6** — Choisir une stratégie unique contre la double comptabilisation : écritures automatiques liées par ID à l'opération source, et interdire le crédit manuel sur les comptes réservés (7041-7044).
  Référence : [services/comptabilite_service.py:249-302](services/comptabilite_service.py:249).
- [ ] **B7** — Remplacer la suppression physique des écritures financières par une annulation tracée (`Annule`, `AnnulePar`, `DateAnnulation`, `MotifAnnulation` + contre-écriture).
  Référence : `services/comptabilite_service.py::delete_mouvement` (~ligne 163-183).
- [ ] **B8** — Table `AuditLog` : utilisateur par `IDUtilisateur` (pas juste `Login` texte), ancienne/nouvelle valeur, horodatage, motif.

## Phase C — Industrialisation technique

- [ ] **C1** — Alembic comme seul mécanisme de migration ; retirer progressivement les blocs `ALTER TABLE` ad hoc de `app/database.py::create_tables()`.
- [ ] **C2** — CI avec PostgreSQL éphémère, tests indépendants de `easy_school_test_db`, exécution Ruff + pytest + migrations sur chaque pull request.
- [ ] **C3** — Logging structuré : remplacer les ~173 `except Exception` / ~99 `print()` / 2 `except:` nus par un logging avec identifiant d'incident et message utilisateur neutre.
- [ ] **C4** — Sauvegardes automatiques (quotidiennes, chiffrées, rotation) + restauration testée mensuellement.
- [ ] **C5** — Nettoyage des 137 erreurs Ruff (89 imports inutilisés, 17 comparaisons booléennes non idiomatiques, 8 noms non définis, 6 noms ambigus, 5 instructions multi-lignes, 2 `except:` nus, 2 variables inutilisées — décompte confirmé via `ruff check . --statistics`).
- [ ] **C6** — Signature de code et versionnement de l'exécutable PyInstaller.

## Phase D — Refactorisation et évolutivité

- [ ] **D1** — Centraliser les règles de tarification (réduction Ebrié d'Abobo-té, supplément nouveaux élèves, réduction 3e enfant) actuellement dupliquées dans `versement_service.py`, `dashboard_service.py`, `statistiques_service.py`.
- [ ] **D2** — Entités `Vente`/`VenteLigne` structurées (entête, total, numéro de reçu, mode de paiement, statut, annulation).
- [ ] **D3** — Normaliser les Kits (`Kit`/`KitArticle` relationnels au lieu de chaînes de texte).
- [ ] **D4** — Scinder les gros fichiers : `utils/list_printer.py` (1490 lignes), `app/styles.py` (1284), `views/caisse_view.py` (995), `views/inscription_view.py` (972), `views/main_window.py` (776), `views/utilisateurs_view.py` (747).
- [ ] **D5** — Pagination et traitements asynchrones (éviter le gel de l'UI sur requêtes/impressions lourdes).
- [ ] **D6** — Nettoyer ou isoler les modules désactivés (cantine, transport, bibliothèque).
- [ ] **D7** — Documentation à jour (README obsolète, dépôt distant encore nommé `easyschool-saint-augustin`).

---

## Tests de recette obligatoires (mappés aux items ci-dessus)

| # | Scénario | Item concerné |
|---|---|---|
| 1 | Une classe contenant une inscription ne peut pas être supprimée | A5, B1 |
| 2 | Un élève avec versements ne peut pas être supprimé physiquement | A5, B1 |
| 3 | Une vente de 3 articles échouant sur le 3e ne modifie aucun stock | B2 |
| 4 | Deux ventes concurrentes ne produisent jamais un stock négatif | B3 |
| 5 | Deux encaissements concurrents ne dépassent jamais le reste dû | B4 |
| 6 | Une réduction ne gonfle pas la recette | B6 |
| 7 | Une restitution réduit correctement la recette | B6 |
| 8 | Les autres frais apparaissent exactement une fois dans la balance | B5 |
| 9 | Une écriture annulée reste visible avec son motif | B7 |
| 10 | Une année clôturée bloque toutes les écritures/modifications concernées | B1-B4 (déjà partiellement en place) |
| 11 | Une migration complète réussit sur une copie de la base | A6, C1 |
| 12 | Une sauvegarde peut être restaurée et les totaux concordent | A3, C4 |
| 13 | Ruff ne signale plus de nom non défini ni de `except:` nu | C5 |
| 14 | Tous les tests passent automatiquement en CI | C2 |
| 15 | L'exécutable démarre depuis un raccourci Windows avec sa config correcte | C6, P1-12 (non repris ci-dessus, a traiter avec C1/C4) |

---

## Notes de suivi

- 2026-07-16 : plan créé à partir de l'audit externe, constats spot-vérifiés dans le code avant intégration.
- 2026-07-16 : Phase A terminée côté code (A4, A5, A6). A1/A2/A3 restent opérationnels, à la charge de l'équipe (mot de passe, archive, sauvegarde serveur). 31/31 tests passent.
