"""Point d'entrée (ligne de commande)"""

from contextlib import contextmanager

import click

from crm import services, views
from crm.auth import (
    AuthentificationError,
    authentifier,
    collaborateur_connecte,
    creer_jeton,
    enregistrer_jeton,
    supprimer_jeton,
)
from crm.database import SessionLocal
from crm.exceptions import ErreurMetier
from crm.permissions import Action, verifier, verifier_role


@contextmanager
def session_authentifiee():
    """Ouvre une session et fournit le collaborateur connecté."""
    with SessionLocal() as session:
        try:
            yield session, collaborateur_connecte(session)
        except ErreurMetier as erreur:
            raise click.ClickException(str(erreur)) from None


@click.group()
def cli() -> None:
    """Clients, contrats et événements."""


@cli.command()
@click.option("--email", prompt="Email")
def login(email: str) -> None:
    """Se connecter et ouvrir une session."""
    supprimer_jeton()
    mot_de_passe = click.prompt("Mot de passe", hide_input=True)
    with SessionLocal() as session:
        try:
            collaborateur = authentifier(session, email, mot_de_passe)
        except AuthentificationError as erreur:
            raise click.ClickException(str(erreur)) from None
        enregistrer_jeton(creer_jeton(collaborateur))
        click.echo(f"Connecté : {collaborateur.nom} ({collaborateur.role.nom}).")


@cli.command()
def whoami() -> None:
    """Afficher l'utilisateur connecté."""
    with session_authentifiee() as (session, collaborateur):
        click.echo(f"{collaborateur.nom} ({collaborateur.role.nom})")


@cli.command()
def logout() -> None:
    """Fermer la session."""
    supprimer_jeton()
    click.echo("Déconnecté.")


@cli.group()
def clients() -> None:
    """Gérer les clients."""


@clients.command("list")
def clients_list() -> None:
    """Afficher tous les clients."""
    with session_authentifiee() as (session, collaborateur):
        views.afficher_clients(services.lister_clients(session, collaborateur))


@clients.command("create")
def clients_create() -> None:
    """Créer un client."""
    with session_authentifiee() as (session, collaborateur):
        verifier(collaborateur, Action.CREER_CLIENT)
        client = services.creer_client(
            session,
            collaborateur,
            nom_complet=click.prompt("Nom complet"),
            email=click.prompt("Email"),
            telephone=click.prompt("Téléphone", default="", show_default=False),
            entreprise=click.prompt("Entreprise", default="", show_default=False),
        )
        click.echo(f"Client créé : {client.nom_complet} (n° {client.id}).")


@clients.command("update")
@click.argument("client_id", type=int)
@click.option("--nom", help="Nouveau nom complet.")
@click.option("--email", help="Nouvel email.")
@click.option("--telephone", help='Nouveau téléphone ("" pour l\'effacer).')
@click.option("--entreprise", help='Nouvelle entreprise ("" pour l\'effacer).')
def clients_update(client_id, nom, email, telephone, entreprise) -> None:
    """Modifier un de vos clients : seules les options fournies changent."""
    with session_authentifiee() as (session, collaborateur):
        client = services.modifier_client(
            session,
            collaborateur,
            client_id,
            nom_complet=nom,
            email=email,
            telephone=telephone,
            entreprise=entreprise,
        )
        click.echo(f"Client n° {client.id} mis à jour.")


@cli.group()
def contrats() -> None:
    """Gérer les contrats."""


@contrats.command("list")
@click.option("--non-signes", is_flag=True, help="Seulement les contrats non signés.")
@click.option("--non-payes", is_flag=True, help="Seulement les contrats non soldés.")
def contrats_list(non_signes: bool, non_payes: bool) -> None:
    """Afficher les contrats."""
    with session_authentifiee() as (session, collaborateur):
        views.afficher_contrats(
            services.lister_contrats(session, collaborateur, non_signes, non_payes)
        )


@contrats.command("create")
def contrats_create() -> None:
    """Créer un contrat non signé pour un client (gestion)."""
    with session_authentifiee() as (session, collaborateur):
        verifier(collaborateur, Action.CREER_CONTRAT)
        contrat = services.creer_contrat(
            session,
            collaborateur,
            client_id=click.prompt("Numéro du client", type=int),
            montant_total=click.prompt("Montant total"),
            montant_restant=click.prompt(
                "Reste à payer (vide = montant total)", default="", show_default=False
            ),
        )
        click.echo(f"Contrat n° {contrat.id} créé pour {contrat.client.nom_complet}.")


@contrats.command("update")
@click.argument("contrat_id", type=int)
@click.option("--montant-total", help="Nouveau montant total.")
@click.option("--montant-restant", help="Nouveau reste à payer.")
@click.option(
    "--client", "client_id", type=int, help="Numéro du nouveau client (gestion)."
)
@click.option(
    "--signe/--non-signe",
    default=None,
    help="Signer, ou annuler la signature (gestion).",
)
def contrats_update(
    contrat_id, montant_total, montant_restant, client_id, signe
) -> None:
    """Modifier un contrat : seules les options fournies changent."""
    with session_authentifiee() as (session, collaborateur):
        contrat = services.modifier_contrat(
            session,
            collaborateur,
            contrat_id,
            montant_total=montant_total,
            montant_restant=montant_restant,
            client_id=client_id,
            signe=signe,
        )
        click.echo(f"Contrat n° {contrat.id} mis à jour.")


@cli.group()
def evenements() -> None:
    """Gérer les événements."""


@evenements.command("list")
@click.option("--sans-support", is_flag=True, help="Seulement ceux sans support.")
@click.option(
    "--mes-evenements", is_flag=True, help="Seulement ceux qui me sont attribués."
)
def evenements_list(sans_support: bool, mes_evenements: bool) -> None:
    """Afficher les événements."""
    with session_authentifiee() as (session, collaborateur):
        views.afficher_evenements(
            services.lister_evenements(
                session, collaborateur, sans_support, mes_evenements
            )
        )


@evenements.command("create")
def evenements_create() -> None:
    """Créer l'événement d'un contrat signé de l'un des clients."""
    with session_authentifiee() as (session, collaborateur):
        verifier_role(collaborateur, Action.CREER_EVENEMENT)
        contrat_id = click.prompt("Numéro du contrat", type=int)
        services.contrat_pour_nouvel_evenement(session, collaborateur, contrat_id)
        evenement = services.creer_evenement(
            session,
            collaborateur,
            contrat_id=contrat_id,
            nom=click.prompt("Nom de l'événement"),
            date_debut=click.prompt("Début (JJ/MM/AAAA HH:MM)"),
            date_fin=click.prompt("Fin (JJ/MM/AAAA HH:MM)"),
            lieu=click.prompt("Lieu"),
            participants=click.prompt("Nombre de participants"),
            notes=click.prompt("Notes", default="", show_default=False),
        )
        click.echo(f"Événement n° {evenement.id} créé : {evenement.nom}.")


@evenements.command("update")
@click.argument("evenement_id", type=int)
@click.option("--nom", help="Nouveau nom.")
@click.option("--debut", help="Nouveau début (JJ/MM/AAAA HH:MM).")
@click.option("--fin", help="Nouvelle fin (JJ/MM/AAAA HH:MM).")
@click.option("--lieu", help="Nouveau lieu.")
@click.option("--participants", help="Nouveau nombre de participants.")
@click.option("--notes", help='Nouvelles notes ("" pour les effacer).')
@click.option(
    "--support", "support_id", type=int, help="Numéro du support à désigner (gestion)."
)
@click.option(
    "--contrat", "contrat_id", type=int, help="Numéro du nouveau contrat (gestion)."
)
def evenements_update(
    evenement_id, nom, debut, fin, lieu, participants, notes, support_id, contrat_id
) -> None:
    """Modifier un événement : seules les options fournies changent."""
    with session_authentifiee() as (session, collaborateur):
        evenement = services.modifier_evenement(
            session,
            collaborateur,
            evenement_id,
            nom=nom,
            date_debut=debut,
            date_fin=fin,
            lieu=lieu,
            participants=participants,
            notes=notes,
            support_id=support_id,
            contrat_id=contrat_id,
        )
        click.echo(f"Événement n° {evenement.id} mis à jour.")


if __name__ == "__main__":
    cli()
