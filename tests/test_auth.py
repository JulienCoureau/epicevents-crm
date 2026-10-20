"""Tests de l'authentification : identifiants, jeton, expiration, falsification."""

from datetime import timedelta

import jwt
import pytest
from sqlalchemy import select

from crm import auth
from crm.auth import (
    AuthentificationError,
    authentifier,
    collaborateur_connecte,
    creer_jeton,
    enregistrer_jeton,
    supprimer_jeton,
)
from crm.models import Collaborateur, Role
from crm.passwords import hacher_mot_de_passe

MOT_DE_PASSE = "codeSecret2026!"


@pytest.fixture
def gestionnaire(session):
    """Un collaborateur du département gestion, enregistré en base."""
    gestion = session.scalars(select(Role).where(Role.nom == "gestion")).one()
    collaborateur = Collaborateur(
        numero_employe="EE001",
        nom="Test Gestion",
        email="gestion@test.fr",
        mot_de_passe_hache=hacher_mot_de_passe(MOT_DE_PASSE),
        role=gestion,
    )
    session.add(collaborateur)
    session.commit()
    return collaborateur


# Vérification des identifiants


def test_les_bons_identifiants_sont_acceptes(session, gestionnaire):
    assert authentifier(session, "gestion@test.fr", MOT_DE_PASSE) == gestionnaire


def test_l_email_ne_tient_pas_compte_des_majuscules(session, gestionnaire):
    assert authentifier(session, " GESTION@test.fr ", MOT_DE_PASSE) == gestionnaire


def test_un_mauvais_mot_de_passe_est_refuse(session, gestionnaire):
    with pytest.raises(AuthentificationError):
        authentifier(session, "gestion@test.fr", "mauvais-mot-de-passe")


def test_email_inconnu_et_mauvais_mot_de_passe_ont_le_meme_message(
    session, gestionnaire
):
    with pytest.raises(AuthentificationError) as mauvais_mot_de_passe:
        authentifier(session, "gestion@test.fr", "mauvais-mot-de-passe")
    with pytest.raises(AuthentificationError) as email_inconnu:
        authentifier(session, "inconnu@test.fr", MOT_DE_PASSE)
    assert str(mauvais_mot_de_passe.value) == str(email_inconnu.value)


# Jeton et session persistante


def test_le_jeton_retrouve_le_collaborateur(session, gestionnaire):
    enregistrer_jeton(creer_jeton(gestionnaire))
    assert collaborateur_connecte(session) == gestionnaire


def test_le_fichier_jeton_n_est_lisible_que_par_son_proprietaire(gestionnaire):
    enregistrer_jeton(creer_jeton(gestionnaire))
    assert auth.FICHIER_JETON.stat().st_mode & 0o777 == 0o600


def test_sans_jeton_l_acces_est_refuse(session):
    with pytest.raises(AuthentificationError):
        collaborateur_connecte(session)


def test_apres_logout_l_acces_est_refuse(session, gestionnaire):
    enregistrer_jeton(creer_jeton(gestionnaire))
    supprimer_jeton()
    with pytest.raises(AuthentificationError):
        collaborateur_connecte(session)


def test_un_jeton_expire_est_refuse_et_efface(session, gestionnaire, monkeypatch):
    monkeypatch.setattr(auth, "DUREE_JETON", timedelta(seconds=-1))
    enregistrer_jeton(creer_jeton(gestionnaire))
    with pytest.raises(AuthentificationError, match="expirée"):
        collaborateur_connecte(session)
    assert not auth.FICHIER_JETON.exists()


def test_un_jeton_signe_avec_un_autre_secret_est_refuse(session, gestionnaire):
    faux_jeton = jwt.encode(
        {"sub": str(gestionnaire.id)},
        "un-autre-secret-qui-n-est-pas-le-bon-0123456789",
        algorithm="HS256",
    )
    enregistrer_jeton(faux_jeton)
    with pytest.raises(AuthentificationError, match="invalide"):
        collaborateur_connecte(session)


def test_un_compte_supprime_perd_l_acces_immediatement(session, gestionnaire):
    enregistrer_jeton(creer_jeton(gestionnaire))
    session.delete(gestionnaire)
    session.commit()
    with pytest.raises(AuthentificationError, match="introuvable"):
        collaborateur_connecte(session)
