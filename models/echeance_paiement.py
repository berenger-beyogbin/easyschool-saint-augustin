from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class EcheancePaiement(Base):
    """Tranche attendue pour un poste financier et une categorie d'eleves."""

    __tablename__ = "EcheancePaiement"
    __table_args__ = (
        UniqueConstraint(
            "IDTAnneeScolaire", "TypeFrais", "Categorie", "NumeroTranche",
            name="uq_echeance_annee_type_categorie_numero",
        ),
    )

    IDEcheancePaiement = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(
        Integer,
        ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"),
        nullable=False,
    )
    TypeFrais = Column(String(20), nullable=False)
    Categorie = Column(String(30), nullable=False)
    NumeroTranche = Column(Integer, nullable=False)
    Libelle = Column(String(80), nullable=False)
    DateEcheance = Column(Date, nullable=True)
    Montant = Column(Numeric(12, 2), nullable=False)

    annee_scolaire = relationship("TAnneeScolaire")

