import os
import pytesseract
from pdf2image import convert_from_path

# =========================
# CONFIGURATION (WINDOWS)
# =========================

# Path to Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Path to Poppler binaries
POPPLER_PATH = r"C:\poppler\Library\bin"

# =========================
# INPUT PDF
# =========================

pdfPath = "Car Lease Agreement.pdf"  # Put your PDF name here

# =========================
# OUTPUT FILE (same name)
# =========================

baseName = os.path.splitext(pdfPath)[0]
outputTxt = baseName + ".txt"

# =========================
# OCR PROCESS
# =========================

try:
    pages = convert_from_path(
        pdfPath,
        dpi=300,
        poppler_path=POPPLER_PATH
    )

    with open(outputTxt, "w", encoding="utf-8") as file:
        for i, page in enumerate(pages, start=1):
            text = pytesseract.image_to_string(page, lang="eng")
            file.write(f"\n--- Page {i} ---\n")
            file.write(text)

    print(f"OCR completed successfully.")
    print(f"Text saved to: {outputTxt}")

except FileNotFoundError:
    print("ERROR: input PDF file not found.")
    print("Make sure the PDF is in the same folder as this script.")

except Exception as e:
    print("OCR failed.")
    print("Reason:", e)
