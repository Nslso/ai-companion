from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import os

class GigaChatEmbeddingFunction(EmbeddingFunction):
    def __init__(self, credentials=os.getenv("GIGACHAT_CREDENTIALS"), model=os.getenv("GIGACHAT_EMBEDDINGS_MODEL")):
        super().__init__()
        self.client = GigaChatEmbeddings(credentials=credentials, scope=os.getenv("GIGACHAT_SCOPE"), verify_ssl_certs=False)
        self.model = model
    
    def __call__(self, input: Documents) -> Embeddings:
        try:
            response = self.client.embed_documents(input)
            return response

        except Exception as e:
            raise Exception(f"GigaChat SDK error: {e}")
