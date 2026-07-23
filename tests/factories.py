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
from models.prestation_annexe import PrestationAnnexe
from models.prestation_tarif_niveau import PrestationTarifNiveau


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


def make_famille(session, nom="Kouassi", tel="0700000000", ebrie_abobote=False, ens_cat_primaire=True, ens_cat_secondaire=False):
    famille = TFamille(
        NomResponsable=nom,
        QualiteResponsable=2,
        CellulaireResponsable=tel,
        EbrieAbobote=ebrie_abobote,
        EnsCatPrimaire=ens_cat_primaire,
        EnsCatSecondaire=ens_cat_secondaire,
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
    )
    session.add(ins)
    session.commit()
    return ins


def make_montant_scol(session, annee, niveau, montant=100000, montant_pri=90000, montant_sec=110000):
    m = MontantScol(
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        IDNiveau=niveau.IDT_Niveau,
        Montant=montant,
        MontantEnsPri=montant_pri,
        MontantEnsSecondaire=montant_sec,
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


def make_prestation(session, code, montant_annuel, is_active=True):
    p = PrestationAnnexe(Code=code, Libelle=code, MontantAnnuel=montant_annuel, IsActive=is_active)
    session.add(p)
    session.commit()
    return p


def make_tarif_niveau(session, annee, niveau, prestation, montant_annuel):
    t = PrestationTarifNiveau(
        IDAnneeScolaire=annee.IDTAnneeScolaire,
        IDT_Niveau=niveau.IDT_Niveau,
        IDPrestation=prestation.IDPrestation,
        MontantAnnuel=montant_annuel,
    )
    session.add(t)
    session.commit()
    return t
