"""Tests de la création et de la modification des clients."""

import pytest
from sqlalchemy import select

from crm import services
from crm.exceptions import DonneesInvalides, ObjetIntrouvable
from crm.models import Collaborateur, Role
from crm.permissions import PermissionRefusee


@pytest.fixture
def employes(session):
    """Deux commerciaux (Bill, Paul) et un support (Kate), enregistrés en base."""
    roles = {role.nom: role for role in session.scalars(select(Role))}

    def employe(nom, role):
        return Collaborateur(
            numero_employe=nom,
            nom=nom,
            email=f"{nom}@test.fr",
            mot_de_passe_hache="empreinte-factice",
            role=roles[role],
        )

    bill = employe("bill", "commercial")
    paul = employe("paul", "commercial")
    kate = employe("kate", "support")
    session.add_all([bill, paul, kate])
    session.commit()
    return bill, paul, kate


@pytest.fixture
def client_de_bill(session, employes):
    """Un client créé par Bill."""
    bill, _, _ = employes
    return services.creer_client(
        session,
        bill,
        "Kevin Casey",
        "kevin@startup.io",
        "+678 123 456 78",
        "Cool Startup LLC",
    )


# --- Création ---


def test_le_createur_devient_le_commercial_du_client(client_de_bill, employes):
    bill, _, _ = employes
    assert client_de_bill.commercial is bill


def test_les_donnees_sont_nettoyees_a_la_creation(session, employes):
    bill, _, _ = employes
    client = services.creer_client(session, bill, "  John Ouick ", " John@Gmail.com ")
    assert client.nom_complet == "John Ouick"
    assert client.email == "john@gmail.com"
    assert client.telephone is None


def test_un_support_ne_peut_pas_creer_de_client(session, employes):
    _, _, kate = employes
    with pytest.raises(PermissionRefusee):
        services.creer_client(session, kate, "Intrus", "intrus@test.fr")


def test_un_email_deja_utilise_est_refuse(session, employes, client_de_bill):
    _, paul, _ = employes
    with pytest.raises(DonneesInvalides, match="déjà"):
        services.creer_client(session, paul, "Autre", "KEVIN@startup.io")


def test_un_email_invalide_est_refuse_a_la_creation(session, employes):
    bill, _, _ = employes
    with pytest.raises(DonneesInvalides):
        services.creer_client(session, bill, "John", "pas-un-email")


# --- Modification ---


def test_le_commercial_modifie_son_client(session, employes, client_de_bill):
    bill, _, _ = employes
    services.modifier_client(
        session, bill, client_de_bill.id, telephone="+33 6 12 34 56 78"
    )
    assert client_de_bill.telephone == "+33 6 12 34 56 78"
    assert client_de_bill.entreprise == "Cool Startup LLC"


def test_une_chaine_vide_efface_un_champ_facultatif(session, employes, client_de_bill):
    bill, _, _ = employes
    services.modifier_client(session, bill, client_de_bill.id, entreprise="")
    assert client_de_bill.entreprise is None


def test_un_commercial_ne_modifie_pas_le_client_d_un_autre(
    session, employes, client_de_bill
):
    _, paul, _ = employes
    with pytest.raises(PermissionRefusee):
        services.modifier_client(session, paul, client_de_bill.id, nom_complet="Pirate")
    assert client_de_bill.nom_complet == "Kevin Casey"


def test_une_modification_invalide_ne_change_rien(session, employes, client_de_bill):
    bill, _, _ = employes
    with pytest.raises(DonneesInvalides):
        services.modifier_client(
            session,
            bill,
            client_de_bill.id,
            nom_complet="Nouveau nom",
            email="pas-un-email",
        )
    assert client_de_bill.nom_complet == "Kevin Casey"


def test_garder_son_propre_email_n_est_pas_un_doublon(
    session, employes, client_de_bill
):
    bill, _, _ = employes
    services.modifier_client(session, bill, client_de_bill.id, email="kevin@startup.io")
    assert client_de_bill.email == "kevin@startup.io"


def test_un_client_inexistant_est_signale(session, employes):
    bill, _, _ = employes
    with pytest.raises(ObjetIntrouvable):
        services.modifier_client(session, bill, 999, nom_complet="Personne")
