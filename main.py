from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import json

from ocr_engine import run_ocr
from sla_extractor import extract_sla


app = FastAPI(title="Car Lease SLA Extraction API")

@app.post("/extract-sla")
async def extract_sla_api(file: UploadFile = File(...)):
    pdf_path = file.filename
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    txt_path = run_ocr(pdf_path)

    sla_json = extract_sla(txt_path)

    json_path = pdf_path.replace(".pdf", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sla_json, f, indent=4)

    return JSONResponse(content=sla_json)
