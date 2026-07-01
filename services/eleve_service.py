from app.database import get_session
from models.eleve import Eleve
from models.inscription import TInscription
from models.versement_scol import VersementScol
from app.session import AppSession
from datetime import date
from sqlalchemy.orm import joinedload
import os
import shutil

class EleveService:
    """
    Service gérant les opérations sur les élèves (Eleve).
    """

    @staticmethod
    def get_all_eleves() -> list[Eleve]:
        """Récupère tous les élèves triés par nom puis prénom."""
        session = get_session()
        try:
            return session.query(Eleve).options(
                joinedload(Eleve.nationalite),
                joinedload(Eleve.religion),
                joinedload(Eleve.famille)
            ).order_by(Eleve.Nom.asc(), Eleve.Prenoms.asc()).all()
        finally:
            session.close()

    @staticmethod
    def get_eleve_by_id(id_eleve: int) -> Eleve | None:
        """Récupère un élève par son ID."""
        session = get_session()
        try:
            return session.query(Eleve).options(
                joinedload(Eleve.nationalite),
                joinedload(Eleve.religion),
                joinedload(Eleve.famille)
            ).filter(Eleve.IDEleve == id_eleve).first()
        finally:
            session.close()

    @staticmethod
    def get_eleves_by_famille(id_famille: int) -> list[Eleve]:
        """Récupère tous les élèves liés à une famille."""
        session = get_session()
        try:
            return session.query(Eleve).options(
                joinedload(Eleve.nationalite),
                joinedload(Eleve.religion),
                joinedload(Eleve.famille)
            ).filter_by(IDFamille=id_famille).order_by(Eleve.Nom.asc(), Eleve.Prenoms.asc()).all()
        finally:
            session.close()

    @staticmethod
    def get_eleves_sans_famille() -> list[Eleve]:
        """Récupère les élèves non liés à aucune famille (IDFamille NULL)."""
        session = get_session()
        try:
            return session.query(Eleve).filter(
                Eleve.IDFamille == None
            ).order_by(Eleve.Nom.asc(), Eleve.Prenoms.asc()).all()
        finally:
            session.close()

    @staticmethod
    def link_famille(id_eleve: int, id_famille: int) -> tuple[bool, str]:
        """Associe un élève existant à une famille."""
        session = get_session()
        try:
            eleve = session.get(Eleve, id_eleve)
            if not eleve:
                return False, "Élève introuvable."
            eleve.IDFamille = id_famille
            session.commit()
            return True, f"{eleve.Nom} {eleve.Prenoms} est maintenant associé(e) à cette famille."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_eleves_non_inscrits_by_famille(id_famille: int, id_annee: int) -> list[Eleve]:
        """
        Récupère les élèves liés à une famille qui ne sont pas inscrits
        pour une année scolaire donnée.
        """
        session = get_session()
        try:
            # Récupérer les id_eleve déjà inscrits pour cette année
            inscrits_ids = session.query(TInscription.IDEleve).filter_by(IDTAnneeScolaire=id_annee).all()
            inscrits_list = [id_tuple[0] for id_tuple in inscrits_ids]
            
            # Récupérer les élèves de la famille non présents dans cette liste
            return session.query(Eleve).options(
                joinedload(Eleve.nationalite),
                joinedload(Eleve.religion),
                joinedload(Eleve.famille)
            ).filter(
                (Eleve.IDFamille == id_famille) & 
                (~Eleve.IDEleve.in_(inscrits_list) if inscrits_list else True)
            ).order_by(Eleve.Nom.asc(), Eleve.Prenoms.asc()).all()
        finally:
            session.close()

    @staticmethod
    def generate_matricule() -> str:
        """
        Génère un matricule au format AA-XXX.
        AA correspond aux 2 derniers chiffres de l'année de début de l'année scolaire active.
        XXX correspond à un numéro séquentiel sur 3 chiffres.
        """
        session = get_session()
        try:
            annee_lib = AppSession.get_active_annee_libelle() # ex: "2026-2027" ou "2026"
            prefix = "26" # fallback
            if annee_lib and "-" in annee_lib:
                annee_debut = annee_lib.split("-")[0].strip()
                if len(annee_debut) >= 2:
                    prefix = annee_debut[-2:]
            elif annee_lib and len(annee_lib) >= 2:
                prefix = annee_lib[-2:]
            
            # Recherche des matricules commençant par le préfixe
            matching_eleves = session.query(Eleve).filter(Eleve.Matricule.like(f"{prefix}-%")).all()
            max_seq = 0
            for el in matching_eleves:
                parts = el.Matricule.split("-")
                if len(parts) == 2 and parts[1].isdigit():
                    val = int(parts[1])
                    if val > max_seq:
                        max_seq = val
            
            next_seq_str = str(max_seq + 1).zfill(3)
            return f"{prefix}-{next_seq_str}"
        except Exception as e:
            print(f"Erreur de génération de matricule: {e}")
            return "26-001"
        finally:
            session.close()

    @staticmethod
    def _handle_photo(photo_source_path: str) -> str | None:
        """
        Copie l'image de l'élève dans assets/photos_eleves/ et retourne le chemin d'accès relatif.
        """
        if not photo_source_path or not os.path.exists(photo_source_path):
            return None
        
        # S'assurer que le dossier de destination existe
        dest_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "photos_eleves")
        os.makedirs(dest_dir, exist_ok=True)
        
        # Générer un nom unique pour éviter les collisions
        import uuid
        ext = os.path.splitext(photo_source_path)[1].lower()
        new_filename = f"photo_{uuid.uuid4().hex}{ext if ext else '.jpg'}"
        dest_path = os.path.join(dest_dir, new_filename)
        
        try:
            shutil.copy2(photo_source_path, dest_path)
            # Retourner le chemin relatif
            return f"assets/photos_eleves/{new_filename}"
        except Exception as e:
            print(f"Erreur de copie de la photo d'élève : {e}")
            return None

    @staticmethod
    def create_eleve(data: dict) -> tuple[bool, str]:
        """Crée un nouvel élève."""
        session = get_session()
        try:
            # Validations requises
            mat = data.get("Matricule", "").strip()
            nom = data.get("Nom", "").strip()
            prenoms = data.get("Prenoms", "").strip()
            dat_nais = data.get("DateNaissance")
            sexe = data.get("Sexe")
            
            if not mat:
                return False, "Le matricule est obligatoire."
            if not nom:
                return False, "Le nom est obligatoire."
            if not prenoms:
                return False, "Le prénom est obligatoire."
            if not dat_nais:
                return False, "La date de naissance est obligatoire."
            if sexe is None:
                return False, "Le sexe est obligatoire."
                
            # Vérifier la date de naissance dans le futur
            if isinstance(dat_nais, date) and dat_nais > date.today():
                return False, "La date de naissance ne peut pas être dans le futur."
                
            # Unicité du matricule
            doublon = session.query(Eleve).filter_by(Matricule=mat).first()
            if doublon:
                return False, f"Le matricule '{mat}' est déjà attribué à un autre élève."

            # Traitement de la photo si renseignée
            photo_src = data.get("PhotoPath")
            photo_dest_rel = None
            if photo_src:
                # S'il s'agit déjà d'un chemin relatif de l'application, on le garde
                if photo_src.startswith("assets/photos_eleves/"):
                    photo_dest_rel = photo_src
                else:
                    photo_dest_rel = EleveService._handle_photo(photo_src)

            # Création
            eleve = Eleve(
                Matricule=mat,
                Nom=nom,
                Prenoms=prenoms,
                DateNaissance=dat_nais,
                LieuNaissance=data.get("LieuNaissance"),
                Sexe=sexe,
                IDNationalite=data.get("IDNationalite"),
                IDReligion=data.get("IDReligion"),
                IDFamille=data.get("IDFamille"),
                PhotoPath=photo_dest_rel,
                NumExtrait=data.get("NumExtrait"),
                DateExtrait=data.get("DateExtrait"),
                LieuDelivrance=data.get("LieuDelivrance"),
                Habitation=data.get("Habitation"),
                NomUrgence=data.get("NomUrgence"),
                ContactUrgence=data.get("ContactUrgence"),
                HabitationUrgence=data.get("HabitationUrgence")
            )
            session.add(eleve)
            session.commit()
            return True, "Élève enregistré avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la création de l'élève : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_eleve(id_eleve: int, data: dict) -> tuple[bool, str]:
        """Modifie un élève existant."""
        session = get_session()
        try:
            eleve = session.get(Eleve, id_eleve)
            if not eleve:
                return False, "L'élève à modifier n'existe pas."

            mat = data.get("Matricule", "").strip()
            nom = data.get("Nom", "").strip()
            prenoms = data.get("Prenoms", "").strip()
            dat_nais = data.get("DateNaissance")
            sexe = data.get("Sexe")
            
            if not mat:
                return False, "Le matricule est obligatoire."
            if not nom:
                return False, "Le nom est obligatoire."
            if not prenoms:
                return False, "Le prénom est obligatoire."
            if not dat_nais:
                return False, "La date de naissance est obligatoire."
            if sexe is None:
                return False, "Le sexe est obligatoire."
                
            if isinstance(dat_nais, date) and dat_nais > date.today():
                return False, "La date de naissance ne peut pas être dans le futur."

            # Unicité matricule hors élève lui-même
            doublon = session.query(Eleve).filter(
                (Eleve.Matricule == mat) & (Eleve.IDEleve != id_eleve)
            ).first()
            if doublon:
                return False, f"Le matricule '{mat}' est déjà utilisé par un autre élève."

            # Traitement photo
            photo_src = data.get("PhotoPath")
            if photo_src:
                if photo_src.startswith("assets/photos_eleves/"):
                    eleve.PhotoPath = photo_src
                else:
                    new_path = EleveService._handle_photo(photo_src)
                    if new_path:
                        eleve.PhotoPath = new_path
            else:
                eleve.PhotoPath = None

            # Mise à jour
            eleve.Matricule = mat
            eleve.Nom = nom
            eleve.Prenoms = prenoms
            eleve.DateNaissance = dat_nais
            eleve.LieuNaissance = data.get("LieuNaissance")
            eleve.Sexe = sexe
            eleve.IDNationalite = data.get("IDNationalite")
            eleve.IDReligion = data.get("IDReligion")
            eleve.IDFamille = data.get("IDFamille")
            eleve.NumExtrait = data.get("NumExtrait")
            eleve.DateExtrait = data.get("DateExtrait")
            eleve.LieuDelivrance = data.get("LieuDelivrance")
            eleve.Habitation = data.get("Habitation")
            eleve.NomUrgence = data.get("NomUrgence")
            eleve.ContactUrgence = data.get("ContactUrgence")
            eleve.HabitationUrgence = data.get("HabitationUrgence")

            session.commit()
            return True, "Fiche élève mise à jour avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur de modification de l'élève : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_eleve(id_eleve: int) -> tuple[bool, str]:
        """Supprime un élève uniquement s'il n'a ni inscription ni versement associé."""
        session = get_session()
        try:
            eleve = session.get(Eleve, id_eleve)
            if not eleve:
                return False, "L'élève à supprimer n'existe pas."

            # Bloquer si l'élève a au moins une inscription (toutes années confondues)
            has_inscriptions = session.query(TInscription).filter_by(IDEleve=id_eleve).first() is not None
            if has_inscriptions:
                return False, "Impossible de supprimer cet élève car il possède déjà une inscription."

            # Bloquer si l'élève a au moins un versement enregistré (protection historique comptable)
            has_versements = session.query(VersementScol).filter_by(IDEleve=id_eleve).first() is not None
            if has_versements:
                return False, "Impossible de supprimer cet élève car il possède déjà un versement."

            session.delete(eleve)
            session.commit()
            return True, "L'élève a été supprimé de la base avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la suppression de l'élève : {str(e)}"
        finally:
            session.close()
