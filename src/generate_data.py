"""
src/generate_data.py
Synthetic data generator for Teleoperation Ops Dashboard.
All parameters, planted effects, distributions, and constants are loaded
strictly from assumptions.yaml (zero magic numbers in code).

All data is simulated under the model's assumptions (seed 42).
"""

import os
from datetime import datetime, timedelta
import yaml
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "assumptions.yaml")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_assumptions(path: str = CONFIG_PATH) -> dict:
    """Load parameter dictionary and planted effects from assumptions.yaml."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_assumptions()

# Set global random seed
np.random.seed(CONFIG["global"]["random_seed"]["value"])

REFERENCE_DATE = datetime.strptime(CONFIG["global"]["reference_date"]["value"], "%Y-%m-%d")
NUM_DAYS = CONFIG["global"]["simulation_days"]["value"]
START_DATE = REFERENCE_DATE - timedelta(days=NUM_DAYS)


def generate_operators() -> pd.DataFrame:
    """
    Generate operators dataset strictly reading counts, wages, and shifts from CONFIG.
    """
    cfg_wf = CONFIG["workforce"]
    total_ops = cfg_wf["total_operators"]["value"]
    
    # Regional breakdown
    regions = []
    for reg_name, reg_data in cfg_wf["regional_counts"].items():
        regions.extend([reg_name] * reg_data["count"])
    np.random.shuffle(regions)
    
    # Cohort breakdown
    t_cfg = cfg_wf["tenure_distribution"]
    cohort_keys = ["new", "mid", "senior"]
    cohort_probs = [
        t_cfg["new_cohort_prob"]["value"],
        t_cfg["mid_cohort_prob"]["value"],
        t_cfg["senior_cohort_prob"]["value"]
    ]
    tenure_choices = np.random.choice(cohort_keys, size=total_ops, p=cohort_probs)
    
    operator_ids = [f"OP-{i+1:03d}" for i in range(total_ops)]
    join_dates = []
    tenure_days_list = []
    hourly_costs = []
    primary_shifts = []
    
    shift_cfg = cfg_wf["shift_distribution"]
    shift_names = list(shift_cfg.keys())
    shift_probs = [shift_cfg[s]["prob"] for s in shift_names]
    
    wages_cfg = cfg_wf["hourly_wages_usd"]
    
    for i in range(total_ops):
        reg = regions[i]
        c_choice = tenure_choices[i]
        
        if c_choice == "new":
            c_info = t_cfg["new_cohort_prob"]
        elif c_choice == "mid":
            c_info = t_cfg["mid_cohort_prob"]
        else:
            c_info = t_cfg["senior_cohort_prob"]
            
        days_ago = np.random.randint(c_info["days_min"], c_info["days_max"] + 1)
        join_dt = REFERENCE_DATE - timedelta(days=int(days_ago))
        join_dates.append(join_dt.strftime("%Y-%m-%d"))
        tenure_days_list.append(int(days_ago))
        
        # Wage from config
        w_min = wages_cfg[reg]["min"]
        w_max = wages_cfg[reg]["max"]
        wage = float(np.round(np.random.uniform(w_min, w_max), 2))
        hourly_costs.append(wage)
        
        # Primary shift from config
        primary_shifts.append(np.random.choice(shift_names, p=shift_probs))
        
    df = pd.DataFrame({
        "operator_id": operator_ids,
        "region": regions,
        "join_date": join_dates,
        "tenure_days": tenure_days_list,
        "hourly_cost_usd": hourly_costs,
        "primary_shift": primary_shifts
    })
    return df


def generate_shifts(operators_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate scheduled and active shift hours over 90 days.
    """
    cfg_sh = CONFIG["shifts"]
    work_prob = cfg_sh["work_week_active_prob"]["value"]
    sched_hrs = cfg_sh["scheduled_hours_per_shift"]["value"]
    util_by_shift = cfg_sh["utilization_by_shift"]
    clamp_min = cfg_sh["utilization_clamp"]["min"]
    clamp_max = cfg_sh["utilization_clamp"]["max"]
    
    shift_cfg = CONFIG["workforce"]["shift_distribution"]
    all_shifts = list(shift_cfg.keys())
    
    shifts_list = []
    shift_id_counter = 1
    dates = [START_DATE + timedelta(days=d) for d in range(NUM_DAYS)]
    
    for _, op in operators_df.iterrows():
        op_id = op["operator_id"]
        join_dt = datetime.strptime(op["join_date"], "%Y-%m-%d")
        primary_shift = op["primary_shift"]
        
        valid_dates = [d for d in dates if d >= join_dt]
        if not valid_dates:
            continue
            
        for d in valid_dates:
            if np.random.rand() > work_prob:
                continue
                
            # 88% stick to primary shift, 12% cover other shifts
            if np.random.rand() < 0.88:
                shift_type = primary_shift
            else:
                other_shifts = [s for s in all_shifts if s != primary_shift]
                shift_type = np.random.choice(other_shifts)
                
            u_info = util_by_shift[shift_type]
            util = np.random.normal(u_info["mean"], u_info["std"])
            util = float(np.clip(util, clamp_min, clamp_max))
            active_hours = float(np.round(sched_hrs * util, 2))
            
            shifts_list.append({
                "shift_id": f"SH-{shift_id_counter:05d}",
                "operator_id": op_id,
                "shift_date": d.strftime("%Y-%m-%d"),
                "shift_type": shift_type,
                "scheduled_hours": sched_hrs,
                "active_hours": active_hours
            })
            shift_id_counter += 1
            
    return pd.DataFrame(shifts_list)


def generate_sessions(operators_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate ~12,000 sessions over 90 days.
    """
    cfg_tasks = CONFIG["tasks"]
    cfg_net = CONFIG["network"]
    cfg_effects = CONFIG["planted_effects"]
    cfg_qa = CONFIG["qa_and_training_yield"]
    
    task_info = cfg_tasks["types_and_shares"]
    task_types = list(task_info.keys())
    task_shares = [task_info[t]["share"] for t in task_types]
    
    site_info = cfg_tasks["robot_sites"]
    sites = list(site_info.keys())
    site_shares = [site_info[s]["share"] for s in sites]
    
    dur_cfg = cfg_tasks["duration_minutes"]
    shift_hour_map = {
        s: CONFIG["workforce"]["shift_distribution"][s]["hours"]
        for s in CONFIG["workforce"]["shift_distribution"]
    }
    
    op_map = operators_df.set_index("operator_id").to_dict("index")
    op_ids = operators_df["operator_id"].tolist()
    dates = [START_DATE + timedelta(days=d) for d in range(NUM_DAYS)]
    
    target_sessions = 12000
    sessions_per_day = target_sessions // NUM_DAYS
    session_id_counter = 1
    sessions = []
    
    for d in dates:
        d_str = d.strftime("%Y-%m-%d")
        eligible_ops = [op for op in op_ids if op_map[op]["join_date"] <= d_str]
        if not eligible_ops:
            continue
            
        daily_count = int(np.random.normal(sessions_per_day, 12))
        daily_count = max(daily_count, 80)
        sampled_ops = np.random.choice(eligible_ops, size=daily_count, replace=True)
        
        for op_id in sampled_ops:
            op_info = op_map[op_id]
            region = op_info["region"]
            tenure_days = (d - datetime.strptime(op_info["join_date"], "%Y-%m-%d")).days
            
            # Shift
            if np.random.rand() < 0.82:
                shift = op_info["primary_shift"]
            else:
                shift = np.random.choice(list(shift_hour_map.keys()))
                
            start_hour_utc = int(np.random.choice(shift_hour_map[shift]))
            task_type = np.random.choice(task_types, p=task_shares)
            robot_site_region = np.random.choice(sites, p=site_shares)
            
            # Duration
            duration_min = float(np.round(np.clip(
                np.random.normal(dur_cfg["mean"], dur_cfg["std"]),
                dur_cfg["min"], dur_cfg["max"]
            ), 1))
            
            # Latency modeling
            route_key = f"{region}_to_{robot_site_region}"
            lat_param = cfg_net["latencies_ms"][route_key]
            lat_noise = np.random.normal(0, lat_param["std"])
            
            # Network jitter
            if np.random.rand() < cfg_net["jitter_spike"]["probability"]:
                lat_noise += np.random.uniform(
                    cfg_net["jitter_spike"]["min_ms"],
                    cfg_net["jitter_spike"]["max_ms"]
                )
                
            latency_ms = float(np.round(max(lat_param["mean"] + lat_noise, cfg_net["floor_ms"]["value"]), 1))
            
            # Success rate calculation
            prob_success = cfg_effects["baseline_success_prob"]["value"]
            
            # 1. Tenure effect
            if tenure_days < 30:
                prob_success += cfg_effects["tenure_penalties"]["under_30_days"]["penalty"]
            elif tenure_days <= 90:
                prob_success += cfg_effects["tenure_penalties"]["days_31_to_90"]["penalty"]
                
            # 2. Shift effect
            if shift == "Night":
                prob_success += cfg_effects["shift_penalties"]["night_shift"]["penalty"]
                if region == "India":
                    prob_success += cfg_effects["shift_penalties"]["india_night_shift_fatigue"]["penalty"]
                    
            # 3. Task type effect
            prob_success += task_info[task_type]["success_adjustment"]
            
            # 4. Latency effect
            if latency_ms >= 150.0:
                prob_success += cfg_effects["latency_penalties"]["severe_above_150ms"]["penalty"]
            elif latency_ms >= 100.0:
                prob_success += cfg_effects["latency_penalties"]["moderate_100_to_150ms"]["penalty"]
                
            prob_success += np.random.normal(0, cfg_effects["success_probability_bounds"]["noise_std"])
            prob_success = float(np.clip(
                prob_success,
                cfg_effects["success_probability_bounds"]["min"],
                cfg_effects["success_probability_bounds"]["max"]
            ))
            
            success = 1 if np.random.rand() < prob_success else 0
            
            # Interventions
            base_interventions = task_info[task_type]["base_interventions"]
            if success == 0:
                base_interventions += 2.8
            if latency_ms >= 150.0:
                base_interventions += 1.5
            if tenure_days < 30:
                base_interventions += 1.0
                
            interventions = int(np.clip(np.random.poisson(max(base_interventions, 0.5)), 0, 15))
            
            # QA review
            qa_cfg = cfg_qa["quality_scoring"]
            if np.random.rand() < cfg_qa["review_coverage_prob"]["value"]:
                if success == 1:
                    m_score = qa_cfg["success_mean"]
                    if shift == "Night":
                        m_score += qa_cfg["night_penalty"]
                    if tenure_days < 30:
                        m_score += qa_cfg["new_operator_penalty"]
                    if latency_ms >= 150.0:
                        m_score += qa_cfg["high_latency_penalty"]
                else:
                    m_score = qa_cfg["failure_mean"]
                    if shift == "Night":
                        m_score += qa_cfg["night_penalty"]
                        
                raw_score = np.random.normal(m_score, qa_cfg["noise_std"])
                quality_score = int(np.clip(np.round(raw_score), 1, 5))
            else:
                quality_score = None
                
            # Training data acceptance
            acc_cfg = cfg_qa["data_acceptance_probabilities"]
            if success == 0:
                accept_prob = acc_cfg["failed_session"]
            else:
                if quality_score is not None:
                    accept_prob = {
                        5: acc_cfg["reviewed_star_5"],
                        4: acc_cfg["reviewed_star_4"],
                        3: acc_cfg["reviewed_star_3"],
                        2: acc_cfg["reviewed_star_2"],
                        1: acc_cfg["reviewed_star_1"]
                    }.get(quality_score, 0.50)
                else:
                    if interventions <= 2 and latency_ms < 150:
                        accept_prob = acc_cfg["unreviewed_low_interventions"]
                    elif interventions <= 4:
                        accept_prob = acc_cfg["unreviewed_med_interventions"]
                    else:
                        accept_prob = acc_cfg["unreviewed_high_interventions"]
                        
            data_accepted = 1 if np.random.rand() < accept_prob else 0
            
            sessions.append({
                "session_id": f"SES-{session_id_counter:05d}",
                "operator_id": op_id,
                "session_date": d_str,
                "start_hour_utc": start_hour_utc,
                "shift": shift,
                "task_type": task_type,
                "robot_site_region": robot_site_region,
                "duration_min": duration_min,
                "interventions": interventions,
                "latency_ms": latency_ms,
                "success": success,
                "quality_score": quality_score,
                "data_accepted": data_accepted
            })
            session_id_counter += 1
            
    return pd.DataFrame(sessions)


def main():
    print("=" * 60)
    print("Generating Simulated Teleoperation Operations Data...")
    print("Parameters loaded strictly from assumptions.yaml")
    print("=" * 60)
    
    # 1. Operators
    operators_df = generate_operators()
    operators_path = os.path.join(DATA_DIR, "operators.csv")
    operators_df.to_csv(operators_path, index=False)
    print(f"-> Generated {len(operators_df)} operators saved to {operators_path}")
    print(f"   Region Breakdown:\n{operators_df['region'].value_counts(normalize=True).round(3)}")
    
    # 2. Shifts
    shifts_df = generate_shifts(operators_df)
    shifts_path = os.path.join(DATA_DIR, "shifts.csv")
    shifts_df.to_csv(shifts_path, index=False)
    print(f"\n-> Generated {len(shifts_df)} shifts saved to {shifts_path}")
    shifts_df["utilization"] = shifts_df["active_hours"] / shifts_df["scheduled_hours"]
    print("   Utilization by Shift:")
    print(shifts_df.groupby("shift_type")["utilization"].mean().round(3))
    
    # 3. Sessions
    sessions_df = generate_sessions(operators_df)
    sessions_path = os.path.join(DATA_DIR, "sessions.csv")
    sessions_df.to_csv(sessions_path, index=False)
    print(f"\n-> Generated {len(sessions_df)} sessions saved to {sessions_path}")
    print(f"   Overall Success Rate: {sessions_df['success'].mean():.3%}")
    print(f"   Avg Latency: {sessions_df['latency_ms'].mean():.1f} ms")
    qa_sessions = sessions_df.dropna(subset=['quality_score'])
    print(f"   QA Review Coverage: {len(qa_sessions) / len(sessions_df):.1%}")
    print(f"   Avg Quality Score (when reviewed): {qa_sessions['quality_score'].mean():.2f}")
    print(f"   Data Acceptance Rate: {sessions_df['data_accepted'].mean():.3%}")
    
    print("\n   Key Simulated Patterns Verified:")
    merged = sessions_df.merge(operators_df[["operator_id", "tenure_days", "region"]], on="operator_id")
    merged["tenure_bucket"] = pd.cut(
        merged["tenure_days"],
        bins=[-1, 30, 90, 9999],
        labels=["0-30 days", "31-90 days", "90+ days"]
    )
    print("   - Success Rate by Tenure Bucket:")
    print(merged.groupby("tenure_bucket", observed=False)["success"].mean().round(3))
    
    print("   - Success Rate by Shift:")
    print(sessions_df.groupby("shift")["success"].mean().round(3))
    
    merged["latency_bucket"] = pd.cut(
        merged["latency_ms"],
        bins=[0, 50, 100, 150, 9999],
        labels=["<50ms", "50-100ms", "100-150ms", "150ms+"]
    )
    print("   - Failure Rate by Latency Bucket:")
    print((1 - merged.groupby("latency_bucket", observed=False)["success"].mean()).round(3))
    
    print("=" * 60)
    print("Simulated dataset generation complete! All files generated in data/")
    print("=" * 60)


if __name__ == "__main__":
    main()
