"""Source unique de la version de l'application (audit P2-12).

A incrementer manuellement a chaque version livree (semver : MAJEUR.MINEUR.CORRECTIF).
Reference aussi par version_info.txt (metadonnees Windows de l'executable, voir
EasySchool.spec) -- les deux doivent rester synchronises a chaque bump de version.
"""

APP_NAME = "Easy School"
__version__ = "2.0.0"
