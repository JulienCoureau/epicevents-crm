"""Tests de la validation des données saisies"""

import pytest

from crm import validators
from crm.exceptions import DonneesInvalides
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo


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


@pytest.mark.parametrize(
    "saisie, attendu",
    [
        ("1500", Decimal("1500.00")),
        ("1 500,50", Decimal("1500.50")),
        ("0", Decimal("0.00")),
        ("12.3", Decimal("12.30")),
    ],
)
def test_un_montant_valide_est_converti(saisie, attendu):
    assert validators.montant(saisie, "montant") == attendu


@pytest.mark.parametrize(
    "saisie", ["abc", "", "-20", "10.555", "NaN", "Infinity", "100000000"]
)
def test_un_montant_invalide_est_refuse(saisie):
    with pytest.raises(DonneesInvalides):
        validators.montant(saisie, "montant")


def test_une_date_valide_est_convertie_a_l_heure_de_paris():
    assert validators.date_heure("04/06/2027 13:00", "début") == datetime(
        2027, 6, 4, 13, 0, tzinfo=ZoneInfo("Europe/Paris")
    )


@pytest.mark.parametrize(
    "saisie", ["2027-06-04 13:00", "31/02/2027 10:00", "04/06/2027", "", "demain"]
)
def test_une_date_invalide_est_refusee(saisie):
    with pytest.raises(DonneesInvalides, match="JJ/MM/AAAA"):
        validators.date_heure(saisie, "début")


@pytest.mark.parametrize("saisie, attendu", [("75", 75), (" 200 ", 200), ("0", 0)])
def test_un_nombre_de_participants_valide(saisie, attendu):
    assert validators.nombre_participants(saisie) == attendu


@pytest.mark.parametrize("saisie", ["-1", "abc", "1.5", "100001"])
def test_un_nombre_de_participants_invalide_est_refuse(saisie):
    with pytest.raises(DonneesInvalides):
        validators.nombre_participants(saisie)
