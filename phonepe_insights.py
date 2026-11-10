"""Selected-quarter insights from state-level PhonePe aggregates."""
import pandas as pd


def get_period_insights(conn, year, quarter):
    params = (str(year), str(quarter))
    period_sql = """
        SELECT state, txn_type, count, amount
        FROM aggregated_transaction
        WHERE level = 'state' AND CAST(year AS TEXT) = ?
          AND CAST(quarter AS TEXT) = ?
    """
    current = pd.read_sql_query(period_sql, conn, params=params)
    previous = pd.read_sql_query(period_sql, conn, params=(str(int(year) - 1), str(quarter)))
    if current.empty:
        return None
    current['count'] = pd.to_numeric(current['count'], errors='coerce').fillna(0)
    current['amount'] = pd.to_numeric(current['amount'], errors='coerce').fillna(0)
    total_count = float(current['count'].sum())
    total_amount = float(current['amount'].sum())
    previous_count = float(pd.to_numeric(previous['count'], errors='coerce').fillna(0).sum()) if not previous.empty else 0
    previous_amount = float(pd.to_numeric(previous['amount'], errors='coerce').fillna(0).sum()) if not previous.empty else 0
    categories = current.groupby('txn_type', dropna=False)[['count', 'amount']].sum().sort_values('amount', ascending=False)
    states = current.groupby('state', dropna=True)['amount'].sum().sort_values(ascending=False)
    return {
        'total_count': total_count,
        'total_amount': total_amount,
        'count_growth': (total_count / previous_count - 1) * 100 if previous_count else None,
        'amount_growth': (total_amount / previous_amount - 1) * 100 if previous_amount else None,
        'categories': categories,
        'states': states,
        'top_five_share': float(states.head(5).sum() / total_amount * 100) if total_amount else None,
    }
