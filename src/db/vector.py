"""ChromaDB vector store wrapper for document embeddings."""

import hashlib
import threading
from pathlib import Path
from typing import Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.core.config import settings


class VectorStore:
    """Wrapper for ChromaDB vector store operations."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name

        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "PE-Nexus document embeddings"},
        )

    @property
    def collection(self):
        """Get the ChromaDB collection."""
        return self._collection

    def add_document_chunks(
        self,
        document_id: UUID,
        chunks: list[str],
        metadatas: Optional[list[dict]] = None,
        embeddings: Optional[list[list[float]]] = None,
    ) -> list[str]:
        """
        Add document chunks to the vector store.

        Args:
            document_id: The source document ID
            chunks: List of text chunks to store
            metadatas: Optional metadata for each chunk
            embeddings: Optional pre-computed embeddings

        Returns:
            List of chunk IDs
        """
        if not chunks:
            return []

        # Generate unique IDs for each chunk (using SHA-256 for consistency with rest of codebase)
        chunk_ids = [
            f"{document_id}_{i}_{hashlib.sha256(chunk.encode()).hexdigest()[:8]}"
            for i, chunk in enumerate(chunks)
        ]

        # Prepare metadata with document reference
        if metadatas is None:
            metadatas = [{} for _ in chunks]

        for i, meta in enumerate(metadatas):
            meta["document_id"] = str(document_id)
            meta["chunk_index"] = i

        # Add to collection
        if embeddings:
            self._collection.add(
                ids=chunk_ids,
                documents=chunks,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        else:
            # ChromaDB will generate embeddings automatically
            self._collection.add(
                ids=chunk_ids,
                documents=chunks,
                metadatas=metadatas,
            )

        return chunk_ids

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> dict:
        """
        Query the vector store for similar documents.

        Args:
            query_text: The query text
            n_results: Maximum number of results to return
            where: Optional metadata filter
            where_document: Optional document content filter

        Returns:
            Query results including documents, distances, and metadata
        """
        results = self._collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def query_by_deal(
        self,
        deal_id: UUID,
        query_text: str,
        n_results: int = 10,
    ) -> dict:
        """Query documents filtered by deal ID."""
        return self.query(
            query_text=query_text,
            n_results=n_results,
            where={"deal_id": str(deal_id)},
        )

    def query_by_document(
        self,
        document_id: UUID,
        query_text: str,
        n_results: int = 10,
    ) -> dict:
        """Query chunks from a specific document."""
        return self.query(
            query_text=query_text,
            n_results=n_results,
            where={"document_id": str(document_id)},
        )

    def get_document_chunks(self, document_id: UUID) -> dict:
        """Get all chunks for a specific document."""
        results = self._collection.get(
            where={"document_id": str(document_id)},
            include=["documents", "metadatas"],
        )

        return {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"],
        }

    def delete_document(self, document_id: UUID) -> None:
        """Delete all chunks for a document."""
        # Get all chunk IDs for this document
        results = self._collection.get(
            where={"document_id": str(document_id)},
        )

        if results["ids"]:
            self._collection.delete(ids=results["ids"])

    def delete_deal_documents(self, deal_id: UUID) -> None:
        """Delete all chunks for all documents in a deal."""
        results = self._collection.get(
            where={"deal_id": str(deal_id)},
        )

        if results["ids"]:
            self._collection.delete(ids=results["ids"])

    def count(self) -> int:
        """Get total number of chunks in the collection."""
        return self._collection.count()

    def reset(self) -> None:
        """Reset the collection (delete all data)."""
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "PE-Nexus document embeddings"},
        )


# Global vector store instance
_vector_store: Optional[VectorStore] = None
_vector_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance (thread-safe)."""
    global _vector_store
    if _vector_store is None:
        with _vector_store_lock:
            # Double-check locking pattern
            if _vector_store is None:
                _vector_store = VectorStore()
    return _vector_store
