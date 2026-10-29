"""Tests de la lecture : filtres repositories, droits des services, vues."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from rich.console import Console
from sqlalchemy import select

from crm import services, views
from crm.models import Client, Collaborateur, Contrat, Evenement, Role
from crm.permissions import PermissionRefusee


@pytest.fixture
def donnees(session):
    """jeu de données"""
    roles = {role.nom: role for role in session.scalars(select(Role))}

    def employe(numero, nom, role):
        return Collaborateur(
            numero_employe=numero,
            nom=nom,
            email=f"{numero}@test.fr",
            mot_de_passe_hache="empreinte-factice",
            role=roles[role],
        )

    bill = employe("C1", "Bill", "commercial")
    kate = employe("S1", "Kate", "support")
    john = Client(nom_complet="John Ouick", email="john@test.fr", commercial=bill)
    kevin = Client(nom_complet="Kevin Casey", email="kevin@test.fr", commercial=bill)

    solde = Contrat(
        client=john,
        montant_total=Decimal("100"),
        montant_restant=Decimal("0"),
        signe=True,
    )
    a_moitie_paye = Contrat(
        client=john,
        montant_total=Decimal("100"),
        montant_restant=Decimal("50"),
        signe=True,
    )
    non_signe = Contrat(
        client=kevin,
        montant_total=Decimal("100"),
        montant_restant=Decimal("100"),
        signe=False,
    )

    mariage = Evenement(
        nom="Mariage",
        contrat=solde,
        support=kate,
        date_debut=datetime(2026, 6, 4, 13),
        date_fin=datetime(2026, 6, 5, 2),
        lieu="Candé-sur-Beuvron",
        participants=75,
    )
    assemblee = Evenement(
        nom="Assemblée générale",
        contrat=a_moitie_paye,
        support=None,
        date_debut=datetime(2026, 5, 5, 15),
        date_fin=datetime(2026, 5, 5, 17),
        lieu="Mufflins",
        participants=200,
    )

    session.add_all([mariage, assemblee, non_signe])
    session.commit()
    return SimpleNamespace(
        bill=bill,
        kate=kate,
        solde=solde,
        a_moitie_paye=a_moitie_paye,
        non_signe=non_signe,
        mariage=mariage,
        assemblee=assemblee,
    )


@pytest.fixture
def ecran(monkeypatch):
    """Console qui enregistre ce qui est affiché"""
    console = Console(record=True, width=200)
    monkeypatch.setattr(views, "console", console)
    return console


# Services et repositories


def test_tout_le_monde_lit_tous_les_clients(session, donnees):
    clients = services.lister_clients(session, donnees.kate)
    assert [client.nom_complet for client in clients] == ["John Ouick", "Kevin Casey"]


def test_les_contrats_sans_filtre(session, donnees):
    assert len(services.lister_contrats(session, donnees.bill)) == 3


def test_le_filtre_contrats_non_signes(session, donnees):
    contrats = services.lister_contrats(session, donnees.bill, non_signes=True)
    assert contrats == [donnees.non_signe]


def test_le_filtre_contrats_non_payes(session, donnees):
    contrats = services.lister_contrats(session, donnees.bill, non_payes=True)
    assert set(contrats) == {donnees.a_moitie_paye, donnees.non_signe}


def test_les_deux_filtres_contrats_se_cumulent(session, donnees):
    contrats = services.lister_contrats(
        session, donnees.bill, non_signes=True, non_payes=True
    )
    assert contrats == [donnees.non_signe]


def test_les_evenements_sont_tries_par_date(session, donnees):
    evenements = services.lister_evenements(session, donnees.bill)
    assert evenements == [donnees.assemblee, donnees.mariage]


def test_le_filtre_evenements_sans_support(session, donnees):
    evenements = services.lister_evenements(session, donnees.bill, sans_support=True)
    assert evenements == [donnees.assemblee]


def test_mes_evenements_pour_le_support(session, donnees):
    evenements = services.lister_evenements(session, donnees.kate, mes_evenements=True)
    assert evenements == [donnees.mariage]


def test_mes_evenements_vide_pour_qui_n_en_a_pas(session, donnees):
    assert services.lister_evenements(session, donnees.bill, mes_evenements=True) == []


def test_le_service_verifie_le_droit_de_lecture(session):
    intrus = Collaborateur(id=99, role=Role(nom="stagiaire"))
    with pytest.raises(PermissionRefusee):
        services.lister_clients(session, intrus)


# Vues


def test_la_vue_signale_une_liste_vide(ecran):
    views.afficher_clients([])
    assert "Aucun client." in ecran.export_text()


def test_la_vue_affiche_les_clients_et_leur_commercial(ecran, donnees):
    views.afficher_clients([donnees.mariage.contrat.client])
    texte = ecran.export_text()
    assert "John Ouick" in texte
    assert "Bill" in texte


def test_la_vue_signale_un_evenement_sans_support(ecran, donnees):
    views.afficher_evenements([donnees.assemblee])
    assert "À attribuer" in ecran.export_text()


def test_la_vue_affiche_le_contact_client_depuis_le_client(ecran, donnees):
    views.afficher_evenements([donnees.mariage])
    assert "john@test.fr" in ecran.export_text()
