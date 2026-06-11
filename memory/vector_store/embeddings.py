from typing import List, Optional

from langchain_huggingface import HuggingFaceEmbeddings

# Default embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingManager:
    """
    Manages text embeddings using a HuggingFace sentence-transformers model.

    Lazy loads the model on first use to avoid slow startup.
    Supports both single‑text and batch embedding.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        """
        Args:
            model_name: HuggingFace model identifier (default: all-MiniLM-L6-v2).
        """
        self._model_name = model_name
        self._embedding_model: Optional[HuggingFaceEmbeddings] = None

    def _load_model(self) -> HuggingFaceEmbeddings:
        """Initialise the embedding model on first access."""
        if self._embedding_model is None:
            self._embedding_model = HuggingFaceEmbeddings(model_name=self._model_name)
        return self._embedding_model

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text."""
        model = self._load_model()
        return model.embed_query(text)

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of documents."""
        model = self._load_model()
        return model.embed_documents(documents)


# Global convenience instance (model is not loaded until first use)
embedding_manager = EmbeddingManager()