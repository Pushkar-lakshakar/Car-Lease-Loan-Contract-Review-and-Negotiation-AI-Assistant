import re
import math

# Utility Extractors
def extract_number(value):
    """Extracts first integer or float from a string."""
    if value is None:
        return None
    nums = re.findall(r"[\d.,]+", str(value))
    if not nums:
        return None
    return float(nums[0].replace(",", ""))

def extract_percentage(value):
    """Extracts percent-like values: 65%, 0.65, etc."""
    if value is None:
        return None
    match = re.search(r"(\d{1,3})\s*%", str(value))
    if match:
        return float(match.group(1))
    return None

def extract_currency(value):
    """Extracts rupee or dollar amounts."""
    return extract_number(value)

# Residual Value Extraction
def estimate_residual_value(sla):
    """
    Extract RV using:
    - purchase_option_price
    - residual_value fields
    - fallback estimate from mileage + make
    """

    # 1) Direct RV in % if present
    if "residual_value" in sla:
        rv_pct = extract_percentage(sla["residual_value"])
        if rv_pct:
            return rv_pct

    # 2) Purchase option price vs expected depreciation
    price = extract_currency(sla.get("purchase_option", {}).get("price"))
    if price:
        # assume typical new car value approx = monthly × (lease_months/0.018)
        m = extract_number(sla.get("monthly_lease_amount"))
        term = extract_number(sla.get("lease_duration")) or 36
        if m:
            est_vehicle_price = (m * term) / 0.018  # approx EMI=1.8%
            rv_pct = (price / est_vehicle_price) * 100
            return rv_pct

    # 3) Fallback based on make
    make = sla.get("vehicle_details", {}).get("make", "").lower()
    if "toyota" in make or "maruti" in make:
        return 70
    if "hyundai" in make or "honda" in make:
        return 63
    if any(lux in make for lux in ["bmw", "audi", "mercedes"]):
        return 45
    
    return 55  # default Indian sedan/hatchback RV

# Implied Interest Rate (IIR)
def estimate_iir(sla):
    """
    A realistic approximation:
    EMI formula reversed:
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    """

    m = extract_number(sla.get("monthly_lease_amount"))
    term = extract_number(sla.get("lease_duration")) or 36

    if not m:
        return None

    # Assume asset value approx:
    # EMI ≈ 2% of vehicle cost
    approx_asset_price = m / 0.02

    # EMI formula rearranged:
    n = term
    EMI = m
    P = approx_asset_price

    # solve approx r ≈ EMI/P per month
    r_month = EMI / P
    r_annual = r_month * 12

    return r_annual

# Main Analysis
def analyze_contract(sla: dict):
    
    fairness = {
        "financial_efficiency": 0,
        "asset_value_alignment": 0,
        "contract_flexibility": 0,
        "operational_transparency": 0
    }
    red_flags = []

    def flag(name, reason):
        red_flags.append({"clause": name, "reason": reason})

    # 1) Financial Efficiency (40%)
    iir = estimate_iir(sla)

    if iir is None:
        fairness["financial_efficiency"] = 50
    else:
        if iir < 0.10:
            fairness["financial_efficiency"] = 100
        elif iir < 0.12:
            fairness["financial_efficiency"] = 75
        elif iir < 0.15:
            fairness["financial_efficiency"] = 40
        else:
            fairness["financial_efficiency"] = 0
            flag("High Implied Interest Rate",
                 "APR is significantly higher than Indian car loan norms (8-11%).")

    # 2) Asset Value Alignment (25%)
    rv = estimate_residual_value(sla)

    make = sla.get("vehicle_details", {}).get("make", "").lower()
    
    if "toyota" in make or "maruti" in make:
        market_rv = 70
    elif "hyundai" in make or "honda" in make:
        market_rv = 63
    else:
        market_rv = 55

    delta = abs(rv - market_rv)

    if delta <= 5:
        fairness["asset_value_alignment"] = 100
    elif delta <= 10:
        fairness["asset_value_alignment"] = 75
    elif delta <= 20:
        fairness["asset_value_alignment"] = 40
        flag("Residual Value Mismatch",
             "Contract RV differs noticeably from expected Indian RV benchmarks.")
    else:
        fairness["asset_value_alignment"] = 0
        flag("Severe RV Mismatch",
             "Residual value deviates by more than 20% from industry expectations.")

    # 3) Contract Flexibility (20%)
    term_fee = extract_number(sla.get("termination_conditions", {}).get("voluntary_early_termination_fee"))
    total_payable = (extract_number(sla.get("monthly_lease_amount")) or 0) * (extract_number(sla.get("lease_duration")) or 36)

    if term_fee and total_payable > 0:
        fee_pct = (term_fee / total_payable) * 100
        if fee_pct <= 3:
            fairness["contract_flexibility"] = 100
        elif fee_pct <= 6:
            fairness["contract_flexibility"] = 75
        else:
            fairness["contract_flexibility"] = 40
            flag("High Early Termination Fee",
                 "Termination penalty exceeds accepted Indian auto-finance norms.")
    else:
        fairness["contract_flexibility"] = 70

    # GST/Cess detection
    contract_text = str(sla).lower()
    if "gst recoverable" in contract_text or "cess recoverable" in contract_text or "change in law" in contract_text:
        fairness["contract_flexibility"] -= 30
        flag("GST/Cess Recovery Risk",
             "Contract passes future tax increases to lessee, raising total cost.")

    fairness["contract_flexibility"] = max(0, fairness["contract_flexibility"])

    # 4) Operational Transparency (15%)
    ops = 100

    mileage = extract_number(sla.get("mileage_limits", {}).get("annual_mileage_limit"))
    if mileage:
        if mileage >= 15000:
            ops = 100
        elif mileage >= 12000:
            ops = 80
        else:
            ops = 40
            flag("Low Mileage Limit",
                 "Mileage allowance is below normal Indian usage (~12,000 km/year).")

    # Restricted repair shops
    if re.search(r"(authorized|approved|must be serviced) (service|repair) center", contract_text):
        ops -= 30
        flag("Restricted Repair Shops",
             "Lessee is limited to specific repair centers, reducing flexibility.")

    fairness["operational_transparency"] = max(0, ops)

    # FINAL SCORE
    final_score = (
        fairness["financial_efficiency"] * 0.40 +
        fairness["asset_value_alignment"] * 0.25 +
        fairness["contract_flexibility"] * 0.20 +
        fairness["operational_transparency"] * 0.15
    )

    final_score = round(max(0, min(100, final_score)))

    return {
        "contract_fairness_score": final_score,
        "red_flag_clauses": red_flags,
        "fairness_breakdown": fairness
    }
