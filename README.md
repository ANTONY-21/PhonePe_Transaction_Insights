# PhonePe Transaction Insights

Explore a PhonePe Pulse data snapshot with Python, SQLite and Streamlit. The dashboard calculates key insights and a conclusion for the selected quarter and shows state transaction rankings, quarterly trends and payment category totals. The snapshot describes historical aggregate records; it does not represent current activity or per-person adoption.

## Run locally

Install Python dependencies from `requirements.txt`, ensure that `pulse.db` is present in this folder, and run:

```bash
streamlit run streamlit_app.py
```

Choose a year and quarter in the sidebar. The state ranking, map and payment category breakdown use that selection. The trend chart covers all quarters. The state map uses the included `geo/india_states.geojson`; all 36 state and union territory names in the snapshot were matched for the quarters checked. Boundaries are from geoBoundaries, based on DataMeet India community and Election Commission of India data, licensed CC BY 2.5 IN. See `geo/metadata.json` for source and vintage details.

To rebuild the database from source Pulse JSON files, see `etl.py` and `db_schema.sql` and check that the original source data and schema match the snapshot. Review source coverage before generalizing results.

## Insights and conclusion

See `phonepe-insights-and-conclusion.md` for checked findings, limitations and reproducible queries. Q4 2024 in this snapshot contains 28.22 billion transactions worth about ₹36.00 lakh crore. Merchant payments made up most of the count, while peer-to-peer payments made up most of the value. State totals are not adoption rates and cannot establish causation.

The transaction table contains both country and state aggregates. Summing both levels counts the same underlying activity twice. The dashboard and queries use `level = 'state'` for national totals and compare quarters stored as `1`, `2`, `3`, or `4` in this snapshot.


The dashboard also displays reported country-level registered users and app opens for the selected quarter. Registered users are not the same as active users, and app opens are events. The original snapshot mixes district/PIN-code transaction and insurance records without source or parent-state context, so that mixed table is not used for rankings. PIN and insurance views use a pinned third-party archive of the historical PhonePe Pulse release. All 5,034 overlapping transaction-category records and 682 insurance records matched the local database. PINs are only the source-provided leaders by count, not a complete dataset. Insurance is already represented in the old database totals and must not be added again. The district explorer uses a newer, restated Pulse revision and chooses one historical boundary collection per state by name-match coverage. Do not combine its values with the older database or archive; boundaries may have changed or split. See the metadata, licenses and attribution in `archive_data` and `district_data`.
