# Audit final des corrections Easy School

Date de cloture : 2026-07-16

Branche de travail : `codex/audit-corrections`

## Objectif

Ce lot de corrections avait pour objectif de stabiliser les zones critiques relevees pendant l'audit :

- protection de l'historique scolaire et financier ;
- durcissement de l'authentification ;
- controles de permissions au niveau service, pas seulement dans l'interface ;
- verrouillage des ecritures sur les annees cloturees ;
- ajout de tests automatises pour figer les comportements sensibles.

## Lots realises

1. `8d52691` Baseline avant corrections d'audit
2. `0420e7d` Ajouter tests d'audit avant corrections
3. `d91878b` Proteger l'historique contre suppressions cascade
4. `aecf164` Renforcer droits de modification metier
5. `4e00ff2` Bloquer mouvements stock sur annee cloturee
6. `1d41a62` Durcir authentification admin et mots de passe
7. `0c5c4e8` Renforcer droits de saisie comptable
8. `11cbcc6` Verrouiller ecritures caisse et kiosque
9. `cddf151` Verrouiller administration utilisateurs profils
10. `1d8fff4` Verrouiller ecritures scolarite eleves inscriptions
11. `5099f94` Verrouiller tarifs et frais de scolarite
12. `d9a1fe3` Verrouiller referentiels comptables

## Corrections principales

### Integrite des donnees

- Les inscriptions et versements ne sont plus exposes a des suppressions en cascade dangereuses.
- Les suppressions de classes/eleves/annees historisees sont bloquees au niveau service et/ou base.
- Les mouvements de stock sont refuses sur une annee scolaire cloturee.

### Authentification

- Le compte admin par defaut n'affiche plus le mot de passe dans la console.
- L'admin cree automatiquement est marque comme devant changer son mot de passe.
- Les mots de passe exigent au moins 8 caracteres, avec lettre et chiffre.
- La verification de hash utilise `hmac.compare_digest`.
- L'ecran de connexion force le changement du mot de passe lorsque necessaire.

### Permissions metier

Les ecritures sensibles sont maintenant controlees dans les services :

- `PARAMETRES_MODIFIER` : parametres scolaires et referentiels generaux.
- `PRESTATIONS_MODIFIER` : prestataires et prestations annexes.
- `SCOLARITE_ELEVES` : eleves, familles, rattachements.
- `SCOLARITE_INSCRIPTIONS` : inscriptions.
- `SCOLARITE_VERSEMENTS` : versements, tarifs scolarite/transport/cantine/autres frais.
- `KIOSQUE_ARTICLES` : articles et kits.
- `KIOSQUE_STOCKS` : approvisionnements.
- `KIOSQUE_VENTES` : ventes/sorties stock.
- `COMPTABILITE_SAISIE` : mouvements comptables, comptes, types de sortie.
- `UTILISATEURS_MODIFIER` : utilisateurs, profils, attribution des droits.

## Points volontairement exclus des blocages service

Certaines ecritures restent autorisees car elles ne sont pas des actions metier utilisateur classiques :

- fonctions de seed/demarrage : permissions, profils, comptes SYSCOA, admin, prestations par defaut ;
- preference imprimante personnelle ;
- recalcul de ventilation analytique, derive des paiements et utilise comme maintenance de coherence.

## Validation

Commandes executees avec succes :

```powershell
venv\Scripts\python.exe -m pytest tests -q
venv\Scripts\python.exe -m compileall app models services tests -q
```

Resultat final :

- `62 passed`
- compilation Python OK
- branche propre apres commit final attendu

## Etat final

Le coeur metier est maintenant nettement plus robuste :

- l'historique critique est protege ;
- les droits ne dependent plus uniquement de l'interface ;
- les tests automatises couvrent les principaux scenarios de refus ;
- les futures regressions sur ces points devraient etre detectees rapidement.

Recommandation suivante : faire une passe fonctionnelle manuelle dans l'interface avec deux profils de test, un profil autorise et un profil lecture seule, pour verifier le ressenti utilisateur et les messages d'erreur.
