"""Tests des autorisations."""

import pytest

from crm.models import Client, Collaborateur, Contrat, Evenement, Role
from crm.permissions import Action, PermissionRefusee, a_le_droit, verifier


def employe(role: str, id: int = 1) -> Collaborateur:
    """Collaborateur en mémoire."""
    return Collaborateur(id=id, role=Role(nom=role))


@pytest.mark.parametrize(
    "role, action, attendu",
    [
        ("gestion", Action.LIRE, True),
        ("commercial", Action.LIRE, True),
        ("support", Action.LIRE, True),
        ("gestion", Action.CREER_COLLABORATEUR, True),
        ("commercial", Action.CREER_COLLABORATEUR, False),
        ("support", Action.CREER_COLLABORATEUR, False),
        ("gestion", Action.CREER_CONTRAT, True),
        ("commercial", Action.CREER_CONTRAT, False),
        ("support", Action.CREER_CONTRAT, False),
        ("gestion", Action.SIGNER_CONTRAT, True),
        ("commercial", Action.SIGNER_CONTRAT, False),
        ("support", Action.SIGNER_CONTRAT, False),
        ("commercial", Action.CREER_CLIENT, True),
        ("gestion", Action.CREER_CLIENT, False),
        ("support", Action.CREER_CLIENT, False),
    ],
)
def test_droits_qui_dependent_seulement_du_role(role, action, attendu):
    assert a_le_droit(employe(role), action) is attendu


def test_un_commercial_modifie_ses_clients_mais_pas_ceux_des_autres():
    commercial = employe("commercial", id=1)
    assert a_le_droit(commercial, Action.MODIFIER_CLIENT, Client(commercial_id=1))
    assert not a_le_droit(commercial, Action.MODIFIER_CLIENT, Client(commercial_id=2))


def test_un_commercial_modifie_seulement_les_contrats_de_ses_clients():
    commercial = employe("commercial", id=1)
    le_sien = Contrat(client=Client(commercial_id=1))
    celui_d_un_autre = Contrat(client=Client(commercial_id=2))
    assert a_le_droit(commercial, Action.MODIFIER_CONTRAT, le_sien)
    assert not a_le_droit(commercial, Action.MODIFIER_CONTRAT, celui_d_un_autre)


def test_un_commercial_cree_un_evenement_seulement_pour_ses_clients():
    commercial = employe("commercial", id=1)
    le_sien = Contrat(client=Client(commercial_id=1))
    celui_d_un_autre = Contrat(client=Client(commercial_id=2))
    assert a_le_droit(commercial, Action.CREER_EVENEMENT, le_sien)
    assert not a_le_droit(commercial, Action.CREER_EVENEMENT, celui_d_un_autre)


def test_la_gestion_modifie_tous_les_contrats_et_tous_les_evenements():
    gestion = employe("gestion")
    contrat = Contrat(client=Client(commercial_id=99))
    assert a_le_droit(gestion, Action.MODIFIER_CONTRAT, contrat)
    assert a_le_droit(gestion, Action.MODIFIER_EVENEMENT, Evenement(support_id=None))


def test_un_support_modifie_seulement_ses_evenements():
    support = employe("support", id=3)
    assert a_le_droit(support, Action.MODIFIER_EVENEMENT, Evenement(support_id=3))
    assert not a_le_droit(support, Action.MODIFIER_EVENEMENT, Evenement(support_id=4))
    assert not a_le_droit(
        support, Action.MODIFIER_EVENEMENT, Evenement(support_id=None)
    )


def test_un_role_inconnu_n_a_aucun_droit():
    assert not a_le_droit(employe("stagiaire"), Action.LIRE)


def test_verifier_leve_une_erreur_si_l_action_est_refusee():
    with pytest.raises(PermissionRefusee, match="créer un client"):
        verifier(employe("support"), Action.CREER_CLIENT)
