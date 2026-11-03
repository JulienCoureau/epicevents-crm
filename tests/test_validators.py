"""Tests de la validation des données saisies"""

import pytest

from crm import validators
from crm.exceptions import DonneesInvalides


def test_un_texte_obligatoire_est_nettoye():
    assert validators.texte_obligatoire("  Kevin Casey ", "nom", 100) == "Kevin Casey"


@pytest.mark.parametrize("valeur", ["", "   ", None])
def test_un_texte_obligatoire_vide_est_refuse(valeur):
    with pytest.raises(DonneesInvalides, match="obligatoire"):
        validators.texte_obligatoire(valeur, "nom", 100)


def test_un_texte_trop_long_est_refuse():
    with pytest.raises(DonneesInvalides, match="dépasse"):
        validators.texte_obligatoire("x" * 101, "nom", 100)


def test_un_texte_facultatif_vide_devient_none():
    assert validators.texte_facultatif("  ", "entreprise", 100) is None


def test_un_email_est_mis_en_minuscules():
    assert validators.email(" Kevin@Startup.IO ") == "kevin@startup.io"


@pytest.mark.parametrize(
    "valeur", ["pas-un-email", "kevin@", "@startup.io", "kevin@startup", "a b@c.fr"]
)
def test_un_email_mal_forme_est_refuse(valeur):
    with pytest.raises(DonneesInvalides):
        validators.email(valeur)


@pytest.mark.parametrize("valeur", ["+678 123 456 78", "+666 12345", "05.56.12.34.56"])
def test_les_telephones_du_cahier_des_charges_sont_acceptes(valeur):
    assert validators.telephone(valeur) == valeur


def test_un_telephone_vide_devient_none():
    assert validators.telephone("") is None


@pytest.mark.parametrize("valeur", ["abc", "12", "06 12 34 56 78; DROP TABLE"])
def test_un_telephone_invalide_est_refuse(valeur):
    with pytest.raises(DonneesInvalides):
        validators.telephone(valeur)
