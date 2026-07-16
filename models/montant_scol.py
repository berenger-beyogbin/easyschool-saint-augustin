from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class MontantScol(Base):
    """
    Parametrage des montants de scolarite par niveau et annee scolaire.
    """
    __tablename__ = "MontantScol"

    __table_args__ = (
        UniqueConstraint("IDTAnneeScolaire", "IDNiveau", name="uq_montant_scol_annee_niveau"),
        CheckConstraint("\"MontantNonAffecte\" >= 0", name="ck_montant_scol_non_affecte_positif"),
        CheckConstraint("\"MontantAffecte\" >= 0", name="ck_montant_scol_affecte_positif"),
    )

    IDMontantScol = Column(Integer, primary_key=True, autoincrement=True)
    # ON DELETE RESTRICT : un tarif configure ne doit pas disparaitre en silence
    # avec le niveau ou l'annee (il proteges des versements calcules dessus).
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    IDNiveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="RESTRICT"), nullable=False)
    # Tarif de scolarité selon le statut d'affectation de l'État de l'inscription (TInscription.StatutAffectation)
    MontantNonAffecte = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantAffecte = Column(Numeric(12, 2), nullable=False, default=0.0)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    niveau = relationship("TNiveau")

    def __repr__(self):
        return f"<MontantScol(ID={self.IDMontantScol}, Niveau={self.IDNiveau}, Affecte={self.MontantAffecte}, NonAffecte={self.MontantNonAffecte})>"
