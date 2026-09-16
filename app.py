import streamlit as st
import pandas as pd
import random
from economic_model import simulate_economy, load_baseline, DEFAULT_COEFFICIENTS

st.set_page_config(page_title="EconLab", layout="wide")

# --- Simple styles ---
st.markdown("""
<style>
.title { text-align:center; font-size:40px; font-weight:bold; letter-spacing:3px; }
.sub   { text-align:center; font-size:16px; color:#888; margin-bottom:20px; }
.good  { background:#0d3b0d; padding:12px; border-left:5px solid #4caf50; border-radius:6px; margin:6px 0; color:#fff; }
.warn  { background:#3b2f0d; padding:12px; border-left:5px solid #ffb300; border-radius:6px; margin:6px 0; color:#fff; }
.bad   { background:#3b0d0d; padding:12px; border-left:5px solid #f44336; border-radius:6px; margin:6px 0; color:#fff; }
.banner { text-align:center; padding:35px 25px; border-radius:15px; margin:20px 0;
          background:linear-gradient(135deg,#1a1a2e,#0f3460); color:#fff; }
.banner h1 { color:#c9a84c; font-size:28px; margin:0 0 12px 0; }
.banner p  { color:#e0e0e0; font-size:16px; margin:0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">ECONLAB</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">MINISTRY OF FINANCE</div>', unsafe_allow_html=True)

# --- Session state ---
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

# --- Levels ---
LEVELS = {
    "Easy":   {"start": 70.0, "mult": 0.5, "events": 0.25, "tol": 1.5,
               "desc": "Relaxed targets and generous starting support. Good for beginners."},
    "Normal": {"start": 60.0, "mult": 1.0, "events": 0.40, "tol": 1.0,
               "desc": "Balanced challenge. Standard conditions."},
    "Hard":   {"start": 55.0, "mult": 1.4, "events": 0.55, "tol": 0.7,
               "desc": "Tighter margins and more frequent crises."},
    "Crisis": {"start": 50.0, "mult": 1.8, "events": 0.70, "tol": 0.5,
               "desc": "Extreme conditions. Events are frequent and punishing."},
}

# --- Polish scenarios ---
SCENARIOS = {
    "None (baseline)": {
        "override": None, "targets": None,
        "desc": "Standard country baseline. Choose your own path.",
        "story": "",
    },
    "1989 - Balcerowicz Plan": {
        "override": {"gdp_growth": -3.0, "inflation": 60.0, "unemployment": 6.5, "real_wage_growth": -10.0},
        "targets": {"gdp_growth": 1.0, "inflation": 15.0, "unemployment": 10.0},
        "desc": "Post-communist shock therapy. Hyperinflation and collapsing output.",
        "story": "You inherit an economy on the brink. Stabilize without destroying hope.",
    },
    "2004 - EU Accession": {
        "override": {"gdp_growth": 5.0, "inflation": 3.5, "unemployment": 19.0, "real_wage_growth": 1.0},
        "targets": {"gdp_growth": 4.0, "inflation": 3.0, "unemployment": 12.0},
        "desc": "Poland joins the EU. Growth accelerates but unemployment stays high.",
        "story": "The EU flag flies over Warsaw. Manage the boom without overheating.",
    },
    "2008 - Global Financial Crisis": {
        "override": {"gdp_growth": -1.0, "inflation": 4.2, "unemployment": 9.5, "real_wage_growth": -1.0},
        "targets": {"gdp_growth": 2.0, "inflation": 2.5, "unemployment": 8.0},
        "desc": "Global credit freeze. Poland narrowly avoided recession.",
        "story": "Lehman Brothers has collapsed. Can you keep Poland out of recession?",
    },
    "2020 - COVID-19 Pandemic": {
        "override": {"gdp_growth": -2.5, "inflation": 3.4, "unemployment": 6.5, "real_wage_growth": -1.0},
        "targets": {"gdp_growth": 3.0, "inflation": 3.5, "unemployment": 5.0},
        "desc": "Lockdowns and supply-chain disruption.",
        "story": "The pandemic has emptied the streets. Protect lives and livelihoods.",
    },
    "2022 - Inflation Crisis": {
        "override": {"gdp_growth": 1.5, "inflation": 16.0, "unemployment": 3.0, "real_wage_growth": -4.0},
        "targets": {"gdp_growth": 2.0, "inflation": 6.0, "unemployment": 5.5},
        "desc": "War in Ukraine and energy shock. Inflation hits double digits.",
        "story": "Energy prices have exploded. The NBP must act — but tightening risks recession.",
    },
}

# --- Glossary ---
GLOSSARY = {
    "GDP (Gross Domestic Product)": "Total value of goods and services produced. Growth above 2-3% is considered healthy.",
    "Inflation": "Rate at which prices rise. Central banks typically target 2%. High inflation erodes purchasing power.",
    "Unemployment": "Percentage of labor force seeking work. 4-5% is often 'full employment'.",
    "Interest Rate": "Central bank's cost of borrowing. Higher rates reduce inflation but slow growth.",
    "VAT": "Consumption tax. Higher VAT raises consumer prices directly.",
    "Income Tax": "Tax on personal earnings. Higher tax reduces disposable income.",
    "Government Spending": "Public expenditure. Increases act as fiscal stimulus (Keynesian multiplier).",
    "Budget Deficit": "Gap when spending exceeds revenue. Stimulates short-term but requires borrowing.",
    "Public Debt": "Accumulated deficits as share of GDP. High debt can slow long-term growth.",
    "Real Wages": "Wages adjusted for inflation. Positive growth means purchasing power is rising.",
    "Fiscal Multiplier": "Ratio of GDP change to government spending change. In Poland, ~0.4-0.8.",
    "Okun's Law": "1% rise in unemployment ↔ ~2% fall in GDP.",
    "Phillips Curve": "Short-run trade-off between unemployment and inflation.",
    "Stagflation": "High inflation + low growth + high unemployment. Rare and hard to fix.",
    "Crowding Out": "High government borrowing raising rates and reducing private investment.",
}

# --- Helpers ---
def classify(v, good, warn, higher_better=True):
    if higher_better:
        return "good" if v >= good else "warn" if v >= warn else "bad"
    return "good" if v <= good else "warn" if v <= warn else "bad"


def random_event(chance):
    pool = [
        {"name": "Global Pandemic", "eff": {"gdp": -2.0, "inf": 0.5, "une": 2.0},
         "text": "A pandemic hits. Lockdowns hurt the economy."},
        {"name": "Oil Price Spike", "eff": {"gdp": -0.5, "inf": 1.5, "une": 0.5},
         "text": "Oil prices skyrocket."},
        {"name": "Tech Boom", "eff": {"gdp": 1.5, "inf": -0.2, "une": -1.0},
         "text": "Technology boom boosts productivity."},
        {"name": "Trade Deal", "eff": {"gdp": 1.0, "inf": -0.3, "une": -0.5},
         "text": "A trade deal opens new markets."},
        {"name": "Natural Disaster", "eff": {"gdp": -1.0, "inf": 0.3, "une": 0.8},
         "text": "A disaster damages infrastructure."},
        {"name": "Investment Surge", "eff": {"gdp": 1.2, "inf": 0.1, "une": -0.8},
         "text": "Foreign investors arrive."},
    ]
    return random.choice(pool) if random.random() < chance else None


def narrative(res, chg):
    p = []
    if res["gdp_growth"] > 4.0: p.append("The economy is booming.")
    elif res["gdp_growth"] > 2.0: p.append("The economy is growing steadily.")
    elif res["gdp_growth"] > 0: p.append("Growth is sluggish.")
    else: p.append("The economy is shrinking. Protests erupt.")

    if res["inflation"] > 8.0: p.append("Inflation is out of control.")
    elif res["inflation"] > 4.0: p.append("Prices are rising quickly.")
    elif res["inflation"] < 1.0: p.append("Very low inflation — deflation fears.")
    else: p.append("Inflation is moderate.")

    if res["unemployment"] < 4.0: p.append("Almost everyone has a job.")
    elif res["unemployment"] < 7.0: p.append("Unemployment is manageable.")
    else: p.append("High unemployment fuels unrest.")

    if chg > 5: p.append("Your approval is soaring.")
    elif chg > 0: p.append("The public is pleased.")
    elif chg > -5: p.append("Some voters are unhappy.")
    else: p.append("Your approval is plummeting. Protests grow.")
    return " ".join(p)


# ---------- OPENING ----------
if not st.session_state.game_started:
    st.markdown("""
    <div class="banner">
        <h1>MINISTRY OF FINANCE</h1>
        <p>
            You are the <strong style="color:#c9a84c;">Minister of Finance</strong>.<br>
            The nation's economic future rests in your hands.<br>
            <em>Can you lead the country through 4 years of challenges?</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Official Appointment Form")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.player_name = st.text_input("Minister's Name",
                                                     value=st.session_state.player_name,
                                                     placeholder="Enter your name...")
    with c2:
        st.session_state.player_style = st.selectbox("Political Affiliation",
            ["Centrist", "Social Democrat", "Conservative", "Libertarian", "Green"])

    st.markdown("### Difficulty Level")
    st.caption("Choose your challenge level.")
    diff_cols = st.columns(4)
    for i, lvl in enumerate(LEVELS):
        with diff_cols[i]:
            label = f"{lvl} ●" if st.session_state.difficulty == lvl else lvl
            if st.button(label, use_container_width=True, key=f"lvl_{lvl}"):
                st.session_state.difficulty = lvl
                st.rerun()

    lv = LEVELS[st.session_state.difficulty]
    st.info(f"**{st.session_state.difficulty}** — {lv['desc']}  |  Starting approval: {lv['start']:.0f}%  |  Event chance: {int(lv['events']*100)}%")

    style_info = {
        "Centrist": "Balanced. No bonuses.",
        "Social Democrat": "+5% approval, +2% spending capacity.",
        "Conservative": "-5% approval, -2% spending (austerity).",
        "Libertarian": "No bonus, -3% spending (small government).",
        "Green": "+10% approval, +1% spending (climate).",
    }
    st.info(f"**{st.session_state.player_style}** — {style_info[st.session_state.player_style]}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Objectives:**\n- Serve 4 years\n- Keep approval above 20%\n- Manage GDP, inflation, unemployment")
    with c2:
        st.markdown("**Instruments:**\n- Interest rate\n- Income tax\n- VAT\n- Government spending")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("BEGIN YOUR TERM", use_container_width=True):
            if st.session_state.player_name.strip() == "":
                st.warning("Please enter your name.")
            else:
                bonuses = {"Centrist": (0, 0), "Social Democrat": (5, 2),
                           "Conservative": (-5, -2), "Libertarian": (0, -3), "Green": (10, 1)}
                ab, sb = bonuses[st.session_state.player_style]
                st.session_state.approval = lv["start"] + ab
                st.session_state.spending_bonus = sb
                st.session_state.game_started = True
                st.rerun()
    st.stop()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Options")
    scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()))
    scenario = SCENARIOS[scenario_name]
    lv = LEVELS[st.session_state.difficulty]

    st.session_state.lesson_mode = st.checkbox("Lesson Mode", value=False)

    with st.expander("Advanced: Model Coefficients"):
        st.caption("Adjust sensitivity of the model.")
        coeffs = st.session_state.coeffs
        coeffs["gdp_spending"] = st.slider("Spending → GDP", -1.0, 1.0, coeffs["gdp_spending"], 0.05)
        coeffs["gdp_interest"] = st.slider("Interest → GDP", -1.0, 1.0, coeffs["gdp_interest"], 0.05)
        coeffs["gdp_income_tax"] = st.slider("Income tax → GDP", -1.0, 1.0, coeffs["gdp_income_tax"], 0.05)
        coeffs["gdp_vat"] = st.slider("VAT → GDP", -1.0, 1.0, coeffs["gdp_vat"], 0.05)
        coeffs["infl_spending"] = st.slider("Spending → Inflation", -1.0, 1.0, coeffs["infl_spending"], 0.05)
        coeffs["infl_interest"] = st.slider("Interest → Inflation", -1.0, 1.0, coeffs["infl_interest"], 0.05)
        coeffs["infl_vat"] = st.slider("VAT → Inflation", -1.0, 1.0, coeffs["infl_vat"], 0.05)
        coeffs["infl_income_tax"] = st.slider("Income tax → Inflation", -1.0, 1.0, coeffs["infl_income_tax"], 0.05)
        coeffs["unemp_spending"] = st.slider("Spending → Unemployment", -1.0, 1.0, coeffs["unemp_spending"], 0.05)
        coeffs["unemp_interest"] = st.slider("Interest → Unemployment", -1.0, 1.0, coeffs["unemp_interest"], 0.05)
        coeffs["unemp_income_tax"] = st.slider("Income tax → Unemployment", -1.0, 1.0, coeffs["unemp_income_tax"], 0.05)
        coeffs["unemp_vat"] = st.slider("VAT → Unemployment", -1.0, 1.0, coeffs["unemp_vat"], 0.05)
        if st.button("Reset coefficients"):
            st.session_state.coeffs = DEFAULT_COEFFICIENTS.copy()
            st.rerun()

    with st.expander("Economics Glossary"):
        for term, definition in GLOSSARY.items():
            st.markdown(f"**{term}**  \n{definition}")

# ---------- STATUS BAR ----------
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Minister", st.session_state.player_name or "—")
with c2: st.metric("Year", f"{st.session_state.year}/4")
with c3:
    ap = st.session_state.approval
    delta = st.session_state.approval_change if st.session_state.approval_change != 0 else None
    st.metric("Approval", f"{ap:.0f}%", delta=delta)
with c4:
    if st.session_state.game_over: st.error("TERM ENDED")
    else: st.info(f"{st.session_state.difficulty} · {st.session_state.player_style}")

# ---------- BASELINE ----------
if scenario["override"] is None:
    country = st.selectbox("Starting economy", ["Poland", "Germany", "USA"], index=0)
    try:
        baseline = load_baseline(country)
    except Exception as e:
        st.error(f"Error loading baseline for {country}: {e}")
        st.info("Please verify data.csv has the correct format.")
        st.stop()
else:
    country = "Scenario"
    baseline = scenario["override"]
    st.info(f"**{scenario_name}** — {scenario['desc']}")

st.write(f"**Baseline:** GDP {baseline['gdp_growth']:.1f}% · Inflation {baseline['inflation']:.1f}% · "
         f"Unemployment {baseline['unemployment']:.1f}% · Real wages {baseline['real_wage_growth']:.1f}%")
if scenario["story"]:
    st.markdown(f"*{scenario['story']}*")

# ---------- CHALLENGE ----------
st.markdown("---")
st.subheader("Challenge")
if scenario["targets"] is not None:
    st.session_state.challenge = scenario["targets"]
    ch = st.session_state.challenge
    st.write(f"GDP ≥ {ch['gdp_growth']}% · Inflation ≤ {ch['inflation']}% · Unemployment ≤ {ch['unemployment']}%")
else:
    if st.button("Generate Challenge"):
        tol = lv["tol"]
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
        st.caption("No challenge yet.")

# ---------- SLIDERS ----------
st.markdown("---")
if st.session_state.lesson_mode:
    st.markdown("### Lesson Mode")
    st.caption("Suggested values. Try lowering inflation without spiking unemployment.")
    interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 6.0, 0.05,
                              help="Higher → lower inflation, slower growth.")
    income_tax = st.slider("Income tax (%)", 0.0, 50.0, 20.0, 0.5,
                           help="Higher → less disposable income.")
    vat = st.slider("VAT (%)", 0.0, 30.0, 20.0, 0.5,
                    help="Higher → raises consumer prices.")
    gov_spending_change = st.slider("Government spending change (%)", -10.0, 10.0, 0.0, 0.1,
                                    help="Higher → more demand, more growth.")
else:
    st.subheader("Your Policy")
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 4.25, 0.05,
                                  help="Monetary policy. Higher → reduces inflation but slows growth.")
    with cc2:
        income_tax = st.slider("Income tax (%)", 0.0, 50.0, 19.0, 0.5,
                               help="Fiscal policy. Higher → less demand.")
    with cc3:
        vat = st.slider("VAT (%)", 0.0, 30.0, 23.0, 0.5,
                        help="Consumption tax. Higher → raises prices directly.")
    with cc4:
        gov_spending_change = st.slider("Gov spending change (%)", -10.0, 10.0, 2.0, 0.1,
                                        help="Fiscal stimulus. Positive → more demand.")

if st.session_state.game_over:
    run_button = False
    st.warning("Your term is over.")
else:
    run_button = st.button("RUN EXPERIMENT", use_container_width=True)

# ---------- SIMULATION ----------
st.markdown("---")
if run_button:
    params = {"interest_rate": interest_rate, "income_tax": income_tax,
              "vat": vat, "gov_spending_change": gov_spending_change + st.session_state.spending_bonus}
    st.session_state.event = random_event(lv["events"])

    try:
        if scenario["override"] is not None:
            # Add scenario row to CSV if missing
            df = pd.read_csv("data.csv")
            if "Scenario" not in df["country"].values:
                row = {"country": "Scenario", "base_gdp_growth": baseline["gdp_growth"],
                       "base_inflation": baseline["inflation"], "base_unemployment": baseline["unemployment"],
                       "base_real_wage_growth": baseline["real_wage_growth"]}
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv("data.csv", index=False)
            res = simulate_economy("Scenario", params, st.session_state.coeffs)
        else:
            res = simulate_economy(country, params, st.session_state.coeffs)

        if st.session_state.event:
            res["gdp_growth"] += st.session_state.event["eff"]["gdp"]
            res["inflation"] += st.session_state.event["eff"]["inf"]
            res["unemployment"] += st.session_state.event["eff"]["une"]
            res["gdp_growth_change"] = res["gdp_growth"] - baseline["gdp_growth"]
            res["inflation_change"] = res["inflation"] - baseline["inflation"]
            res["unemployment_change"] = res["unemployment"] - baseline["unemployment"]

        raw = 0.0
        raw += (res["gdp_growth"] - 2.0) * (3 if res["gdp_growth"] > 2.0 else 5)
        if res["inflation"] > 4.0: raw -= (res["inflation"] - 4.0) * 2
        elif res["inflation"] < 2.0: raw += 1.5
        if res["unemployment"] < 5.0: raw += (5.0 - res["unemployment"]) * 2.5
        else: raw -= (res["unemployment"] - 5.0) * 3.5

        change = raw * lv["mult"]
        st.session_state.approval = max(0, min(100, st.session_state.approval + change))
        st.session_state.results = res
        st.session_state.approval_change = change
        st.session_state.narrative = narrative(res, change)
        st.session_state.history.append({"year": st.session_state.year,
                                         "approval": st.session_state.approval, **res})

        if st.session_state.approval < 20 or st.session_state.year >= 4:
            st.session_state.game_over = True
        else:
            st.session_state.year += 1
    except Exception as e:
        st.error(f"Simulation error: {e}")

# ---------- RESULTS ----------
if st.session_state.results is not None:
    res = st.session_state.results

    def status_card(label, value, change, higher_better=True, good=0, warn=0):
        cls = classify(value, good, warn, higher_better)
        arrow = "▲" if change > 0 else "▼" if change < 0 else "●"
        return f'<div class="{cls}"><b>{label}: {value:.1f}%</b> ({arrow} {change:+.1f}%)</div>'

    st.subheader("Economic Indicators")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(status_card("GDP Growth", res["gdp_growth"], res["gdp_growth_change"], True, 3.0, 0.0), unsafe_allow_html=True)
        st.markdown(status_card("Unemployment", res["unemployment"], res["unemployment_change"], False, 5.0, 7.0), unsafe_allow_html=True)
    with g2:
        st.markdown(status_card("Inflation", res["inflation"], res["inflation_change"], False, 3.0, 5.0), unsafe_allow_html=True)
        st.markdown(status_card("Real Wages", res["real_wage_growth"], res["real_wage_growth_change"], True, 1.0, 0.0), unsafe_allow_html=True)

    if st.session_state.event:
        st.markdown("---")
        st.subheader(f"Event: {st.session_state.event['name']}")
        st.write(st.session_state.event["text"])

    if st.session_state.narrative:
        st.markdown("---")
        st.subheader("News Report")
        st.write(st.session_state.narrative)

    st.markdown("---")
    st.subheader("Baseline vs Your Policy")
    chart = pd.DataFrame({
        "Indicator": ["GDP", "Inflation", "Unemployment", "Real wages"],
        "Baseline": [baseline["gdp_growth"], baseline["inflation"], baseline["unemployment"], baseline["real_wage_growth"]],
        "Your Policy": [res["gdp_growth"], res["inflation"], res["unemployment"], res["real_wage_growth"]],
    }).set_index("Indicator")
    st.bar_chart(chart, height=320)
else:
    if not st.session_state.game_over:
        st.info("Adjust the sliders and click RUN EXPERIMENT.")

# ---------- CLOSING ----------
if st.session_state.game_over:
    st.markdown("---")
    success = st.session_state.approval >= 20
    title = "TERM COMPLETED" if success else "TERM ENDED — PUBLIC UPRISING"
    text = ("You served your nation with distinction. Your legacy is assured."
            if success else
            "Your policies failed the nation. History will remember this.")
    color = "#5cd65c" if success else "#ff5252"
    st.markdown(f'<div class="banner"><h1 style="color:{color}">{title}</h1><p>{text}</p></div>',
                unsafe_allow_html=True)
    st.write(f"**Final Approval: {st.session_state.approval:.0f}%**")
    if st.session_state.history:
        st.line_chart(pd.DataFrame(st.session_state.history)[["approval"]])
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("START NEW TERM", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ---------- TEACHER / STUDENT MATERIALS ----------
st.markdown("---")
with st.expander("Teacher & Student Materials"):
    st.markdown("""
    ### For Teachers — Lesson Plan (90 min)

    1. **Warm-up (10 min)** — Introduce the three goals: growth, low inflation, low unemployment. Discuss conflicts.
    2. **Exploration (30 min)** — Students play on *Easy* for one full 4-year term, recording results.
    3. **Discussion (15 min)** — Compare strategies. Which policy mixes gave highest approval? Why?
    4. **Challenge (25 min)** — Replay on *Normal* using the 2022 Inflation Crisis scenario. Target: inflation ≤ 6%, unemployment ≤ 5.5%.
    5. **Reflection (10 min)** — Write a paragraph on the inflation–unemployment trade-off (Phillips curve).

    ### For Students — Key Concepts

    - **Monetary policy** — interest rates → inflation and growth
    - **Fiscal policy** — spending and taxes → demand
    - **Phillips curve** — inflation vs unemployment
    - **Okun's law** — GDP vs unemployment
    - **Real vs nominal** — wages adjusted for inflation

    ### Exercises

    1. Set interest rate to 10%. What happens to inflation and unemployment? Explain.
    2. Can you reach 3% inflation and 4% unemployment together? What policies did you use?
    3. Play 2022 Inflation Crisis. Why is fighting inflation harder without causing recession?
    4. Compare political affiliations — does the starting bonus change the outcome?

    ### Homework

    - Compare the Balcerowicz Plan (1989) with today's inflation crisis. What lessons apply?
    - Research Poland's actual NBP rate decisions in 2022-23. Did they match your optimal strategy?
    - Should governments always balance the budget? Test arguments in EconLab.
    """)
