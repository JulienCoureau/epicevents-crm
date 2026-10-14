"""Tests du hachage et de la verification des mots de passe."""

import pytest

from crm.passwords import (
    hacher_mot_de_passe,
    valider_mot_de_passe,
    verifier_mot_de_passe,
)

MOT_DE_PASSE = "codeSecret2026!"


def test_l_empreinte_ne_contient_pas_le_mot_de_passe():
    empreinte = hacher_mot_de_passe(MOT_DE_PASSE)
    assert MOT_DE_PASSE not in empreinte
    assert empreinte.startswith("$argon2id$")


def test_deux_empreintes_du_meme_mot_de_passe_sont_differentes():
    assert hacher_mot_de_passe(MOT_DE_PASSE) != hacher_mot_de_passe(MOT_DE_PASSE)


def test_le_bon_mot_de_passe_est_accepte():
    empreinte = hacher_mot_de_passe(MOT_DE_PASSE)
    assert verifier_mot_de_passe(empreinte, MOT_DE_PASSE)


def test_un_mauvais_mot_de_passe_est_refuse():
    empreinte = hacher_mot_de_passe(MOT_DE_PASSE)
    assert not verifier_mot_de_passe(empreinte, "mauvais")


def test_un_mot_de_passe_trop_court_est_refuse():
    with pytest.raises(ValueError):
        valider_mot_de_passe("court")
