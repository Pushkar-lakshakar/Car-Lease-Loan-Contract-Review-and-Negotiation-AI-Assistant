import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r"C:\poppler\Library\bin"


def run_ocr(pdf_path: str) -> str:

    # Output file name (same as PDF but .txt)
    txt_path = pdf_path.replace(".pdf", ".txt")

    # Convert PDF to list of image pages
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)

    # Perform OCR on each page
    with open(txt_path, "w", encoding="utf-8") as f:
        for page in pages:
            text = pytesseract.image_to_string(page, lang="eng")
            f.write(text + "\n")

    return txt_path
