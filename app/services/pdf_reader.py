
import fitz


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF bytes and return (text, page_count)."""

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported yet.")

        pages = []
        for page in document:
            pages.append(page.get_text("text"))

        text = "\n\n".join(pages).strip()

        if not text:
            raise ValueError(
                "No selectable text found. This may be a scanned PDF."
            )

        return text, len(document)
