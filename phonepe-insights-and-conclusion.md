# PhonePe Transaction Insights: revised insights and conclusion

Prepared in response to the reviewer’s request to strengthen the insights and conclusion. These figures were calculated from `pulse.db` in the submitted [PhonePe repository](https://github.com/Palz-official/PhonePe_Transaction_Insights). They describe that database snapshot, not necessarily the latest PhonePe Pulse data.

## Scope and method

The database contains transaction data for 2018–2024. For the findings below, transactions are summed at **state level only**, across payment types. Using both the country and state rows would double count the same activity: in Q4 2024, each level independently totals 28,220,731,268 transactions and ₹36,001,094,840,883. The database stores quarters as `1`, `2`, `3`, and `4`.

## Findings and implications

1. **Activity grew strongly year over year.** Q4 2024 recorded 28.22 billion transactions worth approximately ₹36.00 lakh crore, compared with 19.02 billion and ₹27.05 lakh crore in Q4 2023. That is approximately **48.4% growth in transaction count** and **33.1% growth in value**. Volume grew faster than value, so average value per transaction declined; this could reflect a changing mix of payment types, but the data alone does not establish the cause.

2. **Merchant payments drove transaction frequency, while peer-to-peer payments drove value.** In Q4 2024, merchant payments accounted for approximately **61.7% of transaction count** and **22.4% of value**. Peer-to-peer payments accounted for **33.2% of count** and **74.0% of value**. A business should therefore assess merchant activity and peer transfers with separate measures: transaction count is useful for usage, while amount captures money flowing through the platform.

3. **Transaction value was concentrated in a few states.** Karnataka, Maharashtra, Telangana, Andhra Pradesh, and Uttar Pradesh were the top five states by transaction value in Q4 2024, together contributing about **52.3%** of the state-level total. Karnataka and Maharashtra each contributed about ₹4.15 lakh crore. These absolute totals can guide regional investigation, but they should not be interpreted as adoption rates without population or active-user denominators.

4. **Quarterly momentum continued through 2024.** State-level transaction counts rose from 21.24 billion in Q1 to 28.22 billion in Q4; value rose from ₹29.46 lakh crore to ₹36.00 lakh crore. For a stronger seasonal comparison, use the same quarter in different years as in finding 1, and check subsequent data before treating this pattern as a forecast.

5. **The snapshot reports user totals separately from transactions.** For Q4 2024, its country-level user record reports 586,756,452 registered users and 40,416,377,679 app opens. Registered users are not necessarily active users, and app opens are events rather than unique people. Do not sum registered-user snapshots across quarters.

## Conclusion

The submitted snapshot shows substantial growth in digital payment activity through 2024, with merchant transactions making up most of the count and peer-to-peer transfers most of the value. The dashboard can help compare payment mix and regional activity, but decisions should combine transaction counts, values, and suitable denominators rather than relying on one ranking. The next useful step is to validate the pipeline against the original Pulse files, update the snapshot, and examine per-user or per-capita measures where reliable denominators are available.

## Limitations and validation

- The database contains 36 state/union-territory labels across the quarters in the transaction table. Check source coverage and definitions before generalizing.
- The database's `aggregated_insurance` table is empty, although insurance appears as a transaction type. The app now shows insurance from a pinned third-party archive of the older PhonePe Pulse release; 682 overlapping state-quarter insurance records matched the local database. Do not add those figures to the older dashboard totals again.
- The `top_map` table mixes transaction and insurance records without preserving the source or parent state, so it is not used for rankings. The app shows source-reported leading PINs by count from the archived historical mirror, not all PIN codes. The separate district explorer uses a pinned newer upstream revision, which differs from this database snapshot; its values must not be combined with the findings above. Historical boundary shapes are partial and may not match current district extents.
- These are aggregated observations, not individual transactions. They cannot establish causation, user behavior, or fraud. Differences in population and economic activity affect state totals.
- The existing `queries.sql` sums transaction records without filtering `level`, which can double count country and state rows. Its example filters `quarter = 'Q1'`, but the snapshot uses `'1'`. Apply the level and quarter filters below when reproducing the findings.

## Reproducible SQLite queries

```sql
-- Quarter-over-quarter and same-quarter yearly totals.
SELECT year, quarter, SUM(count) AS transactions,
       ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state' AND year IN (2023, 2024)
GROUP BY year, quarter
ORDER BY year, CAST(quarter AS INTEGER);

-- Payment mix for Q4 2024.
SELECT txn_type, SUM(count) AS transactions,
       ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state' AND year = 2024 AND quarter = '4'
GROUP BY txn_type
ORDER BY amount_inr DESC;

-- State ranking for Q4 2024.
SELECT state, SUM(count) AS transactions,
       ROUND(SUM(amount), 2) AS amount_inr
FROM aggregated_transaction
WHERE level = 'state' AND year = 2024 AND quarter = '4'
GROUP BY state
ORDER BY amount_inr DESC;
```
