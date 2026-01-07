import subprocess
import json
import re

model = "llama3"
txtFile = "Car Lease Agreement.txt"
outputJson = "car_lease_summary.json"

with open(txtFile, "r", encoding="utf-8") as f:
    text = f.read()

prompt = f"""
You are a legal document analyzer.

Return ONLY valid JSON.
Do not add explanations, markdown, or extra text.

JSON schema:
{{
  "lease_start_date": null,
  "lease_end_date": null,
  "lease_duration": null,
  "monthly_lease_amount": null,
  "payment_due_date": null,
  "security_deposit_amount": null,
  "vehicle_details": {{
    "make": null,
    "model": null,
    "year": null,
    "vin": null,
    "color": null
  }},
  "lessee_responsibilities": [],
  "lessor_responsibilities": [],
  "maintenance_and_repairs": null,
  "mileage_limits": null,
  "insurance_requirements": null,
  "purchase_option": null,
  "termination_conditions": null,
  "penalties_and_fees": null
}}

DOCUMENT:
{text}
"""

result = subprocess.run(
    ["ollama", "run", model],
    input=prompt,
    text=True,
    capture_output=True
)

raw_output = result.stdout.strip()

# ---- Extract JSON safely ----
try:
    # Remove code fences if model adds them
    cleaned = re.sub(r"```json|```", "", raw_output).strip()
    structuredData = json.loads(cleaned)

except json.JSONDecodeError:
    # Fallback: save raw output so file is ALWAYS created
    structuredData = {
        "error": "Model did not return valid JSON",
        "raw_response": raw_output
    }

# ---- Always write JSON file ----
with open(outputJson, "w", encoding="utf-8") as f:
    json.dump(structuredData, f, indent=4)

print(f"JSON output saved to: {outputJson}")
