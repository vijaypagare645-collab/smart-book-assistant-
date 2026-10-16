
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book
from app.services.pdf_reader import extract_pdf_text

router = APIRouter(prefix="/api/books", tags=["Books"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


@router.post("/upload")
def upload_book(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(400, "Please upload a PDF file.")

    content = file.file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            413, f"PDF must be smaller than {MAX_UPLOAD_MB} MB."
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "The uploaded file is not a valid PDF.")

    try:
        extracted_text, page_count = extract_pdf_text(content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, "Could not read this PDF.") from exc
    finally:
        file.file.close()

    # Keep the original filename out of the storage path.
    stored_name = f"{uuid.uuid4().hex}.pdf"
    stored_path = UPLOAD_DIR / stored_name

    # Use a longer MySQL text type for book content.
    try:
        stored_path.write_bytes(content)

        book = Book(
            title=Path(file.filename).stem[:255],
            filename=file.filename[:255],
            file_path=str(stored_path),
            extracted_text=extracted_text,
        )

        db.add(book)
        db.commit()
        db.refresh(book)

    except Exception as exc:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            500, "Could not save the book. Check the database configuration."
        ) from exc

    return {
        "message": "PDF uploaded successfully.",
        "book_id": book.id,
        "title": book.title,
        "page_count": page_count,
        "character_count": len(extracted_text),
        "preview": extracted_text[:1500],
    }


@router.get("")
def list_books(db: Session = Depends(get_db)):
    books = db.query(Book).order_by(Book.id.desc()).all()

    return [
        {
            "id": book.id,
            "title": book.title,
            "filename": book.filename,
            "created_at": book.created_at.isoformat()
            if book.created_at else None,
        }
        for book in books
    ]
