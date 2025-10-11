from langchain.tools import StructuredTool
from pydantic import BaseModel


# Schema
class SignalerDerangementSchema(BaseModel):
    phone_number: str
    description : str

class DemandeMigrationFibreSchema(BaseModel):
    client_id: str
    address: str

class SuivreConsommationSchema(BaseModel):
    phone_number: str

class ConsulterFactureSchema(BaseModel):
    client_id: str
    month: str = None

class ConsulterAbonnementSchema(BaseModel):
    client_id: str

class ConsulterCompteSchema(BaseModel):
    client_id: str

class CreateAccountSchema(BaseModel):
    name: str
    email: str
    phone: str



# API implementation
def signaler_derangement(phone_number: str, description :str):
    return f"Signalement reçu pour le numéro {phone_number}. Description: {description}"

def demande_migration_fibre(client_id: str, address: str):
    return f"Demande de migration vers fibre enregistrée pour le client {client_id} à l'adresse {address}."

def suivre_consommation(phone_number: str):
    return f"Les consommations téléphoniques pour {phone_number} sont en cours de récupération."

def consulter_facture(client_id: str, month: str = None):
    if month:
        return f"Facture du mois {month} pour le client {client_id}."
    return f"Dernière facture pour le client {client_id}."

def consulter_abonnement(client_id: str):
    return f"Détails de l'abonnement internet du client {client_id}."

def consulter_compte(client_id: str):
    return f"Détails du compte pour le client {client_id}."

def create_account(name: str, email: str, phone: str):
    return f"Compte créé pour {name} ({email}, {phone})"

# Tool definition

api_tools = [
    StructuredTool.from_function(
        func=signaler_derangement,
        name="signaler_derangement",
        description="Signaler un derangement ou une panne sur une ligne téléphonique",
        args_schema=SignalerDerangementSchema,
    ),
    StructuredTool.from_function(
        func=demande_migration_fibre,
        name="demande_migration_fibre",
        description="Demande de migration vers la fibre optique pour un client.",
        args_schema=DemandeMigrationFibreSchema,
    ),
    StructuredTool.from_function(
        func=suivre_consommation,
        name="suivre_consommation",
        description="Suivre les consommations téléphoniques d'un numéro donné.",
        args_schema=SuivreConsommationSchema,
    ),
    StructuredTool.from_function(
        func=consulter_facture,
        name="consulter_facture",
        description="Consulter la facture téléphonique d'un client.",
        args_schema=ConsulterFactureSchema,
    ),
    StructuredTool.from_function(
        func=consulter_abonnement,
        name="consulter_abonnement",
        description="Consulter les détails de l'abonnement internet d'un client.",
        args_schema=ConsulterAbonnementSchema,
    ),
    StructuredTool.from_function(
        func=consulter_compte,
        name="consulter_compte",
        description="Accéder aux détails du compte d'un client.",
        args_schema=ConsulterCompteSchema,
    ),
    
    StructuredTool.from_function(
        func=create_account,
        name="create_account",
        description="Créer un compte client avec nom, email et numéro de téléphone.",
        args_schema=CreateAccountSchema,
    ),
]