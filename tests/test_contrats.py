"""Tests de la création et de la modification des contrats."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from crm import services
from crm.exceptions import DonneesInvalides, ObjetIntrouvable
from crm.models import Client, Collaborateur, Role
from crm.permissions import PermissionRefusee


@pytest.fixture
def equipe(session):
    """Une gestionnaire, deux commerciaux, un support, et un client par commercial."""
    roles = {role.nom: role for role in session.scalars(select(Role))}

    def employe(nom, role):
        return Collaborateur(
            numero_employe=nom,
            nom=nom,
            email=f"{nom}@test.fr",
            mot_de_passe_hache="empreinte-factice",
            role=roles[role],
        )

    gestion = employe("gestion", "gestion")
    bill = employe("bill", "commercial")
    paul = employe("paul", "commercial")
    kate = employe("kate", "support")
    client_de_bill = Client(nom_complet="Kevin", email="kevin@test.fr", commercial=bill)
    client_de_paul = Client(nom_complet="Jacky", email="jacky@test.fr", commercial=paul)
    session.add_all([gestion, bill, paul, kate, client_de_bill, client_de_paul])
    session.commit()
    return {
        "gestion": gestion,
        "bill": bill,
        "paul": paul,
        "kate": kate,
        "client_de_bill": client_de_bill,
        "client_de_paul": client_de_paul,
    }


@pytest.fixture
def contrat_de_bill(session, equipe):
    """Un contrat de 1000 €, non signé, pour le client de Bill."""
    return services.creer_contrat(
        session, equipe["gestion"], equipe["client_de_bill"].id, "1000"
    )


# Création


def test_la_gestion_cree_un_contrat_non_signe(contrat_de_bill, equipe):
    assert contrat_de_bill.client is equipe["client_de_bill"]
    assert contrat_de_bill.signe is False


def test_sans_reste_precise_il_vaut_le_total(contrat_de_bill):
    assert contrat_de_bill.montant_restant == Decimal("1000.00")


def test_un_commercial_ne_cree_pas_de_contrat(session, equipe):
    with pytest.raises(PermissionRefusee):
        services.creer_contrat(
            session, equipe["bill"], equipe["client_de_bill"].id, "1000"
        )


def test_un_contrat_pour_un_client_inexistant_est_refuse(session, equipe):
    with pytest.raises(ObjetIntrouvable):
        services.creer_contrat(session, equipe["gestion"], 999, "1000")


def test_un_reste_superieur_au_total_est_refuse(session, equipe):
    with pytest.raises(DonneesInvalides, match="dépasser"):
        services.creer_contrat(
            session, equipe["gestion"], equipe["client_de_bill"].id, "1000", "1500"
        )


# Modification


def test_le_commercial_modifie_le_reste_a_payer(session, equipe, contrat_de_bill):
    services.modifier_contrat(
        session, equipe["bill"], contrat_de_bill.id, montant_restant="400"
    )
    assert contrat_de_bill.montant_restant == Decimal("400.00")


def test_un_commercial_ne_modifie_pas_le_contrat_d_un_autre(
    session, equipe, contrat_de_bill
):
    with pytest.raises(PermissionRefusee):
        services.modifier_contrat(
            session, equipe["paul"], contrat_de_bill.id, montant_restant="0"
        )


def test_un_commercial_ne_peut_pas_signer(session, equipe, contrat_de_bill):
    with pytest.raises(PermissionRefusee, match="signer"):
        services.modifier_contrat(
            session, equipe["bill"], contrat_de_bill.id, signe=True
        )
    assert contrat_de_bill.signe is False


def test_la_gestion_signe_un_contrat(session, equipe, contrat_de_bill):
    services.modifier_contrat(
        session, equipe["gestion"], contrat_de_bill.id, signe=True
    )
    assert contrat_de_bill.signe is True


def test_baisser_le_total_sous_le_reste_est_refuse(session, equipe, contrat_de_bill):
    with pytest.raises(DonneesInvalides, match="dépasser"):
        services.modifier_contrat(
            session, equipe["gestion"], contrat_de_bill.id, montant_total="500"
        )
    assert contrat_de_bill.montant_total == Decimal("1000.00")


def test_la_gestion_change_le_client_du_contrat(session, equipe, contrat_de_bill):
    services.modifier_contrat(
        session,
        equipe["gestion"],
        contrat_de_bill.id,
        client_id=equipe["client_de_paul"].id,
    )
    assert contrat_de_bill.client is equipe["client_de_paul"]


def test_un_commercial_ne_change_pas_le_client(session, equipe, contrat_de_bill):
    with pytest.raises(PermissionRefusee):
        services.modifier_contrat(
            session,
            equipe["bill"],
            contrat_de_bill.id,
            client_id=equipe["client_de_paul"].id,
        )
    assert contrat_de_bill.client is equipe["client_de_bill"]


def test_un_contrat_inexistant_est_signale(session, equipe):
    with pytest.raises(ObjetIntrouvable):
        services.modifier_contrat(session, equipe["gestion"], 999, signe=True)
