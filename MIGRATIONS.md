# Migrations de base de données — Alembic

## Flux de démarrage recommandé

La mise à niveau d'une base doit être exécutée explicitement pendant le
déploiement, avant de lancer l'application :

```bash
alembic upgrade head
```

Le démarrage sépare désormais quatre responsabilités :

1. `init_db()` configure le moteur et les sessions SQLAlchemy, sans requête ni DDL.
2. `test_connection()` vérifie PostgreSQL avec un simple `SELECT 1`.
3. `create_tables()` crée/met à niveau une base **locale de dev/test**.
4. Alembic est le seul mécanisme de migration de production.

Avec `APP_ENV=prod`, `main.py` initialise le moteur et vérifie la connexion,
mais n'appelle jamais `create_tables()` : aucun `CREATE TABLE`, `ALTER TABLE`
ou `DROP COLUMN` implicite n'est exécuté. Si `APP_ENV` est absent, le
comportement est volontairement le même que `prod`. Une valeur inconnue
bloque le démarrage avant de toucher la base.

Avec `APP_ENV=dev`, `dev_debug` ou `test`, la création locale automatique est
conservée pour faciliter le premier lancement et la CI.

## Compatibilité historique

Les anciens blocs `ALTER TABLE` de `create_tables()` ne sont pas supprimés :
les tests, la CI et certaines bases locales antérieures à Alembic s'appuient
encore sur le schéma qu'ils produisent. Ils sont confinés au chemin dev/test
et gelés : aucun nouveau changement de schéma ne doit y être ajouté.

Depuis cette introduction, les changements de schéma **futurs** doivent passer
par une révision Alembic versionnée plutôt que par un nouveau bloc `ALTER
TABLE` ajouté à la main dans `app/database.py::create_tables()`.

## Pourquoi ce changement

`create_tables()` accumulait les migrations sous forme de blocs `try/except`
qui continuent silencieusement (juste un `print`) en cas d'échec, sans
historique ni possibilité de rollback. Un schéma peut ainsi rester à moitié
migré sans que personne ne s'en aperçoive. Alembic donne un historique
explicite, ordonné, et rejouable.

`create_tables()` continue de produire le schéma local historique lorsqu'elle
est appelée explicitement ou via un démarrage dev/test. Elle n'est plus
appelée au démarrage en production.

## Mise en route sur une base existante (dev, test, ou une install déjà en prod)

**Ne jamais faire `alembic stamp head` sans avoir vérifié quelle révision
correspond réellement à l'état de la base.** `head` désigne la dernière
révision de l'historique, pas forcément celle que la base a effectivement
subie — si une révision plus récente que l'état réel de la base est marquée
comme appliquée par erreur, Alembic considère à tort qu'elle n'a rien à
rejouer, alors que le changement qu'elle décrit n'a jamais eu lieu.

Concrètement aujourd'hui (2026-07) :

- **`f0e0bbadf6a8` (baseline)** : correspond au schéma tel que produit par
  `create_tables()`, **avec** les tables `Prestataire`, `PrestationAnnexe`,
  `VentilationPrestation` encore présentes.
- **`057c2c9d281a`** : supprime ces 3 tables. Tant que cette révision n'a
  pas été volontairement appliquée (`alembic upgrade 057c2c9d281a`, après
  sauvegarde) sur une base donnée, cette base est seulement à la révision
  **baseline**, pas à `head`.

Avant de stamper quoi que ce soit, vérifiez l'état réel :

```bash
# Les 3 tables existent-elles encore sur cette base ?
psql -d <nom_base> -c "\dt Prestataire PrestationAnnexe VentilationPrestation"
```

- Si elles existent encore → `alembic stamp f0e0bbadf6a8` (baseline).
- Si elles ont déjà été supprimées manuellement ou via cette révision
  → `alembic stamp 057c2c9d281a` (ou `head` si aucune révision plus
  récente n'a été ajoutée depuis).

Sur une base locale neuve (jamais initialisée), un démarrage avec
`APP_ENV=dev` crée le schéma via `create_tables()` (donc toujours avec les 3
tables présentes) ; stamper sur la baseline `f0e0bbadf6a8`, puis lancer
`alembic upgrade head`. En production, préparer la base pendant le déploiement
avant le premier lancement ; l'application ne la crée pas elle-même.

## Ajouter un changement de schéma

1. Modifier le(s) modèle(s) SQLAlchemy concerné(s) dans `models/`.
2. Générer la révision automatiquement à partir du diff modèles ↔ base :
   ```bash
   alembic revision --autogenerate -m "description courte du changement"
   ```
3. **Relire le fichier généré dans `migrations/versions/`** avant de
   l'appliquer — l'autogenerate d'Alembic génère parfois du bruit sans
   rapport avec le changement voulu (ex : recréation de clés étrangères non
   nommées, détectées comme "supprimées puis rajoutées" à cause de
   l'absence de nom explicite sur les `ForeignKey` actuelles). Supprimer ces
   opérations parasites du fichier avant de committer.
4. **Rendre chaque opération idempotente** (`IF NOT EXISTS`/`IF EXISTS`, ou
   vérification d'existence avant un `ADD CONSTRAINT`) — voir "Piège"
   ci-dessous : ne jamais se fier à `op.add_column`/`op.create_table`/
   `op.create_check_constraint` bruts sans les rendre conditionnels.
5. Appliquer : `alembic upgrade head`.

### Piège découvert par la CI (chantier C2, 2026-07) : toujours écrire des migrations idempotentes

Comme le modèle SQLAlchemy est modifié **avant** la révision (étape 1), une
base entièrement neuve créée via `create_tables()`
(`Base.metadata.create_all()`) a **déjà** la colonne/contrainte/table cible
au moment où la révision correspondante est rejouée par-dessus. Un
`op.add_column`/`op.create_table`/`op.create_check_constraint` non protégé
échoue alors avec "already exists", uniquement sur une base neuve — jamais
sur la base de dev/test habituelle (déjà migrée pas à pas). C'est exactement
ce qu'un `alembic upgrade head` lancé en CI sur une base éphémère toute
neuve détecte, et que tester uniquement sur une base locale déjà migrée ne
révèle jamais.

Trois migrations de ce projet ont été corrigées pour cette raison
(`71dbc5eb1292`, `6f2b3468174e`, `a369634edd2b`) : toutes utilisent
désormais du SQL brut avec `IF NOT EXISTS` ou une vérification d'existence
préalable, au lieu des opérations Alembic non protégées générées par
défaut.

## Constat fait lors de la mise en place

Le premier `alembic revision --autogenerate` sur la base de test a révélé que
les tables `Prestataire`, `PrestationAnnexe` et `VentilationPrestation`
existent toujours en base bien que leurs modèles aient été supprimés du code
(refactor CJGA, commit `12b659d`) : `create_tables()` ne fait que créer des
tables, jamais en supprimer. Ce sont des tables mortes sur toute base ayant
tourné avec l'ancien schéma. Aucune suppression n'a été faite automatiquement
ici — `DROP TABLE` est destructif et irréversible sur des données réelles ;
à traiter volontairement via une révision Alembic dédiée si confirmé.

## Configuration

- `alembic.ini` ne contient **aucun identifiant de connexion** committé.
  L'URL de connexion est injectée dynamiquement par `migrations/env.py` via
  `Config.get_db_url()`, qui lit le `.env` local — même mécanisme que le
  reste de l'application.
- `migrations/env.py` importe explicitement tous les modèles (comme le fait
  déjà `create_tables()`) pour que `Base.metadata` soit complet avant toute
  comparaison automatique.
