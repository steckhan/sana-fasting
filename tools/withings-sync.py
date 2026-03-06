#!/usr/bin/env python3
"""
Withings BP sync — fetches latest blood pressure + heart rate readings.
Appends results to memory/YYYY-MM-DD.md

Usage:
  python3 withings-sync.py           # last 7 days
  python3 withings-sync.py --days 30
  python3 withings-sync.py --json
"""

import json
import sys
import time
import argparse
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

CREDENTIALS_FILE = Path(__file__).parent / ".withings-credentials.json"
WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"

# Withings measure types
WEIGHT     = 1
FAT_MASS   = 8
DIASTOLIC  = 9
SYSTOLIC   = 10
HEART_RATE = 11


def load_credentials():
    if not CREDENTIALS_FILE.exists():
        print("❌ No credentials. Run withings-auth.py first.")
        sys.exit(1)
    return json.loads(CREDENTIALS_FILE.read_text())


def refresh_token_if_needed(creds):
    fetched = creds.get("fetched_at", 0)
    expires = creds.get("expires_in", 10800)
    if time.time() - fetched < expires - 300:
        return creds  # still valid

    resp = requests.post("https://wbsapi.withings.net/v2/oauth2", data={
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
    })
    resp.raise_for_status()
    body = resp.json()
    if body.get("status") != 0:
        print(f"❌ Token refresh failed: {body}")
        sys.exit(1)

    token = body["body"]
    creds.update({
        "access_token": token["access_token"],
        "refresh_token": token["refresh_token"],
        "expires_in": token["expires_in"],
        "fetched_at": int(time.time()),
    })
    CREDENTIALS_FILE.write_text(json.dumps(creds, indent=2))
    CREDENTIALS_FILE.chmod(0o600)
    return creds


def fetch_measurements(creds, days=7):
    end = int(time.time())
    start = end - (days * 86400)

    resp = requests.post(
        "https://wbsapi.withings.net/measure",
        headers={"Authorization": f"Bearer {creds['access_token']}"},
        data={
            "action": "getmeas",
            "startdate": start,
            "enddate": end,
            "category": 1,
        },
    )
    resp.raise_for_status()
    body = resp.json()

    if body.get("status") != 0:
        print(f"❌ API error: {body}")
        sys.exit(1)

    readings = {}
    for group in body["body"]["measuregrps"]:
        dt = datetime.fromtimestamp(group["date"], tz=timezone.utc).astimezone()
        ts_key = dt.strftime("%Y-%m-%d %H:%M")
        if ts_key not in readings:
            readings[ts_key] = {
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M"),
            }
        for m in group["measures"]:
            val = m["value"] * (10 ** m["unit"])
            if m["type"] == SYSTOLIC:
                readings[ts_key]["systolic"] = round(val)
            elif m["type"] == DIASTOLIC:
                readings[ts_key]["diastolic"] = round(val)
            elif m["type"] == HEART_RATE:
                readings[ts_key]["hr"] = round(val)
            elif m["type"] == WEIGHT:
                readings[ts_key]["weight"] = round(val, 1)
            elif m["type"] == FAT_MASS:
                readings[ts_key]["fat_mass"] = round(val, 1)

    return sorted(readings.values(), key=lambda x: x["date"] + x["time"])


def log_to_memory(readings):
    today = datetime.now().strftime("%Y-%m-%d")
    MEMORY_DIR.mkdir(exist_ok=True)
    memory_file = MEMORY_DIR / f"{today}.md"

    # Separate BP readings from weight readings
    bp_readings = [r for r in readings if r.get("systolic") or r.get("diastolic")]
    wt_readings = [r for r in readings if r.get("weight")]

    lines = ["\n\n## Withings BP Readings\n"]
    lines.append("| Date | Time | Systolic | Diastolic | HR |")
    lines.append("|------|------|----------|-----------|-----|")
    for r in bp_readings:
        sys_v = str(r.get("systolic", "—"))
        dia_v = str(r.get("diastolic", "—"))
        hr_v  = str(r.get("hr", "—"))
        lines.append(f"| {r['date']} | {r['time']} | {sys_v} | {dia_v} | {hr_v} |")

    if wt_readings:
        lines.append("\n## Withings Weight\n")
        lines.append("| Date | Time | Weight (kg) | Fat Mass (kg) |")
        lines.append("|------|------|-------------|---------------|")
        for r in wt_readings:
            wt_v = str(r.get("weight", "—"))
            fm_v = str(r.get("fat_mass", "—"))
            lines.append(f"| {r['date']} | {r['time']} | {wt_v} | {fm_v} |")

    block = "\n".join(lines)

    if memory_file.exists():
        existing = memory_file.read_text()
        if "## Withings BP Readings" in existing:
            existing = existing[:existing.index("\n\n## Withings BP Readings")]
        memory_file.write_text(existing + block)
    else:
        memory_file.write_text(f"# Session Notes — {today}\n{block}")

    print(f"✅ Logged {len(readings)} readings → {memory_file.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    creds = load_credentials()
    creds = refresh_token_if_needed(creds)
    readings = fetch_measurements(creds, args.days)

    if args.as_json:
        print(json.dumps(readings, indent=2))
        return

    if not readings:
        print(f"No readings found in the last {args.days} days.")
        return

    bp = [r for r in readings if r.get("systolic") or r.get("diastolic")]
    wt = [r for r in readings if r.get("weight")]

    if bp:
        print(f"\n📊 Blood Pressure — last {args.days} days\n")
        print(f"{'Date':<12} {'Time':<6} {'Sys':>5} {'Dia':>5} {'HR':>4}")
        print("─" * 35)
        for r in bp:
            print(f"{r['date']:<12} {r['time']:<6} "
                  f"{str(r.get('systolic','—')):>5} "
                  f"{str(r.get('diastolic','—')):>5} "
                  f"{str(r.get('hr','—')):>4}")

    if wt:
        print(f"\n⚖️  Weight — last {args.days} days\n")
        print(f"{'Date':<12} {'Time':<6} {'Weight':>8} {'Fat':>8}")
        print("─" * 35)
        for r in wt:
            print(f"{r['date']:<12} {r['time']:<6} "
                  f"{str(r.get('weight','—')):>7}kg "
                  f"{str(r.get('fat_mass','—')):>7}kg")

    log_to_memory(readings)


if __name__ == "__main__":
    main()
