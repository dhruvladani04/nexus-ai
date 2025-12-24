import os
from dotenv import load_dotenv

load_dotenv()

# Model Configurations
EMBEDDING_MODEL = "models/embedding-001"
LLM_MODEL = "gemini-2.5-flash"

# Vector Search Configuration
VECTOR_SEARCH_DIMENSIONS = 768
VECTOR_SEARCH_METRIC = "cosine"
INDEX_NAME = "default"

# Database Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "nexus_db"
COLLECTION_NAME = "knowledge_base"

# Ingestion Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
