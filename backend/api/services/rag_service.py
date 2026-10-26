"""Service de Retrieval-Augmented Generation (RAG) avec ChromaDB et Gemini."""

import os
from pathlib import Path
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions

class RAGService:
    def __init__(self, persist_directory: str | None = None):
        if persist_directory is None:
            backend_root = Path(__file__).resolve().parents[2]
            persist_directory = str(backend_root / "chroma_db")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Chroma's default sentence-transformers model to bypass Gemini API limits immediately
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection pour la loi financiere tunisienne
        self.finance_collection = self.client.get_or_create_collection(
            name="finance_docs",
            embedding_function=self.embedding_function
        )

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Ajouter des documents a la base de connaissances finance."""
        if hasattr(self.finance_collection, "upsert"):
            self.finance_collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        else:
            self.finance_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def reset_finance_collection(self):
        """Reset the finance collection for a full re-ingest."""
        try:
            self.client.delete_collection(name="finance_docs")
        except Exception:
            pass
        self.finance_collection = self.client.get_or_create_collection(
            name="finance_docs",
            embedding_function=self.embedding_function
        )
        
    def search(self, query: str, n_results: int = 3) -> list[dict]:
        """Rechercher les documents les plus pertinents pour la requete."""
        try:
            results = self.finance_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            extracted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for idx, doc in enumerate(results['documents'][0]):
                    extracted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][idx] if results['metadatas'] else {},
                        'score': results['distances'][0][idx] if 'distances' in results and results['distances'] else 0
                    })
            return extracted_results
        except Exception as e:
            print(f"Erreur de recherche RAG: {e}")
            return []

rag_service = RAGService()
