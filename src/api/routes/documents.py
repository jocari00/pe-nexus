"""Document management API routes."""

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from src.api.deps import DBSession, EventBusDep, VectorStoreDep
from src.core.config import settings
from src.db.models import DealModel, DocumentModel
from src.schemas.events import EventType

router = APIRouter(prefix="/documents", tags=["documents"])


def get_upload_dir() -> Path:
    """Get the upload directory, creating if needed."""
    upload_dir = settings.base_dir / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


# Maximum file size: 100MB
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024


@router.post("/upload")
async def upload_document(
    deal_id: UUID = Form(...),
    document_type: str = Form(...),
    uploaded_by: str = Form(...),
    file: UploadFile = File(...),
    db: DBSession = None,
    event_bus: EventBusDep = None,
):
    """Upload a document for a deal."""
    # Verify deal exists
    query = select(DealModel).where(DealModel.id == str(deal_id))
    result = await db.execute(query)
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    allowed_extensions = {".pdf", ".xlsx", ".xls", ".csv", ".docx", ".doc"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {allowed_extensions}",
        )

    # Validate file size before reading entire content
    # First check Content-Length header if available
    content_length = file.size
    if content_length and content_length > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
        )

    # Generate document ID and path
    document_id = str(uuid4())
    upload_dir = get_upload_dir() / str(deal_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save with document ID prefix for uniqueness
    safe_filename = f"{document_id[:8]}_{file.filename}"
    file_path = upload_dir / safe_filename

    # Read file content in chunks to validate size
    content = b""
    chunk_size = 1024 * 1024  # 1MB chunks
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content += chunk
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
            )

    checksum = hashlib.sha256(content).hexdigest()
    file_size = len(content)

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine page count for PDFs
    page_count = None
    if file_ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
        except Exception:
            pass

    # Create database record
    db_document = DocumentModel(
        id=document_id,
        deal_id=str(deal_id),
        filename=file.filename,
        document_type=document_type,
        uploaded_at=datetime.now(timezone.utc),
        uploaded_by=uploaded_by,
        file_path=str(file_path),
        file_size_bytes=file_size,
        page_count=page_count,
        checksum=checksum,
        processed=False,
    )

    db.add(db_document)
    await db.commit()

    # Publish event
    await event_bus.publish(
        event_type=EventType.DOCUMENT_UPLOADED,
        deal_id=deal_id,
        document_id=UUID(document_id),
        payload={
            "filename": file.filename,
            "document_type": document_type,
            "file_size": file_size,
            "page_count": page_count,
        },
    )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "document_type": document_type,
        "file_size_bytes": file_size,
        "page_count": page_count,
        "checksum": checksum,
        "message": "Document uploaded successfully",
    }


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    db: DBSession,
):
    """Get document metadata."""
    query = select(DocumentModel).where(DocumentModel.id == str(document_id))
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document.id,
        "deal_id": document.deal_id,
        "filename": document.filename,
        "document_type": document.document_type,
        "uploaded_at": document.uploaded_at.isoformat(),
        "uploaded_by": document.uploaded_by,
        "file_size_bytes": document.file_size_bytes,
        "page_count": document.page_count,
        "checksum": document.checksum,
        "processed": document.processed,
        "extraction_status": document.extraction_status,
    }


@router.get("/deal/{deal_id}")
async def list_deal_documents(
    deal_id: UUID,
    db: DBSession,
):
    """List all documents for a deal."""
    query = (
        select(DocumentModel)
        .where(DocumentModel.deal_id == str(deal_id))
        .order_by(DocumentModel.uploaded_at.desc())
    )
    result = await db.execute(query)
    documents = result.scalars().all()

    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "processed": doc.processed,
            "extraction_status": doc.extraction_status,
        }
        for doc in documents
    ]


@router.post("/{document_id}/process")
async def process_document(
    document_id: UUID,
    db: DBSession,
    event_bus: EventBusDep,
    vector_store: VectorStoreDep,
):
    """Process a document (extract text, create embeddings)."""
    query = select(DocumentModel).where(DocumentModel.id == str(document_id))
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.processed:
        return {
            "document_id": str(document_id),
            "message": "Document already processed",
            "status": document.extraction_status,
        }

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    # Update status
    document.extraction_status = "processing"
    await db.commit()

    try:
        # Process based on file type
        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            from src.agents.forensic import PDFExtractor

            with PDFExtractor(str(file_path)) as extractor:
                # Extract text from all pages
                text_pages = extractor.get_all_text()

                # Create chunks for vector store
                chunks = []
                metadatas = []

                for page in text_pages:
                    # Split page into paragraphs/chunks
                    page_chunks = _split_text(page.text, max_length=1000)
                    for i, chunk in enumerate(page_chunks):
                        chunks.append(chunk)
                        metadatas.append({
                            "deal_id": document.deal_id,
                            "document_id": str(document_id),
                            "page": page.page_number,
                            "chunk_index": i,
                            "document_type": document.document_type,
                        })

                # Add to vector store
                if chunks:
                    vector_store.add_document_chunks(
                        document_id=document_id,
                        chunks=chunks,
                        metadatas=metadatas,
                    )

        # Mark as processed
        document.processed = True
        document.extraction_status = "completed"
        await db.commit()

        # Publish event
        await event_bus.publish(
            event_type=EventType.DOCUMENT_PROCESSED,
            deal_id=UUID(document.deal_id),
            document_id=document_id,
            payload={
                "filename": document.filename,
                "chunks_created": len(chunks) if file_ext == ".pdf" else 0,
            },
        )

        return {
            "document_id": str(document_id),
            "message": "Document processed successfully",
            "status": "completed",
        }

    except Exception as e:
        document.extraction_status = f"failed: {str(e)}"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: DBSession,
    vector_store: VectorStoreDep,
):
    """Delete a document."""
    query = select(DocumentModel).where(DocumentModel.id == str(document_id))
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    vector_store.delete_document(document_id)

    # Delete file
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete database record
    await db.delete(document)
    await db.commit()

    return {"message": f"Document {document_id} deleted"}


def _split_text(text: str, max_length: int = 1000) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_length:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
