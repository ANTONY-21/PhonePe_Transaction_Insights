-- Reproducible queries for the pulse.db snapshot. Use one geographic level.

-- State totals, Q4 2024.
SELECT state, SUM(count) AS transactions, ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state' AND year = 2024 AND quarter = '4'
GROUP BY state ORDER BY amount_inr DESC;

-- Quarter-by-quarter totals.
SELECT year, quarter, SUM(count) AS transactions, ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state'
GROUP BY year, quarter ORDER BY year, CAST(quarter AS INTEGER);

-- Payment mix for the selected example quarter.
SELECT txn_type, SUM(count) AS transactions, ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state' AND year = 2024 AND quarter = '4'
GROUP BY txn_type ORDER BY amount_inr DESC;

-- Same-quarter year-on-year comparison.
SELECT year, SUM(count) AS transactions, ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state' AND quarter = '4' AND year IN (2023, 2024)
GROUP BY year ORDER BY year;
