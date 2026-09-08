import streamlit as st
import pandas as pd
import random
from economic_model import simulate_economy, load_baseline, DEFAULT_COEFFICIENTS

# Page setup
st.set_page_config(
    page_title="EconLab",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        letter-spacing: 3px;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #888;
        margin-bottom: 20px;
    }
    .result-label {
        font-weight: bold;
        font-size: 18px;
    }
    .opening-banner {
        text-align: center;
        padding: 40px 30px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 20px;
        margin: 30px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .opening-banner h1 {
        color: #ffffff;
        font-size: 34px;
        font-weight: bold;
        margin: 0 0 15px 0;
        letter-spacing: 2px;
    }
    .opening-banner p {
        color: #e0e0e0;
        font-size: 17px;
        line-height: 1.6;
        margin: 0;
    }
    .ending-banner-success {
        text-align: center;
        padding: 40px 30px;
        background: linear-gradient(135deg, #0a1a0a 0%, #1a3a1a 50%, #0a2a0a 100%);
        border-radius: 20px;
        margin: 30px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .ending-banner-success h1 {
        color: #c9a84c;
        font-size: 32px;
        font-weight: bold;
        margin: 0 0 15px 0;
        letter-spacing: 2px;
    }
    .ending-banner-fail {
        text-align: center;
        padding: 40px 30px;
        background: linear-gradient(135deg, #2d0000 0%, #4a0000 50%, #1a0000 100%);
        border-radius: 20px;
        margin: 30px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .ending-banner-fail h1 {
        color: #ff4444;
        font-size: 32px;
        font-weight: bold;
        margin: 0 0 15px 0;
        letter-spacing: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="main-title">ECONLAB</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">MINISTRY OF FINANCE</div>', unsafe_allow_html=True)

# Initialize session state
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "player_style" not in st.session_state:
    st.session_state.player_style = "Centrist"
if "approval" not in st.session_state:
    st.session_state.approval = 50.0
if "year" not in st.session_state:
    st.session_state.year = 1
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "history" not in st.session_state:
    st.session_state.history = []
if "event" not in st.session_state:
    st.session_state.event = None
if "results" not in st.session_state:
    st.session_state.results = None
if "narrative" not in st.session_state:
    st.session_state.narrative = None
if "approval_change" not in st.session_state:
    st.session_state.approval_change = 0.0
if "spending_bonus" not in st.session_state:
    st.session_state.spending_bonus = 0
if "coeffs" not in st.session_state:
    st.session_state.coeffs = DEFAULT_COEFFICIENTS.copy()
if "lesson_mode" not in st.session_state:
    st.session_state.lesson_mode = False
if "challenge" not in st.session_state:
    st.session_state.challenge = None

# ---- SCENARIOS ----
SCENARIOS = {
    "None (normal)": {
        "baseline_override": None,
        "targets": None,
        "description": "Standard baseline data from the country file.",
        "narrative": "",
    },
    "COVID-19 Recession": {
        "baseline_override": {
            "gdp_growth": -2.0,
            "inflation": 1.0,
            "unemployment": 9.0,
            "real_wage_growth": -1.0,
        },
        "targets": {
            "gdp_growth": 2.0,
            "inflation": 2.5,
            "unemployment": 6.0,
        },
        "description": "A severe global recession. GDP is shrinking, unemployment is high.",
        "narrative": "The economy is in freefall. Your goal is to stimulate growth without letting inflation run wild.",
    },
    "Overheating Boom": {
        "baseline_override": {
            "gdp_growth": 6.0,
            "inflation": 8.0,
            "unemployment": 2.0,
            "real_wage_growth": 4.0,
        },
        "targets": {
            "gdp_growth": 3.0,
            "inflation": 3.0,
            "unemployment": 4.0,
        },
        "description": "The economy is growing too fast, causing high inflation.",
        "narrative": "Inflation is out of control. Try to cool the economy without causing a recession.",
    },
    "Stagflation": {
        "baseline_override": {
            "gdp_growth": 0.5,
            "inflation": 7.0,
            "unemployment": 8.0,
            "real_wage_growth": -2.0,
        },
        "targets": {
            "gdp_growth": 2.0,
            "inflation": 3.0,
            "unemployment": 6.0,
        },
        "description": "High inflation and high unemployment simultaneously.",
        "narrative": "The worst of both worlds. Can you break the cycle?",
    },
}

# ---- FUNCTIONS ----
def generate_random_event():
    events = [
        {
            "name": "Global Pandemic",
            "effect": {"gdp_growth": -2.0, "inflation": 0.5, "unemployment": 2.0},
            "description": "A global pandemic hits. Lockdowns hurt the economy.",
        },
        {
            "name": "Oil Price Spike",
            "effect": {"gdp_growth": -0.5, "inflation": 1.5, "unemployment": 0.5},
            "description": "Oil prices skyrocket due to geopolitical tensions.",
        },
        {
            "name": "Tech Boom",
            "effect": {"gdp_growth": 1.5, "inflation": -0.2, "unemployment": -1.0},
            "description": "A new technology boom boosts productivity.",
        },
        {
            "name": "Trade Deal Signed",
            "effect": {"gdp_growth": 1.0, "inflation": -0.3, "unemployment": -0.5},
            "description": "A major trade deal opens new markets for your country.",
        },
        {
            "name": "Natural Disaster",
            "effect": {"gdp_growth": -1.0, "inflation": 0.3, "unemployment": 0.8},
            "description": "A natural disaster damages infrastructure.",
        },
        {
            "name": "Foreign Investment Surge",
            "effect": {"gdp_growth": 1.2, "inflation": 0.1, "unemployment": -0.8},
            "description": "Foreign investors flock to your country.",
        },
    ]
    if random.random() < 0.4:
        return random.choice(events)
    return None


def generate_narrative(res, approval_change):
    narrative = []
    if res["gdp_growth"] > 4.0:
        narrative.append("Your economy is booming. Businesses are expanding and new jobs are everywhere.")
    elif res["gdp_growth"] > 2.0:
        narrative.append("The economy is growing steadily. People are cautiously optimistic.")
    elif res["gdp_growth"] > 0:
        narrative.append("Growth is sluggish. Many families are struggling to make ends meet.")
    else:
        narrative.append("The economy is shrinking. Protests are breaking out in major cities.")

    if res["inflation"] > 8.0:
        narrative.append("Inflation is out of control. People rush to buy goods before prices rise again.")
    elif res["inflation"] > 4.0:
        narrative.append("Prices are rising quickly. Citizens are feeling the pinch at the grocery store.")
    elif res["inflation"] < 1.0:
        narrative.append("Inflation is very low. Some economists worry about deflation.")
    else:
        narrative.append("Inflation is moderate. The central bank seems satisfied.")

    if res["unemployment"] < 4.0:
        narrative.append("Almost everyone who wants a job has one. Employers are competing for workers.")
    elif res["unemployment"] < 7.0:
        narrative.append("Unemployment is manageable, but some regions are struggling.")
    else:
        narrative.append("High unemployment is causing social unrest. Young people are especially affected.")

    if approval_change > 5:
        narrative.append("Your approval rating is soaring. You are being called a hero in the newspapers.")
    elif approval_change > 0:
        narrative.append("The public seems pleased with your policies.")
    elif approval_change > -5:
        narrative.append("Some voters are unhappy. Opposition parties are gaining support.")
    else:
        narrative.append("Your approval rating is plummeting. Protests are growing outside your office.")

    return " ".join(narrative)


# ---- OPENING PAGE ----
if not st.session_state.game_started:
    st.markdown("---")

    st.markdown("""
    <div class="opening-banner">
        <h1>MINISTRY OF FINANCE</h1>
        <div style="width:100px;height:2px;background:#c9a84c;margin:20px auto;"></div>
        <p>
            You have been appointed as the <strong style="color:#c9a84c;">Minister of Finance</strong>.<br>
            The nation's economic future rests in your hands.<br>
            <em>Can you lead the country through 4 years of challenges?</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### Official Appointment Form")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.player_name = st.text_input(
            "Minister's Name",
            value=st.session_state.player_name,
            placeholder="Enter your full name...",
        )
    with col2:
        st.session_state.player_style = st.selectbox(
            "Political Affiliation",
            ["Centrist", "Social Democrat", "Conservative", "Libertarian", "Green"],
        )

    style_info = {
        "Centrist": "Balanced fiscal approach. Moderate starting approval and stable indicators.",
        "Social Democrat": "Strong welfare mandate. Higher spending capacity with increased tax burden.",
        "Conservative": "Fiscal discipline focus. Lower spending with cautious growth outlook.",
        "Libertarian": "Minimal government intervention. Lower taxes with reduced safety net.",
        "Green": "Environmental investment priority. New green initiatives with associated costs.",
    }
    st.info(f"**{st.session_state.player_style}** — {style_info[st.session_state.player_style]}")

    st.markdown("---")

    st.markdown("### Official Briefing Document")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Primary Objectives:**
        - Serve a full 4-year term
        - Maintain public approval above 20%
        - Manage key economic indicators
        - Respond to national crises
        """)
    with col2:
        st.markdown("""
        **Policy Instruments:**
        - Interest rates (central bank coordination)
        - Income tax rates
        - VAT adjustments
        - Government spending levels
        """)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("BEGIN YOUR TERM", use_container_width=True):
            if st.session_state.player_name == "":
                st.warning("Please enter your name to proceed.")
            else:
                style_modifiers = {
                    "Centrist": {"approval_bonus": 0, "spending_bonus": 0},
                    "Social Democrat": {"approval_bonus": 5, "spending_bonus": 2},
                    "Conservative": {"approval_bonus": -5, "spending_bonus": -2},
                    "Libertarian": {"approval_bonus": 0, "spending_bonus": -3},
                    "Green": {"approval_bonus": 10, "spending_bonus": 1},
                }
                modifier = style_modifiers[st.session_state.player_style]
                st.session_state.approval = 50 + modifier["approval_bonus"]
                st.session_state.spending_bonus = modifier["spending_bonus"]
                st.session_state.game_started = True
                st.rerun()

    st.stop()


# ---- SIDEBAR ----
with st.sidebar:
    st.header("Options")
    scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()))
    scenario = SCENARIOS[scenario_name]

    st.session_state.lesson_mode = st.checkbox("Lesson Mode", value=False)

    with st.expander("Advanced: Model Coefficients", expanded=False):
        coeffs = st.session_state.coeffs
        coeffs["gdp_spending"] = st.slider("Spending effect on GDP", -1.0, 1.0, coeffs["gdp_spending"], 0.05)
        coeffs["gdp_interest"] = st.slider("Interest effect on GDP", -1.0, 1.0, coeffs["gdp_interest"], 0.05)
        coeffs["gdp_income_tax"] = st.slider("Income tax effect on GDP", -1.0, 1.0, coeffs["gdp_income_tax"], 0.05)
        coeffs["gdp_vat"] = st.slider("VAT effect on GDP", -1.0, 1.0, coeffs["gdp_vat"], 0.05)
        coeffs["infl_spending"] = st.slider("Spending effect on inflation", -1.0, 1.0, coeffs["infl_spending"], 0.05)
        coeffs["infl_interest"] = st.slider("Interest effect on inflation", -1.0, 1.0, coeffs["infl_interest"], 0.05)
        coeffs["infl_vat"] = st.slider("VAT effect on inflation", -1.0, 1.0, coeffs["infl_vat"], 0.05)
        coeffs["infl_income_tax"] = st.slider("Income tax effect on inflation", -1.0, 1.0, coeffs["infl_income_tax"], 0.05)
        coeffs["unemp_spending"] = st.slider("Spending effect on unemployment", -1.0, 1.0, coeffs["unemp_spending"], 0.05)
        coeffs["unemp_interest"] = st.slider("Interest effect on unemployment", -1.0, 1.0, coeffs["unemp_interest"], 0.05)
        coeffs["unemp_income_tax"] = st.slider("Income tax effect on unemployment", -1.0, 1.0, coeffs["unemp_income_tax"], 0.05)
        coeffs["unemp_vat"] = st.slider("VAT effect on unemployment", -1.0, 1.0, coeffs["unemp_vat"], 0.05)
        coeffs["wage_gdp_growth"] = st.slider("GDP growth effect on wages", -1.0, 1.0, coeffs["wage_gdp_growth"], 0.05)
        coeffs["wage_inflation"] = st.slider("Inflation effect on wages", -1.0, 1.0, coeffs["wage_inflation"], 0.05)
        coeffs["wage_spending"] = st.slider("Spending effect on wages", -1.0, 1.0, coeffs["wage_spending"], 0.05)
        coeffs["wage_interest"] = st.slider("Interest effect on wages", -1.0, 1.0, coeffs["wage_interest"], 0.05)

        if st.button("Reset coefficients"):
            st.session_state.coeffs = DEFAULT_COEFFICIENTS.copy()
            st.rerun()


# ---- MAIN GAME AREA ----
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Minister", st.session_state.player_name)
with col2:
    st.metric("Year in Office", f"{st.session_state.year}/4")
with col3:
    st.metric("Approval", f"{st.session_state.approval:.0f}%")
with col4:
    if st.session_state.game_over:
        st.error("TERM ENDED")
    else:
        st.info(st.session_state.player_style)

# Country / scenario baseline
if scenario["baseline_override"] is None:
    country = st.selectbox("Choose your starting economy", ["Poland", "Germany", "USA"], index=0)
    baseline = load_baseline(country)
else:
    country = "Scenario"
    baseline = scenario["baseline_override"]
    st.info(f"Scenario: {scenario['description']}")

st.write(f"**Baseline for {country}:** GDP growth {baseline['gdp_growth']:.1f}% | Inflation {baseline['inflation']:.1f}% | Unemployment {baseline['unemployment']:.1f}% | Wage growth {baseline['real_wage_growth']:.1f}%")

if scenario["narrative"]:
    st.markdown(f"*{scenario['narrative']}*")

st.markdown("---")

# Challenge
st.subheader("Challenge Mode")
if scenario["targets"] is not None:
    st.session_state.challenge = scenario["targets"]
    ch = st.session_state.challenge
    st.write(f"GDP >= {ch['gdp_growth']}% | Inflation <= {ch['inflation']}% | Unemployment <= {ch['unemployment']}%")
else:
    if st.button("Generate Challenge"):
        st.session_state.challenge = {
            "gdp_growth": round(random.uniform(baseline["gdp_growth"] + 1.0, baseline["gdp_growth"] + 3.0), 1),
            "inflation": round(random.uniform(max(0.5, baseline["inflation"] - 1.5), baseline["inflation"] + 0.5), 1),
            "unemployment": round(random.uniform(max(1.0, baseline["unemployment"] - 2.0), baseline["unemployment"] - 0.5), 1),
        }
        st.rerun()
    if st.session_state.challenge:
        ch = st.session_state.challenge
        st.write(f"GDP >= {ch['gdp_growth']}% | Inflation <= {ch['inflation']}% | Unemployment <= {ch['unemployment']}%")
    else:
        st.write("No challenge yet. Generate one.")

st.markdown("---")

# Policy sliders
if st.session_state.lesson_mode:
    st.markdown("### Lesson Mode")
    st.markdown("Try to keep unemployment below 6% while getting inflation below 3%.")
    interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 8.0, 0.05)
    income_tax = st.slider("Income tax (%)", 0.0, 50.0, 20.0, 0.5)
    vat = st.slider("VAT (%)", 0.0, 30.0, 15.0, 0.5)
    gov_spending_change = st.slider("Government spending change (%)", -10.0, 10.0, -2.0, 0.1)
else:
    st.subheader("Your Policy")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 4.25, 0.05)
    with c2:
        income_tax = st.slider("Income tax (%)", 0.0, 50.0, 19.0, 0.5)
    with c3:
        vat = st.slider("VAT (%)", 0.0, 30.0, 23.0, 0.5)
    with c4:
        gov_spending_change = st.slider("Gov spending change (%)", -10.0, 10.0, 2.0, 0.1)

# Run button
if st.session_state.game_over:
    run_button = False
else:
    run_button = st.button("RUN EXPERIMENT", use_container_width=True)

st.markdown("---")

# Results
if run_button and not st.session_state.game_over:
    params = {
        "interest_rate": interest_rate,
        "income_tax": income_tax,
        "vat": vat,
        "gov_spending_change": gov_spending_change + st.session_state.spending_bonus,
    }
    st.session_state.event = generate_random_event()

    if scenario["baseline_override"] is not None:
        df = pd.read_csv("data.csv")
        if "Scenario" not in df["country"].values:
            row = {
                "country": "Scenario",
                "base_gdp_growth": baseline["gdp_growth"],
                "base_inflation": baseline["inflation"],
                "base_unemployment": baseline["unemployment"],
                "base_real_wage_growth": baseline["real_wage_growth"],
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv("data.csv", index=False)
        results = simulate_economy("Scenario", params, st.session_state.coeffs)
    else:
        results = simulate_economy(country, params, st.session_state.coeffs)

    if st.session_state.event:
        results["gdp_growth"] += st.session_state.event["effect"]["gdp_growth"]
        results["inflation"] += st.session_state.event["effect"]["inflation"]
        results["unemployment"] += st.session_state.event["effect"]["unemployment"]
        results["gdp_growth_change"] = results["gdp_growth"] - baseline["gdp_growth"]
        results["inflation_change"] = results["inflation"] - baseline["inflation"]
        results["unemployment_change"] = results["unemployment"] - baseline["unemployment"]

    approval_change = 0.0
    approval_change += (results["gdp_growth"] - 2.0) * (5 if results["gdp_growth"] > 2.0 else 8)
    if results["inflation"] > 4.0:
        approval_change -= (results["inflation"] - 4.0) * 3
    elif results["inflation"] < 2.0:
        approval_change += 2
    if results["unemployment"] < 5.0:
        approval_change += (5.0 - results["unemployment"]) * 4
    else:
        approval_change -= (results["unemployment"] - 5.0) * 5

    st.session_state.approval = max(0, min(100, st.session_state.approval + approval_change))
    st.session_state.results = results
    st.session_state.approval_change = approval_change
    st.session_state.narrative = generate_narrative(results, approval_change)
    st.session_state.history.append({"year": st.session_state.year, "approval": st.session_state.approval, **results})

    if st.session_state.approval < 20 or st.session_state.year >= 4:
        st.session_state.game_over = True
    else:
        st.session_state.year += 1

# Show results
if st.session_state.results is not None:
    res = st.session_state.results
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("GDP Growth", f"{res['gdp_growth']:.1f}%", f"{res['gdp_growth_change']:+.1f}%")
    c2.metric("Inflation", f"{res['inflation']:.1f}%", f"{res['inflation_change']:+.1f}%")
    c3.metric("Unemployment", f"{res['unemployment']:.1f}%", f"{res['unemployment_change']:+.1f}%")
    c4.metric("Real Wage Growth", f"{res['real_wage_growth']:.1f}%", f"{res['real_wage_growth_change']:+.1f}%")

    if st.session_state.event:
        st.markdown("---")
        st.subheader(f"Event: {st.session_state.event['name']}")
        st.write(st.session_state.event["description"])

    if st.session_state.narrative:
        st.markdown("---")
        st.subheader("News Report")
        st.write(st.session_state.narrative)

    st.markdown("---")
    chart_df = pd.DataFrame({
        "Metric": ["GDP", "Inflation", "Unemployment", "Wages"],
        "Baseline": [baseline["gdp_growth"], baseline["inflation"], baseline["unemployment"], baseline["real_wage_growth"]],
        "Your Policy": [res["gdp_growth"], res["inflation"], res["unemployment"], res["real_wage_growth"]],
    }).set_index("Metric")
    st.bar_chart(chart_df, height=350)
else:
    if not st.session_state.game_over:
        st.info("Adjust the policy sliders and click RUN EXPERIMENT.")

# ---- CLOSING PAGE ----
if st.session_state.game_over:
    st.markdown("---")
    if st.session_state.approval < 20:
        st.markdown("""
        <div class="ending-banner-fail">
            <h1>TERM ENDED — PUBLIC UPRISING</h1>
            <div style="width:100px;height:2px;background:#ff4444;margin:20px auto;"></div>
            <p style="color:#cccccc;font-size:16px;">
                Your economic policies have failed the nation.<br>
                Public trust has collapsed. History will remember this failure.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="ending-banner-success">
            <h1>TERM COMPLETED</h1>
            <div style="width:100px;height:2px;background:#c9a84c;margin:20px auto;"></div>
            <p style="color:#e0e0e0;font-size:16px;">
                You have served your nation with distinction.<br>
                The economy is stable. Your legacy is assured.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write(f"**Final Approval Rating: {st.session_state.approval:.0f}%**")
    if st.session_state.history:
        st.line_chart(pd.DataFrame(st.session_state.history)[["approval"]])

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("START NEW TERM", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
