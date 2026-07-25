from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class MontantExamenCM2(Base):
    """
    Montant configure des frais d'examen CM2, par annee scolaire.
    """
    __tablename__ = "MontantExamenCM2"

    __table_args__ = (
        UniqueConstraint("IDTAnneeScolaire", name="uq_montant_examen_cm2_annee"),
    )

    IDMontantExamenCM2 = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    Montant = Column(Numeric(12, 2), nullable=False, default=0.0)

    annee_scolaire = relationship("TAnneeScolaire")

    def __repr__(self):
        return f"<MontantExamenCM2(ID={self.IDMontantExamenCM2}, Annee={self.IDTAnneeScolaire}, Montant={self.Montant})>"


class VersementExamenCM2(Base):
    """
    Encaissement des frais d'examen CM2 : un versement unique par eleve et par
    annee scolaire (frais paye en une seule fois).
    """
    __tablename__ = "VersementExamenCM2"

    __table_args__ = (
        UniqueConstraint("IDEleve", "IDTAnneeScolaire", name="uq_versement_examen_cm2_eleve_annee"),
    )

    IDVersementExamenCM2 = Column(Integer, primary_key=True, autoincrement=True)
    # Historique financier : un versement ne doit jamais disparaître par
    # suppression indirecte d'une famille, année ou élève.
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="RESTRICT"), nullable=False)
    IDFamille = Column(Integer, ForeignKey("TFamille.IdTFamille", ondelete="RESTRICT"), nullable=False)
    DateVers = Column(Date, nullable=False)
    Montant = Column(Numeric(12, 2), nullable=False, default=0.0)
    Login = Column(String(50), nullable=True)

    annee_scolaire = relationship("TAnneeScolaire")
    eleve = relationship("Eleve")
    famille = relationship("TFamille")

    def __repr__(self):
        return f"<VersementExamenCM2(ID={self.IDVersementExamenCM2}, Eleve={self.IDEleve}, Montant={self.Montant})>"
