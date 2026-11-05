"""Tests de la création et de la modification des événements."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from crm import services
from crm.exceptions import DonneesInvalides, ObjetIntrouvable
from crm.models import Client, Collaborateur, Contrat, Role
from crm.permissions import PermissionRefusee

DEBUT = "04/06/2027 13:00"
FIN = "05/06/2027 02:00"


@pytest.fixture
def equipe(session):
    """Gestion, deux commerciaux, deux supports, leurs clients et leurs contrats."""
    roles = {role.nom: role for role in session.scalars(select(Role))}

    def employe(nom, role):
        return Collaborateur(
            numero_employe=nom,
            nom=nom,
            email=f"{nom}@test.fr",
            mot_de_passe_hache="empreinte-factice",
            role=roles[role],
        )

    def contrat(client, signe):
        return Contrat(
            client=client,
            montant_total=Decimal("1000"),
            montant_restant=Decimal("0"),
            signe=signe,
        )

    gestion = employe("gestion", "gestion")
    bill = employe("bill", "commercial")
    paul = employe("paul", "commercial")
    kate = employe("kate", "support")
    alienor = employe("alienor", "support")
    client_de_bill = Client(nom_complet="John", email="john@test.fr", commercial=bill)
    client_de_paul = Client(nom_complet="Jacky", email="jacky@test.fr", commercial=paul)
    signe_bill = contrat(client_de_bill, signe=True)
    non_signe_bill = contrat(client_de_bill, signe=False)
    signe_paul = contrat(client_de_paul, signe=True)
    session.add_all(
        [gestion, bill, paul, kate, alienor, signe_bill, non_signe_bill, signe_paul]
    )
    session.commit()
    return {
        "gestion": gestion,
        "bill": bill,
        "paul": paul,
        "kate": kate,
        "alienor": alienor,
        "signe_bill": signe_bill,
        "non_signe_bill": non_signe_bill,
        "signe_paul": signe_paul,
    }


def creer(session, equipe, collaborateur="bill", contrat="signe_bill", fin=FIN):
    """Crée un événement avec des valeurs valides par défaut."""
    return services.creer_evenement(
        session,
        equipe[collaborateur],
        equipe[contrat].id,
        nom="Mariage",
        date_debut=DEBUT,
        date_fin=fin,
        lieu="Candé-sur-Beuvron",
        participants="75",
    )


@pytest.fixture
def evenement(session, equipe):
    """L'événement du contrat signé de Bill, sans support."""
    return creer(session, equipe)


# Création


def test_le_commercial_cree_l_evenement_de_son_contrat_signe(evenement, equipe):
    assert evenement.contrat is equipe["signe_bill"]
    assert evenement.support is None


def test_un_contrat_non_signe_est_refuse(session, equipe):
    with pytest.raises(DonneesInvalides, match="signé"):
        creer(session, equipe, contrat="non_signe_bill")


def test_un_commercial_ne_cree_pas_pour_le_client_d_un_autre(session, equipe):
    with pytest.raises(PermissionRefusee):
        creer(session, equipe, contrat="signe_paul")


def test_la_gestion_ne_cree_pas_d_evenement(session, equipe):
    with pytest.raises(PermissionRefusee):
        creer(session, equipe, collaborateur="gestion")


def test_un_seul_evenement_par_contrat(session, equipe, evenement):
    with pytest.raises(DonneesInvalides, match="déjà"):
        creer(session, equipe)


def test_une_fin_avant_le_debut_est_refusee(session, equipe):
    with pytest.raises(DonneesInvalides, match="postérieure"):
        creer(session, equipe, fin="01/06/2027 10:00")


# Désignation du support


def test_la_gestion_designe_le_support(session, equipe, evenement):
    services.modifier_evenement(
        session, equipe["gestion"], evenement.id, support_id=equipe["kate"].id
    )
    assert evenement.support is equipe["kate"]


def test_un_commercial_ne_peut_pas_etre_support(session, equipe, evenement):
    with pytest.raises(DonneesInvalides, match="support"):
        services.modifier_evenement(
            session, equipe["gestion"], evenement.id, support_id=equipe["bill"].id
        )


def test_le_support_ne_se_reattribue_pas_l_evenement(session, equipe, evenement):
    services.modifier_evenement(
        session, equipe["gestion"], evenement.id, support_id=equipe["kate"].id
    )
    with pytest.raises(PermissionRefusee):
        services.modifier_evenement(
            session, equipe["kate"], evenement.id, support_id=equipe["alienor"].id
        )
    assert evenement.support is equipe["kate"]


# Modification


def test_le_support_modifie_son_evenement(session, equipe, evenement):
    services.modifier_evenement(
        session, equipe["gestion"], evenement.id, support_id=equipe["kate"].id
    )
    services.modifier_evenement(
        session, equipe["kate"], evenement.id, notes="DJ réservé."
    )
    assert evenement.notes == "DJ réservé."


def test_un_support_ne_modifie_pas_l_evenement_d_un_autre(session, equipe, evenement):
    services.modifier_evenement(
        session, equipe["gestion"], evenement.id, support_id=equipe["kate"].id
    )
    with pytest.raises(PermissionRefusee):
        services.modifier_evenement(
            session, equipe["alienor"], evenement.id, notes="Intrusion"
        )


def test_le_commercial_ne_modifie_pas_l_evenement(session, equipe, evenement):
    with pytest.raises(PermissionRefusee):
        services.modifier_evenement(
            session, equipe["bill"], evenement.id, participants="80"
        )


def test_une_fin_modifiee_avant_le_debut_est_refusee(session, equipe, evenement):
    with pytest.raises(DonneesInvalides, match="postérieure"):
        services.modifier_evenement(
            session, equipe["gestion"], evenement.id, date_fin="01/01/2027 10:00"
        )


def test_un_evenement_inexistant_est_signale(session, equipe):
    with pytest.raises(ObjetIntrouvable):
        services.modifier_evenement(session, equipe["gestion"], 999, nom="Personne")
