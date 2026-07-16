# Migrations de base de données — Alembic

Depuis cette introduction, les changements de schéma **futurs** doivent passer
par une révision Alembic versionnée plutôt que par un nouveau bloc `ALTER
TABLE` ajouté à la main dans `app/database.py::create_tables()`.

## Pourquoi ce changement

`create_tables()` accumulait les migrations sous forme de blocs `try/except`
qui continuent silencieusement (juste un `print`) en cas d'échec, sans
historique ni possibilité de rollback. Un schéma peut ainsi rester à moitié
migré sans que personne ne s'en aperçoive. Alembic donne un historique
explicite, ordonné, et rejouable.

**Le comportement actuel de `create_tables()` n'a pas changé** : il continue
de créer les tables au démarrage de l'application. Cette introduction
d'Alembic est la première étape ; le remplacement complet des blocs `ALTER
TABLE` ad hoc par des révisions Alembic est un chantier séparé.

## Mise en route sur une base existante (dev, test, ou une install déjà en prod)

Toute base qui tourne déjà avec `create_tables()` est considérée à jour par
rapport à la révision baseline (`f0e0bbadf6a8`). Il ne faut **jamais** lancer
`alembic upgrade head` sur une telle base sans l'avoir d'abord marquée :

```bash
# Indique a Alembic "cette base est deja a la revision baseline",
# sans executer aucun SQL.
alembic stamp head
```

Sur une base neuve (jamais initialisée), l'application continue de créer le
schéma via `create_tables()` au premier lancement ; faites ensuite le même
`alembic stamp head` pour la garder synchronisée avec l'historique Alembic.

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
4. Appliquer : `alembic upgrade head`.

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
