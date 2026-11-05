"""
app.py
Streamlit Dashboard for Teleoperation Operations & Analytics.
Visualizes fleet performance, workforce utilization, latency, quality, cost,
and automated operational recommendations using Streamlit and Plotly.
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
    page_title="Teleoperation Ops Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for executive look and feel
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .synthetic-badge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
        border: 1px solid #FCD34D;
    }
    .metric-card {
        background: #FFFFFF;
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 0.3rem;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #10B981;
        margin-top: 0.2rem;
    }
    .chart-caption {
        font-size: 0.85rem;
        color: #475569;
        font-style: italic;
        background-color: #F8FAFC;
        padding: 0.4rem 0.8rem;
        border-left: 3px solid #3B82F6;
        border-radius: 0 4px 4px 0;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }
    .footer {
        text-align: center;
        padding: 1.5rem 0;
        font-size: 0.85rem;
        color: #94A3B8;
        border-top: 1px solid #E2E8F0;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "ops.db")
MEMO_PATH = os.path.join(BASE_DIR, "reports", "ops_memo.md")

# Palette constants
PRIMARY_COLOR = "#2563EB"
SECONDARY_COLOR = "#0D9488"
ACCENT_COLOR = "#F59E0B"
DANGER_COLOR = "#EF4444"
PURPLE_COLOR = "#8B5CF6"


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
        
    # Convert dates
    sessions_df["session_date"] = pd.to_datetime(sessions_df["session_date"])
    shifts_df["shift_date"] = pd.to_datetime(shifts_df["shift_date"])
    operators_df["join_date"] = pd.to_datetime(operators_df["join_date"])
    
    # Merge operator attributes onto sessions
    merged_sessions = sessions_df.merge(
        operators_df[["operator_id", "region", "tenure_days", "hourly_cost_usd", "primary_shift"]],
        on="operator_id",
        how="left"
    )
    
    # Tenure bucket
    merged_sessions["tenure_bucket"] = pd.cut(
        merged_sessions["tenure_days"],
        bins=[-1, 30, 90, 99999],
        labels=["0-30 days", "31-90 days", "90+ days"]
    )
    
    # Latency bucket
    merged_sessions["latency_bucket"] = pd.cut(
        merged_sessions["latency_ms"],
        bins=[0, 50, 100, 150, 99999],
        labels=["<50ms", "50-100ms", "100-150ms", "150ms+"]
    )
    
    return operators_df, shifts_df, merged_sessions


# Load base datasets
operators_raw, shifts_raw, sessions_raw = load_base_data()

# ==========================================
# SIDEBAR FILTERS
# ==========================================
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    st.title("Ops Filter Console")
    st.caption("Slice fleet telemetry across operational parameters")
    
    # Date Range Filter
    min_date = sessions_raw["session_date"].min().date()
    max_date = sessions_raw["session_date"].max().date()
    date_range = st.date_input(
        "Session Date Window",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Region Filter
    all_regions = sorted(operators_raw["region"].unique().tolist())
    selected_regions = st.multiselect(
        "Operator Region",
        options=all_regions,
        default=all_regions
    )
    
    # Shift Filter
    all_shifts = ["Morning", "Evening", "Night"]
    selected_shifts = st.multiselect(
        "Operational Shift",
        options=all_shifts,
        default=all_shifts
    )
    
    # Task Type Filter
    all_tasks = sorted(sessions_raw["task_type"].unique().tolist())
    selected_tasks = st.multiselect(
        "Task Type",
        options=all_tasks,
        default=all_tasks
    )
    
    st.divider()
    st.markdown("**Dataset Parameters:**")
    st.markdown(f"- Active Operators: `{len(operators_raw):,}`")
    st.markdown(f"- Total Tracked Sessions: `{len(sessions_raw):,}`")
    st.markdown(f"- Total Logged Shifts: `{len(shifts_raw):,}`")
    st.divider()
    st.info("💡 **Notice:** Synthetic data for portfolio demonstration only.")


# Filter application
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_filter, end_filter = date_range
else:
    start_filter, end_filter = min_date, max_date

filtered_sessions = sessions_raw[
    (sessions_raw["session_date"].dt.date >= start_filter) &
    (sessions_raw["session_date"].dt.date <= end_filter) &
    (sessions_raw["region"].isin(selected_regions)) &
    (sessions_raw["shift"].isin(selected_shifts)) &
    (sessions_raw["task_type"].isin(selected_tasks))
]

# Filter shifts accordingly
filtered_shifts = shifts_raw.merge(
    operators_raw[["operator_id", "region"]], on="operator_id", how="left"
)
filtered_shifts = filtered_shifts[
    (filtered_shifts["shift_date"].dt.date >= start_filter) &
    (filtered_shifts["shift_date"].dt.date <= end_filter) &
    (filtered_shifts["region"].isin(selected_regions)) &
    (filtered_shifts["shift_type"].isin(selected_shifts))
]

# Prevent empty slice issues
if filtered_sessions.empty:
    st.warning("No sessions match the selected filter criteria. Please broaden your selection.")
    st.stop()


# Header Banner
st.markdown('<div class="main-header">🤖 Teleoperation Ops Intelligence Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Simulated Fleet Performance, Workforce Utilization, Network Latency & Unit Cost Diagnostics</div>', unsafe_allow_html=True)
st.markdown('<div class="synthetic-badge">⚠️ SYNTHETIC DATA FOR PORTFOLIO DEMONSTRATION ONLY</div>', unsafe_allow_html=True)


# TABS NAVIGATION
tabs = st.tabs([
    "📈 Overview",
    "👥 Operators",
    "⏱️ Shifts & Utilization",
    "📡 Latency & Quality",
    "💰 Cost Diagnostics",
    "📋 Ops Memo & Recommendations"
])

# ==========================================
# TAB 1: OVERVIEW
# ==========================================
with tabs[0]:
    # Top KPI Cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_sess = len(filtered_sessions)
    success_rate = filtered_sessions["success"].mean() * 100.0
    avg_latency = filtered_sessions["latency_ms"].mean()
    qa_subset = filtered_sessions.dropna(subset=["quality_score"])
    avg_quality = qa_subset["quality_score"].mean() if not qa_subset.empty else 0.0
    acceptance_rate = filtered_sessions["data_accepted"].mean() * 100.0
    
    # Cost per successful session
    successful_sess = filtered_sessions["success"].sum()
    # Allocate proportional labor cost from shifts
    total_labor_spend = (filtered_shifts["active_hours"] * filtered_shifts.merge(operators_raw[["operator_id", "hourly_cost_usd"]], on="operator_id")["hourly_cost_usd"]).sum()
    cost_per_success = (total_labor_spend / successful_sess) if successful_sess > 0 else 0.0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Sessions</div>
            <div class="metric-value">{total_sess:,}</div>
            <div class="metric-sub">90-Day Teleop Volume</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
            <div class="metric-sub">Target: &ge;85.0%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Latency</div>
            <div class="metric-value">{avg_latency:.1f}<span style="font-size:1rem;">ms</span></div>
            <div class="metric-sub">Target: &le;100ms</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg QA Quality</div>
            <div class="metric-value">{avg_quality:.2f}<span style="font-size:1rem;">/5</span></div>
            <div class="metric-sub">Review Rate: {len(qa_subset)/total_sess:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Data Acceptance</div>
            <div class="metric-value">{acceptance_rate:.1f}%</div>
            <div class="metric-sub">Training Pipeline Yield</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Cost / Success</div>
            <div class="metric-value">${cost_per_success:.2f}</div>
            <div class="metric-sub">Fully Loaded Labor</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Longitudinal Weekly Trend (SQL Window Function Equivalent)
    st.subheader("Longitudinal Fleet Performance (Weekly Aggregation & Rolling 4-Week Moving Average)")
    
    # Compute weekly rolling stats
    filtered_sessions["week_start"] = filtered_sessions["session_date"].dt.to_period("W").dt.start_time
    weekly_agg = filtered_sessions.groupby("week_start").agg(
        sessions=("session_id", "count"),
        success_rate=("success", "mean"),
        quality=("quality_score", "mean"),
        acceptance=("data_accepted", "mean"),
        latency=("latency_ms", "mean")
    ).reset_index()
    
    weekly_agg["success_rate_pct"] = weekly_agg["success_rate"] * 100.0
    weekly_agg["acceptance_pct"] = weekly_agg["acceptance"] * 100.0
    weekly_agg["rolling_4wk_success"] = weekly_agg["success_rate_pct"].rolling(4, min_periods=1).mean()
    weekly_agg["rolling_4wk_quality"] = weekly_agg["quality"].rolling(4, min_periods=1).mean()
    
    fig_weekly = go.Figure()
    # Weekly Success Bar / Scatter
    fig_weekly.add_trace(go.Bar(
        x=weekly_agg["week_start"],
        y=weekly_agg["success_rate_pct"],
        name="Weekly Success Rate (%)",
        marker_color="rgba(37, 99, 235, 0.35)",
        yaxis="y1"
    ))
    # Rolling 4W Success Line
    fig_weekly.add_trace(go.Scatter(
        x=weekly_agg["week_start"],
        y=weekly_agg["rolling_4wk_success"],
        mode="lines+markers",
        name="Rolling 4-Wk Avg Success (%)",
        line=dict(color=PRIMARY_COLOR, width=3),
        yaxis="y1"
    ))
    # Rolling 4W Quality
    fig_weekly.add_trace(go.Scatter(
        x=weekly_agg["week_start"],
        y=weekly_agg["rolling_4wk_quality"],
        mode="lines+markers",
        name="Rolling 4-Wk Avg Quality (1-5)",
        line=dict(color="#10B981", width=3, dash="dot"),
        yaxis="y2"
    ))
    
    fig_weekly.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=40, r=40, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Success Rate (%)", range=[60, 100]),
        yaxis2=dict(title="Quality Rating (1-5)", overlaying="y", side="right", range=[2.5, 5.0])
    )
    st.plotly_chart(fig_weekly, use_container_width=True)
    st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, longitudinal trends reveal how cohort onboarding and shift allocations create weekly variances; 4-week moving average demonstrates simulated fleet stabilization.</div>', unsafe_allow_html=True)
    
    # Breakdown row: Task Distribution + Region Summary
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Session Volume by Task Complexity")
        task_counts = filtered_sessions["task_type"].value_counts().reset_index()
        task_counts.columns = ["Task Type", "Sessions"]
        fig_tasks = px.pie(
            task_counts,
            names="Task Type",
            values="Sessions",
            color_discrete_sequence=px.colors.qualitative.Prism,
            hole=0.45
        )
        fig_tasks.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_tasks, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, simulated pick-and-place & bin-sorting represent over 55% of operations; dexterous deformable handling and door traversal comprise ~26%.</div>', unsafe_allow_html=True)
        
    with c2:
        st.subheader("Regional Performance Breakdown")
        reg_summary = filtered_sessions.groupby("region").agg(
            Sessions=("session_id", "count"),
            Success_Rate=("success", lambda x: f"{x.mean()*100:.1f}%"),
            Avg_Latency=("latency_ms", lambda x: f"{x.mean():.1f} ms"),
            Acceptance=("data_accepted", lambda x: f"{x.mean()*100:.1f}%")
        ).reset_index()
        st.dataframe(
            reg_summary,
            column_config={
                "region": "Operator Region",
                "Sessions": st.column_config.NumberColumn(format="%d"),
                "Success_Rate": "Success Rate",
                "Avg_Latency": "Avg Latency",
                "Acceptance": "Data Acceptance"
            },
            hide_index=True,
            use_container_width=True
        )
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, Indian operators process the majority of sessions at lowest unit cost, while US and Mexico deliver sub-60ms round-trip latency.</div>', unsafe_allow_html=True)


# ==========================================
# TAB 2: OPERATORS
# ==========================================
with tabs[1]:
    st.subheader("Operator Cohort & Experience Diagnostics")
    
    col_t1, col_t2 = st.columns([1, 1])
    
    with col_t1:
        st.markdown("**Performance by Experience Level (Tenure Buckets)**")
        tenure_summary = filtered_sessions.groupby("tenure_bucket", observed=False).agg(
            sessions=("session_id", "count"),
            success_rate=("success", lambda x: x.mean() * 100.0),
            interventions=("interventions", "mean"),
            avg_quality=("quality_score", "mean")
        ).reset_index()
        
        fig_tenure = px.bar(
            tenure_summary,
            x="tenure_bucket",
            y="success_rate",
            color="tenure_bucket",
            text=tenure_summary["success_rate"].apply(lambda v: f"{v:.1f}%"),
            color_discrete_sequence=["#EF4444", "#F59E0B", "#10B981"],
            labels={"tenure_bucket": "Tenure Cohort", "success_rate": "Success Rate (%)"}
        )
        fig_tenure.update_layout(
            template="plotly_white",
            showlegend=False,
            height=340,
            yaxis=dict(range=[50, 100]),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_tenure, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, operators with tenure &lt; 30 days trail senior operators (&gt;90 days) by ~10-14 percentage points, highlighting the simulated ramp penalty.</div>', unsafe_allow_html=True)
        
    with col_t2:
        st.markdown("**Intervention Frequency by Operator Tenure**")
        fig_interv = px.line(
            tenure_summary,
            x="tenure_bucket",
            y="interventions",
            markers=True,
            labels={"tenure_bucket": "Tenure Cohort", "interventions": "Avg Interventions / Session"},
            color_discrete_sequence=[PURPLE_COLOR]
        )
        fig_interv.update_layout(
            template="plotly_white",
            height=340,
            yaxis=dict(range=[1, 5]),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_interv, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, early-tenure operators trigger more interventions per session, increasing supervisor cycle overhead.</div>', unsafe_allow_html=True)
        
    st.divider()
    
    # Bottom 10 Operators Table
    st.subheader("Bottom 10 Operators by Success Rate (Minimum 40 Sessions)")
    st.caption("Identifies candidates for targeted retraining, mentorship pairing, or task-type restrictions.")
    
    op_perf = filtered_sessions.groupby(["operator_id", "region", "tenure_days", "primary_shift"]).agg(
        total_sessions=("session_id", "count"),
        successes=("success", "sum"),
        success_rate=("success", lambda x: x.mean() * 100.0),
        avg_quality=("quality_score", "mean"),
        avg_interventions=("interventions", "mean")
    ).reset_index()
    
    bottom_10 = op_perf[op_perf["total_sessions"] >= 40].sort_values(
        by=["success_rate", "total_sessions"], ascending=[True, False]
    ).head(10)
    
    bottom_10["tenure_bucket"] = pd.cut(
        bottom_10["tenure_days"],
        bins=[-1, 30, 90, 9999],
        labels=["0-30 days", "31-90 days", "90+ days"]
    )
    
    st.dataframe(
        bottom_10[[
            "operator_id", "region", "tenure_bucket", "primary_shift",
            "total_sessions", "success_rate", "avg_quality", "avg_interventions"
        ]],
        column_config={
            "operator_id": "Operator ID",
            "region": "Region",
            "tenure_bucket": "Tenure Cohort",
            "primary_shift": "Shift",
            "total_sessions": "Completed Sessions",
            "success_rate": st.column_config.NumberColumn("Success Rate (%)", format="%.1f%%"),
            "avg_quality": st.column_config.NumberColumn("Avg Quality (1-5)", format="%.2f"),
            "avg_interventions": st.column_config.NumberColumn("Avg Interventions", format="%.2f")
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.divider()
    
    # Regional Leaderboards (Window Rank Equivalent)
    st.subheader("Regional Top Operator Leaderboard (Ranked by Quality Score & Success Rate)")
    leaderboard_candidates = op_perf[op_perf["total_sessions"] >= 30].copy()
    leaderboard_candidates["regional_rank"] = leaderboard_candidates.groupby("region")["avg_quality"].rank(
        ascending=False, method="min"
    ).astype(int)
    
    top_per_region = leaderboard_candidates.sort_values(
        by=["region", "regional_rank"]
    ).groupby("region").head(5)
    
    st.dataframe(
        top_per_region[[
            "region", "regional_rank", "operator_id", "tenure_days", "primary_shift",
            "total_sessions", "avg_quality", "success_rate"
        ]],
        column_config={
            "region": "Region",
            "regional_rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "operator_id": "Operator",
            "tenure_days": "Tenure (Days)",
            "primary_shift": "Shift",
            "total_sessions": "Sessions",
            "avg_quality": st.column_config.NumberColumn("Avg QA Rating", format="%.2f / 5.0"),
            "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1f%%")
        },
        hide_index=True,
        use_container_width=True
    )


# ==========================================
# TAB 3: SHIFTS & UTILIZATION
# ==========================================
with tabs[2]:
    st.subheader("Workforce Utilization & Shift Imbalance Diagnostics")
    
    col_u1, col_u2 = st.columns([1, 1])
    
    with col_u1:
        st.markdown("**Workforce Utilization Heatmap (Shift × Region)**")
        # Compute active / scheduled
        util_matrix = filtered_shifts.groupby(["shift_type", "region"]).apply(
            lambda x: (x["active_hours"].sum() / x["scheduled_hours"].sum()) * 100.0,
            include_groups=False
        ).unstack()
        
        fig_heat = px.imshow(
            util_matrix,
            labels=dict(x="Operator Region", y="Shift", color="Utilization (%)"),
            color_continuous_scale="Blues",
            text_auto=".1f",
            aspect="auto"
        )
        fig_heat.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_heat, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, Evening shifts are heavily congested (&gt;90% utilization across all hubs), while Night shifts suffer simulated underutilization (~55%).</div>', unsafe_allow_html=True)
        
    with col_u2:
        st.markdown("**Session Success Rate & Review Quality by Shift**")
        shift_perf = filtered_sessions.groupby("shift").agg(
            success_rate=("success", lambda x: x.mean() * 100.0),
            quality_score=("quality_score", "mean")
        ).reset_index()
        
        fig_shift_perf = px.bar(
            shift_perf,
            x="shift",
            y="success_rate",
            color="shift",
            text=shift_perf["success_rate"].apply(lambda v: f"{v:.1f}%"),
            color_discrete_map={"Morning": "#10B981", "Evening": "#3B82F6", "Night": "#EF4444"},
            labels={"shift": "Operational Shift", "success_rate": "Success Rate (%)"}
        )
        fig_shift_perf.update_layout(
            template="plotly_white",
            showlegend=False,
            height=340,
            yaxis=dict(range=[60, 100]),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_shift_perf, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, Night shifts exhibit a success rate deficit, simulating circadian disruption on overseas night schedules.</div>', unsafe_allow_html=True)
        
    st.divider()
    
    # Hours comparison
    st.subheader("Scheduled vs. Active Teleoperation Hours by Shift")
    hours_df = filtered_shifts.groupby("shift_type").agg(
        Scheduled_Hours=("scheduled_hours", "sum"),
        Active_Hours=("active_hours", "sum")
    ).reset_index()
    hours_df["Idle_Hours"] = hours_df["Scheduled_Hours"] - hours_df["Active_Hours"]
    hours_df["Utilization_Rate"] = (hours_df["Active_Hours"] / hours_df["Scheduled_Hours"]) * 100.0
    
    fig_hours = go.Figure()
    fig_hours.add_trace(go.Bar(
        name="Active Teleoperation Hours",
        x=hours_df["shift_type"],
        y=hours_df["Active_Hours"],
        marker_color="#2563EB"
    ))
    fig_hours.add_trace(go.Bar(
        name="Idle / Standby Hours",
        x=hours_df["shift_type"],
        y=hours_df["Idle_Hours"],
        marker_color="#CBD5E1"
    ))
    fig_hours.update_layout(
        barmode="stack",
        template="plotly_white",
        height=320,
        yaxis=dict(title="Workforce Hours"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_hours, use_container_width=True)
    st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, Night shifts accumulate unutilized paid standby hours. Transitioning non-urgent data workflows to follow-the-sun daytime hours directly recaptures this lost capacity.</div>', unsafe_allow_html=True)


# ==========================================
# TAB 4: LATENCY & QUALITY
# ==========================================
with tabs[3]:
    st.subheader("Network Latency, Manipulation Complexity & Quality Diagnostics")
    
    col_l1, col_l2 = st.columns([1, 1])
    
    with col_l1:
        st.markdown("**Failure Rate Escalation Across Latency Tiers**")
        lat_summary = filtered_sessions.groupby("latency_bucket", observed=False).agg(
            total_sessions=("session_id", "count"),
            failure_rate=("success", lambda x: (1.0 - x.mean()) * 100.0),
            interventions=("interventions", "mean")
        ).reset_index()
        
        fig_lat = px.bar(
            lat_summary,
            x="latency_bucket",
            y="failure_rate",
            color="latency_bucket",
            text=lat_summary["failure_rate"].apply(lambda v: f"{v:.1f}%"),
            color_discrete_sequence=["#10B981", "#3B82F6", "#F59E0B", "#DC2626"],
            labels={"latency_bucket": "Round-Trip Latency Tier", "failure_rate": "Failure Rate (%)"}
        )
        fig_lat.update_layout(
            template="plotly_white",
            showlegend=False,
            height=340,
            yaxis=dict(range=[0, 50]),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_lat, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, when round-trip latency exceeds 150ms, session failure rate jumps to ~37% (2.5x higher than sub-50ms connections), establishing a simulated routing threshold.</div>', unsafe_allow_html=True)
        
    with col_l2:
        st.markdown("**Success Rate by Robot Task Complexity**")
        task_summary = filtered_sessions.groupby("task_type").agg(
            success_rate=("success", lambda x: x.mean() * 100.0),
            avg_duration=("duration_min", "mean"),
            avg_interventions=("interventions", "mean")
        ).reset_index().sort_values("success_rate", ascending=True)
        
        fig_task = px.bar(
            task_summary,
            x="success_rate",
            y="task_type",
            orientation="h",
            color="success_rate",
            text=task_summary["success_rate"].apply(lambda v: f"{v:.1f}%"),
            color_continuous_scale="Blues",
            labels={"task_type": "Robot Task Type", "success_rate": "Success Rate (%)"}
        )
        fig_task.update_layout(
            template="plotly_white",
            coloraxis_showscale=False,
            height=340,
            xaxis=dict(range=[50, 100]),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_task, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, deformable object handling and door opening present the highest simulated failure rates, reflecting task kinematics.</div>', unsafe_allow_html=True)
        
    st.divider()
    
    # Training Data Acceptance by Shift and Task Type
    st.subheader("Training Data Acceptance Rate (Shift × Task Type)")
    st.caption("Training data generation is a secondary monetization engine; acceptance reflects session quality and smooth execution.")
    
    data_acc_matrix = filtered_sessions.groupby(["shift", "task_type"])["data_accepted"].mean().unstack() * 100.0
    
    fig_acc = px.imshow(
        data_acc_matrix,
        labels=dict(x="Task Type", y="Shift", color="Data Acceptance (%)"),
        color_continuous_scale="Viridis",
        text_auto=".1f",
        aspect="auto"
    )
    fig_acc.update_layout(height=320, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_acc, use_container_width=True)
    st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, daytime pick-and-place yields higher acceptable autonomous training data than complex night sessions.</div>', unsafe_allow_html=True)


# ==========================================
# TAB 5: COST ANALYSIS
# ==========================================
with tabs[4]:
    st.subheader("Unit Economics & Fully Loaded Labor Cost Diagnostics")
    
    col_c1, col_c2 = st.columns([1, 1])
    
    with col_c1:
        st.markdown("**Fully Loaded Labor Cost per Successful Task by Region**")
        # Calculate regional cost per successful task
        # Shifts labor spend / successful sessions
        reg_cost_stats = []
        for reg in selected_regions:
            reg_sess = filtered_sessions[filtered_sessions["region"] == reg]
            reg_succ = reg_sess["success"].sum()
            
            reg_sh = filtered_shifts[filtered_shifts["region"] == reg]
            op_wages = operators_raw.set_index("operator_id")["hourly_cost_usd"].to_dict()
            spend = sum(row["active_hours"] * op_wages.get(row["operator_id"], 10.0) for _, row in reg_sh.iterrows())
            
            unit_cost = (spend / reg_succ) if reg_succ > 0 else 0.0
            avg_wage = operators_raw[operators_raw["region"] == reg]["hourly_cost_usd"].mean()
            
            reg_cost_stats.append({
                "Region": reg,
                "Unit_Cost": unit_cost,
                "Total_Spend": spend,
                "Successful_Tasks": reg_succ,
                "Avg_Wage": avg_wage
            })
            
        cost_df = pd.DataFrame(reg_cost_stats)
        
        fig_unit_cost = px.bar(
            cost_df,
            x="Region",
            y="Unit_Cost",
            color="Region",
            text=cost_df["Unit_Cost"].apply(lambda v: f"${v:.2f}"),
            color_discrete_map={"India": "#10B981", "Mexico": "#3B82F6", "US": "#EF4444"},
            labels={"Unit_Cost": "Cost / Successful Task ($USD)"}
        )
        fig_unit_cost.update_layout(
            template="plotly_white",
            showlegend=False,
            height=340,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_unit_cost, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, India delivers maximum cost efficiency for bulk operations, Mexico offers an optimal cost-to-latency balance, and US reflects domestic wage assumptions.</div>', unsafe_allow_html=True)
        
    with col_c2:
        st.markdown("**Operator Hourly Wage vs. Success Rate Distribution**")
        op_agg = filtered_sessions.groupby(["operator_id", "region"]).agg(
            success_rate=("success", lambda x: x.mean() * 100.0),
            sessions=("session_id", "count"),
            hourly_cost=("hourly_cost_usd", "first")
        ).reset_index()
        
        fig_scatter = px.scatter(
            op_agg,
            x="hourly_cost",
            y="success_rate",
            color="region",
            size="sessions",
            hover_data=["operator_id"],
            labels={"hourly_cost": "Operator Hourly Wage ($USD)", "success_rate": "Success Rate (%)"},
            color_discrete_map={"India": "#10B981", "Mexico": "#3B82F6", "US": "#EF4444"}
        )
        fig_scatter.update_layout(
            template="plotly_white",
            height=340,
            yaxis=dict(range=[55, 100]),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown('<div class="chart-caption">Takeaway: Under the model\'s assumptions, higher wages in the US reflect simulated market wage assumptions rather than a proportional performance premium.</div>', unsafe_allow_html=True)
        
    st.divider()
    
    # Financial Summary Table
    st.subheader("Regional Direct Labor Financial Summary")
    st.dataframe(
        cost_df,
        column_config={
            "Region": "Operator Region",
            "Avg_Wage": st.column_config.NumberColumn("Avg Hourly Wage", format="$%.2f/hr"),
            "Successful_Tasks": st.column_config.NumberColumn("Successful Tasks", format="%d"),
            "Total_Spend": st.column_config.NumberColumn("Total Active Labor Spend", format="$%,.2f"),
            "Unit_Cost": st.column_config.NumberColumn("Direct Cost / Success", format="$%.2f")
        },
        hide_index=True,
        use_container_width=True
    )


# ==========================================
# TAB 6: OPS MEMO & RECOMMENDATIONS
# ==========================================
with tabs[5]:
    st.subheader("Executive Operations Memorandum & Recommendations")
    st.caption("Auto-generated from simulated query results in SQLite under the model's assumptions; zero hardcoded figures.")
    
    if os.path.exists(MEMO_PATH):
        with open(MEMO_PATH, "r", encoding="utf-8") as f:
            memo_markdown = f.read()
        st.markdown(memo_markdown)
    else:
        st.warning("Ops memo file not found. Please run `python src/analysis.py` to compile the report.")


# Dashboard Footer
st.markdown("""
<div class="footer">
    <strong>Teleoperation Ops Intelligence Platform</strong> • 
    Built with Streamlit, Plotly, Pandas & SQLite • 
    <em>Synthetic data for portfolio demonstration only.</em>
</div>
""", unsafe_allow_html=True)

