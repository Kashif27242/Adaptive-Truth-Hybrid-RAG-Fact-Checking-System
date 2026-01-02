import os
import json
import requests
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "fever.jsonl")
URL = "https://fever.ai/download/fever/shared_task_dev.jsonl"
CHROMA_DB_PATH = "chroma_db"
COLLECTION_NAME = "fever-facts"

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
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Use accurate embedding model
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Get or create collection
    try:
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
        print(f"Collection '{COLLECTION_NAME}' already exists. Appending strictly new data is tricky without ID checks. For now, we assume clean slate or overwrite logic if needed.")
        # Optional: client.delete_collection(COLLECTION_NAME) to start fresh
    except:
        print(f"Creating collection '{COLLECTION_NAME}'...")
        collection = client.create_collection(name=COLLECTION_NAME, embedding_function=ef)

    print(f"Processing {DATA_FILE}...")
    
    batch_size = 500 # ChromaDB handles batches well
    documents = []
    metadatas = []
    ids = []
    
    count = 0
    total_processed = 0
    
    # Count total lines for progress bar (optional, but good for UX)
    # total_lines = sum(1 for _ in open(DATA_FILE, 'r', encoding='utf-8')) 
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Ingesting facts"):
            try:
                data = json.loads(line)
                # Only store SUPPORTED claims as "facts"
                if data['label'] == 'SUPPORTS':
                    documents.append(data['claim'])
                    metadatas.append({"source": "FEVER", "label": data['label'], "text": data['claim']})
                    ids.append(str(data['id']))
                    count += 1
                    
                    if count >= batch_size:
                        collection.upsert(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        total_processed += count
                        documents = []
                        metadatas = []
                        ids = []
                        count = 0
            except Exception as e:
                pass # Skip malformed lines

    # Upsert remaining
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        total_processed += count

    print(f"Ingestion complete! Total facts stored: {total_processed}")

if __name__ == "__main__":
    ingest_data()
