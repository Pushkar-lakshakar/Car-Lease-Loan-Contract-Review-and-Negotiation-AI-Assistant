import subprocess
import json


MODEL_NAME = "llama3.1:8b"


# --------------------------
# JSON BLOCK EXTRACTOR
# --------------------------
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


# --------------------------
# MAIN SLA EXTRACTOR
# --------------------------
def extract_sla(txt_path: str) -> dict:

    # Read OCR output
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Safety limit
    text = text[:15000]

    # Your full desired JSON schema
    json_schema = """
{
    "lease_start_date": null,
    "lease_end_date": null,
    "lease_duration": null,

    "monthly_lease_amount": {
        "amount": null,
        "due_date": null
    },

    "payment_method": null,

    "account_details": {
        "bank_name": null,
        "account_name": null,
        "account_number": null,
        "routing_number": null
    },

    "late_fee": null,
    "security_deposit_amount": null,

    "vehicle_details": {
        "make": null,
        "model": null,
        "year": null,
        "vin": null,
        "color": null
    },

    "lessee_responsibilities": [],
    "lessor_responsibilities": [],

    "maintenance_and_repairs": {
        "regular_maintenance": null,
        "minor_repair_cost": null,
        "major_repair_coverage": null
    },

    "mileage_limits": {
        "annual_mileage_limit": null,
        "total_lease_term_mileage_limit": null,
        "excess_mileage_charge_per_mile": null
    },

    "insurance_requirements": {
        "liability_insurance": {
            "bodily_injury": null,
            "property_damage": null
        },
        "collision_and_comprehensive_insurance": {
            "deductible": null
        }
    },

    "purchase_option": {
        "price": null,
        "notice_requirement": null
    },

    "termination_conditions": {
        "voluntary_early_termination_fee": null
    },

    "penalties_and_fees": []
}
"""

    # FINAL PROMPT (One-Stage)
    prompt = f"""
You are an expert legal AI. Extract SLA fields from the TEXT and fill the JSON schema.

RULES:
- Fill values when present.
- Use null when missing.
- Output ONLY one JSON object.
- NO explanation. NO commentary. NO extra text.

JSON_SCHEMA:
{json_schema}

TEXT:
{text}
"""

    # Call Ollama
    result = subprocess.run(
        ["ollama", "run", MODEL_NAME],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    raw = result.stdout.decode("utf-8", errors="ignore").strip()

    # Extract full JSON using brace counter
    json_text = extract_json_block(raw)

    if not json_text:
        return {
            "error": "No JSON found",
            "raw": raw,
            "text_used": text
        }

    # Parse JSON
    try:
        return json.loads(json_text)
    except Exception as e:
        return {
            "error": "Invalid JSON",
            "reason": str(e),
            "json_text": json_text,
            "raw": raw
        }
