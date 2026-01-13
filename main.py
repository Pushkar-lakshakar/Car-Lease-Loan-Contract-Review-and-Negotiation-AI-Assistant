from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import json

from ocr_engine import run_ocr
from gemini import extract_sla_from_text

app = FastAPI(title="Car Lease SLA Extraction API (Auto-run)")


#ENDPOINT: Upload PDF → OCR → Gemini → SLA JSON
@app.post("/extract-sla")
async def extract_sla(file: UploadFile = File(...)):
    """
    Upload a PDF, and this endpoint will:
    1. Save the PDF
    2. Run OCR to extract text
    3. Run Gemini to extract SLA JSON
    4. Return the final JSON
    """

    # 1. Save the uploaded PDF
    pdf_path = file.filename
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # 2. OCR → TXT
    txt_path = run_ocr(pdf_path)

    with open(txt_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    # 3. LLM → SLA JSON
    sla_json = extract_sla_from_text(ocr_text)

    # 4. Save JSON next to PDF
    json_path = pdf_path.replace(".pdf", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sla_json, f, indent=4)

    return JSONResponse(content=sla_json)
