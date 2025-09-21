import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
envpath = find_dotenv()
load_dotenv(envpath)

# API Configuration
MODEL_NAME = os.getenv('MODEL_NAME', '')

# Search Configuration
TOP_N_RESULTS = int(os.getenv('TOP_N_RESULTS', 10))
DATA_PATH = os.getenv('DATA_PATH', 'data/rag_chunks.json')

# Vector Database Configuration
VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', 'data/rag_vector_db.faiss')

# Search Method Configuration
DEFAULT_SEARCH_METHOD = os.getenv('DEFAULT_SEARCH_METHOD', 'hybrid')

# Hybrid Search Configuration
TFIDF_WEIGHT = float(os.getenv('TFIDF_WEIGHT', 0.3))
BM25_WEIGHT = float(os.getenv('BM25_WEIGHT', 0.3))
EMBEDDING_WEIGHT = float(os.getenv('EMBEDDING_WEIGHT', 0.4))
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'jinaai/jina-embeddings-v3')

# Flask Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')  


# Common LLM Settings
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 2048))

MAX_CONVERSATION_LENGTH = 20  # Maximum number of messages to keep in history
CONVERSATION_EXPIRY_TIME = 3600  # Conversation expires after 1 hour of inactivity (in seconds)