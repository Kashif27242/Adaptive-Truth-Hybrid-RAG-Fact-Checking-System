import chromadb
from chromadb.utils import embedding_functions

def check_count():
    client = chromadb.PersistentClient(path="./chroma_db")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_collection(name="fever_facts", embedding_function=sentence_transformer_ef)
    print(f"Total documents in collection: {collection.count()}")

if __name__ == "__main__":
    check_count()
