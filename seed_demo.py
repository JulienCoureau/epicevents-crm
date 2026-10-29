"""jeu de donnée pour démonstration"""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select

from create_manager import demander_mot_de_passe
from crm.database import SessionLocal
from crm.models import Client, Collaborateur, Contrat, Evenement, Role
from crm.passwords import hacher_mot_de_passe

PARIS = ZoneInfo("Europe/Paris")


def main() -> None:
    """Crée collaborateurs, clients, contrats et événements de démonstration."""
    print("Mot de passe commun aux comptes de démonstration :")
    empreinte = hacher_mot_de_passe(demander_mot_de_passe())

    with SessionLocal() as session:
        if session.scalars(select(Client)).first() is not None:
            print("La base contient déjà des clients : rien n'a été ajouté.")
            return

        roles = {role.nom: role for role in session.scalars(select(Role))}

        def collaborateur(numero, nom, email, role):
            return Collaborateur(
                numero_employe=numero,
                nom=nom,
                email=email,
                mot_de_passe_hache=empreinte,
                role=roles[role],
            )

        bill = collaborateur("EE101", "Bill Boquet", "bill@epicevents.fr", "commercial")
        paul = collaborateur("EE102", "Paul Durand", "paul@epicevents.fr", "commercial")
        kate = collaborateur("EE201", "Kate Hastroff", "kate@epicevents.fr", "support")
        alienor = collaborateur(
            "EE202", "Aliénor Vichum", "alienor@epicevents.fr", "support"
        )

        kevin = Client(
            nom_complet="Kevin Casey",
            email="kevin@startup.io",
            telephone="+678 123 456 78",
            entreprise="Cool Startup LLC",
            commercial=bill,
        )
        john = Client(
            nom_complet="John Ouick",
            email="john.ouick@gmail.com",
            telephone="+1 234 567 8901",
            commercial=bill,
        )
        jacky = Client(
            nom_complet="Jacky Blangier",
            email="jacky@loubouzin.grd",
            telephone="+666 12345",
            entreprise="Lou Bouzin",
            commercial=paul,
        )

        contrat_kevin = Contrat(
            client=kevin,
            montant_total=Decimal("3000.00"),
            montant_restant=Decimal("3000.00"),
            signe=False,
        )
        contrat_john = Contrat(
            client=john,
            montant_total=Decimal("12000.00"),
            montant_restant=Decimal("0.00"),
            signe=True,
        )
        contrat_lou = Contrat(
            client=jacky,
            montant_total=Decimal("8500.00"),
            montant_restant=Decimal("4250.00"),
            signe=True,
        )

        tournois = Evenement(
            nom="Tenkaichi Budokai",
            contrat=contrat_john,
            support=kate,
            date_debut=datetime(2027, 6, 7, 13, 0, tzinfo=PARIS),
            date_fin=datetime(2027, 6, 10, 2, 0, tzinfo=PARIS),
            lieu="439e District Est, 22120 Mont Paozu, Japon",
            participants=75,
            notes="Debut du tournois par un test de force. " "Vérifier les perruques.",
        )
        assemblee = Evenement(
            nom="Assemblée Konoha",
            contrat=contrat_lou,
            support=None,
            date_debut=datetime(2026, 5, 5, 15, 0, tzinfo=PARIS),
            date_fin=datetime(2026, 5, 5, 17, 0, tzinfo=PARIS),
            lieu="Bureau du hokage, 33205, Konoha",
            participants=200,
            notes="Assemblée générale des actionnaires.",
        )

        session.add_all([bill, paul, kate, alienor, contrat_kevin, tournois, assemblee])
        session.commit()

    print("Données de démonstration ajoutées. Comptes disponibles :")
    print("  bill@epicevents.fr, paul@epicevents.fr (commercial)")
    print("  kate@epicevents.fr, alienor@epicevents.fr (support)")


if __name__ == "__main__":
    main()
