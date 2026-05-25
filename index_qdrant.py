import json
from pydoc import text
from xml.parsers.expat import model
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,PointStruct,VectorParams
from sentence_transformers import SentenceTransformer
DATA_FILE = "rust_repos.json"
DB_PATH = "qdrant_db"
COLLECTION_NAME = "rust_repositories"
MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DIMENSION = 384
class QdrantManager:
    def __init__(self, db_path=DB_PATH):
        self.client = QdrantClient(path=db_path)
        self.create_qdrant_collection(self.client)
        self.repos = self.load_repositories()
        self.model = SentenceTransformer(MODEL_NAME)
    def load_repositories(self):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    def sentence_embedding(self, text:str):
        vector = self.model.encode(text).tolist()
        return vector
    def create_qdrant_collection(self, client: QdrantClient):
        if not client.collection_exists(COLLECTION_NAME):
            client.create_collection(
                 collection_name=COLLECTION_NAME,
                 vectors_config=VectorParams(
                     size=VECTOR_DIMENSION,
                       distance=Distance.COSINE,
 ),
    )
        return client
    def create_point(self, repo, vector, point_id):
        return PointStruct(
            id=point_id,
            vector=vector,
             payload={
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"],
                "stars": repo["stars"],
                "forks": repo["forks"],
                "url": repo["url"],
                "language": repo["language"],
        },
        )
    def repo_to_text(self, repo):
        description = repo.get("description") or ""
        return (
        f"Name: {repo.get('name')}\n"
        f"Full name: {repo.get('full_name')}\n"
        f"Description: {description}\n"
        f"Language: {repo.get('language')}\n"
        f"Stars: {repo.get('stars')}\n"
        f"Forks: {repo.get('forks')}"
    )
    def insert_points(self, points):
        self.client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )
    def ensure_indexed(self):
        collection_info = self.client.get_collection(COLLECTION_NAME)
        if collection_info.points_count and collection_info.points_count > 0:
             return
        points = []
        for index, repo in enumerate(self.repos):
            text = self.repo_to_text(repo)
            vector = self.sentence_embedding(text)
            point = self.create_point(repo, vector, index)
            points.append(point)
        
        self.insert_points(points)

    def search_repositories(self, query, top_k=5):
        query_vector = self.sentence_embedding(query)
        search_result = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        )
        return search_result.points
