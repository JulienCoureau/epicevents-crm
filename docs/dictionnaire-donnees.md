# Dictionnaire de données 

## Client

| Attribut             | Type            | Obligatoire | Commentaire                                              |
| -------------------- | --------------- | ----------- | -------------------------------------------------------- |
| identifiant          | entier          | oui         | clé primaire, auto-incrémenté                            |
| nom complet          | texte           | oui         |                                                          |
| email                | texte           | oui         | unique                                                   |
| téléphone            | texte           | non         | texte et non nombre (« +678 123 456 78 »)                |
| nom de l'entreprise  | texte           | non         |                                                          |
| date de création     | date et heure   | oui         | = premier contact                                        |
| dernière mise à jour | date et heure   | oui         | = dernier contact                                        |
| contact commercial   | → Collaborateur | oui         | affecté automatiquement au commercial qui crée le client |

## Contrat

| Attribut                | Type          | Obligatoire | Commentaire                                 |
| ----------------------- | ------------- | ----------- | ------------------------------------------- |
| identifiant             | entier        | oui         | clé primaire, auto-incrémenté               |
| client                  | → Client      | oui         | aucune information du client n'est recopiée |
| montant total           | décimal       | oui         | ≥ 0                                         |
| montant restant à payer | décimal       | oui         | entre 0 et le montant total                 |
| date de création        | date et heure | oui         |                                             |
| statut                  | booléen       | oui         | signé / non signé                           |

## Événement

| Attribut               | Type            | Obligatoire | Commentaire                                        |
| ---------------------- | --------------- | ----------- | -------------------------------------------------- |
| identifiant            | entier          | oui         | clé primaire (« Event ID »)                        |
| nom                    | texte           | oui         | ligne 1 de la feuille Excel                        |
| contrat                | → Contrat       | oui         | « Contract ID »                                    |
| date de début          | date et heure   | oui         |                                                    |
| date de fin            | date et heure   | oui         | postérieure à la date de début                     |
| contact support        | → Collaborateur | non         | vide à la création, affecté ensuite par la gestion |
| lieu                   | texte           | oui         |                                                    |
| nombre de participants | entier          | oui         | ≥ 0                                                |
| notes                  | texte long      | non         |                                                    |

## Collaborateur

| Attribut         | Type   | Obligatoire | Commentaire                            |
| ---------------- | ------ | ----------- | -------------------------------------- |
| identifiant      | entier | oui         | clé primaire technique                 |
| numéro d'employé | texte  | oui         | unique ; identifiant métier            |
| nom              | texte  | oui         |                                        |
| email            | texte  | oui         | unique ; identifiant de connexion      |
| mot de passe     | texte  | oui         | stocké haché et salé, jamais en clair  |
| département      | → Rôle | oui         | jamais une chaîne en dur dans la table |

## Rôle

| Attribut    | Type   | Obligatoire | Commentaire                           |
| ----------- | ------ | ----------- | ------------------------------------- |
| identifiant | entier | oui         | clé primaire                          |
| nom         | texte  | oui         | unique : commercial, support, gestion |

## Associations

| Association                    | Multiplicités                       |
| ------------------------------ | ----------------------------------- |
| Rôle regroupe Collaborateur    | 1 — 0..*                            |
| Collaborateur suit Client      | 1 — 0..*                            |
| Client signe Contrat           | 1 — 0..*                            |
| Contrat donne lieu à Événement | 1 — 0..1 (à valider avec le mentor) |
| Collaborateur gère Événement   | 0..1 — 0..*                         |
