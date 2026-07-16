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
- [x] **B5** — Intégré `MontantVersAutres` dans la balance comptable via un nouveau compte SYSCOA `7045 - AUTRES FRAIS` (à valider avec le comptable si un autre numéro est préféré). `get_totaux_entrees_rubriques` agrège désormais aussi les autres frais ; `views/balance_comptes_view.py` reprend automatiquement le nouveau compte (dict `SYSCOA_INCOME_ACCOUNTS`, pas de code en dur). Testé : recette #8 (autres frais exactement une fois dans la balance). [tests/test_comptabilite_service.py](tests/test_comptabilite_service.py).
- [x] **B6** — Stratégie retenue (la plus simple des deux proposées par l'audit, pas celle des écritures auto liées par ID — plus lourde, laissée pour une itération future si besoin) : `create_mouvement`/`update_mouvement` refusent désormais tout crédit manuel sur un compte SYSCOA réservé (7041-7045), déjà alimenté automatiquement par les versements/ventes. Le débit manuel (corrections) reste possible.
  Référence : [services/comptabilite_service.py](services/comptabilite_service.py). Tests : [tests/test_comptabilite_service.py](tests/test_comptabilite_service.py).
- [x] **B7** — `ComptabiliteService.delete_mouvement` → `annuler_mouvement(id, motif, login)` et `VersementService.delete_versement` → `annuler_versement(id, motif, login)` : marquent `Annule`/`AnnulePar`/`DateAnnulation`/`MotifAnnulation` au lieu de supprimer. Exclus des agrégations (balance, reste à payer) mais restent visibles dans les listes (badge "(ANNULÉ)" + tooltip motif dans `enregistrement_mouvement_view.py`). Pas de contre-écriture automatique (jugée hors scope immédiat, l'annulation suffit à la traçabilité demandée par la recette #9).
  Migration [6f2b3468174e](migrations/versions/6f2b3468174e_annulation_tracee_sortiefin_.py). Tests : [tests/test_versement_service.py](tests/test_versement_service.py), [tests/test_comptabilite_service.py](tests/test_comptabilite_service.py).
- [x] **B8** — Table [models/audit_log.py](models/audit_log.py) (`IDUtilisateur` en FK reelle, ancienne/nouvelle valeur, horodatage, motif) + [services/audit_log_service.py](services/audit_log_service.py) (`log`, `get_by_cible`, `get_recent`).
  **Scope limité** : câblé uniquement dans `annuler_mouvement`/`annuler_versement` (B7), pas dans tous les services — instrumentation plus large à faire au fil de l'eau. Aucune vue UI dédiée pour consulter le journal pour l'instant. Migration [a369634edd2b](migrations/versions/a369634edd2b_creer_table_audit_log.py). Tests : [tests/test_audit_log_service.py](tests/test_audit_log_service.py).

## Phase C — Industrialisation technique

- [x] **C1** — Section ad hoc de `app/database.py::create_tables()` gelée (commentaire explicite : plus aucun nouveau bloc, tout changement de schéma futur passe par Alembic — déjà le cas depuis B1). Chaque bloc échoue désormais explicitement (`raise`) au lieu de continuer en silence sur un `print` si son `ALTER TABLE` échoue réellement ; `main.py` affiche alors une erreur de démarrage claire. **Retrait complet des blocs existants volontairement pas fait** : risque réel sur la base CJGA dont l'état exact n'est pas connu depuis cette session. Vérifié : suite de tests complète + une base neuve créée depuis zéro démarrent toutes les deux sans erreur.
- [x] **C2** — [.github/workflows/ci.yml](.github/workflows/ci.yml) : PostgreSQL éphémère, `ruff check`, rejeu complet des migrations Alembic depuis zéro (`create_tables()` → `stamp baseline` → `upgrade head`), puis `pytest --cov`.
  **A révélé 3 vrais bugs** en simulant la séquence localement avant de committer : les migrations `71dbc5eb1292`, `6f2b3468174e`, `a369634edd2b` et `057c2c9d281a` supposaient que les colonnes/contraintes/tables qu'elles ajoutent n'existaient pas encore — faux sur une base neuve, où le modèle SQLAlchemy actuel les crée déjà via `create_tables()`. Corrigées en SQL idempotent (`IF NOT EXISTS`/vérification préalable). Leçon documentée dans [MIGRATIONS.md](MIGRATIONS.md).
  Le job `ruff check .` de la CI passe désormais (C5 fait juste après, même session).
- [x] **C3** — [app/logging_config.py](app/logging_config.py) : logging centralisé (fichier avec rotation 5×5 Mo + console), activé une fois au démarrage (`main.py`). Tous les `print()` de `services/*.py`, `app/database.py` et `app/session.py` remplacés : `logger.exception(...)` dans les blocs `except` (trace complète automatique, plus besoin d'interpoler `{e}`), `logger.info(...)` pour les messages de progression.
  **Bug introduit puis corrigé pendant le chantier** : le remplacement mécanique de `print(f"...{e}")` a rendu la variable `e` inutilisée dans ~66 blocs `except Exception as e:` (détecté par Ruff/F841, autofix sûr après vérification qu'aucun ne référençait `e` ailleurs) — sauf un cas édité à la main (`app/session.py`) où un `raise e` restant aurait provoqué un `NameError` ; corrigé en `raise` nu. Vérifié ensuite par une analyse `ast` sur tout le projet : aucun autre bloc `except` sans binding ne référence `e`.
  Non fait : `views/*.py` et `utils/*.py` gardent leurs `print()` (UI/debug, hors du cœur métier ciblé par l'audit P1-10) — à traiter en suivi si besoin.
- [x] **C4** — [scripts/backup_db.ps1](scripts/backup_db.ps1) (`pg_dump -Fc`, rotation, journal `backup_log.csv`, chiffrement AES-256 optionnel via 7-Zip) + [scripts/restore_db.ps1](scripts/restore_db.ps1) (restaure par défaut dans une base de test séparée, `-Confirm` requis pour cibler une autre base). Procédure complète (planification quotidienne, sauvegarde avant migration, test mensuel) : [BACKUP.md](BACKUP.md).
  Vérifié réellement : sauvegarde de la base de dev locale, restauration dans une base séparée, comparaison des comptes de tables (30/30, identiques), et confirmation que `-TargetDb` sans `-Confirm` est bien refusé.
  **Automatisation de la tâche planifiée Windows non faite ici** — commande prête dans BACKUP.md, à enregistrer sur le poste réel avec le bon chemin de sauvegarde (support externe).
- [x] **C5** — `ruff check .` passe intégralement (0 erreur). Détail :
  - F401 (imports inutilisés, ~117 au moment du nettoyage) : auto-fix (`ruff --fix`).
  - F541 (f-strings sans placeholder) : auto-fix.
  - F821 (4, `app/styles.py`) : réels — annotations de retour en chaîne (`-> "QLabel"`) référençant des classes jamais importées au niveau module (import local dans le corps de fonction). Corrigé avec un bloc `TYPE_CHECKING`, sans changer le comportement runtime.
  - E711/E712 (23) : **tous des faux positifs** — comparaisons `Colonne == True/False/None` dans des `.filter()` SQLAlchemy, où `==`/`!=` est la syntaxe correcte (construit `IS NULL`/`WHERE col = true`) ; la correction suggérée par Ruff (`is`/`not`) casserait silencieusement les requêtes. Réglé par une exclusion documentée dans `pyproject.toml`, pas par une correction ligne à ligne.
  - E741 (6, variable `l` ambiguë) : renommée en `ligne` dans `inscription_autres_frais_service.py` et `versement_service.py`.
  - E702 (5, `main_window.py`) : instructions séparées sur des lignes distinctes.
  - E402 (2) : import déplacé en haut de fichier (`eleve_form_view.py`), import dupliqué en fin de fichier supprimé (`article_list_view.py`, `QDialog` était déjà importé correctement, l'import du bas était mort).
  - E722 (1, `approvisionnement_view.py`) : `except:` → `except Exception:`.
  Vérifié : 134 fichiers compilent, 52/52 tests passent après chaque étape.
- [x] **C6** — Versionnement fait : [app/version.py](app/version.py) (source unique, `__version__ = "2.0.0"`), [version_info.txt](version_info.txt) (métadonnées Windows de l'exécutable : FileVersion, ProductVersion, ProductName, CompanyName), référencé depuis [EasySchool.spec](EasySchool.spec) (`version='version_info.txt'`). Les badges de version dans `login_dialog.py`/`main_window.py` lisent désormais `app/version.py` au lieu d'un `"2.0"` codé en dur à deux endroits différents.
  **Découverte en cours de route** : `EasySchool.spec` n'était pas du tout suivi par Git (règle `.gitignore` pointant vers un chemin `packaging/easy_school.spec` qui n'existe pas) — corrigé, le spec est maintenant versionné.
  Vérifié réellement : build PyInstaller complet exécuté, propriétés du fichier `.exe` produit inspectées (`FileVersion`/`ProductVersion` = 2.0.0.0, `ProductName` = Easy School, etc.) — pas seulement une relecture du spec.
  **Signature de code non faite** : nécessite un certificat de signature (achat/décision externe, hors scope technique).

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
