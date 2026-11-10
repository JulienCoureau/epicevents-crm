"""Vérifie les droits"""

from sqlalchemy.orm import Session

from crm.models import Client, Collaborateur, Contrat, Evenement
from crm.permissions import Action, verifier
from crm.repositories import (
    ClientRepository,
    ContratRepository,
    EvenementRepository,
    CollaborateurRepository,
)
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


def _avec_fuseau(moment):
    """Une date relue sans fuseau est considérée à l'heure de Paris."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=validators.FUSEAU)
    return moment


def _verifier_dates(debut, fin) -> None:
    """La fin d'un événement doit être postérieure à son début."""
    if _avec_fuseau(fin) <= _avec_fuseau(debut):
        raise DonneesInvalides(
            "La date de fin doit être postérieure à la date de début."
        )


def contrat_pour_nouvel_evenement(
    session: Session, collaborateur: Collaborateur, contrat_id: int
) -> Contrat:
    """Vérifie qu'un événement peut être créé pour ce contrat."""
    contrat = _obtenir(ContratRepository(session), contrat_id, "contrat")
    verifier(collaborateur, Action.CREER_EVENEMENT, contrat)
    if not contrat.signe:
        raise DonneesInvalides(f"Le contrat n° {contrat.id} n'est pas encore signé.")
    if contrat.evenement is not None:
        raise DonneesInvalides(f"Le contrat n° {contrat.id} a déjà un événement.")
    return contrat


def creer_evenement(
    session: Session,
    collaborateur: Collaborateur,
    contrat_id: int,
    nom: str,
    date_debut: str,
    date_fin: str,
    lieu: str,
    participants,
    notes: str | None = None,
) -> Evenement:
    """Crée l'événement d'un contrat signé ; réservé au commercial du client."""
    contrat = contrat_pour_nouvel_evenement(session, collaborateur, contrat_id)

    nom = validators.texte_obligatoire(nom, "nom", 100)
    debut = validators.date_heure(date_debut, "date de début")
    fin = validators.date_heure(date_fin, "date de fin")
    _verifier_dates(debut, fin)
    lieu = validators.texte_obligatoire(lieu, "lieu", 255)
    participants = validators.nombre_participants(participants)
    notes = validators.texte_facultatif(notes, "notes", 2000)

    evenement = Evenement(
        contrat=contrat,
        nom=nom,
        date_debut=debut,
        date_fin=fin,
        lieu=lieu,
        participants=participants,
        notes=notes,
    )
    EvenementRepository(session).ajouter(evenement)
    session.commit()
    return evenement


def modifier_evenement(
    session: Session,
    collaborateur: Collaborateur,
    evenement_id: int,
    nom: str | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    lieu: str | None = None,
    participants=None,
    notes: str | None = None,
    support_id: int | None = None,
    contrat_id: int | None = None,
) -> Evenement:
    """Modifie les champs fournis (None = inchangé) d'un événement.

    La gestion modifie tous les événements et désigne le support ;
    un support modifie les événements qui lui sont attribués.
    """
    evenement = _obtenir(EvenementRepository(session), evenement_id, "événement")
    verifier(collaborateur, Action.MODIFIER_EVENEMENT, evenement)
    if support_id is not None:
        verifier(collaborateur, Action.ATTRIBUER_SUPPORT)
    if contrat_id is not None:
        # rattache evenement à un autre contrat
        verifier(collaborateur, Action.CREER_CONTRAT)

    changements = {}
    if nom is not None:
        changements["nom"] = validators.texte_obligatoire(nom, "nom", 100)
    if date_debut is not None:
        changements["date_debut"] = validators.date_heure(date_debut, "date de début")
    if date_fin is not None:
        changements["date_fin"] = validators.date_heure(date_fin, "date de fin")
    _verifier_dates(
        changements.get("date_debut", evenement.date_debut),
        changements.get("date_fin", evenement.date_fin),
    )
    if lieu is not None:
        changements["lieu"] = validators.texte_obligatoire(lieu, "lieu", 255)
    if participants is not None:
        changements["participants"] = validators.nombre_participants(participants)
    if notes is not None:
        changements["notes"] = validators.texte_facultatif(notes, "notes", 2000)
    if support_id is not None:
        support = _obtenir(
            CollaborateurRepository(session), support_id, "collaborateur"
        )
        if support.role.nom != "support":
            raise DonneesInvalides(
                f"{support.nom} ne fait pas partie du département support."
            )
        changements["support"] = support
    if contrat_id is not None:
        contrat = _obtenir(ContratRepository(session), contrat_id, "contrat")
        if not contrat.signe:
            raise DonneesInvalides(
                f"Le contrat n° {contrat.id} n'est pas encore signé."
            )
        if contrat.evenement is not None and contrat.evenement is not evenement:
            raise DonneesInvalides(f"Le contrat n° {contrat.id} a déjà un événement.")
        changements["contrat"] = contrat

    for champ, valeur in changements.items():
        setattr(evenement, champ, valeur)
    session.commit()
    return evenement
