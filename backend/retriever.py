import os
from typing import List
from models import Evidence
from serpapi import GoogleSearch

# Mock for now if keys are missing
def search_web(query: str) -> List[Evidence]:
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY") # Or SerpApi key
    if not api_key:
        print("Warning: No Search API Key found. Returning mock data.")
        return [Evidence(text="Mock web evidence for " + query, source="Web", confidence=0.5)]
    
    # Implementation using SerpApi (google-search-results)
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        print(f"DEBUG: Search Results Keys: {results.keys()}")
        if "error" in results:
             print(f"DEBUG: Search API Error: {results['error']}")
        
        evidence_list = []
        if "organic_results" in results:
            for item in results["organic_results"][:3]: # Top 3 results
                evidence_list.append(Evidence(
                    text=item.get("snippet", "No snippet"),
                    source=item.get("source", "Web"),
                    url=item.get("link"),
                    confidence=0.7
                ))
        return evidence_list
    except Exception as e:
        print(f"Search Error: {e}")
        return [Evidence(text=f"Error searching web: {str(e)}", source="System", confidence=0.0)]

import chromadb
from chromadb.utils import embedding_functions

def search_local(query: str) -> List[Evidence]:
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_collection(name="fever_facts", embedding_function=sentence_transformer_ef)
        
        results = collection.query(
            query_texts=[query],
            n_results=2
        )
        
        evidence_list = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                evidence_list.append(Evidence(
                    text=doc,
                    source=f"Local DB ({meta.get('date', 'Unknown')})",
                    confidence=0.9
                ))
        return evidence_list
    except Exception as e:
        print(f"Local Search Error: {e}")
        return []
