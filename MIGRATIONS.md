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

Sur une base neuve (jamais initialisée), l'application continue de créer le
schéma via `create_tables()` au premier lancement (donc toujours avec les 3
tables présentes) ; stamper sur la baseline `f0e0bbadf6a8`, pas `head`.

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
