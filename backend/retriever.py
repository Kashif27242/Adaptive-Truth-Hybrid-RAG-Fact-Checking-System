import os
import requests
from typing import List
from models import Evidence

# Mock for now if keys are missing
def search_web(query: str) -> List[Evidence]:
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY") 
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        print("Warning: Missing GOOGLE_SEARCH_API_KEY or GOOGLE_CSE_ID. Returning mock data.")
        return [Evidence(text="Mock web evidence for " + query, source="Web", confidence=0.5)]
    
    # Implementation using Google Custom Search JSON API
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": api_key,
            "cx": cse_id,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        
        evidence_list = []
        if "items" in results:
            for item in results["items"][:3]: # Top 3 results
                evidence_list.append(Evidence(
                    text=item.get("snippet", "No snippet"),
                    source=item.get("displayLink", "Web"), # Use displayLink for source
                    url=item.get("link"),
                    confidence=0.7
                ))
        return evidence_list
    except Exception as e:
        print(f"Search Error: {e}")
        return [Evidence(text=f"Process Error: Could not retrieve web evidence. Details: {str(e)}", source="System Error", confidence=0.0)]

import chromadb
from chromadb.utils import embedding_functions

# Initialize Chroma Client globally
CHROMA_DB_PATH = "chroma_db"
COLLECTION_NAME = "fever-facts"
try:
    _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    _collection = _chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=_embed_fn)
except Exception as e:
    print(f"ChromaDB Init Error: {e}")
    _collection = None

def search_local(query: str) -> List[Evidence]:
    if not _collection:
        return [Evidence(text="Local DB not initialized.", source="System", confidence=0.0)]

    try:
        # ChromaDB handles embedding internally via embedding_function
        results = _collection.query(
            query_texts=[query],
            n_results=2
        )
        
        evidence_list = []
        if results['documents']:
            # Chroma returns lists of lists
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0] # Cosine distance
            
            for i, doc in enumerate(docs):
                # Convert distance to similarity/confidence (approx)
                # Cosine distance: 0 is identical, 1 is opposite. 
                # We want 1.0 = good. 
                confidence = 1 - distances[i] 
                
                evidence_list.append(Evidence(
                    text=doc,
                    source=f"Local (ChromaDB)",
                    confidence=confidence
                ))
            
        return evidence_list
    except Exception as e:
        print(f"ChromaDB Search Error: {e}")
        return [Evidence(text=f"Error accessing Vector DB: {str(e)}", source="System Error", confidence=0.0)]
