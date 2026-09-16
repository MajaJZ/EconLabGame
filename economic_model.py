"""
EconLab economic simulation model.

Uses a delta-based approach: policy effects are measured as deviations
from a reference (neutral) policy. This is mathematically consistent
with standard macroeconomic theory (IS curve, Phillips curve, Okun's law).
"""

import pandas as pd

# Reference policy = a neutral baseline. Effects are computed relative to this.
REFERENCE_POLICY = {
    "interest_rate": 4.0,
    "income_tax": 19.0,
    "vat": 23.0,
    "gov_spending_change": 0.0,
}

# Coefficients based on empirical macroeconomic literature.
# (values are per 1 percentage point change in the policy variable)
DEFAULT_COEFFICIENTS = {
    # GDP growth (IS curve / multipliers)
    "gdp_spending": 0.40,      # fiscal multiplier ~0.4-1.0 (conservative)
    "gdp_interest": -0.30,     # monetary tightening reduces growth
    "gdp_income_tax": -0.25,   # tax multiplier (smaller than spending multiplier)
    "gdp_vat": -0.20,          # consumption tax reduces demand

    # Inflation (Phillips curve + cost-push)
    "infl_spending": 0.12,     # demand-pull inflation
    "infl_interest": -0.35,    # monetary policy disinflation
    "infl_vat": 0.40,          # VAT pass-through to consumer prices
    "infl_income_tax": -0.08,  # lower demand reduces price pressure

    # Unemployment (Okun's law)
    "unemp_spending": -0.15,
    "unemp_interest": 0.15,
    "unemp_income_tax": 0.12,
    "unemp_vat": 0.05,

    # Real wage growth
    "wage_gdp_growth": 0.40,   # wages track productivity/GDP
    "wage_inflation": -0.50,   # inflation erodes real wages
    "wage_spending": 0.05,
    "wage_interest": -0.05,
}


def load_baseline(country: str) -> dict:
    """Load baseline economic indicators for a given country from data.csv."""
    df = pd.read_csv("data.csv")
    if country not in df["country"].values:
        raise ValueError(f"Country {country} not found in data.csv")
    row = df[df["country"] == country].iloc[0]
    return {
        "gdp_growth": float(row["base_gdp_growth"]),
        "inflation": float(row["base_inflation"]),
        "unemployment": float(row["base_unemployment"]),
        "real_wage_growth": float(row["base_real_wage_growth"]),
    }


def simulate_economy(country: str, params: dict, coefficients: dict = None) -> dict:
    """
    Simulate economy based on policy parameters.

    The model computes the *change* from the reference policy and applies
    it to the country's baseline. This means setting every slider to its
    reference value reproduces the baseline exactly.
    """
    base = load_baseline(country)
    coeff = coefficients if coefficients is not None else DEFAULT_COEFFICIENTS

    # Delta from reference policy
    d_rate = params.get("interest_rate", REFERENCE_POLICY["interest_rate"]) - REFERENCE_POLICY["interest_rate"]
    d_tax = params.get("income_tax", REFERENCE_POLICY["income_tax"]) - REFERENCE_POLICY["income_tax"]
    d_vat = params.get("vat", REFERENCE_POLICY["vat"]) - REFERENCE_POLICY["vat"]
    d_spend = params.get("gov_spending_change", REFERENCE_POLICY["gov_spending_change"]) - REFERENCE_POLICY["gov_spending_change"]

    # GDP growth
    gdp_growth = (
        base["gdp_growth"]
        + coeff["gdp_spending"] * d_spend
        + coeff["gdp_interest"] * d_rate
        + coeff["gdp_income_tax"] * d_tax
        + coeff["gdp_vat"] * d_vat
    )

    # Inflation
    inflation = (
        base["inflation"]
        + coeff["infl_spending"] * d_spend
        + coeff["infl_interest"] * d_rate
        + coeff["infl_vat"] * d_vat
        + coeff["infl_income_tax"] * d_tax
    )

    # Unemployment
    unemployment = (
        base["unemployment"]
        + coeff["unemp_spending"] * d_spend
        + coeff["unemp_interest"] * d_rate
        + coeff["unemp_income_tax"] * d_tax
        + coeff["unemp_vat"] * d_vat
    )

    # Real wage growth
    real_wage_growth = (
        base["real_wage_growth"]
        + coeff["wage_gdp_growth"] * (gdp_growth - base["gdp_growth"])
        + coeff["wage_inflation"] * (inflation - base["inflation"])
        + coeff["wage_spending"] * d_spend
        + coeff["wage_interest"] * d_rate
    )

    # Bounds
    gdp_growth = max(-8.0, min(15.0, gdp_growth))
    inflation = max(-2.0, min(30.0, inflation))
    unemployment = max(1.0, min(30.0, unemployment))
    real_wage_growth = max(-8.0, min(10.0, real_wage_growth))

    return {
        "gdp_growth": gdp_growth,
        "inflation": inflation,
        "unemployment": unemployment,
        "real_wage_growth": real_wage_growth,
        "gdp_growth_change": gdp_growth - base["gdp_growth"],
        "inflation_change": inflation - base["inflation"],
        "unemployment_change": unemployment - base["unemployment"],
        "real_wage_growth_change": real_wage_growth - base["real_wage_growth"],
    }
