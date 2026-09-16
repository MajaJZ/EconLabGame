"""EconLab economic simulation model.

Delta-based approach: policy effects are measured as deviations from a
reference (neutral) policy. This is consistent with standard macro theory
(IS curve, Phillips curve, Okun's law)."""

import pandas as pd

REFERENCE_POLICY = {
    "interest_rate": 4.0, "income_tax": 19.0, "vat": 23.0, "gov_spending_change": 0.0,
}

DEFAULT_COEFFICIENTS = {
    "gdp_spending": 0.40, "gdp_interest": -0.30, "gdp_income_tax": -0.25, "gdp_vat": -0.20,
    "infl_spending": 0.12, "infl_interest": -0.35, "infl_vat": 0.40, "infl_income_tax": -0.08,
    "unemp_spending": -0.15, "unemp_interest": 0.15, "unemp_income_tax": 0.12, "unemp_vat": 0.05,
    "wage_gdp_growth": 0.40, "wage_inflation": -0.50, "wage_spending": 0.05, "wage_interest": -0.05,
}


def load_baseline(country):
    df = pd.read_csv("data.csv")
    if country not in df["country"].values:
        raise ValueError(f"Country '{country}' not found in data.csv")
    row = df[df["country"] == country].iloc[0]
    return {
        "gdp_growth": float(row["base_gdp_growth"]),
        "inflation": float(row["base_inflation"]),
        "unemployment": float(row["base_unemployment"]),
        "real_wage_growth": float(row["base_real_wage_growth"]),
    }


def simulate_economy(country, params, coefficients=None):
    base = load_baseline(country)
    c = coefficients if coefficients is not None else DEFAULT_COEFFICIENTS

    d_rate = params.get("interest_rate", REFERENCE_POLICY["interest_rate"]) - REFERENCE_POLICY["interest_rate"]
    d_tax = params.get("income_tax", REFERENCE_POLICY["income_tax"]) - REFERENCE_POLICY["income_tax"]
    d_vat = params.get("vat", REFERENCE_POLICY["vat"]) - REFERENCE_POLICY["vat"]
    d_spend = params.get("gov_spending_change", REFERENCE_POLICY["gov_spending_change"]) - REFERENCE_POLICY["gov_spending_change"]

    gdp = base["gdp_growth"] + c["gdp_spending"]*d_spend + c["gdp_interest"]*d_rate + c["gdp_income_tax"]*d_tax + c["gdp_vat"]*d_vat
    inf = base["inflation"] + c["infl_spending"]*d_spend + c["infl_interest"]*d_rate + c["infl_vat"]*d_vat + c["infl_income_tax"]*d_tax
    une = base["unemployment"] + c["unemp_spending"]*d_spend + c["unemp_interest"]*d_rate + c["unemp_income_tax"]*d_tax + c["unemp_vat"]*d_vat
    wage = (base["real_wage_growth"] + c["wage_gdp_growth"]*(gdp - base["gdp_growth"])
            + c["wage_inflation"]*(inf - base["inflation"]) + c["wage_spending"]*d_spend + c["wage_interest"]*d_rate)

    gdp = max(-8.0, min(15.0, gdp))
    inf = max(-2.0, min(30.0, inf))
    une = max(1.0, min(30.0, une))
    wage = max(-8.0, min(10.0, wage))

    return {
        "gdp_growth": gdp, "inflation": inf, "unemployment": une, "real_wage_growth": wage,
        "gdp_growth_change": gdp - base["gdp_growth"],
        "inflation_change": inf - base["inflation"],
        "unemployment_change": une - base["unemployment"],
        "real_wage_growth_change": wage - base["real_wage_growth"],
    }
