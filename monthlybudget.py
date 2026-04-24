import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import math

st.set_page_config(
    page_title="💰 Budget Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stApp { background-color: #0f1117; }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252a3d);
        border-radius: 12px;
        padding: 18px 22px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 12px;
    }
    .metric-card.danger  { border-left-color: #f44336; }
    .metric-card.warning { border-left-color: #FF9800; }
    .metric-card.info    { border-left-color: #2196F3; }
    .metric-card h3 { margin: 0 0 4px 0; font-size: 0.85rem; color: #9aa3b2; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card h2 { margin: 0; font-size: 1.8rem; font-weight: 700; color: #ffffff; }
    .metric-card p  { margin: 4px 0 0 0; font-size: 0.8rem; color: #9aa3b2; }

    /* Alerts */
    .alert-danger  { background:#3d1a1a; border:1px solid #f44336; border-radius:8px; padding:12px 16px; margin:6px 0; color:#ff8a80; }
    .alert-warning { background:#3d2e1a; border:1px solid #FF9800; border-radius:8px; padding:12px 16px; margin:6px 0; color:#ffcc80; }
    .alert-success { background:#1a3d1a; border:1px solid #4CAF50; border-radius:8px; padding:12px 16px; margin:6px 0; color:#a5d6a7; }
    .alert-info    { background:#1a2a3d; border:1px solid #2196F3; border-radius:8px; padding:12px 16px; margin:6px 0; color:#90caf9; }

    /* Section headers */
    .section-header {
        font-size: 1.3rem; font-weight: 700; color: #ffffff;
        padding: 10px 0 6px; border-bottom: 2px solid #2a2f45; margin-bottom: 16px;
    }

    /* Savings goal card */
    .goal-card {
        background: linear-gradient(135deg, #1e2130, #252a3d);
        border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
        border: 1px solid #2a2f45;
    }

    div[data-testid="stNumberInput"] input { background-color: #1e2130 !important; color: #fff !important; border-color: #3a3f55 !important; }
    div[data-testid="stTextInput"]   input { background-color: #1e2130 !important; color: #fff !important; border-color: #3a3f55 !important; }
    .stSlider > div { padding: 0; }
    [data-testid="stSidebar"] { background-color: #151822; }
</style>
""", unsafe_allow_html=True)

# ── Session-state defaults ───────────────────────────────────────────────────
BUDGET_DEFAULTS = {
    # Housing
    "Rent / Mortgage": 2000,
    "Electricity":     120,
    "Water & Sewer":    60,
    "Internet":         80,
    "Phone":            85,
    # Transportation
    "Car Payment":     450,
    "Gas":             150,
    "Car Insurance":   180,
    "Parking / Tolls":  40,
    "Public Transit":    0,
    # Food
    "Groceries":       500,
    "Dining Out":      250,
    "Coffee Shops":     60,
    # Health
    "Health Insurance": 300,
    "Gym / Fitness":    50,
    "Prescriptions":    30,
    # Personal
    "Clothing":        100,
    "Personal Care":    60,
    "Subscriptions":    80,
    "Entertainment":   120,
    "Miscellaneous":   100,
}

SPENDING_DEFAULTS = {k: round(v * (0.85 + 0.3 * hash(k) % 100 / 100), 0)
                     for k, v in BUDGET_DEFAULTS.items()}

CATEGORY_MAP = {
    "🏠 Housing":       ["Rent / Mortgage","Electricity","Water & Sewer","Internet","Phone"],
    "🚗 Transportation":["Car Payment","Gas","Car Insurance","Parking / Tolls","Public Transit"],
    "🍽️ Food":          ["Groceries","Dining Out","Coffee Shops"],
    "🏥 Health":        ["Health Insurance","Gym / Fitness","Prescriptions"],
    "👤 Personal":      ["Clothing","Personal Care","Subscriptions","Entertainment","Miscellaneous"],
}

BILLS = {"Rent / Mortgage","Electricity","Water & Sewer","Internet","Phone",
         "Car Payment","Car Insurance","Health Insurance"}

if "budgets"  not in st.session_state:
    st.session_state.budgets  = dict(BUDGET_DEFAULTS)
if "spending" not in st.session_state:
    st.session_state.spending = dict(SPENDING_DEFAULTS)
if "income"   not in st.session_state:
    st.session_state.income   = 7500.0
if "savings_goals" not in st.session_state:
    st.session_state.savings_goals = []
if "monthly_savings_target" not in st.session_state:
    st.session_state.monthly_savings_target = 500.0
if "sim_increases" not in st.session_state:
    st.session_state.sim_increases = {}

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR – Income & Monthly Savings Target
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Global Settings")
    st.session_state.income = st.number_input(
        "💵 Monthly Net Income ($)", min_value=0.0,
        value=float(st.session_state.income), step=100.0, format="%.2f"
    )
    st.session_state.monthly_savings_target = st.number_input(
        "🎯 Monthly Savings Target ($)", min_value=0.0,
        value=float(st.session_state.monthly_savings_target), step=50.0, format="%.2f"
    )

    st.markdown("---")
    st.markdown("### 📋 Quick Reset")
    if st.button("Reset Budgets to Default"):
        st.session_state.budgets = dict(BUDGET_DEFAULTS)
        st.rerun()
    if st.button("Reset Spending to Default"):
        st.session_state.spending = dict(SPENDING_DEFAULTS)
        st.rerun()
    if st.button("Clear All Simulations"):
        st.session_state.sim_increases = {}
        st.rerun()

    st.markdown("---")
    st.markdown("### 📅 Budget Month")
    budget_month = st.date_input("Select Month", value=date.today().replace(day=1))

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def total_budget():   return sum(st.session_state.budgets.values())
def total_spending():  return sum(st.session_state.spending.values())
def total_simulated(): return sum(st.session_state.budgets[k] + st.session_state.sim_increases.get(k, 0)
                                   for k in st.session_state.budgets)
def remaining(use_sim=False):
    total = total_simulated() if use_sim else total_budget()
    return st.session_state.income - total - st.session_state.monthly_savings_target

def overspent_items():
    items = []
    for k, budget in st.session_state.budgets.items():
        spent = st.session_state.spending.get(k, 0)
        if spent > budget and k not in BILLS:
            items.append((k, budget, spent, spent - budget))
    return sorted(items, key=lambda x: -x[3])

def near_limit_items(pct=0.85):
    items = []
    for k, budget in st.session_state.budgets.items():
        spent = st.session_state.spending.get(k, 0)
        if budget > 0 and pct <= spent / budget < 1.0 and k not in BILLS:
            items.append((k, budget, spent))
    return items

# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("# 💰 Monthly Budget Dashboard")
st.markdown(f"**{budget_month.strftime('%B %Y')}**  |  Track · Simulate · Save")
st.markdown("---")

# ─── Top-level KPI row ──────────────────────────────────────────────────────
income      = st.session_state.income
budgeted    = total_budget()
spent_total = total_spending()
rem_budget  = income - budgeted - st.session_state.monthly_savings_target
rem_spent   = income - spent_total - st.session_state.monthly_savings_target
savings_pct = (st.session_state.monthly_savings_target / income * 100) if income else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card info">
        <h3>Monthly Income</h3><h2>${income:,.0f}</h2>
        <p>After savings target: ${income - st.session_state.monthly_savings_target:,.0f}</p>
    </div>""", unsafe_allow_html=True)
with col2:
    color = "danger" if budgeted > income else ("warning" if rem_budget < 200 else "")
    st.markdown(f"""<div class="metric-card {color}">
        <h3>Total Budgeted</h3><h2>${budgeted:,.0f}</h2>
        <p>Remaining: ${rem_budget:,.0f}</p>
    </div>""", unsafe_allow_html=True)
with col3:
    color = "danger" if spent_total > budgeted else ("warning" if spent_total/budgeted > 0.9 else "")
    st.markdown(f"""<div class="metric-card {color}">
        <h3>Actual Spending</h3><h2>${spent_total:,.0f}</h2>
        <p>{"⚠️ Over budget!" if spent_total > budgeted else f"Under by ${budgeted - spent_total:,.0f}"}</p>
    </div>""", unsafe_allow_html=True)
with col4:
    color = "" if rem_spent >= st.session_state.monthly_savings_target else ("warning" if rem_spent >= 0 else "danger")
    st.markdown(f"""<div class="metric-card {color}">
        <h3>Savings Target</h3><h2>${st.session_state.monthly_savings_target:,.0f}</h2>
        <p>{savings_pct:.1f}% of income</p>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Budget Overview",
    "🔮 Budget Simulator",
    "🚨 Spending Alerts",
    "🎯 Savings Goals",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 – BUDGET OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">📝 Enter Your Budget & Actual Spending</div>', unsafe_allow_html=True)

    for cat, items in CATEGORY_MAP.items():
        with st.expander(cat, expanded=True):
            hdr = st.columns([2.5, 1.5, 1.5, 1.5])
            hdr[0].markdown("**Category**")
            hdr[1].markdown("**Budget ($)**")
            hdr[2].markdown("**Spent ($)**")
            hdr[3].markdown("**Status**")

            for item in items:
                c0, c1, c2, c3 = st.columns([2.5, 1.5, 1.5, 1.5])
                c0.markdown(f"{'🔒 ' if item in BILLS else ''}{item}")

                new_budget = c1.number_input(
                    f"bud_{item}", label_visibility="collapsed",
                    min_value=0.0, value=float(st.session_state.budgets[item]),
                    step=10.0, key=f"bud_{item}"
                )
                st.session_state.budgets[item] = new_budget

                new_spent = c2.number_input(
                    f"spd_{item}", label_visibility="collapsed",
                    min_value=0.0, value=float(st.session_state.spending.get(item, 0)),
                    step=10.0, key=f"spd_{item}"
                )
                st.session_state.spending[item] = new_spent

                budget = st.session_state.budgets[item]
                spent  = st.session_state.spending[item]
                if budget == 0:
                    c3.markdown("—")
                elif spent > budget:
                    c3.markdown(f"🔴 Over **${spent - budget:.0f}**")
                elif spent / budget >= 0.85:
                    c3.markdown(f"🟡 {spent/budget*100:.0f}%")
                else:
                    c3.markdown(f"🟢 {spent/budget*100:.0f}%")

    st.markdown("---")
    st.markdown('<div class="section-header">📊 Spending vs Budget Chart</div>', unsafe_allow_html=True)

    labels, budgets_vals, spent_vals, colors = [], [], [], []
    for item in BUDGET_DEFAULTS:
        b = st.session_state.budgets[item]
        s = st.session_state.spending.get(item, 0)
        if b > 0 or s > 0:
            labels.append(item)
            budgets_vals.append(b)
            spent_vals.append(s)
            colors.append("#f44336" if s > b else ("#FF9800" if b > 0 and s/b >= 0.85 else "#4CAF50"))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Budget",  x=labels, y=budgets_vals, marker_color="#2196F3", opacity=0.6))
    fig.add_trace(go.Bar(name="Spent",   x=labels, y=spent_vals,   marker_color=colors))
    fig.update_layout(
        barmode="group", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font_color="#ffffff", legend=dict(bgcolor="#1e2130"),
        xaxis=dict(tickangle=-35, gridcolor="#2a2f45"),
        yaxis=dict(gridcolor="#2a2f45", tickprefix="$"),
        height=420, margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Pie of budgeted spending by category
    cat_totals = {cat: sum(st.session_state.budgets[i] for i in items)
                  for cat, items in CATEGORY_MAP.items()}
    fig2 = px.pie(
        names=list(cat_totals.keys()), values=list(cat_totals.values()),
        title="Budget Allocation by Category",
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        hole=0.4
    )
    fig2.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font_color="#ffffff", height=360,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 – BUDGET SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">🔮 Budget Increase Simulator</div>', unsafe_allow_html=True)
    st.markdown("Drag the sliders to simulate cost increases and see their impact in real-time.")

    sim_cols = st.columns(2)
    all_items = list(BUDGET_DEFAULTS.keys())
    half = math.ceil(len(all_items) / 2)

    for col_idx, items_slice in enumerate([all_items[:half], all_items[half:]]):
        with sim_cols[col_idx]:
            for item in items_slice:
                base = st.session_state.budgets[item]
                inc  = st.slider(
                    f"{item}  (base: ${base:.0f})",
                    min_value=0, max_value=int(base * 1.5) + 200,
                    value=st.session_state.sim_increases.get(item, 0),
                    step=10, key=f"sim_{item}"
                )
                st.session_state.sim_increases[item] = inc

    sim_total   = total_simulated()
    sim_rem     = remaining(use_sim=True)
    base_total  = total_budget()
    delta       = sim_total - base_total

    st.markdown("---")
    st.markdown("### 📈 Simulation Results")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"""<div class="metric-card info">
            <h3>Original Budget Total</h3><h2>${base_total:,.0f}</h2>
            <p>Current allocations</p>
        </div>""", unsafe_allow_html=True)
    with r2:
        color = "danger" if sim_total > income else "warning" if sim_rem < 300 else ""
        st.markdown(f"""<div class="metric-card {color}">
            <h3>Simulated Total</h3><h2>${sim_total:,.0f}</h2>
            <p>+${delta:,.0f} from increases</p>
        </div>""", unsafe_allow_html=True)
    with r3:
        color = "danger" if sim_rem < 0 else ("warning" if sim_rem < 300 else "")
        st.markdown(f"""<div class="metric-card {color}">
            <h3>Remaining After Sim</h3><h2>${sim_rem:,.0f}</h2>
            <p>{"🔴 OVER BUDGET" if sim_rem < 0 else "Available"}</p>
        </div>""", unsafe_allow_html=True)

    # Alerts
    st.markdown("### 🚨 Simulation Alerts")
    has_alert = False
    for item, inc in st.session_state.sim_increases.items():
        if inc > 0:
            has_alert = True
            new_val = st.session_state.budgets[item] + inc
            pct = (inc / st.session_state.budgets[item] * 100) if st.session_state.budgets[item] else 0
            st.markdown(f"""<div class="alert-warning">
                ⚠️ <strong>{item}</strong>: +${inc:,.0f} increase ({pct:.1f}%) → New total: <strong>${new_val:,.0f}</strong>
            </div>""", unsafe_allow_html=True)

    if sim_rem < 0:
        st.markdown(f"""<div class="alert-danger">
            🔴 <strong>OVER BUDGET!</strong> These increases push you <strong>${abs(sim_rem):,.0f} over</strong> your income/savings targets.
            You need to cut ${abs(sim_rem):,.0f} elsewhere to stay on track.
        </div>""", unsafe_allow_html=True)
    elif sim_rem < 300:
        st.markdown(f"""<div class="alert-warning">
            🟡 <strong>TIGHT BUDGET</strong> – Only <strong>${sim_rem:,.0f}</strong> remaining after these increases.
            Consider reviewing discretionary spending.
        </div>""", unsafe_allow_html=True)
    elif not has_alert:
        st.markdown("""<div class="alert-success">
            ✅ No increases applied. Move the sliders above to simulate cost changes.
        </div>""", unsafe_allow_html=True)

    # Waterfall chart
    if has_alert:
        st.markdown("### 📊 Impact Breakdown")
        wf_items = [(k, v) for k, v in st.session_state.sim_increases.items() if v > 0]
        wf_labels = ["Base Budget"] + [k for k, _ in wf_items] + ["Simulated Total"]
        wf_values = [base_total] + [v for _, v in wf_items] + [sim_total]
        wf_colors = ["#2196F3"] + ["#FF9800"] * len(wf_items) + (["#f44336"] if sim_total > income else ["#4CAF50"])
        fig_wf = go.Figure(go.Bar(x=wf_labels, y=wf_values, marker_color=wf_colors))
        fig_wf.update_layout(
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font_color="#ffffff", height=320,
            yaxis=dict(tickprefix="$", gridcolor="#2a2f45"),
            xaxis=dict(gridcolor="#2a2f45"),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_wf, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 – SPENDING ALERTS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">🚨 Spending Alerts & Insights</div>', unsafe_allow_html=True)
    st.markdown("*Bills (rent, insurance, car payment, etc.) are excluded — focus is on controllable expenses.*")

    overspent = overspent_items()
    near      = near_limit_items()

    # ── Overspending section ────────────────────────────────────────────────
    st.markdown("### 🔴 Over Budget (Controllable Expenses)")
    if overspent:
        for item, budget, spent, diff in overspent:
            pct_over = diff / budget * 100
            st.markdown(f"""<div class="alert-danger">
                🔴 <strong>{item}</strong> — Budgeted: <strong>${budget:,.0f}</strong> |
                Spent: <strong>${spent:,.0f}</strong> |
                Over by: <strong>${diff:,.0f} ({pct_over:.1f}%)</strong>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="alert-success">
            ✅ No controllable expenses are over budget this month!
        </div>""", unsafe_allow_html=True)

    # ── Near limit section ──────────────────────────────────────────────────
    st.markdown("### 🟡 Approaching Budget Limit (85%+)")
    if near:
        for item, budget, spent in near:
            pct = spent / budget * 100
            st.markdown(f"""<div class="alert-warning">
                ⚠️ <strong>{item}</strong> — ${spent:,.0f} of ${budget:,.0f} budget used ({pct:.1f}%)
                — only <strong>${budget - spent:,.0f}</strong> remaining
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="alert-success">✅ All expenses are under 85% of budget.</div>""", unsafe_allow_html=True)

    # ── Spending chart ──────────────────────────────────────────────────────
    st.markdown("### 📊 Controllable Expense Breakdown")
    exp_items   = [k for k in BUDGET_DEFAULTS if k not in BILLS]
    exp_budgets = [st.session_state.budgets[k] for k in exp_items]
    exp_spent   = [st.session_state.spending.get(k, 0) for k in exp_items]
    exp_colors  = ["#f44336" if s > b else ("#FF9800" if b > 0 and s/b >= 0.85 else "#4CAF50")
                   for s, b in zip(exp_spent, exp_budgets)]

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Budget", x=exp_items, y=exp_budgets, marker_color="#2196F3", opacity=0.5))
    fig3.add_trace(go.Bar(name="Spent",  x=exp_items, y=exp_spent,   marker_color=exp_colors))
    fig3.update_layout(
        barmode="overlay", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font_color="#ffffff", height=380,
        xaxis=dict(tickangle=-35, gridcolor="#2a2f45"),
        yaxis=dict(gridcolor="#2a2f45", tickprefix="$"),
        legend=dict(bgcolor="#1e2130"),
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Spending Reduction Recommendations ─────────────────────────────────
    st.markdown("### ✂️ Where to Cut Spending")
    if overspent:
        st.markdown("Based on your overspending, here are suggested reductions:")
        for item, budget, spent, diff in overspent:
            pct_cut = min(30, diff / spent * 100 + 5)
            savings = spent * pct_cut / 100
            tips = {
                "Dining Out":    "Try meal-prepping 2–3 times a week to cut restaurant visits.",
                "Coffee Shops":  "Brew at home — a $20 bag of beans ≈ 30+ cups vs $5/cup out.",
                "Entertainment": "Audit subscriptions; rotate streaming services month to month.",
                "Groceries":     "Use a shopping list, buy store brands, and batch-cook proteins.",
                "Clothing":      "Implement a 30-day rule before any non-essential clothing purchase.",
                "Miscellaneous": "Track every purchase for 2 weeks to find hidden leaks.",
                "Personal Care": "Compare costs online before buying; buy in bulk for staples.",
                "Subscriptions": "Cancel unused subscriptions — review bank statements for recurring charges.",
            }
            tip = tips.get(item, f"Set a weekly cash envelope for {item} to enforce the limit.")
            st.markdown(f"""<div class="alert-info">
                💡 <strong>{item}</strong>: Cutting by ~{pct_cut:.0f}% saves <strong>${savings:,.0f}/mo</strong><br>
                <em>{tip}</em>
            </div>""", unsafe_allow_html=True)
    else:
        total_discretionary = sum(st.session_state.spending.get(k, 0) for k in exp_items)
        potential = total_discretionary * 0.10
        st.markdown(f"""<div class="alert-info">
            💡 <strong>Proactive tip:</strong> Even trimming discretionary expenses by 10% would save
            <strong>${potential:,.0f}/month</strong> (${potential*12:,.0f}/year) toward your goals.
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 – SAVINGS GOALS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">🎯 Savings Goals Tracker</div>', unsafe_allow_html=True)

    # ── Add new goal form ───────────────────────────────────────────────────
    st.markdown("### ➕ Add a New Savings Goal")
    with st.container():
        gc1, gc2, gc3, gc4 = st.columns([2, 1.5, 1.5, 1])
        goal_name   = gc1.text_input("Goal Name", placeholder="e.g. Emergency Fund, Vacation, New Car")
        goal_amount = gc2.number_input("Target Amount ($)", min_value=0.0, value=5000.0, step=100.0)
        goal_date   = gc3.date_input("Target Date", value=date.today() + relativedelta(months=12))
        goal_saved  = gc1.number_input("Already Saved ($)", min_value=0.0, value=0.0, step=50.0)

        if gc4.button("➕ Add Goal", use_container_width=True):
            if goal_name.strip():
                st.session_state.savings_goals.append({
                    "name":       goal_name.strip(),
                    "target":     goal_amount,
                    "saved":      goal_saved,
                    "date":       goal_date.isoformat(),
                    "created":    date.today().isoformat(),
                })
                st.success(f"✅ Goal '{goal_name}' added!")
                st.rerun()
            else:
                st.error("Please enter a goal name.")

    # ── Display goals ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Your Savings Goals")

    if not st.session_state.savings_goals:
        st.markdown("""<div class="alert-info">
            🎯 No goals yet! Add your first savings goal above.
        </div>""", unsafe_allow_html=True)
    else:
        today = date.today()
        for idx, goal in enumerate(st.session_state.savings_goals):
            target_date = date.fromisoformat(goal["date"])
            months_left = max(1, (target_date.year - today.year) * 12 + (target_date.month - today.month))
            remaining_amt = max(0, goal["target"] - goal["saved"])
            needed_per_month = remaining_amt / months_left if months_left > 0 else remaining_amt
            progress_pct = min(100, goal["saved"] / goal["target"] * 100) if goal["target"] > 0 else 0
            on_track = needed_per_month <= st.session_state.monthly_savings_target

            status_color = "alert-success" if progress_pct >= 100 else ("alert-warning" if not on_track else "alert-info")
            status_icon  = "✅" if progress_pct >= 100 else ("⚠️" if not on_track else "🟢")

            with st.container():
                st.markdown(f"""<div class="goal-card">
                    <h3 style="color:#fff;margin:0 0 8px">{goal['name']}</h3>
                </div>""", unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Target",         f"${goal['target']:,.0f}")
                col_b.metric("Saved So Far",   f"${goal['saved']:,.0f}")
                col_c.metric("Still Needed",   f"${remaining_amt:,.0f}")

                col_d, col_e, col_f = st.columns(3)
                col_d.metric("Target Date",    target_date.strftime("%b %Y"))
                col_e.metric("Months Left",    str(months_left))
                col_f.metric("Needed / Month", f"${needed_per_month:,.0f}")

                # Progress bar
                bar_color = "#4CAF50" if progress_pct >= 100 else ("#2196F3" if on_track else "#FF9800")
                st.markdown(f"""
                <div style="background:#1e2130;border-radius:8px;overflow:hidden;height:18px;margin:8px 0">
                    <div style="width:{progress_pct:.1f}%;background:{bar_color};height:100%;
                                border-radius:8px;transition:width 0.3s;
                                display:flex;align-items:center;justify-content:center;
                                font-size:0.7rem;color:#fff;font-weight:700">
                        {progress_pct:.1f}%
                    </div>
                </div>""", unsafe_allow_html=True)

                st.markdown(f"""<div class="{status_color}" style="margin:6px 0">
                    {status_icon} <strong>Status:</strong>
                    {'🎉 Goal reached!' if progress_pct >= 100
                     else f'Need <strong>${needed_per_month:,.0f}/mo</strong> — '
                          + ('On track ✅' if on_track
                             else f'⚠️ Exceeds your ${st.session_state.monthly_savings_target:,.0f} savings target by ${needed_per_month - st.session_state.monthly_savings_target:,.0f}/mo')}
                </div>""", unsafe_allow_html=True)

                # Where to cut if needed
                if not on_track and progress_pct < 100:
                    shortfall = needed_per_month - st.session_state.monthly_savings_target
                    exp_items = [(k, st.session_state.spending.get(k, 0)) for k in BUDGET_DEFAULTS if k not in BILLS]
                    exp_items_sorted = sorted(exp_items, key=lambda x: -x[1])
                    cut_suggestions, total_cut = [], 0
                    for item, spent in exp_items_sorted:
                        if total_cut >= shortfall:
                            break
                        cut_by = min(spent * 0.20, shortfall - total_cut)
                        if cut_by > 5:
                            cut_suggestions.append((item, cut_by))
                            total_cut += cut_by

                    if cut_suggestions:
                        suggestions_html = " | ".join([f"Cut <em>{item}</em> by ${cut:.0f}" for item, cut in cut_suggestions])
                        st.markdown(f"""<div class="alert-info" style="margin:4px 0">
                            ✂️ <strong>To close the ${shortfall:,.0f}/mo gap:</strong> {suggestions_html}
                        </div>""", unsafe_allow_html=True)

                # Update saved amount & delete
                with st.expander(f"✏️ Update '{goal['name']}'"):
                    upd1, upd2 = st.columns(2)
                    new_saved = upd1.number_input(
                        "Update Amount Saved ($)",
                        min_value=0.0, max_value=float(goal["target"]),
                        value=float(goal["saved"]), step=50.0,
                        key=f"update_saved_{idx}"
                    )
                    if upd1.button("💾 Save", key=f"save_goal_{idx}"):
                        st.session_state.savings_goals[idx]["saved"] = new_saved
                        st.rerun()
                    if upd2.button("🗑️ Delete Goal", key=f"del_goal_{idx}"):
                        st.session_state.savings_goals.pop(idx)
                        st.rerun()

                st.markdown("---")

    # ── Overall savings picture ─────────────────────────────────────────────
    if st.session_state.savings_goals:
        st.markdown("### 📈 Goals Progress Overview")
        goal_names   = [g["name"]   for g in st.session_state.savings_goals]
        goal_targets = [g["target"] for g in st.session_state.savings_goals]
        goal_saveds  = [g["saved"]  for g in st.session_state.savings_goals]
        goal_colors  = ["#4CAF50" if s >= t else "#2196F3" for s, t in zip(goal_saveds, goal_targets)]

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Target", x=goal_names, y=goal_targets, marker_color="#1e2130", marker_line_color="#2196F3", marker_line_width=2))
        fig4.add_trace(go.Bar(name="Saved",  x=goal_names, y=goal_saveds,  marker_color=goal_colors))
        fig4.update_layout(
            barmode="overlay", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font_color="#ffffff", height=320,
            yaxis=dict(tickprefix="$", gridcolor="#2a2f45"),
            xaxis=dict(gridcolor="#2a2f45"),
            legend=dict(bgcolor="#1e2130"),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig4, use_container_width=True)

        total_goals   = sum(goal_targets)
        total_saved   = sum(goal_saveds)
        overall_pct   = total_saved / total_goals * 100 if total_goals else 0
        st.markdown(f"""<div class="alert-info">
            📊 <strong>Overall:</strong> You've saved <strong>${total_saved:,.0f}</strong> of
            <strong>${total_goals:,.0f}</strong> across all goals ({overall_pct:.1f}%)
        </div>""", unsafe_allow_html=True)
