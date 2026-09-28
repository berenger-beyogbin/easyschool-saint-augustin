# Mise à jour Easy School CJGA 2.1.0

## Avant de commencer

1. Fermer Easy School sur tous les postes.
2. Effectuer une sauvegarde de la base PostgreSQL depuis le serveur.
3. Exécuter la mise à jour sur un poste ayant accès au serveur PostgreSQL.

## Installation

1. Lancer `EasySchool_CJGA_Mise_A_Jour_v2.1.0.exe` en tant qu’administrateur.
2. Vérifier que le dossier proposé est le dossier Easy School existant.
3. Terminer l’assistant. La configuration `.env` est conservée et sauvegardée sous
   `.env.avant-mise-a-jour-v2.1.0`.
4. L’installateur applique automatiquement les migrations de base de données.
5. Relancer Easy School et contrôler la connexion, l’Internat et le tableau de bord.

## Déploiement sur les autres postes

Après la première mise à jour réussie, exécuter le même installateur sur chaque poste.
Les migrations sont idempotentes : la base déjà à jour ne sera pas modifiée une seconde fois.

## En cas d’erreur

Le journal se trouve dans `%LOCALAPPDATA%\EasySchool\logs\easy_school.log`.
La configuration précédente reste disponible dans le dossier d’installation.
