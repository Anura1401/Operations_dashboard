-- =====================================================================
-- Teleoperation Operations Dashboard - SQL Analysis Suite
-- All queries contain business context and use CTEs, aggregations,
-- window functions, and joins across operators, shifts, and sessions.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query 1: Overall Operational KPIs
-- Business Question: What are the overarching performance KPIs across all operations (volume, success rate, latency, QA quality, and data acceptance rate)?
-- ---------------------------------------------------------------------
-- NAME: overall_kpis
SELECT
    COUNT(*) AS total_sessions,
    ROUND(AVG(success) * 100.0, 2) AS overall_success_rate_pct,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms,
    ROUND(AVG(CASE WHEN quality_score IS NOT NULL THEN quality_score END), 2) AS avg_quality_score,
    ROUND(AVG(data_accepted) * 100.0, 2) AS data_acceptance_rate_pct,
    ROUND(AVG(duration_min), 1) AS avg_duration_min,
    ROUND(AVG(interventions), 2) AS avg_interventions
FROM sessions;


-- ---------------------------------------------------------------------
-- Query 2: Performance by Operator Tenure Bucket
-- Business Question: How does operator performance (success rate, quality score, and intervention frequency) evolve across experience levels (0-30 days, 31-90 days, 90+ days)?
-- ---------------------------------------------------------------------
-- NAME: tenure_performance
SELECT
    CASE
        WHEN o.tenure_days <= 30 THEN '0-30 days'
        WHEN o.tenure_days <= 90 THEN '31-90 days'
        ELSE '90+ days'
    END AS tenure_bucket,
    COUNT(s.session_id) AS session_count,
    COUNT(DISTINCT o.operator_id) AS operator_count,
    ROUND(AVG(s.success) * 100.0, 2) AS success_rate_pct,
    ROUND(AVG(s.quality_score), 2) AS avg_quality_score,
    ROUND(AVG(s.interventions), 2) AS avg_interventions,
    ROUND(AVG(s.data_accepted) * 100.0, 2) AS data_acceptance_rate_pct
FROM sessions s
JOIN operators o ON s.operator_id = o.operator_id
GROUP BY tenure_bucket
ORDER BY
    CASE tenure_bucket
        WHEN '0-30 days' THEN 1
        WHEN '31-90 days' THEN 2
        ELSE 3
    END;


-- ---------------------------------------------------------------------
-- Query 3: Success Rate and Quality by Shift and Operator Region
-- Business Question: How do session success rate and review quality vary across operational shifts and operator geographic regions?
-- ---------------------------------------------------------------------
-- NAME: shift_region_performance
SELECT
    s.shift,
    o.region AS operator_region,
    COUNT(s.session_id) AS total_sessions,
    ROUND(AVG(s.success) * 100.0, 2) AS success_rate_pct,
    ROUND(AVG(s.quality_score), 2) AS avg_quality_score,
    ROUND(AVG(s.latency_ms), 1) AS avg_latency_ms,
    ROUND(AVG(s.data_accepted) * 100.0, 2) AS data_acceptance_pct
FROM sessions s
JOIN operators o ON s.operator_id = o.operator_id
GROUP BY s.shift, o.region
ORDER BY s.shift, o.region;


-- ---------------------------------------------------------------------
-- Query 4: Shift Utilization by Shift and Operator Region
-- Business Question: What is the workforce utilization rate (active hours divided by scheduled hours) across shifts and regions, and where is staffing imbalanced?
-- ---------------------------------------------------------------------
-- NAME: utilization_by_shift_region
SELECT
    sh.shift_type AS shift,
    o.region AS operator_region,
    COUNT(sh.shift_id) AS total_shifts,
    ROUND(SUM(sh.scheduled_hours), 1) AS total_scheduled_hours,
    ROUND(SUM(sh.active_hours), 1) AS total_active_hours,
    ROUND(SUM(sh.active_hours) / SUM(sh.scheduled_hours) * 100.0, 2) AS utilization_rate_pct
FROM shifts sh
JOIN operators o ON sh.operator_id = o.operator_id
GROUP BY sh.shift_type, o.region
ORDER BY sh.shift_type, o.region;


-- ---------------------------------------------------------------------
-- Query 5: Failure Rate by Latency Bucket
-- Business Question: What is the relationship between network latency and task failure rate across discrete latency tiers?
-- ---------------------------------------------------------------------
-- NAME: failure_by_latency
SELECT
    CASE
        WHEN latency_ms < 50 THEN '<50ms'
        WHEN latency_ms < 100 THEN '50-100ms'
        WHEN latency_ms < 150 THEN '100-150ms'
        ELSE '150ms+'
    END AS latency_bucket,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failed_sessions,
    ROUND((1.0 - AVG(success)) * 100.0, 2) AS failure_rate_pct,
    ROUND(AVG(success) * 100.0, 2) AS success_rate_pct,
    ROUND(AVG(interventions), 2) AS avg_interventions,
    ROUND(AVG(data_accepted) * 100.0, 2) AS data_acceptance_pct
FROM sessions
GROUP BY latency_bucket
ORDER BY
    CASE latency_bucket
        WHEN '<50ms' THEN 1
        WHEN '50-100ms' THEN 2
        WHEN '100-150ms' THEN 3
        ELSE 4
    END;


-- ---------------------------------------------------------------------
-- Query 6: Success Rate and Complexity by Task Type
-- Business Question: How does operator success rate and intervention frequency vary by robot task type and physical manipulation complexity?
-- ---------------------------------------------------------------------
-- NAME: performance_by_task_type
SELECT
    task_type,
    COUNT(*) AS total_sessions,
    ROUND(AVG(success) * 100.0, 2) AS success_rate_pct,
    ROUND(AVG(duration_min), 1) AS avg_duration_min,
    ROUND(AVG(interventions), 2) AS avg_interventions,
    ROUND(AVG(quality_score), 2) AS avg_quality_score,
    ROUND(AVG(data_accepted) * 100.0, 2) AS data_acceptance_rate_pct
FROM sessions
GROUP BY task_type
ORDER BY success_rate_pct DESC;


-- ---------------------------------------------------------------------
-- Query 7: Cost Per Successful Task by Operator Region
-- Business Question: What is the fully loaded direct labor cost per successful teleoperation task across geographic regions, accounting for regional hourly wages and success rates?
-- ---------------------------------------------------------------------
-- NAME: cost_per_successful_task
WITH operator_session_stats AS (
    SELECT
        o.region,
        COUNT(s.session_id) AS total_sessions,
        SUM(s.success) AS successful_sessions
    FROM sessions s
    JOIN operators o ON s.operator_id = o.operator_id
    GROUP BY o.region
),
operator_shift_costs AS (
    SELECT
        o.region,
        COUNT(DISTINCT o.operator_id) AS active_operators,
        ROUND(AVG(o.hourly_cost_usd), 2) AS avg_hourly_wage_usd,
        SUM(sh.active_hours) AS total_active_hours,
        SUM(sh.scheduled_hours) AS total_scheduled_hours,
        SUM(sh.active_hours * o.hourly_cost_usd) AS direct_active_labor_cost_usd
    FROM shifts sh
    JOIN operators o ON sh.operator_id = o.operator_id
    GROUP BY o.region
)
SELECT
    osc.region,
    osc.active_operators,
    osc.avg_hourly_wage_usd,
    oss.total_sessions,
    oss.successful_sessions,
    ROUND(CAST(oss.successful_sessions AS REAL) / oss.total_sessions * 100.0, 2) AS success_rate_pct,
    ROUND(osc.total_active_hours, 1) AS total_active_hours,
    ROUND(osc.direct_active_labor_cost_usd, 2) AS total_labor_cost_usd,
    ROUND(osc.direct_active_labor_cost_usd / oss.successful_sessions, 2) AS cost_per_successful_task_usd
FROM operator_shift_costs osc
JOIN operator_session_stats oss ON osc.region = oss.region
ORDER BY cost_per_successful_task_usd ASC;


-- ---------------------------------------------------------------------
-- Query 8: Bottom 10 Operators by Success Rate (min 40 sessions)
-- Business Question: Which operators exhibit the lowest success rates (with a minimum sample of 40 sessions) to identify candidates for retraining, mentoring, or task reassignment?
-- ---------------------------------------------------------------------
-- NAME: bottom_10_operators
SELECT
    o.operator_id,
    o.region,
    o.tenure_days,
    CASE
        WHEN o.tenure_days <= 30 THEN '0-30 days'
        WHEN o.tenure_days <= 90 THEN '31-90 days'
        ELSE '90+ days'
    END AS tenure_bucket,
    o.primary_shift,
    COUNT(s.session_id) AS total_sessions,
    SUM(s.success) AS successful_sessions,
    ROUND(AVG(s.success) * 100.0, 2) AS success_rate_pct,
    ROUND(AVG(s.quality_score), 2) AS avg_quality_score,
    ROUND(AVG(s.interventions), 2) AS avg_interventions
FROM operators o
JOIN sessions s ON o.operator_id = s.operator_id
GROUP BY o.operator_id, o.region, o.tenure_days, o.primary_shift
HAVING COUNT(s.session_id) >= 40
ORDER BY success_rate_pct ASC, total_sessions DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- Query 9: Weekly Longitudinal Trend with Rolling 4-Week Average (Window Function)
-- Business Question: What is the longitudinal trend of weekly success rate and QA quality, and what does a 4-week moving average reveal about operational stability?
-- ---------------------------------------------------------------------
-- NAME: weekly_trend_window
WITH weekly_raw AS (
    SELECT
        strftime('%Y-W%W', session_date) AS week_year,
        MIN(session_date) AS week_start_date,
        COUNT(*) AS weekly_sessions,
        SUM(success) AS weekly_successes,
        AVG(success) AS raw_success_rate,
        AVG(quality_score) AS raw_avg_quality,
        AVG(data_accepted) AS raw_acceptance_rate,
        AVG(latency_ms) AS raw_avg_latency
    FROM sessions
    GROUP BY strftime('%Y-W%W', session_date)
)
SELECT
    week_year,
    week_start_date,
    weekly_sessions,
    ROUND(raw_success_rate * 100.0, 2) AS weekly_success_rate_pct,
    ROUND(
        AVG(raw_success_rate) OVER (
            ORDER BY week_year
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) * 100.0,
        2
    ) AS rolling_4wk_success_rate_pct,
    ROUND(raw_avg_quality, 2) AS weekly_avg_quality,
    ROUND(
        AVG(raw_avg_quality) OVER (
            ORDER BY week_year
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_4wk_avg_quality,
    ROUND(raw_acceptance_rate * 100.0, 2) AS weekly_data_acceptance_pct,
    ROUND(
        AVG(raw_acceptance_rate) OVER (
            ORDER BY week_year
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) * 100.0,
        2
    ) AS rolling_4wk_acceptance_rate_pct,
    ROUND(raw_avg_latency, 1) AS weekly_avg_latency_ms
FROM weekly_raw
ORDER BY week_year ASC;


-- ---------------------------------------------------------------------
-- Query 10: Operator Quality Leaderboard with Regional Ranking (Window Function)
-- Business Question: Who are the top operators within each operational region ranked by QA quality score and success rate using window functions?
-- ---------------------------------------------------------------------
-- NAME: regional_operator_rankings
WITH operator_metrics AS (
    SELECT
        o.region,
        o.operator_id,
        o.tenure_days,
        o.primary_shift,
        COUNT(s.session_id) AS total_sessions,
        ROUND(AVG(s.success) * 100.0, 2) AS success_rate_pct,
        ROUND(AVG(s.quality_score), 2) AS avg_quality_score,
        COUNT(s.quality_score) AS reviewed_sessions_count
    FROM operators o
    JOIN sessions s ON o.operator_id = s.operator_id
    GROUP BY o.region, o.operator_id, o.tenure_days, o.primary_shift
    HAVING COUNT(s.session_id) >= 30 AND COUNT(s.quality_score) >= 10
)
SELECT
    region,
    RANK() OVER (
        PARTITION BY region
        ORDER BY avg_quality_score DESC, success_rate_pct DESC
    ) AS regional_rank,
    operator_id,
    tenure_days,
    primary_shift,
    total_sessions,
    reviewed_sessions_count,
    avg_quality_score,
    success_rate_pct
FROM operator_metrics
ORDER BY region, regional_rank ASC;


-- ---------------------------------------------------------------------
-- Query 11: Data Acceptance Rate by Shift and Task Type
-- Business Question: What proportion of teleoperated sessions qualify as saleable autonomous training data segmented across shifts and task complexities?
-- ---------------------------------------------------------------------
-- NAME: data_acceptance_by_shift_task
SELECT
    shift,
    task_type,
    COUNT(*) AS total_sessions,
    SUM(data_accepted) AS accepted_sessions,
    ROUND(AVG(data_accepted) * 100.0, 2) AS data_acceptance_rate_pct,
    ROUND(AVG(success) * 100.0, 2) AS success_rate_pct,
    ROUND(AVG(quality_score), 2) AS avg_quality_score
FROM sessions
GROUP BY shift, task_type
ORDER BY shift, data_acceptance_rate_pct DESC;

