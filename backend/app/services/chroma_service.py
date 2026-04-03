import logging

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.config import settings

logger = logging.getLogger(__name__)


class ChromaService:
    """Singleton service for ChromaDB vector store operations."""

    def __init__(self) -> None:
        self._client: chromadb.PersistentClient | None = None
        self._collection = None
        self._embedding_fn: OpenAIEmbeddingFunction | None = None

    def initialize(self) -> None:
        """Create or get the salon_faq collection. Called at application startup."""
        self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._embedding_fn = OpenAIEmbeddingFunction(
            api_key=settings.LLM_API_KEY,
            api_base=settings.LLM_API_BASE,
            model_name=settings.EMBEDDING_MODEL,
        )
        self._collection = self._client.get_or_create_collection(
            name="salon_faq",
            embedding_function=self._embedding_fn,
        )
        logger.info("ChromaDB collection 'salon_faq' initialized.")

    def add_faq(self, faq_id: int, question: str, answer: str, category: str) -> None:
        """Upsert a FAQ document into the collection."""
        self._collection.upsert(
            ids=[str(faq_id)],
            documents=[f"Q: {question}\nA: {answer}"],
            metadatas=[{"category": category, "question": question, "answer": answer}],
        )
        logger.info("FAQ %d upserted into ChromaDB.", faq_id)

    def delete_faq(self, faq_id: int) -> None:
        """Delete a FAQ document from the collection by id."""
        self._collection.delete(ids=[str(faq_id)])
        logger.info("FAQ %d deleted from ChromaDB.", faq_id)

    def query(self, text: str, n_results: int = 3) -> list[dict]:
        """Query the collection and return matching documents with metadata and distance."""
        results = self._collection.query(query_texts=[text], n_results=n_results)
        output: list[dict] = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                output.append(
                    {
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None,
                    }
                )
        return output


chroma_service = ChromaService()
