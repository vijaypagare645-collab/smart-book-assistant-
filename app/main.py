
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pypdf import PdfReader

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(APP_DIR / "static").mkdir(parents=True, exist_ok=True)
(APP_DIR / "templates").mkdir(parents=True, exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

MAX_SIZE = 10 * 1024 * 1024  # 10 MB

context = {
    "filename": "",
    "content_type": "",
    "file_size": 0,
    "error": "",
    "addbook": False,
    "yourbooks": False,
    "folder": [],
    "pages": [],
}


def get_books():
    return sorted(UPLOAD_DIR.glob("*.pdf"))


def render_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )


@app.get("/")
def home(request: Request):
    context["folder"] = [
        str(book.relative_to(BASE_DIR)).replace("\\", "/")
        for book in get_books()
    ]
    return render_page(request)


@app.post("/addbook")
def add_book():
    context["addbook"] = not context["addbook"]
    context["error"] = ""
    return RedirectResponse("/", status_code=303)


@app.post("/yourbooks")
def your_books():
    context["yourbooks"] = not context["yourbooks"]
    context["error"] = ""
    return RedirectResponse("/", status_code=303)


@app.post("/upload")
async def upload_file(myfile: UploadFile = File(...)):
    try:
        if not myfile.filename:
            context["error"] = "Please select a file."
            return RedirectResponse("/", status_code=303)

        # Restrict uploads to PDF files.
        if Path(myfile.filename).suffix.lower() != ".pdf":
            context["error"] = "Please upload a PDF file."
            return RedirectResponse("/", status_code=303)

        data = await myfile.read(MAX_SIZE + 1)

        if len(data) > MAX_SIZE:
            context["error"] = "File must be 10 MB or smaller."
            return RedirectResponse("/", status_code=303)

        # Avoid using a user-supplied path as the save path.
        safe_name = Path(myfile.filename).name
        file_path = UPLOAD_DIR / safe_name

        # Validate that the file is a readable PDF.
        try:
            import io
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                context["error"] = "Password-protected PDFs are not supported."
                return RedirectResponse("/", status_code=303)
            _ = len(reader.pages)
        except Exception:
            context["error"] = "The selected file is not a valid readable PDF."
            return RedirectResponse("/", status_code=303)

        # Save the uploaded PDF.
        file_path.write_bytes(data)

        # Display the uploaded book immediately.
        reader = PdfReader(str(file_path))
        context.update({
            "filename": safe_name,
            "content_type": myfile.content_type or "application/pdf",
            "file_size": len(data),
            "error": "",
            "addbook": False,
            "pages": [
                page.extract_text() or ""
                for page in reader.pages
            ],
        })

        return RedirectResponse("/", status_code=303)

    except OSError:
        context["error"] = "Unable to save the PDF. Check the uploads folder."
        return RedirectResponse("/", status_code=303)

    finally:
        await myfile.close()


@app.post("/content")
def open_book(book: str = Form(...)):
    try:
        # Accept only PDF files from the uploads directory.
        requested = Path(book)

        if requested.is_absolute() or ".." in requested.parts:
            context["error"] = "Invalid book path."
            return RedirectResponse("/", status_code=303)

        file_path = (BASE_DIR / requested).resolve()

        if file_path.parent != UPLOAD_DIR.resolve():
            context["error"] = "Invalid book path."
            return RedirectResponse("/", status_code=303)

        if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
            context["error"] = "Book not found."
            return RedirectResponse("/", status_code=303)

        reader = PdfReader(str(file_path))

        if reader.is_encrypted:
            context["error"] = "Password-protected PDFs are not supported."
            return RedirectResponse("/", status_code=303)

        context.update({
            "filename": file_path.name,
            "content_type": "application/pdf",
            "file_size": file_path.stat().st_size,
            "pages": [
                page.extract_text() or ""
                for page in reader.pages
            ],
            "error": "",
        })

    except Exception:
        context["error"] = "Unable to read this PDF file."

    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
