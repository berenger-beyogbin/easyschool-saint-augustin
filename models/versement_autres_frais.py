from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class VersementAutresFrais(Base):
    """
    Lie un versement (VersementScol) aux frais annexes (InscriptionAutresFrais) qu'il solde.
    Presence d'une ligne = ce frais annexe a ete regle par ce versement ; permet de retirer
    un frais deja paye de la liste des frais a verser proposee a la caisse.
    """
    __tablename__ = "VersementAutresFrais"

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
