from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CantineTarif(Base):
    __tablename__ = "CantineTarif"
    __table_args__ = (
        UniqueConstraint("IDTAnneeScolaire", name="uq_cantine_tarif_annee"),
        CheckConstraint('"Montant" >= 0', name="ck_cantine_tarif_positif"),
    )

    IDTarifCantine = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    Montant = Column(Numeric(12, 2), nullable=False, default=50000)
    Actif = Column(Boolean, nullable=False, default=True)

    annee_scolaire = relationship("TAnneeScolaire")


class InscriptionCantine(Base):
    __tablename__ = "InscriptionCantine"
    __table_args__ = (
        UniqueConstraint("IDEleve", "IDTAnneeScolaire", name="uq_cantine_eleve_annee"),
        CheckConstraint("\"Statut\" IN ('EN_COURS','SOLDE','SUSPENDU','SORTIE')", name="ck_cantine_statut"),
        CheckConstraint('"MontantTotal" >= 0', name="ck_cantine_montant_total_positif"),
    )

    IDInscriptionCantine = Column(Integer, primary_key=True, autoincrement=True)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="RESTRICT"), nullable=False)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    MontantTotal = Column(Numeric(12, 2), nullable=False)
    DateInscription = Column(Date, nullable=False)
    ResponsableNom = Column(String(150), nullable=True)
    ResponsableContact = Column(String(50), nullable=True)
    Statut = Column(String(15), nullable=False, default="EN_COURS")
    DateSortie = Column(Date, nullable=True)
    MotifSortie = Column(Text, nullable=True)
    Login = Column(String(50), nullable=True)

    eleve = relationship("Eleve")
    annee_scolaire = relationship("TAnneeScolaire")
    versements = relationship("VersementCantine", back_populates="inscription_cantine")


class VersementCantine(Base):
    __tablename__ = "VersementCantine"
    __table_args__ = (
        UniqueConstraint("NumeroRecu", name="uq_versement_cantine_numero_recu"),
        CheckConstraint('"Montant" > 0', name="ck_versement_cantine_montant_positif"),
    )

    IDVersementCantine = Column(Integer, primary_key=True, autoincrement=True)
    IDInscriptionCantine = Column(Integer, ForeignKey("InscriptionCantine.IDInscriptionCantine", ondelete="RESTRICT"), nullable=False)
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

    inscription_cantine = relationship("InscriptionCantine", back_populates="versements")

    def annuler(self, motif: str, login: str | None) -> None:
        self.Annule = True
        self.AnnulePar = login
        self.DateAnnulation = datetime.now()
        self.MotifAnnulation = motif
