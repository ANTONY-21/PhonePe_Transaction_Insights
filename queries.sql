-- queries.sql

-- 1. Top 10 states by transaction amount (all time)
SELECT state, SUM(amount) as total_amount
FROM aggregated_transaction
WHERE state IS NOT NULL
GROUP BY state
ORDER BY total_amount DESC
LIMIT 10;

-- 2. Top 10 districts by transaction count in a specific quarter
SELECT district, SUM(count) as total_count
FROM aggregated_transaction
WHERE quarter = 'Q1' AND year = 2022 AND district IS NOT NULL
GROUP BY district
ORDER BY total_count DESC
LIMIT 10;

-- 3. Year-over-year total transaction amount by quarter
SELECT year, quarter, SUM(amount) as total_amount
FROM aggregated_transaction
GROUP BY year, quarter
ORDER BY year, quarter;

-- 4. Payment category popularity (by amount)
SELECT txn_type, SUM(amount) as total_amount
FROM aggregated_transaction
GROUP BY txn_type
ORDER BY total_amount DESC;

-- 5. Insurance-specific aggregation (if insurance stored in aggregated_insurance)
SELECT year, quarter, state, SUM(amount) as total
FROM aggregated_insurance
GROUP BY year, quarter, state
ORDER BY total DESC
LIMIT 20;

-- 6. Customer segmentation: users vs transaction volume per state
SELECT a.state,
       SUM(a.amount) as total_amount,
       COALESCE(MAX(u.registered_users),0) as registered_users
FROM aggregated_transaction a
LEFT JOIN aggregated_user u ON u.state = a.state AND u.year = a.year AND u.quarter = a.quarter
GROUP BY a.state
ORDER BY total_amount DESC;

-- 7. Fraud detection heuristic: unusually large average txn values per district
WITH district_avg AS (
  SELECT district, AVG(amount) as avg_amt
  FROM aggregated_transaction
  WHERE district IS NOT NULL
  GROUP BY district
),
median_cte AS (
  SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY avg_amt) AS median_avg FROM district_avg
)
SELECT d.district, d.avg_amt, m.median_avg
FROM district_avg d, median_cte m
WHERE d.avg_amt > m.median_avg * 4
ORDER BY d.avg_amt DESC
LIMIT 50;

-- 8. Top pincodes / regions from top_map
SELECT category, region, amount, rank
FROM top_map
WHERE category LIKE '%pincode%' OR category LIKE '%pin%'
ORDER BY amount DESC
LIMIT 20;
