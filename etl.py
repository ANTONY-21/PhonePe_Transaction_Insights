# etl_fixed.py
"""
Robust ETL for PhonePe Pulse JSON -> SQLite
Usage:
    python etl_fixed.py --pulse_path ./pulse --sqlite_path pulse.db [--overwrite]
"""
import argparse
import json
from pathlib import Path
import sqlite3
import os

SCHEMA_SQL = open("db_schema.sql", "r").read()

def prepare_db(sqlite_path, overwrite=False):
    if overwrite and os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)
    conn.commit()
    return conn

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0

def safe_int(x):
    try:
        return int(x)
    except:
        return 0

def parse_aggregated_transaction(j, year, quarter, state_name, inserts):
    # Expect j['data']['transactionData'] -> list of { "name": "...", "paymentInstruments": [ { "type":"TOTAL", "count":..., "amount":... } ] }
    data = j.get("data", {})
    txlist = data.get("transactionData") or data.get("transactionDataList") or data.get("transaction") or data.get("transactionData", None)
    if not txlist and isinstance(data, dict):
        # look for keys that are lists containing dicts with "paymentInstruments"
        for v in data.values():
            if isinstance(v, list):
                txlist = v
                break
    if not isinstance(txlist, list):
        return
    for item in txlist:
        name = item.get("name") or item.get("title") or item.get("txn", None)
        pis = item.get("paymentInstruments") or item.get("paymentInstrument", [])
        if isinstance(pis, dict):
            pis = [pis]
        for p in pis:
            if p.get("type","").upper() == "TOTAL" or len(pis)==1:
                inserts.append({
                    'year': year, 'quarter': quarter, 'level': 'state' if state_name else 'country',
                    'state': state_name, 'district': None,
                    'txn_type': name, 'count': safe_int(p.get("count")), 'amount': safe_float(p.get("amount"))
                })
                break

def parse_aggregated_user(j, year, quarter, state_name, inserts):
    # Expect j['data']['aggregated'] -> {'registeredUsers': X, 'appOpens': Y}
    data = j.get("data", {})
    agg = data.get("aggregated") or data.get("aggregatedData") or data.get("aggregated", None)
    if isinstance(agg, dict):
        inserts.append({
            'year': year, 'quarter': quarter, 'level': 'state' if state_name else 'country',
            'state': state_name, 'district': None,
            'registered_users': safe_int(agg.get("registeredUsers") or agg.get("registered_users") or agg.get("registered")),
            'app_opens': safe_int(agg.get("appOpens") or agg.get("app_opens") or agg.get("appOpensCount"))
        })

def parse_aggregated_insurance(j, year, quarter, state_name, inserts):
    # Similar to transaction: transactionData list structure but with "Insurance"
    parse_aggregated_transaction(j, year, quarter, state_name, inserts)  # same structure

def parse_map_hover(j, year, quarter, inserts_map):
    # Hover data can be 'hoverDataList' (list of {name, metric: [ {type, count, amount} ] })
    data = j.get("data", {})
    hover_list = data.get("hoverDataList") or data.get("hoverData") or data.get("hoverDataList", None)
    if isinstance(hover_list, dict):
        # some files use hoverData as dict of states -> metrics
        for state, metrics in hover_list.items():
            if isinstance(metrics, dict):
                mlist = metrics.get("metric") or metrics.get("metrics") or [metrics]
            elif isinstance(metrics, list):
                mlist = metrics
            else:
                continue
            for m in mlist:
                if (m.get("type","").upper() == "TOTAL") or True:
                    inserts_map.append({
                        'year': year, 'quarter': quarter, 'level': 'state',
                        'state': state, 'district': None,
                        'total_amount': safe_float(m.get("amount")), 'total_count': safe_int(m.get("count"))
                    })
    elif isinstance(hover_list, list):
        for item in hover_list:
            name = item.get("name") or item.get("entityName") or item.get("state")
            metric_list = item.get("metric") or item.get("metricList") or item.get("metrics") or []
            if isinstance(metric_list, dict):
                metric_list = [metric_list]
            for m in metric_list:
                if (m.get("type","").upper() == "TOTAL") or True:
                    inserts_map.append({
                        'year': year, 'quarter': quarter, 'level': 'state',
                        'state': name, 'district': None,
                        'total_amount': safe_float(m.get("amount")), 'total_count': safe_int(m.get("count"))
                    })

def parse_top(j, year, quarter, inserts_top):
    data = j.get("data", {})
    # data may have keys: states, districts, pincodes where items have entityName + metric
    for key in ("states","districts","pincodes","statesList"):
        arr = data.get(key)
        if isinstance(arr, list):
            for idx, item in enumerate(arr, start=1):
                name = item.get("entityName") or item.get("name") or item.get("region") or item.get("entity") or item.get("key")
                metric = item.get("metric") or item.get("metrics") or {}
                if isinstance(metric, dict) and ("amount" in metric or "count" in metric):
                    inserts_top.append({
                        'year': year, 'quarter': quarter,
                        'category': key, 'level': key[:-1] if key.endswith("s") else key,
                        'region': name, 'count': safe_int(metric.get("count")), 'amount': safe_float(metric.get("amount")), 'rank': idx
                    })
            # continue, we found and processed this key

    # Some top user files have 'states' list of dicts with 'name' and 'registeredUsers'
    states_alt = data.get("states")
    if isinstance(states_alt, list):
        for idx, it in enumerate(states_alt, start=1):
            name = it.get("name") or it.get("entityName")
            reg = it.get("registeredUsers") or it.get("registeredUsers")
            if reg is not None:
                inserts_top.append({
                    'year': year, 'quarter': quarter,
                    'category': 'user_states', 'level': 'state',
                    'region': name, 'count': safe_int(reg), 'amount': 0.0, 'rank': idx
                })

def ingest_records(conn, aggregated_txn, aggregated_user, map_values, top_map):
    cur = conn.cursor()
    ct=0
    for r in aggregated_txn:
        cur.execute("""
        INSERT INTO aggregated_transaction(year, quarter, level, state, district, txn_type, count, amount)
        VALUES (?,?,?,?,?,?,?,?)
        """, (r['year'], r['quarter'], r['level'], r['state'], r['district'], r['txn_type'], r['count'], r['amount']))
        ct+=1
    for r in aggregated_user:
        cur.execute("""
        INSERT INTO aggregated_user(year, quarter, level, state, district, registered_users, app_opens)
        VALUES (?,?,?,?,?,?,?)
        """, (r['year'], r['quarter'], r['level'], r['state'], r['district'], r['registered_users'], r['app_opens']))
    for r in map_values:
        cur.execute("""
        INSERT INTO map_values(year, quarter, level, state, district, total_amount, total_count)
        VALUES (?,?,?,?,?,?,?)
        """, (r['year'], r['quarter'], r['level'], r['state'], r['district'], r['total_amount'], r['total_count']))
    for r in top_map:
        cur.execute("""
        INSERT INTO top_map(year, quarter, category, level, region, count, amount, rank)
        VALUES (?,?,?,?,?,?,?,?)
        """, (r['year'], r['quarter'], r['category'], r['level'], r['region'], r['count'], r['amount'], r['rank']))
    conn.commit()
    return ct

def infer_year_quarter_from_path(parts):
    # parts is list of path components after .../data/...
    # expected ... / <section> / <type> / country / india / [state/...] / YEAR / QUARTER.json
    year=None; quarter=None; state=None
    # search for numeric folder (year)
    for i, p in enumerate(parts):
        if p.isdigit() and len(p)==4:
            year = int(p)
            # next part often quarter filename or subfolder
            if i+1 < len(parts):
                qpart = parts[i+1]
                # qpart might be '1.json' or '1' (folder) or '1.json' file if last component included
                if qpart.endswith(".json"):
                    quarter = Path(qpart).stem
                else:
                    # if there is a file under this folder, we'll inspect the filename later
                    # try to find a json file in that folder - not necessary here
                    pass
            break
    # try to pick quarter from last path element if it's a file
    last = parts[-1]
    if last.endswith(".json"):
        try:
            q = Path(last).stem
            if q.isdigit():
                quarter = q
        except:
            pass
    # attempt state name: if 'state' appears in parts, next component is state name
    if "state" in parts:
        try:
            idx = parts.index("state")
            state = parts[idx+1]
        except:
            state = None
    return year, quarter, state

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pulse_path', default='./pulse', help='path to cloned pulse repo')
    parser.add_argument('--sqlite_path', default='pulse.db', help='sqlite db path')
    parser.add_argument('--overwrite', action='store_true', help='overwrite sqlite db if exists')
    args = parser.parse_args()

    pulse_data = Path(args.pulse_path) / "data"
    if not pulse_data.exists():
        print("ERROR: pulse/data not found at", pulse_data)
        return

    conn = prepare_db(args.sqlite_path, overwrite=args.overwrite)

    aggregated_txn=[]
    aggregated_user=[]
    map_values=[]
    top_map=[]
    file_count=0

    for f in pulse_data.rglob("*.json"):
        file_count += 1
        rel = f.relative_to(pulse_data)
        parts = [p for p in rel.parts]
        # infer year/quarter/state
        year, quarter, state_name = infer_year_quarter_from_path(parts + [f.name])
        # load json
        try:
            j = json.load(open(f, 'r', encoding='utf-8'))
        except Exception as e:
            print("skip (bad json):", f, e)
            continue
        # determine section: aggregated / map / top
        if "aggregated" in parts:
            # determine type: transaction / user / insurance
            if "transaction" in parts:
                parse_aggregated_transaction(j, year, quarter, state_name, aggregated_txn)
            elif "user" in parts:
                parse_aggregated_user(j, year, quarter, state_name, aggregated_user)
            elif "insurance" in parts:
                parse_aggregated_insurance(j, year, quarter, state_name, aggregated_txn)  # insurance similar
        elif "map" in parts:
            # map files (hover)
            parse_map_hover(j, year, quarter, map_values)
        elif "top" in parts:
            parse_top(j, year, quarter, top_map)
        else:
            # unknown - try to discover keys
            if isinstance(j.get("data"), dict):
                if any(k in j["data"] for k in ("transactionData","transaction")):
                    parse_aggregated_transaction(j, year, quarter, state_name, aggregated_txn)
                elif any(k in j["data"] for k in ("hoverDataList","hoverData")):
                    parse_map_hover(j, year, quarter, map_values)
                elif any(k in j["data"] for k in ("states","districts","pincodes")):
                    parse_top(j, year, quarter, top_map)

    # ingest to sqlite
    print("Files scanned:", file_count)
    print("Prepared inserts - txn:", len(aggregated_txn), "users:", len(aggregated_user), "map:", len(map_values), "top:", len(top_map))
    ingest_records(conn, aggregated_txn, aggregated_user, map_values, top_map)
    # final counts
    cur = conn.cursor()
    def cnt(t): 
        try:
            return cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except:
            return 0
    print("Final table counts:")
    print(" aggregated_transaction:", cnt("aggregated_transaction"))
    print(" aggregated_user     :", cnt("aggregated_user"))
    print(" map_values          :", cnt("map_values"))
    print(" top_map             :", cnt("top_map"))
    conn.close()

if __name__ == "__main__":
    main()
