"""
SQL Persistent Vector Store for InsightFlow AI RAG Pipeline.
Stores document chunks and embedding vectors in relational tables (MySQL / SQLite).
Computes exact cosine similarity ranking, supports top-k retrieval, metadata filtering,
and atomic cascade deletion without extra server infrastructure.
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.document import DocumentModel, DocumentChunkModel
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.chunker import DocumentChunk

logger = logging.getLogger("insightflow.rag.vectorstore")


class SqlVectorStore:
    """
    Relational database persistent vector store.
    """

    @classmethod
    def store_document_chunks(
        cls,
        db: Session,
        document_id: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """
        Persists document chunks and their embedding vectors in the database.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)}).")

        chunk_models = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"chk_{uuid.uuid4().hex[:16]}"
            chunk_models.append(
                DocumentChunkModel(
                    id=chunk_id,
                    document_id=document_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    char_count=chunk.char_count,
                    embedding=vector,
                    metadata_json=chunk.metadata,
                )
            )

        db.add_all(chunk_models)
        db.flush()
        return len(chunk_models)

    @classmethod
    def search_similar_chunks(
        cls,
        db: Session,
        query_vector: List[float],
        top_k: int = 4,
        document_ids: Optional[List[str]] = None,
        min_similarity: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most semantically relevant chunks based on cosine similarity.
        Optionally filters by specific document IDs.
        """
        query = (
            db.query(DocumentChunkModel, DocumentModel.filename)
            .join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)
            .filter(DocumentModel.status == "indexed")
        )

        if document_ids:
            query = query.filter(DocumentChunkModel.document_id.in_(document_ids))

        all_candidates = query.all()
        if not all_candidates:
            return []

        scored_chunks: List[Dict[str, Any]] = []

        for chunk_model, filename in all_candidates:
            vector = chunk_model.embedding
            sim = EmbeddingService.cosine_similarity(query_vector, vector)
            if sim >= min_similarity:
                scored_chunks.append({
                    "chunk_id": chunk_model.id,
                    "document_id": chunk_model.document_id,
                    "document_name": filename,
                    "page_number": chunk_model.page_number,
                    "chunk_index": chunk_model.chunk_index,
                    "content": chunk_model.content,
                    "char_count": chunk_model.char_count,
                    "relevance_score": sim,
                    "metadata": chunk_model.metadata_json or {},
                })

        # Rank descending by cosine similarity score
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_chunks[:top_k]

    @classmethod
    def delete_document(cls, db: Session, document_id: str) -> bool:
        """
        Deletes a document and automatically cascade-deletes all associated chunks and vectors.
        """
        doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not doc:
            return False

        # Explicitly clean up all chunks for this document
        db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).delete(synchronize_session=False)
        db.delete(doc)
        db.commit()
        return True


    @classmethod
    def get_stats(cls, db: Session) -> Dict[str, Any]:
        """
        Returns indexed document and chunk counts.
        """
        total_docs = db.query(func.count(DocumentModel.id)).scalar() or 0
        indexed_docs = db.query(func.count(DocumentModel.id)).filter(DocumentModel.status == "indexed").scalar() or 0
        total_chunks = db.query(func.count(DocumentChunkModel.id)).scalar() or 0

        return {
            "total_documents": total_docs,
            "indexed_documents": indexed_docs,
            "total_chunks": total_chunks,
        }
