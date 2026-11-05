# Teleoperation Ops Intelligence Dashboard & Analytics Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Database-SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-orange.svg)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Pytest-Passing-brightgreen.svg)](https://pytest.org/)

> ** CRITICAL DISCLAIMER: ALL DATA IS SYNTHETIC**  
> *This repository simulates the operational telemetry and workforce dynamics of a remote robot-teleoperation company. **All data, metrics, operator profiles, logs, and financial models are 100% synthetically generated** for portfolio demonstration and analytics evaluation under explicit model assumptions. Do not present or interpret this repository as real company data.*

---

## 1. Project Summary

In robot-teleoperation companies, fleets of physical robots (manipulators, mobile bases, warehouse pickers) deployed across customer sites encounter autonomy edge cases. When an autonomous robot encounters ambiguity, a distributed network of human teleoperators intervenes remotely to control and assist the machine.

This portfolio project builds an end-to-end **Analytics Engineering & Operations Intelligence Platform** that:
1. **Generates simulated teleoperation logs** across 150 operators, ~7,700 shifts, and ~12,000 live sessions over a 90-day window under explicit parameters in `assumptions.yaml`.
2. **Loads and models relational data in SQLite (`data/ops.db`)** with strict foreign keys, indexing, and data integrity constraints.
3. **Executes analytical SQL diagnostics** using CTEs, window functions (`RANK()`, rolling 4-week window moving averages), and multi-table aggregations.
4. **Delivers an interactive Streamlit + Plotly executive dashboard (`app.py`)** for multi-dimensional operational filtering across cohorts, shifts, network latency, and robot tasks.
5. **Auto-generates an executive Operations Memorandum (`reports/ops_memo.md`)** with zero hardcoded numbers, deriving data-backed recommendations with stated sensitivity ranges ($\pm 25\%$) and calculations.
6. **Validates data quality via automated Pytest sanity checks (`tests/test_sanity.py`)**.

---

## 2. Business Questions Answered

This platform answers 11 critical operational questions faced by robotics and operations leadership:

1. **Overall Fleet KPIs:** What are our overarching operational numbers across volume, task success, network latency, QA quality ratings, and training data yields under the model's assumptions?
2. **Cohort Onboarding & Tenure:** How does teleoperator task success and intervention frequency evolve across experience cohorts (0–30 days, 31–90 days, 90+ days)?
3. **Shift & Geography Matrix:** How do session completion and quality ratings vary across shifts (Morning, Evening, Night) and operator hubs (India, Mexico, US)?
4. **Workforce Utilization & Scheduling Imbalance:** What is the ratio of active teleoperation hours to scheduled hours, and where is staffing congested or underutilized?
5. **Latency Degradation Thresholds:** At what round-trip network latency tiers do robot task failure rates escalate?
6. **Task Complexity Discrepancies:** Which physical manipulation tasks (`pick_and_place`, `bin_sorting`, `deformable_handling`, `door_navigation`, `recovery_assist`) exhibit the lowest autonomous and teleoperated success?
7. **Fully Loaded Unit Labor Economics:** What is the direct labor cost per successful intervention across regions after accounting for hourly wage differentials and regional success rates?
8. **Underperforming Operator Identification:** Which operators exhibit the lowest success rates (sample size $\ge 40$ sessions) for targeted retraining or mentorship?
9. **Longitudinal Rolling Trends:** What does a 4-week moving average reveal about fleet performance stability, learning curves, and quality evolution?
10. **Regional Quality Leaderboards:** Who are the highest-performing operators ranked within each geographic hub using SQL window functions?
11. **Training Data Pipeline Yield:** What proportion of teleoperated sessions meet QA standards to be sold or utilized as imitation learning demonstration data?

---

## 3. Architecture & Repository Structure

```
ops_dashboard/
├── README.md                 # Complete system documentation, findings & guide
├── assumptions.yaml          # Parameter dictionary for all planted simulation effects
├── requirements.txt          # Pinned Python dependencies
├── app.py                    # Multi-page interactive Streamlit + Plotly dashboard
├── data/
│   ├── operators.csv         # 150 operators (India 60%, Mexico 25.3%, US 14.7%)
│   ├── sessions.csv          # ~12,000 teleop sessions over 90 days
│   ├── shifts.csv            # ~7,700 logged workforce shifts
│   └── ops.db                # SQLite relational database with indexes and schema
├── sql/
│   └── queries.sql           # 11 commented SQL analysis queries
├── src/
│   ├── generate_data.py      # Seeded synthetic telemetry generator (reads assumptions.yaml)
│   ├── load_db.py            # SQLite database schema loader, indexes & constraints
│   └── analysis.py           # SQL runner, memo numbers generator & markdown exporter
├── reports/
│   └── ops_memo.md           # Auto-generated executive memo with data-backed findings
└── tests/
    └── test_sanity.py        # Pytest suite for IDs, foreign keys, latency & utilization
```

---

## 4. Key Operational Findings (Under the Model's Assumptions)

*All figures below are dynamically computed from the underlying SQLite database (`reports/ops_memo.md`):*

- **The Early-Tenure Ramp Penalty:** Novice operators (tenure $<30$ days) achieve a **72.4%** success rate, trailing seasoned operators ($>90$ days tenure at **82.5%**) by **10.1 percentage points**, while triggering significantly more supervisory interventions (4.03 vs 2.59).
- **Shift Congestion vs. Graveyard Underutilization:** Evening shifts operate near capacity at **92.2%** utilization, whereas Night shifts drop to **55.0%** utilization. Night shift success rates drop to **72.6%** (vs **84.8%** on daytime shifts) due to simulated circadian disruption on offshore graveyard schedules.
- **Latency Non-Linear Failure Cliff:** When round-trip network latency crosses 150 ms, session failure rate jumps to **37.7%** (a **2.5x increase** over sub-50 ms connections at 15.0%).
- **Unit Economics Arbitrage:** Fully loaded labor cost per successful teleoperated task is **$25.76** in India, **$41.14** in Mexico, and **$103.37** in the US. Mexico delivers a strong value-to-latency balance (55 ms round-trip latency to US robot sites at $41.14/task).

---

## 5. Model Assumptions Table

All synthetic parameters are declared in `assumptions.yaml` and loaded by `src/generate_data.py`. No magic numbers exist in the generator:

| Category | Parameter Name | Simulated Value | One-Line Rationale | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Global** | `random_seed` | `42` | Guarantees exact reproducible dataset generation across runs | Assumption, not real data |
| **Global** | `simulation_days` | `90` | Standard quarterly operational simulation window (90 days) | Assumption, not real data |
| **Workforce** | `total_operators` | `150` | Target size of distributed operator fleet across hubs | Assumption, not real data |
| **Workforce** | `regional_counts` | India: 90, Mex: 38, US: 22 | Hub split (offshore: 60%, nearshore: 25.3%, domestic: 14.7%) | Assumption, not real data |
| **Workforce** | `hourly_wages_usd` | India: \$4–\$6, Mex: \$7–\$10, US: \$20–\$26 | Simulated competitive regional wage brackets | Assumption, not real data |
| **Workforce** | `tenure_distribution` | New: 16%, Mid: 22%, Senior: 62% | Continuous hiring cohorts spread across preceding 18 months | Assumption, not real data |
| **Shifts** | `utilization_by_shift` | Eve: 92%, Morn: 77%, Night: 55% | Peak evening customer volume vs. graveyard standby idle time | Assumption, not real data |
| **Tasks** | `task_shares` | Pick: 32%, Sort: 26%, Recovery: 16%, Door: 13%, Deform: 13% | Distribution of physical warehouse/logistics robot interventions | Assumption, not real data |
| **Network** | `latencies_ms` | US-US: 40ms, Mex-US: 55ms, Ind-US: 130ms | Speed-of-light fiber routing delays across global regions | Assumption, not real data |
| **Planted Effect** | `tenure_penalties` | $<30$d: -14%, 31–90d: -6% | Novice operator learning curve and control unfamiliarity | Assumption, not real data |
| **Planted Effect** | `night_shift_penalties`| Night: -8%, India Night: -5% | Compound circadian fatigue on counter-cyclical shifts | Assumption, not real data |
| **Planted Effect** | `latency_penalties` | $100–150$ms: -3%, $>150$ms: -20% | Human control instability cliff when teleop feedback exceeds 150ms | Assumption, not real data |
| **QA Yield** | `review_coverage` | `40%` of all sessions | Sub-sampled supervisor QA audit process | Assumption, not real data |
| **QA Yield** | `data_acceptance` | Low-interv: 84%, High-interv: 30%, Failed: 3% | Training dataset acceptance gate based on smooth execution | Assumption, not real data |

---

## 6. How to Run the Project

### Prerequisites
- Python 3.11+ (tested on Python 3.11 and Python 3.13).

### Step-by-Step Execution

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate the synthetic dataset (parameters loaded from `assumptions.yaml`):**
   ```bash
   python src/generate_data.py
   ```
   *Generates `operators.csv` (150 rows), `shifts.csv` (~7,700 rows), and `sessions.csv` (~11,875 rows) in `data/`.*

3. **Initialize the SQLite database and create indexes:**
   ```bash
   python src/load_db.py
   ```
   *Creates `data/ops.db`, applies schema, primary keys, foreign key constraints, and performance indexes.*

4. **Execute SQL analytics and compile the executive Operations Memo:**
   ```bash
   python src/analysis.py
   ```
   *Runs all 11 SQL queries, prints headline operational metrics, and generates `reports/ops_memo.md` with sensitivity ranges ($\pm 25\%$).*

5. **Launch the Streamlit interactive dashboard:**
   ```bash
   streamlit run app.py
   ```
   *Open [http://localhost:8501](http://localhost:8501) in your browser.*

6. **Run the automated sanity test suite:**
   ```bash
   pytest tests/test_sanity.py -v
   ```

*(Note for Windows environments without python in global PATH: helper scripts `.\python.cmd`, `.\streamlit.cmd`, and `.\pytest.cmd` are included in the repository root for convenience).*

---

## 7. Dashboard Preview & Features

```
+------------------------------------------------------------------------------------------+
|  Teleoperation Ops Intelligence Dashboard                    [SYNTHETIC DATA NOTICE]     |
+------------------------------------------------------------------------------------------+
|  Total Sessions   | Success Rate | Avg Latency | Avg QA Score | Data Accept | Cost/Task  |
|     11,875        |    79.7%     |   99.2 ms   |   3.71 / 5   |    62.4%    |   $42.15   |
+------------------------------------------------------------------------------------------+
|  [Tab 1: Overview]          - Weekly 4-week rolling trend & volume distributions         |
|  [Tab 2: Operators]         - Tenure bucket analysis, bottom-10 table & leaderboard      |
|  [Tab 3: Utilization]       - Shift x Region heatmap & scheduled vs active hours         |
|  [Tab 4: Latency & Quality] - Latency failure tiers & task complexity breakdown          |
|  [Tab 5: Cost Diagnostics]  - Unit labor economics & hourly wage vs success scatter      |
|  [Tab 6: Ops Memo]          - Live markdown rendering of dynamic executive memo          |
+------------------------------------------------------------------------------------------+
```

### Key Dashboard Views
- **Executive Overview:** High-level KPI scorecards and an interactive Plotly dual-axis chart showing weekly task success rate alongside a 4-week moving average and QA review scores under the model's assumptions.
- **Operator Diagnostics:** Direct comparison of new vs. senior cohorts with an actionable bottom-10 operator list (min. 40 sessions) for supervisor intervention.
- **Shift & Utilization Heatmap:** Matrix visualizing workforce utilization percentages across shifts and geographic operating centers.
- **Latency & Failure Tiers:** Clear visual representation of the $>150$ ms latency cliff and manipulation task complexity differences.
- **Cost Diagnostics:** Direct labor cost per successful intervention by region and operator hourly wage scatter plots.
- **Operations Memo:** Formatted executive memo rendering actionable recommendations with sensitivity ranges directly in-app.

---

## 8. Assumptions & Limitations

1. **Synthetic Nature of Data:** All operator records, shift timestamps, robot teleoperation sessions, latency figures, and QA review ratings are artificially synthesized using probabilistic distributions declared in `assumptions.yaml`.
2. **Simplified Direct Labor Cost Model:** The cost model accounts for operator hourly wages applied across shift active hours divided by successful sessions. It omits peripheral overhead such as supervisory management, data annotation tools, cloud streaming egress costs, hardware depreciation, and customer site infrastructure fees.
3. **Simulated Network Latency:** Latency distributions model typical transatlantic and transpacific fiber routes (US-to-US ~40 ms, Mexico-to-US ~55 ms, India-to-US ~130 ms) with occasional synthetic packet jitter. Real-world 5G and edge network fluctuations may introduce different variance profiles.
4. **Task Simplification:** Real-world robotic teleoperation involves complex multi-degree-of-freedom kinematics, collision recovery, and varying levels of human-in-the-loop autonomy. In this project, tasks are modeled at the session intervention level.

---

## 9. License & Attribution

This project is released under the **MIT License**. Created as an analytics engineering portfolio demonstration showcasing reproducible data generation, relational modeling, advanced SQL analysis, interactive visualization, and data-backed business reporting under explicit model assumptions.
