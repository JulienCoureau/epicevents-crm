# Schéma de la base de données

```mermaid
erDiagram
    role ||--o{ collaborateur : regroupe
    collaborateur ||--o{ client : "commercial de"
    client ||--o{ contrat : signe
    contrat ||--o| evenement : "donne lieu à"
    collaborateur |o--o{ evenement : "support de"

    role {
        int id PK
        string nom UK
    }
    collaborateur {
        int id PK
        string numero_employe UK
        string nom
        string email UK
        string mot_de_passe_hache
        int role_id FK
    }
    client {
        int id PK
        string nom_complet
        string email UK
        string telephone
        string entreprise
        datetime date_creation
        datetime derniere_mise_a_jour
        int commercial_id FK
    }
    contrat {
        int id PK
        int client_id FK
        decimal montant_total
        decimal montant_restant
        datetime date_creation
        boolean signe
    }
    evenement {
        int id PK
        string nom
        int contrat_id FK "unique"
        int support_id FK "nullable"
        datetime date_debut
        datetime date_fin
        string lieu
        int participants
        string notes
    }
```