import os
import json
from dotenv import load_dotenv
from google import genai

# LOAD API KEY
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("ERROR: GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

PROMPT = """
Extract all SLA-related fields present in this car lease contract.

SLA fields include (but are not limited to):
- Lease Term / Lease Duration
- Start Date and End Date
- Monthly Lease Amount
- Payment Due Date
- Late Fee Amount and Conditions
- Security Deposit and Refund Rules
- Mileage Limit (annual and total)
- Excess Mileage Charge
- Maintenance Responsibilities (minor/major repairs)
- Authorized Repair Shops
- Insurance Requirements (liability, comprehensive, deductible)
- Early Termination Fee
- Renewal Rules
- Purchase Option Price and Conditions
- Any numeric limits, thresholds, deadlines, or penalties

Rules:
- Extract EVERY SLA field you can find.
- Output ONLY valid JSON.
- Each SLA field must be a direct key-value pair:
  {{ "LEASE TERM": "36 months" }}
- Do NOT output arrays unless multiple values exist for the same field.

CONTRACT:
{doc_text}
"""

# JSON extraction helper
def extract_json_block(text: str):
    start = text.find("{")
    if start == -1:
        return None

    stack = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0:
                return text[start:i+1]
    return None

# MAIN FUNCTION
def extract_sla_from_text(ocr_text: str) -> dict:
    prompt = PROMPT.format(doc_text=ocr_text)

    result = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": prompt}]}]
    )

    raw_output = result.text.strip()
    json_text = extract_json_block(raw_output)

    if not json_text:
        return {"error": "No JSON found", "raw_output": raw_output}

    try:
        return json.loads(json_text)

    except Exception as e:
        return {
            "error": "Invalid JSON",
            "reason": str(e),
            "json_text": json_text,
            "raw_output": raw_output
        }
