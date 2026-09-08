import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
        font-size: 48px;
        font-weight: bold;
        letter-spacing: 3px;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        font-size: 20px;
        color: #666;
        margin-bottom: 30px;
    }
    .result-label {
        font-weight: bold;
        font-size: 18px;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        border-bottom: 1px dotted #999;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .opening-banner {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin: 20px 0;
    }
    .opening-banner h1 {
        color: white;
        margin: 0;
    }
    .opening-banner p {
        color: #f0f0f0;
        font-size: 18px;
        margin-top: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="main-title">ECONLAB</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">EXPERIMENT WITH THE ECONOMY</div>', unsafe_allow_html=True)

# Initialize session state
for key in ["results", "challenge", "lesson_mode", "coeffs",
            "approval", "year", "game_over", "history", "event",
            "game_started", "player_name", "player_style",
            "narrative", "approval_change", "spending_bonus"]:
    if key not in st.session_state:
        if key == "coeffs":
            st.session_state[key] = DEFAULT_COEFFICIENTS.copy()
        elif key == "approval":
            st.session_state[key] = 50.0
        elif key == "year":
            st.session_state[key] = 1
        elif key == "game_over":
            st.session_state[key] = False
        elif key == "history":
            st.session_state[key] = []
        elif key == "event":
            st.session_state[key] = None
        elif key == "game_started":
            st.session_state[key] = False
        elif key == "player_name":
            st.session_state[key] = ""
        elif key == "player_style":
            st.session_state[key] = "Centrist"
        elif key == "spending_bonus":
            st.session_state[key] = 0
        else:
            st.session_state[key] = None

# ---- SCENARIO DEFINITIONS ----
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

# ---- RANDOM EVENTS ----
def generate_random_event():
    """Generate a random economic event that affects the simulation."""
    events = [
        {
            "name": "Global Pandemic",
            "effect": {"gdp_growth": -2.0, "inflation": 0.5, "unemployment": 2.0},
            "description": "A global pandemic hits! Lockdowns hurt the economy."
        },
        {
            "name": "Oil Price Spike",
            "effect": {"gdp_growth": -0.5, "inflation": 1.5, "unemployment": 0.5},
            "description": "Oil prices skyrocket due to geopolitical tensions."
        },
        {
            "name": "Tech Boom",
            "effect": {"gdp_growth": 1.5, "inflation": -0.2, "unemployment": -1.0},
            "description": "A new technology boom boosts productivity!"
        },
        {
            "name": "Trade Deal Signed",
            "effect": {"gdp_growth": 1.0, "inflation": -0.3, "unemployment": -0.5},
            "description": "A major trade deal opens new markets for your country."
        },
        {
            "name": "Natural Disaster",
            "effect": {"gdp_growth": -1.0, "inflation": 0.3, "unemployment": 0.8},
            "description": "A natural disaster damages infrastructure."
        },
        {
            "name": "Foreign Investment Surge",
            "effect": {"gdp_growth": 1.2, "inflation": 0.1, "unemployment": -0.8},
            "description": "Foreign investors flock to your country."
        }
    ]
    
    # 40% chance of an event occurring
    if random.random() < 0.4:
        return random.choice(events)
    return None

# ---- NARRATIVE GENERATOR ----
def generate_narrative(res, approval_change):
    """Generate a story based on the simulation results."""
    narrative = []
    
    # GDP Growth narrative
    if res["gdp_growth"] > 4.0:
        narrative.append("Your economy is booming! Businesses are expanding and new jobs are everywhere.")
    elif res["gdp_growth"] > 2.0:
        narrative.append("The economy is growing steadily. People are cautiously optimistic.")
    elif res["gdp_growth"] > 0:
        narrative.append("Growth is sluggish. Many families are struggling to make ends meet.")
    else:
        narrative.append("The economy is shrinking! Protests are breaking out in major cities.")
    
    # Inflation narrative
    if res["inflation"] > 8.0:
        narrative.append("Inflation is out of control! People rush to buy goods before prices rise again.")
    elif res["inflation"] > 4.0:
        narrative.append("Prices are rising quickly. Your citizens are feeling the pinch at the grocery store.")
    elif res["inflation"] < 1.0:
        narrative.append("Inflation is very low. Some economists worry about deflation.")
    else:
        narrative.append("Inflation is moderate. The central bank seems satisfied.")
    
    # Unemployment narrative
    if res["unemployment"] < 4.0:
        narrative.append("Almost everyone who wants a job has one. Employers are competing for workers.")
    elif res["unemployment"] < 7.0:
        narrative.append("Unemployment is manageable, but some regions are struggling.")
    else:
        narrative.append("High unemployment is causing social unrest. Young people are especially affected.")
    
    # Approval rating narrative
    if approval_change > 5:
        narrative.append("Your approval rating is soaring! You're being called a hero in the newspapers.")
    elif approval_change > 0:
        narrative.append("The public seems pleased with your policies.")
    elif approval_change > -5:
        narrative.append("Some voters are unhappy. Opposition parties are gaining support.")
    else:
        narrative.append("Your approval rating is plummeting! Protests are growing outside your office.")
    
    return " ".join(narrative)

# ---- OPENING PAGE ----
if not st.session_state.game_started:
    st.markdown("---")
    
    # Dramatic opening banner
    st.markdown("""
    <div class="opening-banner">
        <h1>WELCOME TO POLITICS</h1>
        <p>
            You have just been appointed as the <strong>Minister of Finance</strong>.<br>
            The economy is in your hands. The people are watching.<br>
            <strong>Can you survive 4 years without causing an uprising?</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Character creation
    st.subheader("Create Your Political Persona")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.player_name = st.text_input(
            "Your Name:",
            value=st.session_state.player_name,
            placeholder="Enter your name...",
            help="This is how you'll be addressed in the game."
        )
    
    with col2:
        st.session_state.player_style = st.selectbox(
            "Political Style:",
            ["Centrist", "Social Democrat", "Conservative", "Libertarian", "Green"],
            help="Your political style affects your starting conditions and how voters react."
        )
    
    # Style descriptions
    style_info = {
        "Centrist": "Balanced approach. You start with 50% approval and moderate economic indicators.",
        "Social Democrat": "You promise strong welfare programs. Start with higher spending but higher taxes.",
        "Conservative": "You promise fiscal discipline. Start with lower spending but lower growth.",
        "Libertarian": "You promise minimal government. Start with lower taxes but weaker safety net.",
        "Green": "You promise environmental investment. Start with new green spending but higher costs."
    }
    
    st.info(f"**{st.session_state.player_style}:** {style_info[st.session_state.player_style]}")
    
    st.markdown("---")
    
    # Mission briefing
    st.subheader("Your Mission")
    st.markdown("""
    - **Serve 4 years** as Minister of Finance
    - **Keep approval rating above 20%** (or you'll be overthrown!)
    - **Manage the economy**: GDP growth, inflation, unemployment
    - **Handle random events**: pandemics, oil crises, trade wars
    - **Make tough choices** with interest rates, taxes, and spending
    
    *Every year, you'll make policy decisions and see the results.*
    *The people will judge you. Will you be a hero or a tyrant?*
    """)
    
    st.markdown("---")
    
    # Start button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("START YOUR TERM", use_container_width=True, type="primary"):
            if st.session_state.player_name == "":
                st.warning("Please enter your name first!")
            else:
                # Apply starting modifiers based on political style
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
                
                # Start the game
                st.session_state.game_started = True
                st.success(f"Good luck, {st.session_state.player_name}! The nation awaits.")
                st.balloons()
                st.experimental_rerun()
    
    # Stop here - don't show the rest of the app
    st.stop()

# ---- SIDEBAR ----
with st.sidebar:
    st.header("Options")
    scenario_name = st.selectbox(
        "Scenario",
        list(SCENARIOS.keys()),
        help="Choose a predefined economic scenario to simulate.",
    )
    scenario = SCENARIOS[scenario_name]

    # Lesson mode toggle
    lesson_mode = st.checkbox("Lesson Mode", value=False,
                              help="Turn on guided instructions. Some sliders will be locked.")
    st.session_state.lesson_mode = lesson_mode

    # Adjustable coefficients (advanced)
    with st.expander("Advanced: Model Coefficients", expanded=False):
        st.write("Change how strongly each policy affects the economy.")
        coeffs = st.session_state.coeffs
        
        st.markdown("**GDP growth**")
        coeffs["gdp_spending"] = st.slider("Spending effect on GDP", -1.0, 1.0, coeffs["gdp_spending"], 0.05)
        coeffs["gdp_interest"] = st.slider("Interest effect on GDP", -1.0, 1.0, coeffs["gdp_interest"], 0.05)
        coeffs["gdp_income_tax"] = st.slider("Income tax effect on GDP", -1.0, 1.0, coeffs["gdp_income_tax"], 0.05)
        coeffs["gdp_vat"] = st.slider("VAT effect on GDP", -1.0, 1.0, coeffs["gdp_vat"], 0.05)

        st.markdown("**Inflation**")
        coeffs["infl_spending"] = st.slider("Spending effect on inflation", -1.0, 1.0, coeffs["infl_spending"], 0.05)
        coeffs["infl_interest"] = st.slider("Interest effect on inflation", -1.0, 1.0, coeffs["infl_interest"], 0.05)
        coeffs["infl_vat"] = st.slider("VAT effect on inflation", -1.0, 1.0, coeffs["infl_vat"], 0.05)
        coeffs["infl_income_tax"] = st.slider("Income tax effect on inflation", -1.0, 1.0, coeffs["infl_income_tax"], 0.05)

        st.markdown("**Unemployment**")
        coeffs["unemp_spending"] = st.slider("Spending effect on unemployment", -1.0, 1.0, coeffs["unemp_spending"], 0.05)
        coeffs["unemp_interest"] = st.slider("Interest effect on unemployment", -1.0, 1.0, coeffs["unemp_interest"], 0.05)
        coeffs["unemp_income_tax"] = st.slider("Income tax effect on unemployment", -1.0, 1.0, coeffs["unemp_income_tax"], 0.05)
        coeffs["unemp_vat"] = st.slider("VAT effect on unemployment", -1.0, 1.0, coeffs["unemp_vat"], 0.05)

        st.markdown("**Real wage growth**")
        coeffs["wage_gdp_growth"] = st.slider("GDP growth effect on wages", -1.0, 1.0, coeffs["wage_gdp_growth"], 0.05)
        coeffs["wage_inflation"] = st.slider("Inflation effect on wages", -1.0, 1.0, coeffs["wage_inflation"], 0.05)
        coeffs["wage_spending"] = st.slider("Spending effect on wages", -1.0, 1.0, coeffs["wage_spending"], 0.05)
        coeffs["wage_interest"] = st.slider("Interest effect on wages", -1.0, 1.0, coeffs["wage_interest"], 0.05)

        if st.button("Reset coefficients to default"):
            st.session_state.coeffs = DEFAULT_COEFFICIENTS.copy()
            st.experimental_rerun()

# ---- MAIN AREA ----
# Game status display
st.markdown("---")
col_status1, col_status2, col_status3, col_status4 = st.columns(4)

with col_status1:
    st.metric("Minister", st.session_state.player_name)

with col_status2:
    st.metric("Year in Office", f"{st.session_state.year}/4")

with col_status3:
    if st.session_state.approval >= 60:
        approval_emoji = "😊"
    elif st.session_state.approval >= 40:
        approval_emoji = "😐"
    else:
        approval_emoji = "😟"
    st.metric("👍 Approval Rating", f"{approval_emoji} {st.session_state.approval:.0f}%")

with col_status4:
    if st.session_state.game_over:
        st.error("GAME OVER")
    else:
        st.info(f"{st.session_state.player_style}")

# Country selection (unless scenario overrides baseline)
if scenario["baseline_override"] is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        country = st.selectbox(
            "Choose your starting economy",
            ["Poland", "Germany", "USA"],
            index=0,
            help="Select a country to use its baseline economic indicators.",
        )
    baseline = load_baseline(country)
else:
    country = "Scenario"
    baseline = scenario["baseline_override"]
    st.info(f"Using scenario baseline: {scenario['description']}")

# Display baseline
st.write(f"**Baseline indicators for {country}:**")
st.write(
    f"GDP growth: {baseline['gdp_growth']:.1f}% | Inflation: {baseline['inflation']:.1f}% | "
    f"Unemployment: {baseline['unemployment']:.1f}% | Real wage growth: {baseline['real_wage_growth']:.1f}%"
)

if scenario["narrative"]:
    st.markdown(f"*{scenario['narrative']}*")

st.markdown("---")

# ---- CHALLENGE / TARGETS ----
st.subheader("Challenge Mode")

# If scenario has predefined targets, use them
if scenario["targets"] is not None:
    st.session_state.challenge = scenario["targets"]
    st.write("This scenario has fixed targets:")
    ch = st.session_state.challenge
    st.write(f"**GDP growth ≥ {ch['gdp_growth']}%**")
    st.write(f"**Inflation ≤ {ch['inflation']}%**")
    st.write(f"**Unemployment ≤ {ch['unemployment']}%**")
else:
    col_ch1, col_ch2, col_ch3 = st.columns([1, 1, 1])
    with col_ch1:
        if st.button("Generate Challenge"):
            target_gdp = round(random.uniform(baseline["gdp_growth"] + 1.0, baseline["gdp_growth"] + 3.0), 1)
            target_inflation = round(random.uniform(max(0.5, baseline["inflation"] - 1.5), baseline["inflation"] + 0.5), 1)
            target_unemployment = round(random.uniform(max(1.0, baseline["unemployment"] - 2.0), baseline["unemployment"] - 0.5), 1)
            st.session_state.challenge = {
                "gdp_growth": target_gdp,
                "inflation": target_inflation,
                "unemployment": target_unemployment,
            }
            st.success("New challenge generated!")

    if st.session_state.challenge:
        ch = st.session_state.challenge
        st.write(f"**Target GDP growth:** ≥ {ch['gdp_growth']}%")
        st.write(f"**Target inflation:** ≤ {ch['inflation']}%")
        st.write(f"**Target unemployment:** ≤ {ch['unemployment']}%")
    else:
        st.write("Click **Generate Challenge** to get your targets.")

st.markdown("---")

# ---- LESSON MODE ----
if st.session_state.lesson_mode:
    st.subheader("Lesson Mode")
    st.markdown("""
    **Goal:** Learn how to control inflation without causing a recession.
    
    1. Set the **interest rate** high (e.g., 8–10%) – this reduces inflation but may increase unemployment.
    2. Lower **government spending** to a negative value (e.g., -2%) – also cools the economy.
    3. Keep **income tax** moderate (around 20%) to avoid reducing demand too much.
    4. Set **VAT** to 15% or lower – lower VAT reduces prices directly.
    
    Try to keep unemployment below 6% while getting inflation below 3%.
    """)
    st.info("For this lesson, the following starting values are suggested (adjust them if you wish):")
    interest_rate = st.slider("Interest rate (%)", 0.0, 15.0, 8.0, 0.05)
    income_tax = st.slider("Income tax (%)", 0.0, 50.0, 20.0, 0.5)
    vat = st.slider("VAT (%)", 0.0, 30.0, 15.0, 0.5)
    gov_spending_change = st.slider("Government spending change (%)", -10.0, 10.0, -2.0, 0.1)
else:
    # ---- POLICY SLIDERS ----
    st.subheader("Your Policy")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        interest_rate = st.slider(
            "Interest rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=4.25,
            step=0.05,
            help="Set by the central bank. Higher rates cool inflation but may hurt growth.",
        )

    with col2:
        income_tax = st.slider(
            "Income tax (%)",
            min_value=0.0,
            max_value=50.0,
            value=19.0,
            step=0.5,
            help="Direct tax on household income. Higher taxes reduce disposable income.",
        )

    with col3:
        vat = st.slider(
            "VAT (%)",
            min_value=0.0,
            max_value=30.0,
            value=23.0,
            step=0.5,
            help="Value-added tax. Higher VAT increases prices and reduces consumption.",
        )

    with col4:
        gov_spending_change = st.slider(
            "Government spending change (%)",
            min_value=-10.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="Percentage change from baseline government spending. Positive values are expansionary.",
        )

# ---- RUN EXPERIMENT BUTTON ----
if st.session_state.game_over:
    st.warning("Your term is over! See the results below.")
    run_button = False
else:
    run_button = st.button("RUN EXPERIMENT", use_container_width=True)

# ---- RESULTS ----
st.markdown("---")
st.subheader("Results")

if run_button and not st.session_state.game_over:
    params = {
        "interest_rate": interest_rate,
        "income_tax": income_tax,
        "vat": vat,
        "gov_spending_change": gov_spending_change,
    }
    
    # Apply political style starting modifier to government spending
    params["gov_spending_change"] += st.session_state.spending_bonus
    
    # Generate random event
    st.session_state.event = generate_random_event()
    
    # Handle scenario baseline overrides
    if scenario["baseline_override"] is not None:
        # Temporarily add "Scenario" to the CSV data
        df = pd.read_csv("data.csv")
        
        if "Scenario" not in df["country"].values:
            scenario_row = {
                "country": "Scenario",
                "base_gdp_growth": scenario["baseline_override"]["gdp_growth"],
                "base_inflation": scenario["baseline_override"]["inflation"],
                "base_unemployment": scenario["baseline_override"]["unemployment"],
                "base_real_wage_growth": scenario["baseline_override"]["real_wage_growth"],
            }
            df = pd.concat([df, pd.DataFrame([scenario_row])], ignore_index=True)
            df.to_csv("data.csv", index=False)
        
        results = simulate_economy("Scenario", params, st.session_state.coeffs)
    else:
        results = simulate_economy(country, params, st.session_state.coeffs)
    
    # Apply random event effects
    if st.session_state.event:
        results["gdp_growth"] += st.session_state.event["effect"]["gdp_growth"]
        results["inflation"] += st.session_state.event["effect"]["inflation"]
        results["unemployment"] += st.session_state.event["effect"]["unemployment"]
        # Recalculate changes
        results["gdp_growth_change"] = results["gdp_growth"] - baseline["gdp_growth"]
        results["inflation_change"] = results["inflation"] - baseline["inflation"]
        results["unemployment_change"] = results["unemployment"] - baseline["unemployment"]
    
    # Calculate approval rating change
    approval_change = 0.0
    
    # Good GDP growth increases approval
    if results["gdp_growth"] > 2.0:
        approval_change += (results["gdp_growth"] - 2.0) * 5
    else:
        approval_change += (results["gdp_growth"] - 2.0) * 8
    
    # High inflation decreases approval
    if results["inflation"] > 4.0:
        approval_change -= (results["inflation"] - 4.0) * 3
    elif results["inflation"] < 2.0:
        approval_change += 2
    
    # Low unemployment increases approval
    if results["unemployment"] < 5.0:
        approval_change += (5.0 - results["unemployment"]) * 4
    else:
        approval_change -= (results["unemployment"] - 5.0) * 5
    
    # Update approval rating
    st.session_state.approval = max(0, min(100, st.session_state.approval + approval_change))
    
    # Store results and narrative
    st.session_state["results"] = results
    st.session_state["approval_change"] = approval_change
    st.session_state["narrative"] = generate_narrative(results, approval_change)
    
    # Store in history
    st.session_state.history.append({
        "year": st.session_state.year,
        "approval": st.session_state.approval,
        **results
    })
    
    # Check for game over
    if st.session_state.approval < 20:
        st.session_state.game_over = True
    
    # Advance year
    if st.session_state.year >= 4:
        st.session_state.game_over = True
    else:
        st.session_state.year += 1

# Display results if available
if st.session_state["results"] is not None:
    res = st.session_state["results"]

    col1, col2, col3, col4 = st.columns(4)

    # Helper to display metric with tooltip
    def show_metric(label, value, change, tooltip_text, progress_range, progress_value, column):
        with column:
            st.markdown(
                f'<div class="result-label">{label} <span class="tooltip">?<span class="tooltiptext">{tooltip_text}</span></span></div>',
                unsafe_allow_html=True
            )
            progress = (progress_value - progress_range[0]) / (progress_range[1] - progress_range[0])
            st.progress(min(1.0, max(0.0, progress)))
            st.write(f"**{value:.1f}%**")
            st.write(f"({'+' if change >= 0 else ''}{change:.1f}% vs baseline)")

    show_metric(
        "GDP Growth",
        res["gdp_growth"],
        res["gdp_growth_change"],
        "Gross Domestic Product growth rate. Higher is generally better, but too high can cause inflation.",
        (-5, 15),
        res["gdp_growth"],
        col1
    )
    show_metric(
        "Inflation",
        res["inflation"],
        res["inflation_change"],
        "General increase in prices. Central banks typically target around 2%.",
        (-2, 20),
        res["inflation"],
        col2
    )
    show_metric(
        "Unemployment",
        res["unemployment"],
        res["unemployment_change"],
        "Percentage of labor force without jobs. Lower is better, but very low can lead to wage inflation.",
        (1, 30),
        res["unemployment"],
        col3
    )
    show_metric(
        "Real Wage Growth",
        res["real_wage_growth"],
        res["real_wage_growth_change"],
        "Increase in wages adjusted for inflation. Positive means workers' purchasing power is rising.",
        (-5, 10),
        res["real_wage_growth"],
        col4
    )

    # Display random event if it occurred
    if st.session_state.event:
        st.markdown("---")
        st.subheader(f"Random Event: {st.session_state.event['name']}")
        st.write(st.session_state.event["description"])
        st.write("This event has affected your economic indicators.")

    # Display narrative
    if st.session_state.narrative:
        st.markdown("---")
        st.subheader("News Report")
        st.write(st.session_state.narrative)

    # Scoring
    if st.session_state.challenge:
        ch = st.session_state.challenge
        score = 0.0
        if res["gdp_growth"] >= ch["gdp_growth"]:
            score += 40.0
        else:
            score += 40.0 * max(0.0, res["gdp_growth"] / ch["gdp_growth"]) if ch["gdp_growth"] > 0 else 40.0
        if res["inflation"] <= ch["inflation"]:
            score += 30.0
        else:
            score += 30.0 * max(0.0, ch["inflation"] / res["inflation"]) if res["inflation"] > 0 else 0.0
        if res["unemployment"] <= ch["unemployment"]:
            score += 30.0
        else:
            score += 30.0 * max(0.0, ch["unemployment"] / res["unemployment"]) if res["unemployment"] > 0 else 0.0
        score = round(min(100.0, score), 1)
        st.markdown("---")
        st.subheader("🎯 Challenge Score")
        st.write(f"**Your score: {score}/100**")
        if score >= 80:
            st.success("Excellent! You hit almost all targets.")
        elif score >= 60:
            st.warning("Good effort, but you could improve some indicators.")
        else:
            st.error("Your policy missed most targets. Try different settings!")

    st.markdown("---")
    st.subheader("Visual Comparison")
    metrics = ["GDP Growth", "Inflation", "Unemployment", "Real Wage Growth"]
    baseline_vals = [
        baseline["gdp_growth"],
        baseline["inflation"],
        baseline["unemployment"],
        baseline["real_wage_growth"],
    ]
    result_vals = [
        res["gdp_growth"],
        res["inflation"],
        res["unemployment"],
        res["real_wage_growth"],
    ]

    df = pd.DataFrame({"Metric": metrics, "Baseline": baseline_vals, "Your Policy": result_vals})
    df.set_index("Metric", inplace=True)
    st.bar_chart(df, height=400)
else:
    if not st.session_state.game_over:
        st.info("Adjust the policy sliders and click **RUN EXPERIMENT** to see the effects.")

# ---- GAME OVER SCREEN ----
if st.session_state.game_over:
    st.markdown("---")
    st.subheader("Final Results")
    
    if st.session_state.approval < 20:
        st.error(f"UPRISING! {st.session_state.player_name}, you were overthrown by angry citizens!")
        st.markdown("""
        *The mob storms the Ministry of Finance building...*
        *Your economic policies have failed the people.*
        *History will remember you as a cautionary tale.*
        """)
    else:
        st.success(f"Congratulations, {st.session_state.player_name}! You completed your 4-year term!")
        st.balloons()
        st.markdown("""
        *You step down peacefully, handing over the reins to your successor.*
        *The economy is stable, and the people are content.*
        *Your legacy as a skilled financial leader is secure.*
        """)
    
    st.write(f"**Final Approval Rating:** {st.session_state.approval:.0f}%")
    
    # Calculate final score
    final_score = st.session_state.approval
    
    if final_score >= 70:
        st.success("Outstanding leadership! You'll go down in history as a great leader.")
    elif final_score >= 50:
        st.info("Good job! You maintained reasonable stability.")
    else:
        st.warning("Your time in office was challenging. The next leader has big shoes to fill.")
    
    # Show history
    if st.session_state.history:
        st.subheader("Your Track Record")
        history_df = pd.DataFrame(st.session_state.history)
        st.line_chart(history_df[["approval"]])
    
    # Reset button
    if st.button("Play Again"):
        # Reset all game state
        st.session_state.approval = 50.0
        st.session_state.year = 1
        st.session_state.game_over = False
