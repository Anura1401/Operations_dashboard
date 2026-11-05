# Operator Onboarding & QA Playbook

## Section 1: Purpose
This playbook establishes standardized operational procedures for onboarding, task assignment, quality scoring, and escalation across global teleoperation hubs. It is designed for shift supervisors, training leads, and operations managers. *Notice: Synthetic data for portfolio demonstration only; all parameters and findings reflect simulated model assumptions.*

## Section 2: Operator Onboarding Checklist (Weeks 1-4)
Data shows operators in their first 30 days trail senior operators (>90 days tenure) by **10.1 percentage points** in success rate (72.4% vs 82.5%) and trigger **4.03 interventions per session** (vs 2.59 for seniors). Novice operators are therefore restricted from high-difficulty tasks until demonstrating target proficiency on baseline workflows.

| Week | Focus | Tasks Allowed | Exit Criteria |
| :--- | :--- | :--- | :--- |
| **Week 1** | Controls Orientation & Shadowing | Shadowing only on `pick_and_place` (84.2%) and `bin_sorting` (82.4%) | 100% attendance; pass simulator test with >= 85.0% success and zero joint limit breaches |
| **Week 2** | Supervised Solo Routine Execution | Solo restricted to `pick_and_place` and `bin_sorting` under 1-on-1 mentor oversight | Complete 40 live sessions with >= 80.0% success rate and <= 2.50 interventions/session |
| **Week 3** | Independent Standard Tasks & Recovery | `pick_and_place`, `bin_sorting`, plus `recovery_assist` (79.4%) | Maintain >= 80.0% success over 60 cumulative sessions; <= 3.0 interventions on recovery runs |
| **Week 4** | Full Clearance to Dexterous Manipulation | Clearance granted to `deformable_handling` (71.5%) and `door_navigation` (71.4%) | 30-day exit audit: >= 80.0% rolling success rate and >= 3.70 average QA quality score |

## Section 3: QA Scoring Rubric
Session recordings are audited on a 1-5 scale based on completion, intervention frequency, latency handling, and control smoothness. High QA scores directly determine whether recorded telemetry qualifies as marketable imitation learning training data.

| Score | Rating Level | Task Completion | Interventions | Latency & Control Smoothness | Training Data Acceptance Rule |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **5** | Excellent | Completed on first attempt | 0 to 1 intervention | Flawless trajectory; zero overshoot under latency; full compliance | **Accepted (95% probability):** Premium demonstration quality |
| **4** | Good | Completed successfully | Exactly 2 interventions | Minor motion hesitation; well-managed recovery; fully compliant | **Accepted (86% probability):** Standard commercial training yield |
| **3** | Marginal | Completed with delay | 3 to 4 interventions | Visible oscillations or latency lag; requires supervisor sign-off | **Conditional (48% probability):** Borderline; sub-sampled for audit |
| **2** | Poor | Aborted or incomplete | > 4 interventions | Significant hunting or near-collision; operator struggled with delay | **Rejected (14% probability):** Disqualified from training pipeline |
| **1** | Critical Failure | Hard failure or timeout | Task abandoned | Joint limit violation, dropped item, or emergency override triggered | **Rejected (4% probability):** Disqualified; triggers escalation review |

*Data Acceptance Threshold Rule:* In the operational data model, successful sessions with a QA score >= 4 qualify for training data sale (86% to 95% acceptance). Unreviewed sessions require success = 1, latency < 150 ms, and <= 2 interventions to achieve automatic acceptance (84% probability). Failed sessions (success = 0) are strictly disqualified (<= 3% acceptance).

## Section 4: Escalation Rules
Escalations are triggered when operational telemetry breaches statistical thresholds established in the analysis.

| Trigger Condition | Data Benchmark & Justification | Reviewer | Max Response Time | Mandatory Action |
| :--- | :--- | :--- | :--- | :--- |
| **Latency Breach (>= 150 ms)** | Latency >= 150 ms yields a **37.7% failure rate** (2.5x higher than the 15.0% baseline at <50 ms) | Dispatch Broker / Systems Lead | Immediate (< 5 min) | Reroute complex manipulation (`deformable_handling`, `door_navigation`) to nearshore hubs; downgrade robot to safe stop |
| **Operator Performance Dip** | Rolling 7-day success rate falls **> 8.0 percentage points** below fleet average (< 71.7%) | Shift Supervisor | Within 4 hours | Reassign operator to `pick_and_place`; assign senior peer mentor for 10 shadowed runs |
| **Shift Quality Deficit** | Shift average QA score falls **> 0.40 points** below fleet average (observed on Night shift at 3.23 vs 3.71 fleet) | Operations Lead | Start of next shift | Institute mandatory 10-minute micro-breaks every 2 hours; verify graveyard shift rotation caps |
| **Repeated Task Aborts** | 2 consecutive failures on the same task type by a single operator | Senior Peer Mentor | Immediate (< 15 min) | Conduct live root-cause debrief; check camera feed calibration and latency jitter |

## Section 5: Shift & Capacity Rules
Telemetry reveals structural capacity imbalance: Evening shifts are congested at **92.2% utilization**, while Night shifts stagnate at **55.0% utilization** with a **12.2 percentage point** success penalty (72.6% vs 84.8% daytime average).

1. **Capacity Ceilings & Floors:** Enforce an operational utilization ceiling of **85.0%** on Evening shifts to prevent queue buildup and operator burnout. Enforce a minimum utilization floor of **65.0%** on Night shifts.
2. **Follow-the-Sun Hour Transfers:** Reallocate **35% of nominal Night shift scheduled hours** into daytime operational windows across Indian and Mexican hubs. Move non-urgent autonomous dataset curation and recovery assistance to local daytime hours.
3. **Latency-Aware Task Dispatch:** Complex manipulation tasks (`deformable_handling` at 71.5% and `door_navigation` at 71.4%) must be routed to hubs with round-trip latency <= 80 ms (Mexico at 55.1 ms and US at 44.9 ms). Standard latency-tolerant tasks (`pick_and_place` at 84.2%) are routed to India to leverage its **$25.76** unit cost efficiency.

## Section 6: Weekly Metrics Scorecard
Operations teams track 5 core KPIs weekly against realistic improvement targets derived from the analysis:

| Metric | Current Value | Weekly Target | Owner Role | Target Justification |
| :--- | :---: | :---: | :--- | :--- |
| **Overall Success Rate** | **79.7%** | **82.5%** | Training Lead | Gating novice operators and routing high-latency tasks lifts completion toward senior levels |
| **Training Data Acceptance Rate** | **62.4%** | **66.0%** | QA Lead | Enforcing rubric adherence and shifting curation runs to daytime windows improves yields |
| **Evening / Night Utilization** | **92.2% / 55.0%** | **85.0% / 65.0%** | Workforce Manager | Follow-the-sun scheduling smooths evening congestion and eliminates night standby waste |
| **High-Latency Session Share (>= 150 ms)** | **8.5%** (1,010 runs) | **< 4.0%** | Infrastructure Lead | Dynamic dispatch ceilings keep latency-critical manipulation away from congested overseas links |
| **Blended Cost per Successful Task** | **$41.47** | **$39.50** | VP of Operations | Reducing failed task retries and night idle hours lowers net labor spend per successful task |

## Section 7: Expected Impact (Estimates)
All projected gains are estimates derived under simulated model assumptions, varying the key adoption parameter by +/-25%:

1. **Novice Gating & Mentorship:**
   - *Inputs & Denominator:* 257 novice sessions; 10.1% tenure success deficit; total fleet sessions $N = 11,875$.
   - *Calculation:* $\text{Recovered Sessions} = 257 \times 10.1\% \times \alpha$, where $\alpha = 50\%$ closed ($[37.5\%, 62.5\%]$ range).
   - *Estimated Impact:* Recovers **13 sessions/quarter** (range: **10 to 16 sessions**), lifting fleet throughput by **+0.11%** (range: **+0.08% to +0.13%**).

2. **Follow-the-Sun Shift Rebalancing:**
   - *Inputs & Denominator:* 3,188 night shift sessions; 12.2% day-night success deficit; total fleet sessions $N = 11,875$.
   - *Calculation:* $\text{Recovered Sessions} = 3,188 \times 12.2\% \times \gamma$, where $\gamma = 50\%$ deficit recovered ($[37.5\%, 62.5\%]$ range).
   - *Estimated Impact:* Recovers **194 sessions/quarter** (range: **146 to 243 sessions**), lifting fleet throughput by **+1.63%** (range: **+1.23% to +2.05%**).

3. **Latency-Aware Dispatch Broker:**
   - *Inputs & Denominator:* 1,010 sessions at >= 150 ms; 37.7% failure rate (381 failures); total fleet sessions $N = 11,875$.
   - *Calculation:* $\text{Avoided Failures} = 381 \times \delta$, where $\delta = 50\%$ failures avoided ($[37.5\%, 62.5\%]$ range).
   - *Estimated Impact:* Prevents **190 failed sessions/quarter** (range: **143 to 238 failures**), lifting fleet throughput by **+1.60%** (range: **+1.20% to +2.00%**).
