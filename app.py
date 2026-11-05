"""
app.py
Minimalist, shadcn-inspired Operations Intelligence Dashboard for Teleoperation.
Features:
  - Focused executive landing page with high-signal stats & charts
  - Predefined user test cases / scenario quick-switches (Baseline, Novice Risk, Shift Fatigue, Latency Cliff)
  - Neutral zinc/slate monochrome palette with subtle borders and clean typography
  - Zero clutter: only essential stats, graphs, and actionable recommendations
  - Fully dynamic slicing and memo synchronization
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Teleoperation Ops Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# shadcn/ui Inspired Minimalist Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #09090b;
    }
    
    /* Top clean spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Header typography */
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #09090b;
        margin-bottom: 0.25rem;
    }
    .hero-sub {
        font-size: 0.95rem;
        color: #71717a;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    
    /* shadcn Badge Pill */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border-radius: 9999px;
        border: 1px solid #e4e4e7;
        background-color: #fafafa;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 500;
        color: #71717a;
        margin-bottom: 1.25rem;
    }
    .badge-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #71717a;
    }
    
    /* shadcn Card */
    .shadcn-card {
        background: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 10px;
        padding: 1.25rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        margin-bottom: 1rem;
    }
    
    /* Metric Card specifics */
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #71717a;
        margin-bottom: 0.4rem;
    }
    .metric-num {
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #09090b;
        line-height: 1.1;
    }
    .metric-meta {
        font-size: 0.78rem;
        color: #71717a;
        margin-top: 0.35rem;
    }
    .metric-meta.positive {
        color: #16a34a;
        font-weight: 500;
    }
    .metric-meta.warning {
        color: #dc2626;
        font-weight: 500;
    }
    
    /* Scenario Callout Banner */
    .scenario-banner {
        background-color: #fafafa;
        border: 1px solid #e4e4e7;
        border-left: 3px solid #18181b;
        border-radius: 8px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 1.25rem;
        font-size: 0.875rem;
        color: #27272a;
    }
    .scenario-banner strong {
        color: #09090b;
    }
    
    /* Recommendation Card */
    .rec-card {
        background: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
    }
    .rec-badge {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 2px 8px;
        border-radius: 4px;
        background: #f4f4f5;
        color: #18181b;
        margin-bottom: 0.5rem;
    }
    .rec-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #09090b;
        margin-bottom: 0.35rem;
    }
    .rec-body {
        font-size: 0.83rem;
        color: #52525b;
        line-height: 1.45;
        margin-bottom: 0.5rem;
    }
    .rec-impact {
        font-size: 0.8rem;
        font-weight: 600;
        color: #09090b;
        background: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 6px;
        padding: 0.4rem 0.65rem;
    }
    
    /* Clean Footer */
    .minimal-footer {
        text-align: center;
        padding: 2.5rem 0 1rem 0;
        font-size: 0.78rem;
        color: #a1a1aa;
        border-top: 1px solid #f4f4f5;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "ops.db")
MEMO_PATH = os.path.join(BASE_DIR, "reports", "ops_memo.md")

# Minimalist Plotly Theme Settings
PLOT_FONT = dict(family="Inter, sans-serif", color="#27272a", size=12)
GRID_COLOR = "#f4f4f5"
LINE_COLOR = "#18181b"
MUTED_BAR = "#e4e4e7"
ACCENT_BAR = "#18181b"
RED_BAR = "#ef4444"


@st.cache_data(ttl=600)
def load_base_data():
    """Load core tables from SQLite database into memory."""
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at `{DB_PATH}`. Please run `python src/load_db.py` first.")
        st.stop()

    conn = sqlite3.connect(DB_PATH)
    try:
        operators_df = pd.read_sql_query("SELECT * FROM operators", conn)
        sessions_df = pd.read_sql_query("SELECT * FROM sessions", conn)
        shifts_df = pd.read_sql_query("SELECT * FROM shifts", conn)
    finally:
        conn.close()

    sessions_df["session_date"] = pd.to_datetime(sessions_df["session_date"])
    shifts_df["shift_date"] = pd.to_datetime(shifts_df["shift_date"])
    operators_df["join_date"] = pd.to_datetime(operators_df["join_date"])

    merged_sessions = sessions_df.merge(
        operators_df[["operator_id", "region", "tenure_days", "hourly_cost_usd", "primary_shift"]],
        on="operator_id",
        how="left"
    )

    merged_sessions["tenure_bucket"] = pd.cut(
        merged_sessions["tenure_days"],
        bins=[-1, 30, 90, 99999],
        labels=["0-30 days", "31-90 days", "90+ days"]
    )

    merged_sessions["latency_bucket"] = pd.cut(
        merged_sessions["latency_ms"],
        bins=[0, 50, 100, 150, 99999],
        labels=["<50ms", "50-100ms", "100-150ms", "150ms+"]
    )

    return operators_df, shifts_df, merged_sessions


operators_raw, shifts_raw, sessions_raw = load_base_data()

# ==============================================================================
# PREDEFINED USER TEST CASES / OPERATIONAL SCENARIOS
# ==============================================================================
# Store active scenario in session state
if "scenario" not in st.session_state:
    st.session_state["scenario"] = "baseline"

# Header Section
st.markdown('<div class="hero-title">Teleoperation Ops Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Simulated telemetry across 150 human operators, 11,875 sessions, and 3 global hubs under the model\'s assumptions.</div>', unsafe_allow_html=True)
st.markdown('<div class="badge-pill"><span class="badge-dot"></span> Synthetic Data Simulation &bull; Model Parameters Seed 42 &bull; Portfolio Demo</div>', unsafe_allow_html=True)

# Scenario Selector Bar
st.markdown("**Predefined Scenarios & Test Cases:**")
sc_col1, sc_col2, sc_col3, sc_col4 = st.columns(4)

with sc_col1:
    if st.button("🎯 Baseline Fleet", use_container_width=True, type="primary" if st.session_state["scenario"] == "baseline" else "secondary"):
        st.session_state["scenario"] = "baseline"
        st.rerun()

with sc_col2:
    if st.button("👶 Novice Ramp Risk", use_container_width=True, type="primary" if st.session_state["scenario"] == "novice" else "secondary"):
        st.session_state["scenario"] = "novice"
        st.rerun()

with sc_col3:
    if st.button("🌙 Graveyard Shift Fatigue", use_container_width=True, type="primary" if st.session_state["scenario"] == "night" else "secondary"):
        st.session_state["scenario"] = "night"
        st.rerun()

with sc_col4:
    if st.button("⚡ High Latency Cliff", use_container_width=True, type="primary" if st.session_state["scenario"] == "latency" else "secondary"):
        st.session_state["scenario"] = "latency"
        st.rerun()

# Apply Scenario Filter Logic
active_scenario = st.session_state["scenario"]

if active_scenario == "novice":
    scenario_desc = "<strong>Test Case: Novice Ramp-Up (<30 Days Tenure).</strong> Isolates newly joined operators to evaluate training friction, supervisory intervention overhead, and the 10.1% baseline success deficit."
    filtered_sessions = sessions_raw[sessions_raw["tenure_bucket"] == "0-30 days"]
elif active_scenario == "night":
    scenario_desc = "<strong>Test Case: Graveyard Shift Circadian Fatigue.</strong> Isolates overnight operational sessions, demonstrating the 12.2% day-night success gap and 55% shift underutilization across offshore hubs."
    filtered_sessions = sessions_raw[sessions_raw["shift"] == "Night"]
elif active_scenario == "latency":
    scenario_desc = "<strong>Test Case: High Latency Routing Cliff (>150 ms).</strong> Isolates intercontinental teleoperation sessions where feedback lag triggers a 37.7% task failure cliff (2.5x higher than sub-50 ms)."
    filtered_sessions = sessions_raw[sessions_raw["latency_bucket"] == "150ms+"]
else:
    scenario_desc = "<strong>Test Case: Full Fleet Baseline.</strong> Complete 90-day simulated telemetry across all regions (India, Mexico, US), shifts (Morning, Evening, Night), and manipulation task types."
    filtered_sessions = sessions_raw

st.markdown(f'<div class="scenario-banner">{scenario_desc}</div>', unsafe_allow_html=True)

# Calculate Core Metrics from Filtered Slice
total_sess = len(filtered_sessions)
overall_succ = filtered_sessions["success"].mean() * 100.0
avg_lat = filtered_sessions["latency_ms"].mean()
avg_interv = filtered_sessions["interventions"].mean()

# High latency failure rate in slice
high_lat_slice = filtered_sessions[filtered_sessions["latency_ms"] >= 150.0]
high_lat_fail_rate = (1.0 - high_lat_slice["success"].mean()) * 100.0 if len(high_lat_slice) > 0 else 0.0

# Shift utilization overall
shift_summary = shifts_raw.groupby("shift_type").agg(
    sched=("scheduled_hours", "sum"),
    active=("active_hours", "sum")
).reset_index()
shift_summary["util"] = (shift_summary["active"] / shift_summary["sched"]) * 100.0
eve_util = shift_summary[shift_summary["shift_type"] == "Evening"]["util"].values[0]
night_util = shift_summary[shift_summary["shift_type"] == "Night"]["util"].values[0]

# Regional Unit Labor Cost
reg_cost_dict = {}
for r in ["India", "Mexico", "US"]:
    r_sess = sessions_raw[sessions_raw["region"] == r]
    r_succ = r_sess["success"].sum()
    r_shifts = shifts_raw.merge(operators_raw[["operator_id", "region"]], on="operator_id")
    r_shifts = r_shifts[r_shifts["region"] == r]
    wages = operators_raw.set_index("operator_id")["hourly_cost_usd"].to_dict()
    spend = sum(row["active_hours"] * wages.get(row["operator_id"], 10.0) for _, row in r_shifts.iterrows())
    reg_cost_dict[r] = (spend / r_succ) if r_succ > 0 else 0.0

# ==============================================================================
# ESSENTIAL STATS ROW (4 High-Signal Cards)
# ==============================================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="shadcn-card">
        <div class="metric-label">Task Success Rate</div>
        <div class="metric-num">{overall_succ:.1f}%</div>
        <div class="metric-meta {'positive' if overall_succ >= 80 else 'warning'}">
            {'Target: ≥85.0% SLA' if overall_succ >= 80 else 'Trailing 85.0% target'} &bull; {total_sess:,} sessions
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="shadcn-card">
        <div class="metric-label">Latency Failure Rate (≥150ms)</div>
        <div class="metric-num">{high_lat_fail_rate:.1f}%</div>
        <div class="metric-meta warning">
            2.5x baseline failure risk &bull; {len(high_lat_slice):,} sessions
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="shadcn-card">
        <div class="metric-label">Shift Utilization Gap</div>
        <div class="metric-num">{eve_util:.0f}% <span style="font-size:1.1rem; color:#71717a; font-weight:400;">vs</span> {night_util:.0f}%</div>
        <div class="metric-meta">
            Evening saturated &bull; Night idle standby
        </div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="shadcn-card">
        <div class="metric-label">Unit Cost / Success</div>
        <div class="metric-num">${reg_cost_dict.get('India', 25.76):.2f} <span style="font-size:1.1rem; color:#71717a; font-weight:400;">/</span> ${reg_cost_dict.get('US', 103.37):.2f}</div>
        <div class="metric-meta">
            India offshore vs US domestic labor
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# NAVIGATION TABS (Landing Overview + Focused Deeper Dives)
# ==============================================================================
main_tabs = st.tabs([
    "Executive Overview",
    "Actionable Recommendations",
    "Detailed Telemetry & Leaderboards",
    "Unit Economics"
])

# ------------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# ------------------------------------------------------------------------------
with main_tabs[0]:
    # 1. Primary Longitudinal Chart
    st.markdown("##### Longitudinal Fleet Reliability & 4-Week Moving Average")
    
    weekly_agg = filtered_sessions.groupby(
        filtered_sessions["session_date"].dt.to_period("W").dt.start_time
    ).agg(
        sessions=("session_id", "count"),
        success_rate=("success", lambda x: x.mean() * 100.0)
    ).reset_index()
    weekly_agg.columns = ["week_start", "sessions", "success_rate"]
    weekly_agg["rolling_4w"] = weekly_agg["success_rate"].rolling(4, min_periods=1).mean()

    fig_trend = go.Figure()
    # Benchmark line
    fig_trend.add_hline(
        y=85.0, line_dash="dash", line_color="#d4d4d8", line_width=1.5,
        annotation_text="85% Target SLA", annotation_position="top right",
        annotation_font=dict(size=11, color="#71717a")
    )
    # Weekly raw bars
    fig_trend.add_trace(go.Bar(
        x=weekly_agg["week_start"],
        y=weekly_agg["success_rate"],
        name="Weekly Success",
        marker_color="#f4f4f5",
        marker_line=dict(color="#e4e4e7", width=1),
        hoverinfo="x+y"
    ))
    # Rolling 4W line
    fig_trend.add_trace(go.Scatter(
        x=weekly_agg["week_start"],
        y=weekly_agg["rolling_4w"],
        mode="lines",
        name="4-Week Rolling Average",
        line=dict(color="#18181b", width=2.5)
    ))
    fig_trend.update_layout(
        template="plotly_white",
        height=320,
        font=PLOT_FONT,
        margin=dict(l=30, r=20, t=10, b=30),
        yaxis=dict(range=[60, 100], gridcolor=GRID_COLOR, zeroline=False, title="Success Rate (%)"),
        xaxis=dict(showgrid=False, title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("##### The Three Root Operational Drivers (Simulated)")

    # 3-Column Minimalist Drivers Breakdown
    d_col1, d_col2, d_col3 = st.columns(3)

    with d_col1:
        st.markdown("**1. Experience Curve (Tenure)**")
        t_summary = sessions_raw.groupby("tenure_bucket", observed=False)["success"].mean().reset_index()
        t_summary["pct"] = t_summary["success"] * 100.0

        fig_t = px.bar(
            t_summary,
            x="tenure_bucket",
            y="pct",
            text=t_summary["pct"].apply(lambda v: f"{v:.1f}%"),
            color_discrete_sequence=["#18181b"]
        )
        fig_t.update_layout(
            template="plotly_white",
            height=240,
            font=PLOT_FONT,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(range=[50, 100], gridcolor=GRID_COLOR, showticklabels=False, title=None),
            xaxis=dict(title=None)
        )
        fig_t.update_traces(textposition="outside", marker_color=["#ef4444", "#71717a", "#18181b"])
        st.plotly_chart(fig_t, use_container_width=True)
        st.caption("Novice operators (<30d) exhibit a 10.1% deficit vs seniors.")

    with d_col2:
        st.markdown("**2. Shift Circadian Deficit**")
        s_summary = sessions_raw.groupby("shift")["success"].mean().reset_index()
        s_summary["pct"] = s_summary["success"] * 100.0

        fig_s = px.bar(
            s_summary,
            x="shift",
            y="pct",
            text=s_summary["pct"].apply(lambda v: f"{v:.1f}%"),
            color_discrete_sequence=["#18181b"]
        )
        fig_s.update_layout(
            template="plotly_white",
            height=240,
            font=PLOT_FONT,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(range=[50, 100], gridcolor=GRID_COLOR, showticklabels=False, title=None),
            xaxis=dict(title=None)
        )
        fig_s.update_traces(textposition="outside", marker_color=["#18181b", "#18181b", "#ef4444"])
        st.plotly_chart(fig_s, use_container_width=True)
        st.caption("Night shift operations drop 12.2% below daytime benchmarks.")

    with d_col3:
        st.markdown("**3. Network Latency Cliff**")
        l_summary = sessions_raw.groupby("latency_bucket", observed=False)["success"].apply(
            lambda x: (1.0 - x.mean()) * 100.0
        ).reset_index()
        l_summary.columns = ["latency_bucket", "fail_pct"]

        fig_l = px.bar(
            l_summary,
            x="latency_bucket",
            y="fail_pct",
            text=l_summary["fail_pct"].apply(lambda v: f"{v:.1f}%"),
            color_discrete_sequence=["#18181b"]
        )
        fig_l.update_layout(
            template="plotly_white",
            height=240,
            font=PLOT_FONT,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(range=[0, 50], gridcolor=GRID_COLOR, showticklabels=False, title=None),
            xaxis=dict(title=None)
        )
        fig_l.update_traces(textposition="outside", marker_color=["#e4e4e7", "#e4e4e7", "#71717a", "#ef4444"])
        st.plotly_chart(fig_l, use_container_width=True)
        st.caption("Failure rate jumps to 37.7% on round-trip delays ≥150ms.")


# ------------------------------------------------------------------------------
# TAB 2: ACTIONABLE RECOMMENDATIONS (DATA-BACKED MEMO SUMMARY)
# ------------------------------------------------------------------------------
with main_tabs[1]:
    st.markdown("##### Executive Recommendations & Quantified ROI (Under Model Assumptions)")
    st.caption("Each impact estimate includes explicit inputs, denominators, calculations, and +/-25% sensitivity bounds.")

    r_col1, r_col2, r_col3 = st.columns(3)

    with r_col1:
        st.markdown("""
        <div class="rec-card">
            <span class="rec-badge">Recommendation 1</span>
            <div class="rec-title">Novice Gating & Mentorship</div>
            <div class="rec-body">
                <strong>Finding:</strong> Novice operators (<30d) achieve only 72.4% success (10.1% deficit) and trigger 4.03 interventions/task.<br><br>
                <strong>Action:</strong> Restrict new operators to routine pick-and-place; mandate 40 live shadowed sessions with senior peers.
            </div>
            <div class="rec-impact">
                Estimated Lift: +0.11% fleet throughput<br>
                <span style="font-weight:400; color:#71717a;">Range (±25%): +0.08% to +0.13% (10–16 sessions)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with r_col2:
        st.markdown("""
        <div class="rec-card">
            <span class="rec-badge">Recommendation 2</span>
            <div class="rec-title">Follow-the-Sun Rebalance</div>
            <div class="rec-body">
                <strong>Finding:</strong> Evening shifts are 92% congested; Night shifts are 55% underutilized with a 12.2% day-night success gap.<br><br>
                <strong>Action:</strong> Shift 35% of nominal graveyard capacity to daytime rosters in India/Mexico hubs; reschedule data curation tasks.
            </div>
            <div class="rec-impact">
                Estimated Lift: +1.63% fleet throughput<br>
                <span style="font-weight:400; color:#71717a;">Range (±25%): +1.23% to +2.05% (146–243 sessions)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with r_col3:
        st.markdown("""
        <div class="rec-card">
            <span class="rec-badge">Recommendation 3</span>
            <div class="rec-title">Latency-Aware Dispatch Broker</div>
            <div class="rec-body">
                <strong>Finding:</strong> Latency ≥150ms spikes failures to 37.7% (vs 15.0% for <50ms); intercontinental routing harms dexterous tasks.<br><br>
                <strong>Action:</strong> Enforce ≤80ms hard ceiling on complex manipulation (Mexico & US); route latency-tolerant tasks to India.
            </div>
            <div class="rec-impact">
                Estimated Lift: +1.60% fleet throughput<br>
                <span style="font-weight:400; color:#71717a;">Range (±25%): +1.20% to +2.00% (143–238 failures avoided)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    with st.expander("📄 View Full Markdown Operations Memorandum (Auto-Generated)"):
        if os.path.exists(MEMO_PATH):
            with open(MEMO_PATH, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("Run `python src/analysis.py` to compile the memorandum.")


# ------------------------------------------------------------------------------
# TAB 3: DETAILED TELEMETRY & LEADERBOARDS
# ------------------------------------------------------------------------------
with main_tabs[2]:
    tab3_c1, tab3_c2 = st.columns([1, 1])

    with tab3_c1:
        st.markdown("##### Bottom 10 Operators by Success Rate (Min 40 Sessions)")
        st.caption("Identifies candidates for targeted mentorship or complexity restrictions.")
        
        op_agg = sessions_raw.groupby(["operator_id", "region", "tenure_days", "primary_shift"]).agg(
            sessions=("session_id", "count"),
            success_rate=("success", lambda x: x.mean() * 100.0),
            interventions=("interventions", "mean")
        ).reset_index()

        bottom_10 = op_agg[op_agg["sessions"] >= 40].sort_values("success_rate", ascending=True).head(10)
        st.dataframe(
            bottom_10,
            column_config={
                "operator_id": "Operator",
                "region": "Hub",
                "tenure_days": "Tenure (Days)",
                "primary_shift": "Shift",
                "sessions": "Sessions",
                "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1f%%"),
                "interventions": st.column_config.NumberColumn("Interventions", format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )

    with tab3_c2:
        st.markdown("##### Task Type Success & Physical Difficulty")
        st.caption("Structured vs dexterous manipulation completion rates.")

        task_agg = sessions_raw.groupby("task_type").agg(
            sessions=("session_id", "count"),
            success_rate=("success", lambda x: x.mean() * 100.0),
            avg_duration=("duration_min", "mean")
        ).reset_index().sort_values("success_rate", ascending=False)

        st.dataframe(
            task_agg,
            column_config={
                "task_type": "Robot Task Type",
                "sessions": "Completed Runs",
                "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1f%%"),
                "avg_duration": st.column_config.NumberColumn("Avg Duration (min)", format="%.1f")
            },
            hide_index=True,
            use_container_width=True
        )


# ------------------------------------------------------------------------------
# TAB 4: UNIT ECONOMICS
# ------------------------------------------------------------------------------
with main_tabs[3]:
    st.markdown("##### Fully Loaded Labor Economics by Regional Operating Center")
    st.caption("Shift wages applied across active operational hours divided by successful teleoperated tasks.")

    cost_rows = []
    for reg, label in [("India", "Offshore (India)"), ("Mexico", "Nearshore (Mexico)"), ("US", "Domestic (US)")]:
        r_sess = sessions_raw[sessions_raw["region"] == reg]
        r_succ = r_sess["success"].sum()
        r_tot = len(r_sess)
        r_shifts = shifts_raw.merge(operators_raw[["operator_id", "region"]], on="operator_id")
        r_shifts = r_shifts[r_shifts["region"] == reg]
        wages = operators_raw.set_index("operator_id")["hourly_cost_usd"].to_dict()
        spend = sum(row["active_hours"] * wages.get(row["operator_id"], 10.0) for _, row in r_shifts.iterrows())
        unit_cost = (spend / r_succ) if r_succ > 0 else 0.0
        avg_w = operators_raw[operators_raw["region"] == reg]["hourly_cost_usd"].mean()

        cost_rows.append({
            "Hub": label,
            "Avg_Wage": avg_w,
            "Sessions": r_tot,
            "Success_Rate": (r_succ / r_tot) * 100.0,
            "Active_Spend": spend,
            "Unit_Cost": unit_cost
        })

    cost_table_df = pd.DataFrame(cost_rows)

    st.dataframe(
        cost_table_df,
        column_config={
            "Hub": "Operating Hub",
            "Avg_Wage": st.column_config.NumberColumn("Avg Wage", format="$%.2f/hr"),
            "Sessions": st.column_config.NumberColumn("Sessions", format="%d"),
            "Success_Rate": st.column_config.NumberColumn("Success Rate", format="%.1f%%"),
            "Active_Spend": st.column_config.NumberColumn("Total Active Labor", format="$%,.2f"),
            "Unit_Cost": st.column_config.NumberColumn("Cost / Successful Task", format="$%.2f")
        },
        hide_index=True,
        use_container_width=True
    )
    st.caption("Strategic Takeaway: Mexico offers the highest value-to-latency ratio ($41.14/success with ~55ms latency to US sites), whereas India provides bulk volume scale ($25.76/success).")

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("""
<div class="minimal-footer">
    Teleoperation Operations Intelligence &bull; Minimalist Executive Architecture &bull; 
    <em>Synthetic data for portfolio demonstration only under model assumptions.</em>
</div>
""", unsafe_allow_html=True)
