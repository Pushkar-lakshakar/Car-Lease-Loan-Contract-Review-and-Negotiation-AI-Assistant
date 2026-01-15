from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import json

from ocr_engine import run_ocr
from gemini import extract_sla_from_text
from risk_analysis import analyze_contract

app = FastAPI(title="Car Lease SLA + Risk Analysis API")


# ENDPOINT: Upload PDF → OCR → Gemini → SLA JSON → Risk Analysis
@app.post("/extract-sla")
async def extract_sla(file: UploadFile = File(...)):
    """
    Pipeline:
    1. Save PDF
    2. OCR to text
    3. Gemini → SLA JSON only
    4. Risk Analysis → fairness + red flags
    5. Combine & return
    """

    # 1. Save PDF
    pdf_path = file.filename
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # 2. OCR → TXT
    txt_path = run_ocr(pdf_path)

    with open(txt_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    # 3. Extract SLA using Gemini
    sla_json = extract_sla_from_text(ocr_text)

    # 4. Risk analysis (no LLM)
    risk_result = analyze_contract(sla_json)

    # 5. Combine outputs
    final_output = {
        "sla_fields": sla_json,
        "contract_fairness_score": risk_result["contract_fairness_score"],
        "red_flag_clauses": risk_result["red_flag_clauses"],
        "fairness_breakdown": risk_result["fairness_breakdown"]
    }

    # 6. Save result JSON
    json_path = pdf_path.replace(".pdf", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    return JSONResponse(content=final_output)
