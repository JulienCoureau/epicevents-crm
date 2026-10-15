"""Creation du premier collaborateur"""

from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from crm.database import SessionLocal
from crm.models import Collaborateur, Role
from crm.passwords import hacher_mot_de_passe, valider_mot_de_passe


def demander(question: str) -> str:
    """Pose une question jusqu'à obtenir une réponse non vide."""
    while True:
        reponse = input(question).strip()
        if reponse:
            return reponse
        print("Ce champ est obligatoire.")


def demander_mot_de_passe() -> str:
    """Demande le mot de passe 2 fois, sans l'afficher, et le valide."""
    while True:
        mot_de_passe = getpass("Mot de passe : ")
        try:
            valider_mot_de_passe(mot_de_passe)
        except ValueError as erreur:
            print(erreur)
            continue
        if getpass("Confirmation : ") == mot_de_passe:
            return mot_de_passe
        print("Les deux saisies ne correspondent pas.")


def main() -> None:
    """Saisit les informations puis enregistre le collaborateur."""
    numero = demander("Numéro d'employé : ")
    nom = demander("Nom : ")
    email = demander("Email : ").lower()
    mot_de_passe = demander_mot_de_passe()

    with SessionLocal() as session:
        gestion = session.scalars(select(Role).where(Role.nom == "gestion")).one()
        session.add(
            Collaborateur(
                numero_employe=numero,
                nom=nom,
                email=email,
                mot_de_passe_hache=hacher_mot_de_passe(mot_de_passe),
                role=gestion,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            print("Ce numéro d'employé ou cet email existe déjà.")
            return

    print(f"Employe {nom} créé dans le département gestion.")


if __name__ == "__main__":
    main()
