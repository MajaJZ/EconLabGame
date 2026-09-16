import streamlit as st
import pandas as pd
import random
from economic_model import simulate_economy, load_baseline, DEFAULT_COEFFICIENTS

st.set_page_config(page_title="EconLab", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

# ---------- STYLES ----------
st.markdown("""
<style>
.main-title { text-align:center; font-size:42px; font-weight:bold; letter-spacing:3px; margin-bottom:0; }
.subtitle { text-align:center; font-size:18px; color:#888; margin-bottom:20px; }
.banner {
    text-align:center; padding:40px 30px; border-radius:20px;
    margin:30px 0; box-shadow:0 10px 30px rgba(0,0,0,0.3);
}
.banner h1 { font-size:32px; font-weight:bold; margin:0 0 15px 0; letter-spacing:2px; }
.banner p { font-size:17px; line-height:1.6; margin:0; }

.banner-neutral { background: linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%); }
.banner-neutral h1 { color:#ffffff; } .banner-neutral p { color:#e0e0e0; }

.banner-success { background: linear-gradient(135deg,#0a1a0a 0%,#1a3a1a 50%,#0a2a0a 100%); }
.banner-success h1 { color:#5cd65c; } .banner-success p { color:#e0e0e0; }

.banner-fail { background: linear-gradient(135deg,#2d0000 0%,#4a0000 50%,#1a0000 100%); }
.banner-fail h1 { color:#ff5252; } .banner-fail p { color:#cccccc; }

.divider-gold { width:100px; height:2px; background:#c9a84c; margin:20px auto; }
.divider-red { width:100px; height:2px; background:#ff4444; margin:20px auto; }

/* Color-coded status boxes */
.status-good { background:#0d3b0d; padding:14px; border-left:5px solid #4caf50; border-radius:8px; margin:6px 0; }
.status-warn { background:#3b2f0d; padding:14px; border-left:5px solid #ffb300; border-radius:8px; margin:6px 0; }
.status-bad  { background:#3b0d0d; padding:14px; border-left:5px solid #f44336; border-radius:8px; margin:6px 0; }
.status-good b, .status-warn b, .status-bad b { color:#ffffff; }
.status-good span, .status-warn span, .status-bad span { color:#dddddd; }

/* Glossary cards */
.glossary-card {
    background:#1e1e2e; padding:16px 20px; border-radius:10px;
    margin:8px 0; border-left:4px solid #c9a84c;
}
.glossary-card h4 { color:#c9a84c; margin:0 0 6px 0; }
.glossary-card p { color:#d0d0d0; margin:0; font-size:14px; line-height:1.5; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">ECONLAB</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">MINISTRY OF FINANCE</div>', unsafe_allow_html=True)

# ---------- SESSION STATE ----------
defaults = {
    "game_started": False, "player_name": "", "player_style": "Centrist",
    "difficulty": "Normal", "approval": 60.0, "year": 1, "game_over": False,
    "history": [], "event": None, "results": None, "narrative": None,
    "approval_change": 0.0, "spending_bonus": 0, "coeffs": DEFAULT_COEFFICIENTS.copy(),
    "lesson_mode": False, "challenge": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- DIFFICULTY LEVELS ----------
LEVELS = {
    "Easy": {
        "start_approval": 70.0,
        "penalty_multiplier": 0.5,
        "events_chance": 0.25,
        "target_tolerance": 1.5,
        "description": "Relaxed targets and generous starting support. Recommended for first-time players.",
    },
    "Normal": {
        "start_approval": 60.0,
        "penalty_multiplier": 1.0,
        "events_chance": 0.40,
        "target_tolerance": 1.0,
        "description": "Balanced challenge. Standard economic conditions.",
    },
    "Hard": {
        "start_approval": 55.0,
        "penalty_multiplier": 1.4,
        "events_chance": 0.55,
        "target_tolerance": 0.7,
        "description": "Tighter margins and more frequent crises. For experienced ministers.",
    },
    "Crisis": {
        "start_approval": 50.0,
        "penalty_multiplier": 1.8,
        "events_chance": 0.70,
        "target_tolerance": 0.5,
        "description": "Extreme conditions. Random events are frequent and punishing.",
    },
}

# ---------- POLISH SCENARIOS ----------
SCENARIOS = {
    "None (baseline)": {
        "baseline_override": None, "targets": None,
        "description": "Standard country baseline. Choose your own path.",
        "narrative": "",
    },
    "1989 - Balcerowicz Plan": {
        "baseline_override": {"gdp_growth": -3.0, "inflation": 250.0, "unemployment": 6.5, "real_wage_growth": -15.0},
        "targets": {"gdp_growth": 1.0, "inflation": 30.0, "unemployment": 10.0},
        "description": "Post-communist shock therapy. Hyperinflation, collapsing output, but the chance to build a market economy.",
        "narrative": "You inherit an economy on the brink. Prices are spiraling; state enterprises are failing. Your task: stabilize without destroying hope.",
    },
    "2004 - EU Accession": {
        "baseline_override": {"gdp_growth": 5.0, "inflation": 3.5, "unemployment": 19.0, "real_wage_growth": 1.0},
        "targets": {"gdp_growth": 4.0, "inflation": 3.0, "unemployment": 12.0},
        "description": "Poland joins the EU. Growth accelerates, but unemployment in rural areas remains stubbornly high.",
        "narrative": "The EU flag flies over Warsaw. Foreign investment is arriving, but millions still lack opportunity. Manage the boom without overheating.",
    },
    "2008 - Global Financial Crisis": {
        "baseline_override": {"gdp_growth": -1.0, "inflation": 4.2, "unemployment": 9.5, "real_wage_growth": -1.0},
        "targets": {"gdp_growth": 2.0, "inflation": 2.5, "unemployment": 8.0},
        "description": "Global credit freeze. Poland is the only EU country to avoid recession, but pressure is intense.",
        "narrative": "Lehman Brothers has collapsed. World markets are in chaos. Can you keep Poland out of recession?",
    },
    "2020 - COVID-19 Pandemic": {
        "baseline_override": {"gdp_growth": -2.5, "inflation": 3.4, "unemployment": 6.5, "real_wage_growth": -1.0},
        "targets": {"gdp_growth": 3.0, "inflation": 3.5, "unemployment": 5.0},
        "description": "Lockdowns and supply-chain disruption. Tourism and services collapse.",
        "narrative": "The pandemic has emptied the streets. Restaurants and airlines are pleading for help. Protect lives and livelihoods.",
    },
    "2022 - Inflation Crisis": {
        "baseline_override": {"gdp_growth": 1.5, "inflation": 16.0, "unemployment": 3.0, "real_wage_growth": -4.0},
        "targets": {"gdp_growth": 2.0, "inflation": 6.0, "unemployment": 5.5},
        "description": "War in Ukraine and energy shock. Inflation hits double digits for the first time in 25 years.",
        "narrative": "Energy prices have exploded. Real wages are falling. The NBP must act — but too much tightening risks recession.",
    },
}

# ---------- GLOSSARY ----------
GLOSSARY = {
    "GDP (Gross Domestic Product)": "The total market value of all goods and services produced in a country in a given period. Growth above 2-3% is typically considered healthy for a developed economy.",
    "Inflation": "The rate at which the general level of prices for goods and services rises. Central banks typically target around 2%. High inflation erodes purchasing power.",
    "Unemployment": "The percentage of the labor force actively seeking work but unable to find it. 4-5% is often considered 'full employment' in advanced economies.",
    "Interest Rate": "The cost of borrowing set by the central bank. Higher rates reduce inflation but slow growth (monetary policy).",
    "VAT (Value Added Tax)": "A consumption tax applied at each stage of production. Higher VAT raises consumer prices directly (cost-push inflation).",
    "Income Tax": "A tax on personal earnings. Higher income tax reduces disposable income and consumer demand, cooling the economy.",
    "Government Spending": "Public expenditure on goods, services, and transfers. An increase acts as fiscal stimulus, boosting demand (Keynesian multiplier).",
    "Budget Deficit": "The gap when government spending exceeds revenue. Deficits stimulate the economy short-term but require borrowing.",
    "Public Debt": "Accumulated deficits expressed as a share of GDP. High debt (above 90% of GDP) can slow long-term growth.",
    "Real Wages": "Wages adjusted for inflation. Positive real-wage growth means workers' purchasing power is improving.",
    "Fiscal Multiplier": "The ratio of change in GDP to change in government spending or taxes. In Poland, estimated around 0.4-0.8.",
    "Okun's Law": "Empirical relationship: a 1% rise in unemployment is associated with roughly a 2% fall in GDP.",
    "Phillips Curve": "Inverse relationship between unemployment and inflation in the short run. Lower unemployment tends to push inflation up.",
    "Stagflation": "A combination of high inflation, low growth, and high unemployment. Rare and difficult to resolve.",
    "Crowding Out": "When high government borrowing raises interest rates and reduces private investment.",
}

# ---------- HELPERS ----------
def classify(value, good, warn, higher_is_better=True):
    """Return 'good', 'warn', or 'bad'."""
    if higher_is_better:
        if value >= good: return "good"
        if value >= warn: return "warn"
        return "bad"
    else:
        if value <= good: return "good"
        if value <= warn: return "warn"
        return "bad"


def generate_random_event(chance):
    events = [
        {"name": "Global Pandemic", "effect": {"gdp_growth": -2.0, "inflation": 0.5, "unemployment": 2.0},
         "description": "A global pandemic hits. Lockdowns hurt the economy."},
        {"name": "Oil Price Spike", "effect": {"gdp_growth": -0.5, "inflation": 1.5, "unemployment": 0.5},
         "description": "Oil prices skyrocket due to geopolitical tensions."},
        {"name": "Tech Boom", "effect": {"gdp_growth": 1.5, "inflation": -0.2, "unemployment": -1.0},
         "description": "A technology boom boosts productivity."},
        {"name": "Trade Deal Signed", "effect": {"gdp_growth": 1.0, "inflation": -0.3, "unemployment": -0.5},
         "description": "A major trade deal opens new markets."},
        {"name": "Natural Disaster", "effect": {"gdp_growth": -1.0, "inflation": 0.3, "unemployment": 0.8},
         "description": "A natural disaster damages infrastructure."},
        {"name": "Foreign Investment Surge", "effect": {"gdp_growth": 1.2, "inflation": 0.1, "unemployment": -0.8},
         "description": "Foreign investors flock to the country."},
        {"name": "Currency Depreciation", "effect": {"gdp_growth": 0.5, "inflation": 0.8, "unemployment": -0.3},
         "description": "The zloty weakens, helping exporters but raising import prices."},
    ]
    if random.random() < chance:
        return random.choice(events)
    return None


def generate_narrative(res, approval_change):
    parts = []
    if res["gdp_growth"] > 4.0: parts.append("The economy is booming. Businesses are expanding and jobs are everywhere.")
    elif res["gdp_growth"] > 2.0: parts.append("The economy is growing steadily. People are cautiously optimistic.")
    elif res["gdp_growth"] > 0: parts.append("Growth is sluggish. Many families struggle to make ends meet.")
    else: parts.append("The economy is shrinking. Protests are breaking out in major cities.")

    if res["inflation"] > 8.0: parts.append("Inflation is out of control. People rush to buy goods before prices rise again.")
    elif res["inflation"] > 4.0: parts.append("Prices are rising quickly. Citizens feel the pinch at the grocery store.")
    elif res["inflation"] < 1.0: parts.append("Inflation is very low. Some economists worry about deflation.")
    else: parts.append("Inflation is moderate. The central bank seems satisfied.")

    if res["unemployment"] < 4.0: parts.append("Almost everyone who wants a job has one.")
    elif res["unemployment"] < 7.0: parts.append("Unemployment is manageable, though some regions struggle.")
    else: parts.append("High unemployment is causing social unrest, especially among the young.")

    if approval_change > 5: parts.append("Your approval rating is soaring.")
    elif approval_change > 0: parts.append("The public seems pleased with your policies.")
    elif approval_change > -5: parts.append("Some voters are unhappy. Opposition parties are gaining ground.")
    else: parts.append("Your approval is plummeting. Protests are growing outside your office.")

    return " ".join(parts)


# ---------- OPENING PAGE ----------
if not st.session_state.game_started:
    st.markdown("---")
    st.markdown("""
    <div class="banner banner-neutral">
        <h1>MINISTRY OF FINANCE</h1>
        <div class="divider-gold"></div>
        <p>
            You have been appointed as the <strong style="color:#c9a84c;">Minister of Finance</strong>.<br>
            The nation's economic future rests in your hands.<br>
            <em>Can you lead the country through 4 years of challenges?</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Official Appointment Form")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.player_name = st.text_input("Minister's Name", value=st.session_state.player_name,
                                                     placeholder="Enter your full name...")
    with col2:
        st.session_state.player_style = st.selectbox(
            "Political Affiliation",
            ["Centrist", "Social Democrat", "Conservative", "Libertarian", "Green"])

    st.markdown("### Difficulty Level")
    diff_cols = st.columns(4)
    for i, (lvl, info) in enumerate(LEVELS.items()):
        with diff_cols[i]:
            if st.button(f"{lvl}", use_container_width=True,
                         type="primary" if st.session_state.difficulty == lvl else "secondary"):
                st.session_state.difficulty = lvl
                st.rerun()

    level = LEVELS[st.session_state.difficulty]
    st.info(f"**{st.session_state.difficulty}** — {level['description']}  |  Starting approval: {level['start_approval']:.0f}%  |  Event chance: {int(level['events_chance']*100)}%")

    style_info = {
        "Centrist": "Balanced approach. No bonuses or penalties.",
        "Social Democrat": "+5% starting approval, +2% spending capacity.",
        "Conservative": "-5% starting approval, -2% spending (fiscal discipline).",
        "Libertarian": "No approval bonus, -3% spending (small government).",
        "Green": "+10% starting approval, +1% spending (climate investment).",
    }
    st.info(f"**{st.session_state.player_style}** — {style_info[st.session_state.player_style]}")

    st.markdown("---")
    st.markdown("### Official Briefing")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **Objectives:**
        - Serve a full 4-year term
        - Keep approval above 20%
        - Manage GDP, inflation, unemployment
        - Respond to crises
        """)
    with c2:
        st.markdown("""
        **Instruments:**
        - Interest rate (monetary policy)
        - Income tax (fiscal policy)
        - VAT (consumption tax)
        - Government spending (fiscal stimulus)
        """)

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("BEGIN YOUR TERM", use_container_width=True):
            if st.session_state.player_name == "":
                st.warning("Please enter your name to proceed.")
            else:
                bonuses = {
                    "Centrist": (0, 0), "Social Democrat": (5, 2), "Conservative": (-5, -2),
                    "Libertarian": (0, -3), "Green": (10, 1),
                }
                app_b, spend_b = bonuses[st.session_state.player_style]
                st.session_state.approval = level["start_approval"] + app_b
                st.session_state.spending_bonus = spend_b
                st.session_state.game_started = True
                st.rerun()
    st.stop()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Options")
    scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()))
    scenario = SCENARIOS[scenario_name]
    level = LEVELS[st.session_state.difficulty]

    st.session_state.lesson_mode = st.checkbox("Lesson Mode", value=False,
        help="Simplified guidance for first-time players.")

    with st.expander("Advanced: Model Coefficients", expanded=False):
        st.caption("Adjust how strongly each policy affects the economy.")
        coeffs = st.session_state.coeffs
        for key, label in [
            ("gdp_spending", "Spending → GDP"), ("gdp_interest", "Interest → GDP"),
            ("gdp_income_tax", "Income tax → GDP"), ("gdp_vat", "VAT → GDP"),
            ("infl_spending", "Spending → Inflation"), ("infl_interest", "Interest → Inflation"),
            ("infl_vat", "VAT → Inflation"), ("infl_income_tax", "Income tax → Inflation"),
            ("unemp_spending", "Spending → Unemployment"), ("unemp_interest", "Interest → Unemployment"),
            ("unemp_income_tax", "Income tax → Unemployment"), ("unemp_vat", "VAT → Unemployment"),
        ]:
            lo, hi = -1.0, 1.0
            coeffs[key] = st.slider(label, lo, hi, coeffs[key], 0.05)
        if st.button("Reset coefficients"):
            st.session_state.coeffs = DEFAULT_COEFFICIENTS.copy()
            st.rerun()

    with st.expander("Economics Glossary", expanded=False):
        st.caption("Key terms used in this simulation.")
        for term, definition in GLOSSARY.items():
            st.markdown(f'<div class="glossary-card"><h4>{term}</h4><p>{definition}</p></div>',
                        unsafe_allow_html=True)

# ---------- MAIN GAME ----------
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Minister", st.session_state.player_name or "—")
with c2: st.metric("Year", f"{st.session_state.year}/4")
with c3:
    ap = st.session_state.approval
    st.metric("Approval", f"{ap:.0f}%",
              delta=f"{st.session_state.approval_change:+.1f}" if st.session_state.approval_change else None)
with c4:
    if st.session_state.game_over: st.error("TERM ENDED")
    else: st.info(f"{st.session_state.difficulty} · {st.session_state.player_style}")

# Baseline
if scenario["baseline_override"] is None:
    country = st.selectbox("Starting economy", ["Poland", "Germany", "USA"], index=0)
    baseline = load_baseline(country)
else:
    country = "Scenario"
    baseline = scenario["baseline_override"]
    st.info(f"**{scenario_name}** — {scenario['description']}")

st.write(f"**Baseline:** GDP {baseline['gdp_growth']:.1f}% · Inflation {baseline['inflation']:.1f}% · "
         f"Unemployment {baseline['unemployment']:.1f}% · Real wages {baseline['real_wage_growth']:.1f}%")

if scenario["narrative"]:
    st.markdown(f"*{scenario['narrative']}*")

st.markdown("---")

# Challenge
st.subheader("Challenge Mode")
if scenario["targets"] is not None:
    st.session_state.challenge = scenario["targets"]
    ch = st.session_state.challenge
    st.write(f"GDP ≥ {ch['gdp_growth']}% · Inflation ≤ {ch['inflation']}% · Unemployment ≤ {ch['unemployment']}%")
else:
    if st.button("Generate Challenge"):
        tol = level["target_tolerance"]
        st.session_state.challenge = {
            "gdp_growth": round(baseline["gdp_growth"] + 1.0 / tol, 1),
            "inflation": round(baseline["inflation"] + 0.5 * tol, 1),
            "unemployment": round(max(1.0, baseline["unemployment"] - 1.0 * tol), 1),
        }
        st.rerun()
    if st.session_state.challenge:
        ch = st.session_state.challenge
        st.write(f"GDP ≥ {ch['gdp_growth']}% · Inflation ≤ {ch['inflation']}% · Unemployment ≤ {ch['unemployment']}%")
    else:
        st.caption("No challenge yet. Generate one for scoring.")

st.markdown("---")

# Policy sliders
if st.session_state.lesson_mode:
    st.markdown("### Lesson Mode")
    st.caption("Suggested values shown. Try lowering inflation without spiking unemployment.")
    interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 6.0, 0.05,
                              help="Higher → lower inflation, slower growth.")
    income_tax = st.slider("Income tax (%)", 0.0, 50.0, 20.0, 0.5,
                           help="Higher → less disposable income, cooler economy.")
    vat = st.slider("VAT (%)", 0.0, 30.0, 20.0, 0.5,
                    help="Higher → directly raises consumer prices.")
    gov_spending_change = st.slider("Government spending change (%)", -10.0, 10.0, 0.0, 0.1,
                                    help="Higher → more demand, more growth, more inflation.")
else:
    st.subheader("Your Policy")
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 4.25, 0.05,
                                  help="Monetary policy. Higher rates reduce inflation but slow growth.")
    with cc2:
        income_tax = st.slider("Income tax (%)", 0.0, 50.0, 19.0, 0.5,
                               help="Fiscal policy. Higher taxes reduce demand.")
    with cc3:
        vat = st.slider("VAT (%)", 0.0, 30.0, 23.0, 0.5,
                        help="Consumption tax. Higher VAT raises prices directly.")
    with cc4:
        gov_spending_change = st.slider("Gov spending change (%)", -10.0, 10.0, 2.0, 0.1,
                                        help="Fiscal stimulus. Positive values expand demand.")

run_button = False if st.session_state.game_over else st.button("RUN EXPERIMENT", use_container_width=True)

st.markdown("---")

# Run simulation
if run_button and not st.session_state.game_over:
    params = {
        "interest_rate": interest_rate, "income_tax": income_tax,
        "vat": vat, "gov_spending_change": gov_spending_change + st.session_state.spending_bonus,
    }
    st.session_state.event = generate_random_event(level["events_chance"])

    if scenario["baseline_override"] is not None:
        df = pd.read_csv("data.csv")
        if "Scenario" not in df["country"].values:
            row = {"country": "Scenario", "base_gdp_growth": baseline["gdp_growth"],
                   "base_inflation": baseline["inflation"], "base_unemployment": baseline["unemployment"],
                   "base_real_wage_growth": baseline["real_wage_growth"]}
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

    # Approval change with difficulty multiplier
    raw_change = 0.0
    raw_change += (results["gdp_growth"] - 2.0) * (3 if results["gdp_growth"] > 2.0 else 5)
    if results["inflation"] > 4.0: raw_change -= (results["inflation"] - 4.0) * 2
    elif results["inflation"] < 2.0: raw_change += 1.5
    if results["unemployment"] < 5.0: raw_change += (5.0 - results["unemployment"]) * 2.5
    else: raw_change -= (results["unemployment"] - 5.0) * 3.5

    approval_change = raw_change * level["penalty_multiplier"]
    st.session_state.approval = max(0, min(100, st.session_state.approval + approval_change))
    st.session_state.results = results
    st.session_state.approval_change = approval_change
    st.session_state.narrative = generate_narrative(results, approval_change)
    st.session_state.history.append({"year": st.session_state.year, "approval": st.session_state.approval, **results})

    if st.session_state.approval < 20 or st.session_state.year >= 4:
        st.session_state.game_over = True
    else:
        st.session_state.year += 1

# ---------- RESULTS ----------
if st.session_state.results is not None:
    res = st.session_state.results

    def render_status(label, value, change, unit="%", higher_better=True, thresholds=(0, 0)):
        cls = classify(value, thresholds[0], thresholds[1], higher_better)
        arrow = "▲" if change > 0 else "▼" if change < 0 else "●"
        return f'<div class="status-{cls}"><b>{label}: {value:.1f}{unit}</b> <span>({arrow} {change:+.1f}{unit})</span></div>'

    st.subheader("Economic Indicators")
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        st.markdown(render_status("GDP Growth", res["gdp_growth"], res["gdp_growth_change"],
                                  higher_better=True, thresholds=(3.0, 0.0)), unsafe_allow_html=True)
        st.markdown(render_status("Unemployment", res["unemployment"], res["unemployment_change"],
                                  higher_better=False, thresholds=(5.0, 7.0)), unsafe_allow_html=True)
    with gcol2:
        st.markdown(render_status("Inflation", res["inflation"], res["inflation_change"],
                                  higher_better=False, thresholds=(3.0, 5.0)), unsafe_allow_html=True)
        st.markdown(render_status("Real Wages", res["real_wage_growth"], res["real_wage_growth_change"],
                                  higher_better=True, thresholds=(1.0, 0.0)), unsafe_allow_html=True)

    if st.session_state.event:
        st.markdown("---")
        st.subheader(f"Event: {st.session_state.event['name']}")
        st.write(st.session_state.event["description"])

    if st.session_state.narrative:
        st.markdown("---")
        st.subheader("News Report")
        st.write(st.session_state.narrative)

    st.markdown("---")
    st.subheader("Baseline vs Your Policy")
    chart_df = pd.DataFrame({
        "Indicator": ["GDP growth", "Inflation", "Unemployment", "Real wages"],
        "Baseline": [baseline["gdp_growth"], baseline["inflation"], baseline["unemployment"], baseline["real_wage_growth"]],
        "Your Policy": [res["gdp_growth"], res["inflation"], res["unemployment"], res["real_wage_growth"]],
    }).set_index("Indicator")
    st.bar_chart(chart_df, height=350)
else:
    if not st.session_state.game_over:
        st.info("Adjust the policy sliders and click RUN EXPERIMENT.")

# ---------- CLOSING PAGE ----------
if st.session_state.game_over:
    st.markdown("---")
    success = st.session_state.approval >= 20
    banner_class = "banner-success" if success else "banner-fail"
    banner_title = "TERM COMPLETED" if success else "TERM ENDED — PUBLIC UPRISING"
    banner_text = (
        "You have served your nation with distinction.<br>The economy is stable. Your legacy is assured."
        if success else
        "Your economic policies have failed the nation.<br>Public trust has collapsed. History will remember this failure."
    )
    st.markdown(f"""
    <div class="banner {banner_class}">
        <h1>{banner_title}</h1>
        <div class="{'divider-gold' if success else 'divider-red'}"></div>
        <p>{banner_text}</p>
    </div>
    """, unsafe_allow_html=True)

    st.write(f"**Final Approval Rating: {st.session_state.approval:.0f}%**")
    if st.session_state.history:
        st.subheader("Approval Over Time")
        st.line_chart(pd.DataFrame(st.session_state.history)[["approval"]])

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("START NEW TERM", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ---------- TEACHER / STUDENT MATERIALS ----------
st.markdown("---")
with st.expander("📘 Teacher & Student Materials", expanded=False):
    st.markdown("""
    ### For Teachers

    **Lesson Plan: Introduction to Macroeconomic Policy (90 min)**

    1. **Warm-up (10 min)** — Introduce the three goals: growth, low inflation, low unemployment. Discuss why they can conflict.
    2. **Exploration (30 min)** — Students play EconLab on *Easy* difficulty for one full 4-year term, recording results for each year.
    3. **Discussion (15 min)** — Compare strategies. Which policy mixes produced the highest approval ratings? Why?
    4. **Challenge (25 min)** — Students replay on *Normal* difficulty using the 2022 Inflation Crisis scenario. Aim for inflation ≤ 6% and unemployment ≤ 5.5%.
    5. **Reflection (10 min)** — Students write a paragraph explaining the trade-off between inflation and unemployment (Phillips curve).

    ---

    ### For Students

    **Key concepts covered in EconLab:**

    - **Monetary policy** — how central bank interest rates influence inflation and growth.
    - **Fiscal policy** — how government spending and taxation affect demand.
    - **The Phillips curve** — the short-run trade-off between inflation and unemployment.
    - **Okun's law** — the relationship between GDP and unemployment.
    - **Real vs nominal** — why real wages (adjusted for inflation) matter more than nominal ones.

    **Exercises:**

    1. Set interest rate to 10%. What happens to inflation? To unemployment? Explain.
    2. Try to reach 3% inflation with 4% unemployment. Is it possible? What were your policies?
    3. Play the 2022 Inflation Crisis scenario. Why is it harder to fight inflation without causing recession?
    4. Which political affiliation gives the best starting conditions? Does it change the outcome?

    ---

    ### Homework / Research Questions

    - Compare the Balcerowicz Plan (1989) with today's inflation crisis. What lessons can be drawn?
    - Research Poland's actual interest rate decisions in 2022-2023. Did they match the "optimal" strategy in EconLab?
    - Should governments always aim for a balanced budget? Use EconLab to test arguments for and against.

    ---

    *Tip: All sliders include hover-over explanations. The **Economics Glossary** in the sidebar defines every key term used.*
    """)

# ---------- ANALYTICS NOTE ----------
# Note: Streamlit Cloud automatically collects basic usage analytics
# (page views, session counts, unique visitors). To view them:
#   1. Go to share.streamlit.io
#   2. Click your app
#   3. Click "Analytics" in the sidebar
# For custom event tracking, add this to your Streamlit Cloud secrets
# and inject a Google Analytics script via st.markdown(). See the README for details.
