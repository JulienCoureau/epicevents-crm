"""Vérifie les droits"""

from sqlalchemy.orm import Session

from crm.models import Client, Collaborateur, Contrat, Evenement
from crm.permissions import Action, verifier
from crm.repositories import ClientRepository, ContratRepository, EvenementRepository
from crm import validators
from crm.exceptions import DonneesInvalides, ObjetIntrouvable


def lister_clients(session: Session, collaborateur: Collaborateur) -> list[Client]:
    """Tous les clients, pour un collaborateur autorisé à lire."""
    verifier(collaborateur, Action.LIRE)
    return ClientRepository(session).lister()


def lister_contrats(
    session: Session,
    collaborateur: Collaborateur,
    non_signes: bool = False,
    non_payes: bool = False,
) -> list[Contrat]:
    """Les contrats, éventuellement filtrés."""
    verifier(collaborateur, Action.LIRE)
    return ContratRepository(session).lister(non_signes, non_payes)


def lister_evenements(
    session: Session,
    collaborateur: Collaborateur,
    sans_support: bool = False,
    mes_evenements: bool = False,
) -> list[Evenement]:
    """Les événements, éventuellement filtrés ; « mes événements » pour le support."""
    verifier(collaborateur, Action.LIRE)
    support_id = collaborateur.id if mes_evenements else None
    return EvenementRepository(session).lister(sans_support, support_id)


def _obtenir(repository, identifiant: int, nom: str):
    """Retourne l'objet demandé, ou lève ObjetIntrouvable."""
    objet = repository.obtenir(identifiant)
    if objet is None:
        raise ObjetIntrouvable(f"Aucun {nom} avec l'identifiant {identifiant}.")
    return objet


def _verifier_email_client_libre(
    repository: ClientRepository, email: str, client: Client | None = None
) -> None:
    """Refuse un email déjà utilisé par un autre client."""
    existant = repository.trouver_par_email(email)
    if existant is not None and existant is not client:
        raise DonneesInvalides(f"Un client utilise déjà l'email « {email} ».")


def creer_client(
    session: Session,
    collaborateur: Collaborateur,
    nom_complet: str,
    email: str,
    telephone: str | None = None,
    entreprise: str | None = None,
) -> Client:
    """Crée un client, automatiquement associé au commercial qui le crée."""
    verifier(collaborateur, Action.CREER_CLIENT)
    repository = ClientRepository(session)

    nom_complet = validators.texte_obligatoire(nom_complet, "nom complet", 100)
    email = validators.email(email)
    telephone = validators.telephone(telephone)
    entreprise = validators.texte_facultatif(entreprise, "entreprise", 100)
    _verifier_email_client_libre(repository, email)

    client = Client(
        nom_complet=nom_complet,
        email=email,
        telephone=telephone,
        entreprise=entreprise,
        commercial=collaborateur,
    )
    repository.ajouter(client)
    session.commit()
    return client


def modifier_client(
    session: Session,
    collaborateur: Collaborateur,
    client_id: int,
    nom_complet: str | None = None,
    email: str | None = None,
    telephone: str | None = None,
    entreprise: str | None = None,
) -> Client:
    """Modifie les champs fournis (None = inchangé) d'un client du commercial."""
    repository = ClientRepository(session)
    client = _obtenir(repository, client_id, "client")
    verifier(collaborateur, Action.MODIFIER_CLIENT, client)

    changements = {}
    if nom_complet is not None:
        changements["nom_complet"] = validators.texte_obligatoire(
            nom_complet, "nom complet", 100
        )
    if email is not None:
        changements["email"] = validators.email(email)
        _verifier_email_client_libre(repository, changements["email"], client)
    if telephone is not None:
        changements["telephone"] = validators.telephone(telephone)
    if entreprise is not None:
        changements["entreprise"] = validators.texte_facultatif(
            entreprise, "entreprise", 100
        )

    for champ, valeur in changements.items():
        setattr(client, champ, valeur)
    session.commit()
    return client


def _verifier_montants(total, restant) -> None:
    """Le reste à payer ne peut pas dépasser le montant total."""
    if restant > total:
        raise DonneesInvalides(
            "Le reste à payer ne peut pas dépasser le montant total."
        )


def creer_contrat(
    session: Session,
    collaborateur: Collaborateur,
    client_id: int,
    montant_total,
    montant_restant=None,
) -> Contrat:
    """Crée un contrat non signé pour un client"""
    verifier(collaborateur, Action.CREER_CONTRAT)
    client = _obtenir(ClientRepository(session), client_id, "client")
    total = validators.montant(montant_total, "montant total")
    if montant_restant in (None, ""):
        restant = total
    else:
        restant = validators.montant(montant_restant, "reste à payer")
    _verifier_montants(total, restant)

    contrat = Contrat(
        client=client, montant_total=total, montant_restant=restant, signe=False
    )
    ContratRepository(session).ajouter(contrat)
    session.commit()
    return contrat


def modifier_contrat(
    session: Session,
    collaborateur: Collaborateur,
    contrat_id: int,
    montant_total=None,
    montant_restant=None,
    client_id: int | None = None,
    signe: bool | None = None,
) -> Contrat:
    """Modifie les champs fournis (None = inchangé) d'un contrat.

    Changer le client ou le statut de signature demande des droits en plus.
    """
    contrat = _obtenir(ContratRepository(session), contrat_id, "contrat")
    verifier(collaborateur, Action.MODIFIER_CONTRAT, contrat)
    if signe is not None and signe != contrat.signe:
        verifier(collaborateur, Action.SIGNER_CONTRAT)
    if client_id is not None:
        # Changer de client revient à réattribuer le contrat :
        # réservé à ceux qui créent les contrats, c'est-à-dire la gestion.
        verifier(collaborateur, Action.CREER_CONTRAT)

    changements = {}
    if montant_total is not None:
        changements["montant_total"] = validators.montant(
            montant_total, "montant total"
        )
    if montant_restant is not None:
        changements["montant_restant"] = validators.montant(
            montant_restant, "reste à payer"
        )
    _verifier_montants(
        changements.get("montant_total", contrat.montant_total),
        changements.get("montant_restant", contrat.montant_restant),
    )
    if client_id is not None:
        changements["client"] = _obtenir(ClientRepository(session), client_id, "client")
    if signe is not None:
        changements["signe"] = signe

    for champ, valeur in changements.items():
        setattr(contrat, champ, valeur)
    session.commit()
    return contrat
