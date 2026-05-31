import os
from typing import List

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)


# embedding config

GOOGLE_API_KEY = os.getenv(
    "GOOGLE_API_KEY"
)

EMBEDDING_MODEL = (
    "gemini-embedding-2-preview"
)


# embedding manager

class EmbeddingManager:
    """
    Embedding generation system.

    Responsibilities:
    - generate vector embeddings
    - support semantic retrieval
    - enable memory similarity search
    """

    def __init__(self):

        self.embedding_model = (
            GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL,
                google_api_key=GOOGLE_API_KEY
            )
        )


    # embed single text

    def embed_text(
        self,
        text: str
    ) -> List[float]:
        """
        Generate embedding for single text.
        """

        return (
            self.embedding_model
            .embed_query(text)
        )


    # embed multiple text

    def embed_documents(
        self,
        documents: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for documents.
        """

        return (
            self.embedding_model
            .embed_documents(documents)
        )


# global embedding instance

embedding_manager = EmbeddingManager()