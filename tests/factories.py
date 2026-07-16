"""Fonctions utilitaires pour construire les objets de test (annee, eleve, inscription...)."""
from datetime import date

from models.annee_scolaire import TAnneeScolaire
from models.cycle import TCycle
from models.niveau import TNiveau
from models.classe import TClasse
from models.famille import TFamille
from models.eleve import Eleve
from models.inscription import TInscription
from models.montant_scol import MontantScol
from models.montant_transport import MontantTransport
from models.montant_cantine import MontantCantine
from models.autres_frais import AutresFrais
from models.inscription_autres_frais import InscriptionAutresFrais


def make_annee(session, libelle="2026-2027", cloturer=False):
    annee = TAnneeScolaire(Libelle=libelle, Cloturer=cloturer)
    session.add(annee)
    session.commit()
    return annee


def make_niveau_classe(session, annee, libelle_niveau="CM2"):
    cycle = TCycle(Libelle="Primaire", IDAnneeScolaire=annee.IDTAnneeScolaire)
    session.add(cycle)
    session.commit()

    niveau = TNiveau(Libelle=libelle_niveau, IDT_Cycle=cycle.IDT_Cycle, IDAnneeScolaire=annee.IDTAnneeScolaire)
    session.add(niveau)
    session.commit()

    classe = TClasse(LibClasse=f"{libelle_niveau} A", IDT_Niveau=niveau.IDT_Niveau, IDAnneeScolaire=annee.IDTAnneeScolaire)
    session.add(classe)
    session.commit()
    return niveau, classe


def make_famille(session, nom="Kouassi", tel="0700000000", ebrie_abobote=False):
    famille = TFamille(
        NomResponsable=nom,
        QualiteResponsable=2,
        CellulaireResponsable=tel,
        EbrieAbobote=ebrie_abobote,
    )
    session.add(famille)
    session.commit()
    return famille


def make_eleve(session, famille, matricule, nom="Kouassi", prenoms="Jean"):
    eleve = Eleve(
        Matricule=matricule,
        Nom=nom,
        Prenoms=prenoms,
        DateNaissance=date(2015, 1, 1),
        Sexe=1,
        IDFamille=famille.IdTFamille,
    )
    session.add(eleve)
    session.commit()
    return eleve


def make_inscription(session, annee, famille, eleve, niveau, classe, **opts):
    ins = TInscription(
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        IDFamille=famille.IdTFamille,
        IDEleve=eleve.IDEleve,
        IDNiveau=niveau.IDT_Niveau,
        IDClasse=classe.IDTClasse,
        DateInscription=date.today(),
        Nouveau=opts.get("nouveau", False),
        Scolarite=opts.get("scolarite", True),
        Transport=opts.get("transport", False),
        Cantine=opts.get("cantine", False),
        AutresFrais=opts.get("autres_frais", False),
        StatutAffectation=opts.get("statut_affectation", "AFFECTE_ETAT"),
    )
    session.add(ins)
    session.commit()
    return ins


def make_montant_scol(session, annee, niveau, montant_affecte=100000, montant_non_affecte=100000):
    m = MontantScol(
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        IDNiveau=niveau.IDT_Niveau,
        MontantAffecte=montant_affecte,
        MontantNonAffecte=montant_non_affecte,
    )
    session.add(m)
    session.commit()
    return m


def make_montant_transport(session, annee, niveau, montant=15000):
    m = MontantTransport(IDTAnneeScolaire=annee.IDTAnneeScolaire, IDNiveau=niveau.IDT_Niveau, Montant=montant)
    session.add(m)
    session.commit()
    return m


def make_montant_cantine(session, annee, niveau, montant=20000):
    m = MontantCantine(IDTAnneeScolaire=annee.IDTAnneeScolaire, IDNiveau=niveau.IDT_Niveau, Montant=montant)
    session.add(m)
    session.commit()
    return m


def make_inscription_autres_frais(session, inscription, code="TENUE", libelle="Tenue", montant=6000):
    autre_frais = AutresFrais(CodeFrais=code, LibelleFrais=libelle)
    session.add(autre_frais)
    session.commit()

    ligne = InscriptionAutresFrais(
        IDTInscription=inscription.IDTInscription,
        IDAutres_Frais=autre_frais.IDAutres_Frais,
        MontantApplique=montant,
        CodeFraisSnapshot=code,
        LibelleSnapshot=libelle,
    )
    session.add(ligne)
    session.commit()
    return ligne
