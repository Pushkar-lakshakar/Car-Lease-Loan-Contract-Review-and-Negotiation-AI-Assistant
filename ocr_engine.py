import pytesseract
from pdf2image import convert_from_path

# Path to Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Path to Poppler
POPPLER_PATH = r"C:\poppler\Library\bin"


def run_ocr(pdf_path: str) -> str:
    """
    Converts a PDF to OCR text and returns the path of the TXT file.
    """

    txt_path = pdf_path.replace(".pdf", ".txt")

    # Convert PDF to Images
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)

    # OCR all pages into text file
    with open(txt_path, "w", encoding="utf-8") as f:
        for page in pages:
            text = pytesseract.image_to_string(page, lang="eng")
            f.write(text + "\n")

    return txt_path
