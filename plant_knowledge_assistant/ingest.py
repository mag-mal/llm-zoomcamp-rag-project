import os
import pandas as pd
from qdrant_client import QdrantClient, models

COLLECTION_NAME = "rag-project-sparse-and-dense"
DATA_PATH = os.getenv("DATA_PATH", "../data/plants_data.csv")
QDRANT_URL = os.getenv('QDRANT_URL')
# Qdrant client

def get_client(url: str = QDRANT_URL) -> QdrantClient:
    """Initialize and return a Qdrant client."""
    #url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url)

def load_data(path: str = DATA_PATH) -> list[dict]:
    """CSV -> list[dict]."""
    return pd.read_csv(path).to_dict(orient='records')


def recreate_collection(client: QdrantClient) -> None:
    """(Re)create collection with dense + sparse configs."""
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "jina-small": models.VectorParams(
                size=512,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            )
        }
    )
    print("collection created")

def upsert_points(client: QdrantClient, docs: list[dict]) -> None:
    """Build points from docs and upsert them into the collection."""

    points = []

    for i, doc in enumerate(docs):
        
        text = " ".join(str(doc.get(field, "")) for field in ["name", "summary", "cultivation", "toxicity"])

        vector = {
            "jina-small": models.Document(
                text=text,
                model="jinaai/jina-embeddings-v2-small-en",
            ),
            "bm25": models.Document(
                text=text, 
                model="Qdrant/bm25",
            ),
        }
        
        points.append(
            models.PointStruct(
            id=i,
            vector=vector,
            payload=doc
            )
        )


    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

def main(path: str = DATA_PATH) -> QdrantClient:
    """Main entry: load CSV into Qdrant with embeddings."""
    client = get_client()
    documents = load_data(path)
    recreate_collection(client)
    upsert_points(client, documents)
    return client