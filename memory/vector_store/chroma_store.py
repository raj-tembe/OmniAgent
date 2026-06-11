import os
import logging
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from memory.vector_store.embeddings import (
    embedding_manager
)
from config import CHROMA_DB_PATH


# chroma vector store

class ChromaMemoryStore:
    """
    ChromaDB-based vector memory system.

    Responsibilities:
    - persistent vector storage
    - semantic similarity search
    - long-term memory retrieval
    - autonomous contextual recall
    """

    def __init__(
        self,
        collection_name: str = "omniagent_memory"
    ):

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(
                anonymized_telemetry=False
            )
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name
            )
        )


    # add memory 

    def add_memory(
        self,
        memory_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Store memory embedding in ChromaDB.
        """

        try:

            embedding = (
                embedding_manager.embed_text(text)
            )

            self.collection.add(

                ids=[memory_id],

                documents=[text],

                embeddings=[embedding],

                metadatas=[metadata or {}]
            )

            return {

                "success": True,

                "memory_id": memory_id
            }

        except Exception as e:
            logging.getLogger(__name__).error("ChromaMemoryStore.store_memory failed: %s", e, exc_info=True)

            return {

                "success": False,

                "error": str(e)
            }


    # search memories

    def search_memories(
        self,
        query: str,
        limit: int = 5
    ) -> Dict:
        """
        Semantic similarity search.
        """

        try:

            query_embedding = (
                embedding_manager.embed_text(
                    query
                )
            )

            results = self.collection.query(

                query_embeddings=[
                    query_embedding
                ],

                n_results=limit
            )

            return {

                "success": True,

                "query": query,

                "results": results
            }

        except Exception as e:
            logging.getLogger(__name__).error("ChromaMemoryStore.search_memories failed: %s", e, exc_info=True)

            return {

                "success": False,

                "query": query,

                "error": str(e),

                "results": []
            }


    # get memory 

    def get_memory(
        self,
        memory_id: str
    ) -> Dict:
        """
        Retrieve memory by ID.
        """

        try:

            result = self.collection.get(
                ids=[memory_id]
            )

            return {

                "success": True,

                "memory": result
            }

        except Exception as e:
            logging.getLogger(__name__).error("ChromaMemoryStore.get_memory failed: %s", e, exc_info=True)

            return {

                "success": False,

                "error": str(e)
            }


    # delete memory

    def delete_memory(
        self,
        memory_id: str
    ) -> Dict:
        """
        Delete memory from vector store.
        """

        try:

            self.collection.delete(
                ids=[memory_id]
            )

            return {

                "success": True,

                "deleted_memory_id": memory_id
            }

        except Exception as e:
            logging.getLogger(__name__).error("ChromaMemoryStore.delete_memory failed: %s", e, exc_info=True)

            return {

                "success": False,

                "error": str(e)
            }


    # memory count

    def count_memories(self) -> int:
        """
        Total stored memory count.
        """

        return self.collection.count()


    # reset collection

    def reset_collection(self) -> Dict:
        """
        Clear all stored memories.
        """

        try:

            self.client.delete_collection(
                self.collection.name
            )

            self.collection = (
                self.client.get_or_create_collection(
                    name=self.collection.name
                )
            )

            return {

                "success": True
            }

        except Exception as e:
            logging.getLogger(__name__).error("ChromaMemoryStore.clear_all_memories failed: %s", e, exc_info=True)

            return {

                "success": False,

                "error": str(e)
            }


# global vector store

vector_store = ChromaMemoryStore()