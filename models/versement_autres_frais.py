from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class VersementAutresFrais(Base):
    """
    Lie un versement (VersementScol) aux frais annexes (InscriptionAutresFrais) qu'il solde.
    Presence d'une ligne = ce frais annexe a ete regle par ce versement ; permet de retirer
    un frais deja paye de la liste des frais a verser proposee a la caisse.

    Contrainte unique sur IDInscriptionAutresFrais : un frais annexe ne peut etre lie qu'a
    un seul versement, meme sous acces concurrent (le controle applicatif dans
    VersementService.create_versement peut manquer une course entre deux caisses).
    """
    __tablename__ = "VersementAutresFrais"

    __table_args__ = (
        UniqueConstraint("IDInscriptionAutresFrais", name="uq_versement_autres_frais_inscription"),
    )

    IDVersementAutresFrais = Column(Integer, primary_key=True, autoincrement=True)
    IDVersementScol = Column(Integer, ForeignKey("VersementScol.IDVersementScol", ondelete="CASCADE"), nullable=False)
    IDInscriptionAutresFrais = Column(
        Integer,
        ForeignKey("InscriptionAutresFrais.IDInscriptionAutresFrais", ondelete="CASCADE"),
        nullable=False,
    )

    # Relations
    versement = relationship("VersementScol")
    inscription_autres_frais = relationship("InscriptionAutresFrais")

    def __repr__(self):
        return f"<VersementAutresFrais(Versement={self.IDVersementScol}, Frais={self.IDInscriptionAutresFrais})>"
