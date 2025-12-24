import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import OperationFailure
from config import settings
import json

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.DB_NAME]
        self.collection: Collection = self.db[settings.COLLECTION_NAME]

    def init_search_index(self):
        """
        Checks if the Vector Search Index exists. 
        If not, prints the JSON Schema for manual creation.
        """
        print(f"Checking for index '{settings.INDEX_NAME}' in collection '{settings.COLLECTION_NAME}'...")
        
        try:
            indexes = list(self.collection.list_search_indexes())
            index_names = [idx['name'] for idx in indexes]
            
            if settings.INDEX_NAME in index_names:
                print(f"[OK] Index '{settings.INDEX_NAME}' already exists.")
                return
            else:
                self._print_index_schema()
                
        except OperationFailure as e:
            print(f"[!] Could not list indexes (check permissions): {e}")
            self._print_index_schema()
        except Exception as e:
            print(f"[!] An error occurred while checking indexes: {e}")
            self._print_index_schema()

    def _print_index_schema(self):
        schema = {
            "mappings": {
                "dynamic": True,
                "fields": {
                    "embedding": {
                        "dimensions": settings.VECTOR_SEARCH_DIMENSIONS,
                        "similarity": settings.VECTOR_SEARCH_METRIC,
                        "type": "knnVector"
                    },
                    "source_type": {
                        "type": "token"
                    }
                }
            }
        }
        
        print("\n[X] Vector Search Index not found or could not be verified.")
        print(f"Please create it manually in MongoDB Atlas.")
        print(f"1. Name the index: {settings.INDEX_NAME}")
        print("2. Paste this into the JSON Editor:")
        print(json.dumps(schema, indent=4))
        print("\nNote: The 'embedding' field must be mapped as type 'knnVector'.")

    def get_collection(self):
        return self.collection

# Initialize global handler if needed, or allow instantiation
mongo_handler = MongoDBHandler()
