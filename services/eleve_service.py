from app.database import get_session
from models.eleve import Eleve
from models.cursus_anterieur import CursusAnterieur
from models.inscription import TInscription
from models.classe import TClasse
from models.famille import TFamille
from models.versement_scol import VersementScol
from app.session import AppSession
from datetime import date
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload, aliased
import os
import shutil
import logging
logger = logging.getLogger(__name__)


class EleveService:
    @staticmethod
    def normalize_matricule_national(value: str | None) -> str | None:
        """Retourne une forme stable du matricule national pour comparaison et stockage."""
        normalized = "".join((value or "").split()).upper()
        return normalized or None

    @staticmethod
    def _find_by_matricule_national(session, matricule_national: str, exclude_id: int | None = None):
        """Recherche aussi les anciennes valeurs contenant des espaces ou des minuscules."""
        normalized_column = func.upper(func.replace(Eleve.MatriculeNational, " ", ""))
        query = session.query(Eleve).filter(normalized_column == matricule_national)
        if exclude_id is not None:
            query = query.filter(Eleve.IDEleve != exclude_id)
        return query.first()

    @staticmethod
    def _duplicate_matricule_national_message(eleve: Eleve) -> str:
        return (
            "Ce matricule national appartient deja a "
            f"{eleve.Nom} {eleve.Prenoms} "
            f"(matricule interne {eleve.Matricule}). "
            "Recherchez et selectionnez cette fiche au lieu de creer un nouvel eleve."
        )

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
                joinedload(Eleve.famille),
                joinedload(Eleve.cursus_anterieur)
            ).filter(Eleve.IDEleve == id_eleve).first()
        finally:
            session.close()

    @staticmethod
    def search_eleves(query: str = "", id_annee: int | None = None, limit: int = 200) -> list[dict]:
        """Recherche d'élèves pour le parcours "élève d'abord" (écran
        d'inscription) : matricule interne, matricule national, nom,
        prénoms, ou téléphone d'un parent de la famille liée.

        Une seule requête (LEFT JOIN famille + inscription/classe de
        l'année active) — pas de N+1, pas de requête par ligne. Retourne des
        dicts simples (jamais d'objets détachés) prêts pour l'affichage :
        statut "Inscrit"/"Non inscrit" et classe actuelle pour id_annee.
        """
        session = get_session()
        try:
            ins = aliased(TInscription)
            classe = aliased(TClasse)

            q = session.query(
                Eleve.IDEleve, Eleve.Matricule, Eleve.MatriculeNational,
                Eleve.Nom, Eleve.Prenoms, Eleve.Sexe, Eleve.IDFamille,
                TFamille.NomResponsable,
                ins.IDTInscription, classe.LibClasse,
            ).outerjoin(
                TFamille, TFamille.IdTFamille == Eleve.IDFamille
            ).outerjoin(
                ins, (ins.IDEleve == Eleve.IDEleve) & (ins.IDTAnneeScolaire == id_annee)
            ).outerjoin(
                classe, classe.IDTClasse == ins.IDClasse
            )

            q_clean = (query or "").strip()
            if q_clean:
                like = f"%{q_clean}%"
                q = q.filter(or_(
                    Eleve.Matricule.ilike(like),
                    Eleve.MatriculeNational.ilike(like),
                    Eleve.Nom.ilike(like),
                    Eleve.Prenoms.ilike(like),
                    TFamille.CellulaireResponsable.ilike(like),
                    TFamille.TelPere.ilike(like),
                    TFamille.TelMere.ilike(like),
                    TFamille.CelTuteur.ilike(like),
                ))

            q = q.order_by(Eleve.Nom.asc(), Eleve.Prenoms.asc()).limit(limit)

            return [
                {
                    "id_eleve": row.IDEleve,
                    "matricule": row.Matricule,
                    "matricule_national": row.MatriculeNational or "",
                    "nom": row.Nom,
                    "prenoms": row.Prenoms,
                    "sexe": row.Sexe,
                    "id_famille": row.IDFamille,
                    "famille_label": row.NomResponsable or "",
                    "inscrit": row.IDTInscription is not None,
                    "classe_libelle": row.LibClasse or "",
                }
                for row in q.all()
            ]
        finally:
            session.close()

    @staticmethod
    def associer_famille(id_eleve: int, id_famille: int) -> tuple[bool, str]:
        """Associe (ou change) la famille d'un élève.

        Ne touche JAMAIS aux inscriptions existantes (passées ou active) ni
        aux versements historiques : c'est une décision volontaire et
        distincte, laissée à l'appelant (UI, avec confirmation explicite) —
        voir InscriptionService.synchroniser_famille_inscription_active pour
        appliquer le changement à l'inscription active si l'utilisateur le
        demande.
        """
        if not id_eleve:
            return False, "Élève introuvable."
        if not id_famille:
            return False, "Veuillez sélectionner une famille."
        session = get_session()
        try:
            eleve = session.get(Eleve, id_eleve)
            if not eleve:
                return False, "Élève introuvable."
            famille = session.get(TFamille, id_famille)
            if not famille:
                return False, "Famille introuvable."
            eleve.IDFamille = id_famille
            session.commit()
            return True, f"Famille associée à {eleve.Nom} {eleve.Prenoms}."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {e}"
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
        except Exception:
            logger.exception("Erreur de génération de matricule")
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
        except Exception:
            logger.exception("Erreur de copie de la photo d'élève")
            return None

    @staticmethod
    def _replace_cursus_anterieur(session, id_eleve: int, rows: list[dict]) -> None:
        """Remplace l'integralite du cursus scolaire anterieur d'un eleve.

        Les lignes n'ont pas d'identite propre pour l'utilisateur (simple
        tableau libre repris de la fiche papier) : on efface et on reinsere
        plutot que de diffing, ce qui reste simple et correct tant que ce
        tableau n'est edite que depuis ce formulaire.
        """
        session.query(CursusAnterieur).filter_by(IDEleve=id_eleve).delete()
        for row in rows or []:
            annee = (row.get("AnneeScolaire") or "").strip()
            classe = (row.get("Classe") or "").strip()
            etablissement = (row.get("Etablissement") or "").strip()
            moyenne = row.get("MoyenneAnnuelle")
            if not annee and not classe and not etablissement and moyenne is None:
                continue
            session.add(CursusAnterieur(
                IDEleve=id_eleve,
                AnneeScolaire=annee or None,
                Classe=classe or None,
                MoyenneAnnuelle=moyenne,
                Etablissement=etablissement or None,
            ))

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

            matricule_national = EleveService.normalize_matricule_national(data.get("MatriculeNational"))
            if matricule_national:
                doublon_national = EleveService._find_by_matricule_national(session, matricule_national)
                if doublon_national:
                    return False, EleveService._duplicate_matricule_national_message(doublon_national)

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
                HabitationUrgence=data.get("HabitationUrgence"),
                MatriculeNational=matricule_national,
                EtablissementOrigine=data.get("EtablissementOrigine"),
                ClasseSuivieOrigine=data.get("ClasseSuivieOrigine"),
                DeuxiemeLangue=data.get("DeuxiemeLangue"),
                VitChezQui=data.get("VitChezQui"),
                Baptise=data.get("Baptise"),
                Confirme=data.get("Confirme"),
                ParoisseActuelle=data.get("ParoisseActuelle"),
                ActiviteParoisse=data.get("ActiviteParoisse"),
                PreciserEglise=data.get("PreciserEglise"),
                NDossier=data.get("NDossier"),
                DateAdmission=data.get("DateAdmission"),
                AutorisationCourrier=data.get("AutorisationCourrier"),
                DocExtraitNaissance=data.get("DocExtraitNaissance", False),
                DocCertifScolarite=data.get("DocCertifScolarite", False),
                DocBulletins=data.get("DocBulletins", False),
                DocPhotos=data.get("DocPhotos", False),
                DocCarnetVaccination=data.get("DocCarnetVaccination", False),
                DocCarnetSante=data.get("DocCarnetSante", False),
                DocDispenseEPS=data.get("DocDispenseEPS", False),
                DocDispenseEPSCertificat=data.get("DocDispenseEPSCertificat", False),
                DocCarteSejour=data.get("DocCarteSejour", False),
                DocLivretScolaire=data.get("DocLivretScolaire", False),
                AccidentNom1=data.get("AccidentNom1"),
                AccidentTel1=data.get("AccidentTel1"),
                AccidentCel1=data.get("AccidentCel1"),
                AccidentBureau1=data.get("AccidentBureau1"),
                AccidentNom2=data.get("AccidentNom2"),
                AccidentTel2=data.get("AccidentTel2"),
                AccidentCel2=data.get("AccidentCel2"),
                AccidentBureau2=data.get("AccidentBureau2"),
                AccidentAdresse=data.get("AccidentAdresse"),
                ConduireHopital=data.get("ConduireHopital"),
                ConduireHopitalPrecision=data.get("ConduireHopitalPrecision"),
                ConduireClinique=data.get("ConduireClinique"),
                ConduireCliniquePrecision=data.get("ConduireCliniquePrecision"),
                MedecinNom=data.get("MedecinNom"),
                MedecinTel=data.get("MedecinTel"),
                MedecinCel=data.get("MedecinCel"),
                MedecinBureau=data.get("MedecinBureau"),
                MedecinAdresse=data.get("MedecinAdresse"),
                Maladie=data.get("Maladie"),
                ContreIndications=data.get("ContreIndications"),
            )
            session.add(eleve)
            session.flush()
            EleveService._replace_cursus_anterieur(session, eleve.IDEleve, data.get("CursusAnterieur", []))
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

            matricule_national = EleveService.normalize_matricule_national(data.get("MatriculeNational"))
            if matricule_national:
                doublon_national = EleveService._find_by_matricule_national(
                    session, matricule_national, exclude_id=id_eleve,
                )
                if doublon_national:
                    return False, EleveService._duplicate_matricule_national_message(doublon_national)

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

            eleve.MatriculeNational = matricule_national
            eleve.EtablissementOrigine = data.get("EtablissementOrigine")
            eleve.ClasseSuivieOrigine = data.get("ClasseSuivieOrigine")
            eleve.DeuxiemeLangue = data.get("DeuxiemeLangue")
            eleve.VitChezQui = data.get("VitChezQui")
            eleve.Baptise = data.get("Baptise")
            eleve.Confirme = data.get("Confirme")
            eleve.ParoisseActuelle = data.get("ParoisseActuelle")
            eleve.ActiviteParoisse = data.get("ActiviteParoisse")
            eleve.PreciserEglise = data.get("PreciserEglise")
            eleve.NDossier = data.get("NDossier")
            eleve.DateAdmission = data.get("DateAdmission")
            eleve.AutorisationCourrier = data.get("AutorisationCourrier")
            eleve.DocExtraitNaissance = data.get("DocExtraitNaissance", False)
            eleve.DocCertifScolarite = data.get("DocCertifScolarite", False)
            eleve.DocBulletins = data.get("DocBulletins", False)
            eleve.DocPhotos = data.get("DocPhotos", False)
            eleve.DocCarnetVaccination = data.get("DocCarnetVaccination", False)
            eleve.DocCarnetSante = data.get("DocCarnetSante", False)
            eleve.DocDispenseEPS = data.get("DocDispenseEPS", False)
            eleve.DocDispenseEPSCertificat = data.get("DocDispenseEPSCertificat", False)
            eleve.DocCarteSejour = data.get("DocCarteSejour", False)
            eleve.DocLivretScolaire = data.get("DocLivretScolaire", False)
            eleve.AccidentNom1 = data.get("AccidentNom1")
            eleve.AccidentTel1 = data.get("AccidentTel1")
            eleve.AccidentCel1 = data.get("AccidentCel1")
            eleve.AccidentBureau1 = data.get("AccidentBureau1")
            eleve.AccidentNom2 = data.get("AccidentNom2")
            eleve.AccidentTel2 = data.get("AccidentTel2")
            eleve.AccidentCel2 = data.get("AccidentCel2")
            eleve.AccidentBureau2 = data.get("AccidentBureau2")
            eleve.AccidentAdresse = data.get("AccidentAdresse")
            eleve.ConduireHopital = data.get("ConduireHopital")
            eleve.ConduireHopitalPrecision = data.get("ConduireHopitalPrecision")
            eleve.ConduireClinique = data.get("ConduireClinique")
            eleve.ConduireCliniquePrecision = data.get("ConduireCliniquePrecision")
            eleve.MedecinNom = data.get("MedecinNom")
            eleve.MedecinTel = data.get("MedecinTel")
            eleve.MedecinCel = data.get("MedecinCel")
            eleve.MedecinBureau = data.get("MedecinBureau")
            eleve.MedecinAdresse = data.get("MedecinAdresse")
            eleve.Maladie = data.get("Maladie")
            eleve.ContreIndications = data.get("ContreIndications")

            EleveService._replace_cursus_anterieur(session, id_eleve, data.get("CursusAnterieur", []))

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
