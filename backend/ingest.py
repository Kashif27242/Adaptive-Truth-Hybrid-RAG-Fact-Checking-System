import chromadb
from chromadb.utils import embedding_functions
import requests
import json
import os

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "fever.jsonl")
URL = "https://fever.ai/download/fever/shared_task_dev.jsonl"

def download_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if os.path.exists(DATA_FILE):
        print(f"Dataset already exists at {DATA_FILE}")
        return

    print(f"Downloading dataset from {URL}...")
    response = requests.get(URL, stream=True)
    
    with open(DATA_FILE, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete.")

def ingest_data():
    download_data()

    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Use a standard embedding model
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.get_or_create_collection(name="fever_facts", embedding_function=sentence_transformer_ef)
    
    documents = []
    metadatas = []
    ids = []
    
    print(f"Processing {DATA_FILE}...")
    count = 0
    print(f"Processing {DATA_FILE}...")
    count = 0
    # Process entire file
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line:
                try:
                    data = json.loads(line)
                    # FEVER labels are SUPPORTS, REFUTES, NOT ENOUGH INFO
                    if data['label'] == 'SUPPORTS':
                        documents.append(data['claim'])
                        metadatas.append({"source": "FEVER", "label": data['label']})
                        ids.append(str(data['id']))
                        count += 1
                        
                        if count % 1000 == 0:
                            print(f"Processed {count} supported claims...")
                except Exception as e:
                    pass

    if documents:
        print(f"Adding {len(documents)} documents to ChromaDB...")
        # Upsert in batches to avoid payload limits
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            collection.upsert(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
            if i % 1000 == 0:
                print(f"Upserted batch {i} to {i+batch_size}")
            
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
