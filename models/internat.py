from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class InternatEcheance(Base):
    __tablename__ = "InternatEcheance"
    __table_args__ = (
        UniqueConstraint("IDTAnneeScolaire", "Code", name="uq_internat_echeance_annee_code"),
        CheckConstraint('"MontantNouvelle" >= 0', name="ck_internat_echeance_nouvelle_positif"),
        CheckConstraint('"MontantAncienne" >= 0', name="ck_internat_echeance_ancienne_positif"),
    )

    IDEcheance = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    Code = Column(String(30), nullable=False)
    Libelle = Column(String(80), nullable=False)
    Ordre = Column(Integer, nullable=False)
    DateLimite = Column(Date, nullable=True)
    MontantNouvelle = Column(Numeric(12, 2), nullable=False, default=0)
    MontantAncienne = Column(Numeric(12, 2), nullable=False, default=0)
    Actif = Column(Boolean, nullable=False, default=True)

    annee_scolaire = relationship("TAnneeScolaire")


class InscriptionInternat(Base):
    __tablename__ = "InscriptionInternat"
    __table_args__ = (
        UniqueConstraint("IDTInscription", name="uq_internat_inscription_scolaire"),
        UniqueConstraint("IDEleve", "IDTAnneeScolaire", name="uq_internat_eleve_annee"),
        CheckConstraint("\"OrigineScolaire\" IN ('COLLEGE','EXTERNE')", name="ck_internat_origine_scolaire"),
        CheckConstraint("\"TypePensionnaire\" IN ('NOUVELLE','ANCIENNE')", name="ck_internat_type_pensionnaire"),
        CheckConstraint("\"Statut\" IN ('DOSSIER_INCOMPLET','EN_ATTENTE_PAIEMENT','ADMISE','SUSPENDUE','SORTIE')", name="ck_internat_statut"),
        CheckConstraint('"MontantAnnuel" >= 0', name="ck_internat_montant_annuel_positif"),
    )

    IDInscriptionInternat = Column(Integer, primary_key=True, autoincrement=True)
    IDTInscription = Column(Integer, ForeignKey("TInscription.IDTInscription", ondelete="RESTRICT"), nullable=True)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="RESTRICT"), nullable=False)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    OrigineScolaire = Column(String(10), nullable=False, default="COLLEGE")
    EtablissementFrequente = Column(String(120), nullable=True)
    ClasseFrequentee = Column(String(50), nullable=True)
    ResponsableNom = Column(String(100), nullable=True)
    ResponsableContact = Column(String(50), nullable=True)
    TypePensionnaire = Column(String(10), nullable=False)
    DateAdmission = Column(Date, nullable=False)
    DateDebutPension = Column(Date, nullable=False)
    MontantAnnuel = Column(Numeric(12, 2), nullable=False)
    Statut = Column(String(25), nullable=False, default="DOSSIER_INCOMPLET")
    DateSortie = Column(Date, nullable=True)
    MotifSortie = Column(Text, nullable=True)
    Login = Column(String(50), nullable=True)

    inscription = relationship("TInscription")
    eleve = relationship("Eleve")
    annee_scolaire = relationship("TAnneeScolaire")
    pieces = relationship("InternatPieceDossier", back_populates="inscription_internat", cascade="all, delete-orphan")
    versements = relationship("VersementInternat", back_populates="inscription_internat")


class InternatPieceDossier(Base):
    __tablename__ = "InternatPieceDossier"
    __table_args__ = (
        UniqueConstraint("IDInscriptionInternat", "CodePiece", name="uq_internat_dossier_piece"),
        CheckConstraint('"QuantiteDemandee" > 0', name="ck_internat_piece_qte_demandee"),
        CheckConstraint('"QuantiteRecue" >= 0', name="ck_internat_piece_qte_recue"),
    )

    IDPieceDossier = Column(Integer, primary_key=True, autoincrement=True)
    IDInscriptionInternat = Column(Integer, ForeignKey("InscriptionInternat.IDInscriptionInternat", ondelete="CASCADE"), nullable=False)
    CodePiece = Column(String(40), nullable=False)
    Libelle = Column(String(160), nullable=False)
    Obligatoire = Column(Boolean, nullable=False, default=True)
    QuantiteDemandee = Column(Integer, nullable=False, default=1)
    QuantiteRecue = Column(Integer, nullable=False, default=0)
    DateReception = Column(Date, nullable=True)
    Observation = Column(Text, nullable=True)
    VerifiePar = Column(String(50), nullable=True)

    inscription_internat = relationship("InscriptionInternat", back_populates="pieces")


class VersementInternat(Base):
    __tablename__ = "VersementInternat"
    __table_args__ = (
        UniqueConstraint("NumeroRecu", name="uq_versement_internat_numero_recu"),
        CheckConstraint('"Montant" > 0', name="ck_versement_internat_montant_positif"),
    )

    IDVersementInternat = Column(Integer, primary_key=True, autoincrement=True)
    IDInscriptionInternat = Column(Integer, ForeignKey("InscriptionInternat.IDInscriptionInternat", ondelete="RESTRICT"), nullable=False)
    NumeroRecu = Column(String(40), nullable=False)
    DateVersement = Column(Date, nullable=False)
    Montant = Column(Numeric(12, 2), nullable=False)
    ModePaiement = Column(String(30), nullable=False, default="ESPECES")
    ReferencePaiement = Column(String(80), nullable=True)
    Login = Column(String(50), nullable=True)
    Annule = Column(Boolean, nullable=False, default=False)
    AnnulePar = Column(String(50), nullable=True)
    DateAnnulation = Column(DateTime, nullable=True)
    MotifAnnulation = Column(Text, nullable=True)

    inscription_internat = relationship("InscriptionInternat", back_populates="versements")

    def annuler(self, motif: str, login: str | None) -> None:
        self.Annule = True
        self.AnnulePar = login
        self.DateAnnulation = datetime.now()
        self.MotifAnnulation = motif
