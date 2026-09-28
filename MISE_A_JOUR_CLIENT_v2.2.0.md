# Mise à jour Easy School CJGA 2.2.0

## Nouveautés de cette version

- **Modification de la capacité d'une classe** (Paramètres > Classes).
- **Correction guidée d'une inscription bloquée par un paiement** (Scolarité > Inscription) :
  propose d'annuler le(s) versement(s) concerné(s) (piste d'audit conservée) puis d'appliquer
  la correction de niveau/statut.
- **Duplicata de reçu** : double-clic sur une ligne de l'historique des versements (Caisse)
  pour réimprimer un reçu.
- **Mode de paiement (Espèces / Chèque)** enregistré sur chaque versement de scolarité, avec
  numéro de chèque facultatif, visible dans l'historique et sur le reçu.
- **KPI Cantine** ajoutés au tableau de bord (versements, reste à recouvrer) ; les "Recettes
  encaissées" incluent désormais les paiements de la Cantine.
- **Droits par rapport statistique** : chaque rapport du module Statistiques (Inscrits,
  Nouveaux, Scolarité, Internat, Vente, Stock, Liste Alphabétique, État Périodique) peut être
  autorisé individuellement par profil, dans Utilisateurs > Droits par profil. Les profils
  existants gardent tous les rapports auxquels ils avaient déjà accès.
- **Matricule de l'état** (au lieu du matricule interne) affiché sur les impressions par classe
  et sur les reçus de paiement, quand il est renseigné dans la fiche élève.
- Corrections d'affichage diverses (boutons de dialogues illisibles, sélection de ligne dans
  les tableaux de recherche à un seul résultat) et renommage "Cantine externe" → "Cantine"
  dans l'interface.

## Avant de commencer

1. Fermer Easy School sur tous les postes.
2. Effectuer une sauvegarde de la base PostgreSQL depuis le serveur.
3. Exécuter la mise à jour sur un poste ayant accès au serveur PostgreSQL.

## Installation

1. Lancer `EasySchool_CJGA_Mise_A_Jour_v2.2.0.exe` en tant qu'administrateur.
2. Vérifier que le dossier proposé est le dossier Easy School existant.
3. Terminer l'assistant. La configuration `.env` est conservée et sauvegardée sous
   `.env.avant-mise-a-jour-v2.2.0`.
4. L'installateur applique automatiquement les migrations de base de données (dont l'ajout du
   mode de paiement sur les versements scolarité).
5. Relancer Easy School et contrôler la connexion, le tableau de bord et un versement en Caisse.

## Déploiement sur les autres postes

Après la première mise à jour réussie, exécuter le même installateur sur chaque poste.
Les migrations sont idempotentes : la base déjà à jour ne sera pas modifiée une seconde fois.

## En cas d'erreur

Le journal se trouve dans `%LOCALAPPDATA%\EasySchool\logs\easy_school.log`.
La configuration précédente reste disponible dans le dossier d'installation.
