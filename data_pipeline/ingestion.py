import argparse
import sys
import os
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
import certifi

# Adjust path so we can import config/database modules relative to root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from database.mongo import mongo_handler
from data_pipeline.loaders import get_loader

def ingest_data(source_type: str, url: str):
    """
    Ingests data, splits it, tags it, and pushes to MongoDB Vector Search.
    """
    print(f"[INFO] Starting ingestion for type='{source_type}' from '{url}'...")

    # 1. Load Data
    try:
        loader = get_loader(source_type)
        documents = loader.load(url)
        print(f"[INFO] Loaded {len(documents)} document(s).")
    except Exception as e:
        print(f"[ERROR] Error loading data: {e}")
        return

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[INFO] Split into {len(chunks)} chunks.")

    # 3. Add Metadata
    for chunk in chunks:
        chunk.metadata["source_type"] = source_type
        # Ensure we have a valid source field
        chunk.metadata["source"] = url

    # 4. Embed & Store
    # Initialize Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY
    )

    # Initialize Vector Store
    # We reuse the mongo_handler connection details
    vector_store = MongoDBAtlasVectorSearch(
        collection=mongo_handler.get_collection(),
        embedding=embeddings,
        index_name=settings.INDEX_NAME,
        relevance_score_fn=settings.VECTOR_SEARCH_METRIC
    )

    try:
        vector_store.add_documents(chunks)
        print("[SUCCESS] Data successfully ingested into MongoDB!")
    except Exception as e:
        print(f"[ERROR] Error storing chunks: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexus AI Data Ingestion CLI")
    parser.add_argument("--type", required=True, choices=["resume", "video", "web"], help="Type of data source")
    parser.add_argument("--url", required=True, help="URL or File Path")

    args = parser.parse_args()
    
    # Ensure Mongo Index is ready (prints schema if not)
    mongo_handler.init_search_index()

    ingest_data(args.type, args.url)
