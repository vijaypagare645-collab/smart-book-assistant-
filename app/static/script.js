
const uploadForm = document.getElementById("uploadForm");
const pdfFile = document.getElementById("pdfFile");
const statusText = document.getElementById("status");
const preview = document.getElementById("preview");
const bookInfo = document.getElementById("bookInfo");
const bookList = document.getElementById("bookList");

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = pdfFile.files[0];

    if (!file) {
        statusText.textContent = "Please select a PDF first.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    statusText.textContent = "Uploading and extracting text...";

    try {
        const response = await fetch("/api/books/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Upload failed.");
        }

        statusText.textContent = result.message;
        bookInfo.textContent =
            `${result.title} | ${result.page_count} pages | ` +
            `${result.character_count} characters`;

        preview.textContent = result.preview;
        pdfFile.value = "";

        await loadBooks();
    } catch (error) {
        statusText.textContent = `Error: ${error.message}`;
    }
});

async function loadBooks() {
    try {
        const response = await fetch("/api/books");

        if (!response.ok) {
            throw new Error("Could not load books.");
        }

        const books = await response.json();
        bookList.replaceChildren();

        for (const book of books) {
            const item = document.createElement("li");
            item.textContent =
                `${book.title} (Book ID: ${book.id})`;
            bookList.appendChild(item);
        }
    } catch (error) {
        statusText.textContent = error.message;
    }
}

document.getElementById("refreshBooks")
    .addEventListener("click", loadBooks);

loadBooks();