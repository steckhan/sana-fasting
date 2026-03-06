#!/usr/bin/env python3
"""
BP Analyzer — Fasting Context Intelligence
Reads BP readings from memory/YYYY-MM-DD.md files and provides
smart interpretation within the context of Nico's 5-day oat fast.

Usage:
  python3 bp-analyze.py                    # analyze today
  python3 bp-analyze.py --days 5           # compare across last N days (fast trend)
  python3 bp-analyze.py --date 2026-03-04  # analyze specific date
  python3 bp-analyze.py --json             # machine-readable output
"""

import re
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"

# Nico's profile
BASELINE_SYS = 140
BASELINE_DIA = 95
FAST_START = "2026-03-02"
FAST_END   = "2026-03-06"

# Thresholds
RED_SYS_LOW   = 90
RED_SYS_HIGH  = 160
RED_DIA_LOW   = 60
RED_DIA_HIGH  = 105
YELLOW_SYS_LOW = 105
YELLOW_DIA_HIGH = 102
ORTHO_DROP    = 20  # mmHg systolic drop = orthostatic risk


def parse_bp_table(text):
    """Extract BP readings from a markdown table in memory file."""
    readings = []
    in_table = False
    for line in text.splitlines():
        if "| Date | Time | Systolic" in line:
            in_table = True
            continue
        if in_table:
            if line.startswith("|---") or not line.startswith("|"):
                if not line.startswith("|"):
                    in_table = False
                continue
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                try:
                    reading = {
                        "date": parts[0],
                        "time": parts[1],
                        "systolic": int(parts[2]) if parts[2] != "—" else None,
                        "diastolic": int(parts[3]) if parts[3] != "—" else None,
                        "hr": int(parts[4]) if len(parts) > 4 and parts[4] != "—" else None,
                    }
                    readings.append(reading)
                except (ValueError, IndexError):
                    continue
    return readings


def get_fasting_day(date_str):
    """Return fasting day number (1–5) or None if not during fast."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        start = datetime.strptime(FAST_START, "%Y-%m-%d").date()
        end   = datetime.strptime(FAST_END, "%Y-%m-%d").date()
        if start <= d <= end:
            return (d - start).days + 1
    except ValueError:
        pass
    return None


def classify_reading(sys_val, dia_val):
    """Returns (status, message) for a single reading."""
    if sys_val is None or dia_val is None:
        return "UNKNOWN", "Incomplete reading"

    if sys_val < RED_SYS_LOW or dia_val < RED_DIA_LOW:
        return "RED", f"⛔ HYPOTENSION: SBP {sys_val} / DBP {dia_val} — break fast, assess immediately"
    if sys_val > RED_SYS_HIGH:
        return "RED", f"⛔ HIGH: SBP {sys_val} unexpectedly elevated during fast — contact doctor"
    if dia_val > RED_DIA_HIGH:
        return "RED", f"⛔ HIGH DIASTOLIC: DBP {dia_val} — monitor closely, consider medical contact"

    if sys_val < YELLOW_SYS_LOW:
        return "YELLOW", f"⚠️  SBP {sys_val} — low, stay hydrated, add salt, rest"
    if dia_val > YELLOW_DIA_HIGH:
        return "YELLOW", f"⚠️  DBP {dia_val} — slightly elevated, check stress/hydration"

    drop_sys = BASELINE_SYS - sys_val
    drop_dia = BASELINE_DIA - dia_val
    if drop_sys >= 10 and drop_dia >= 5:
        return "GREEN", f"✅ OPTIMAL DROP: SBP {sys_val} (−{drop_sys}) / DBP {dia_val} (−{drop_dia}) — fasting working"
    if drop_sys >= 5:
        return "GREEN", f"✅ TRENDING DOWN: SBP {sys_val} (−{drop_sys}) / DBP {dia_val}"
    return "GREEN", f"✅ STABLE: SBP {sys_val} / DBP {dia_val} — within normal fasting range"


def analyze_day(date_str, readings):
    """Full analysis for a single day's readings."""
    fasting_day = get_fasting_day(date_str)
    
    # Filter complete readings
    complete = [r for r in readings if r["systolic"] and r["diastolic"]]
    if not complete:
        return {"date": date_str, "status": "NO_DATA", "summary": "No BP readings found."}

    # Prefer second reading if close together (measurement anxiety)
    morning = [r for r in complete if r["time"] < "12:00"]
    evening = [r for r in complete if r["time"] >= "12:00"]

    # Best morning reading: second one if multiple close together
    best_morning = None
    if len(morning) >= 2:
        best_morning = morning[1]  # second reading = more accurate
    elif morning:
        best_morning = morning[0]

    best_evening = evening[-1] if evening else None

    # Classify
    results = []
    if best_morning:
        status, msg = classify_reading(best_morning["systolic"], best_morning["diastolic"])
        results.append({"time": "morning", "reading": best_morning, "status": status, "message": msg})
    
    if best_evening:
        status, msg = classify_reading(best_evening["systolic"], best_evening["diastolic"])
        # Extra check: evening DBP much higher than morning?
        if best_morning and best_evening["diastolic"] and best_morning["diastolic"]:
            evening_rise = best_evening["diastolic"] - best_morning["diastolic"]
            if evening_rise > 15:
                msg += f" (DBP rose {evening_rise} mmHg from morning — non-dipping pattern)"
        results.append({"time": "evening", "reading": best_evening, "status": status, "message": msg})

    # Overall status: worst of the pair
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "UNKNOWN": 3}
    overall_status = min(results, key=lambda x: order[x["status"]])["status"] if results else "NO_DATA"

    # Average of best readings
    sys_vals = [r["reading"]["systolic"] for r in results if r["reading"]["systolic"]]
    dia_vals = [r["reading"]["diastolic"] for r in results if r["reading"]["diastolic"]]
    avg_sys = round(sum(sys_vals) / len(sys_vals)) if sys_vals else None
    avg_dia = round(sum(dia_vals) / len(dia_vals)) if dia_vals else None

    # Fasting context
    fasting_context = ""
    if fasting_day:
        day_notes = {
            1: "Day 1: BP fluctuation normal. Body shedding water/sodium. Watch for dizziness.",
            2: "Day 2: Ghrelin peaks. Some BP noise expected. Hydrate well.",
            3: "Day 3: Ketosis kicking in. Expect BP to start dropping meaningfully.",
            4: "Day 4: Optimal fasting zone. BP drop beneficial. Sleep quality often improves.",
            5: "Day 5: Maximum therapeutic effect. Monitor for hypotension. Stay hydrated.",
        }
        fasting_context = f"[FAST DAY {fasting_day}] {day_notes.get(fasting_day, '')}"

    return {
        "date": date_str,
        "fasting_day": fasting_day,
        "overall_status": overall_status,
        "avg_systolic": avg_sys,
        "avg_diastolic": avg_dia,
        "vs_baseline": {
            "systolic_drop": (BASELINE_SYS - avg_sys) if avg_sys else None,
            "diastolic_drop": (BASELINE_DIA - avg_dia) if avg_dia else None,
        },
        "readings": results,
        "fasting_context": fasting_context,
    }


def format_report(analysis, verbose=True):
    """Human-readable coaching report."""
    lines = []
    d = analysis["date"]
    
    # Header
    if analysis["fasting_day"]:
        lines.append(f"🔥 Fast Day {analysis['fasting_day']} — {d}")
    else:
        lines.append(f"📊 BP Analysis — {d}")

    lines.append("─" * 40)

    if analysis["overall_status"] == "NO_DATA":
        lines.append("No BP readings found for this date.")
        return "\n".join(lines)

    # Status badge
    badge = {"RED": "⛔ ACTION NEEDED", "YELLOW": "⚠️  MONITOR", "GREEN": "✅ GOOD"}.get(
        analysis["overall_status"], "?"
    )
    lines.append(f"Status: {badge}")
    lines.append("")

    # Readings
    for r in analysis["readings"]:
        reading = r["reading"]
        time_label = r["time"].capitalize()
        lines.append(f"{time_label} ({reading['time']}): "
                      f"{reading['systolic']}/{reading['diastolic']} mmHg, "
                      f"HR {reading.get('hr', '?')}")
        lines.append(f"  → {r['message']}")

    lines.append("")

    # Average + baseline comparison
    if analysis["avg_systolic"] and analysis["avg_diastolic"]:
        d_sys = analysis["vs_baseline"]["systolic_drop"]
        d_dia = analysis["vs_baseline"]["diastolic_drop"]
        lines.append(f"Average: {analysis['avg_systolic']}/{analysis['avg_diastolic']} mmHg")
        if d_sys is not None:
            sign_sys = "−" if d_sys >= 0 else "+"
            sign_dia = "−" if d_dia >= 0 else "+"
            lines.append(f"vs. Baseline (140/95): {sign_sys}{abs(d_sys)} sys / {sign_dia}{abs(d_dia)} dia")

    # Fasting context
    if analysis["fasting_context"]:
        lines.append("")
        lines.append(f"📋 {analysis['fasting_context']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="BP Analyzer — Fasting Intelligence")
    parser.add_argument("--days", type=int, default=1, help="Analyze last N days")
    parser.add_argument("--date", type=str, help="Specific date (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.date:
        dates = [args.date]
    else:
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(args.days - 1, -1, -1)]

    all_analyses = []
    for date_str in dates:
        memory_file = MEMORY_DIR / f"{date_str}.md"
        if not memory_file.exists():
            all_analyses.append({"date": date_str, "fasting_day": get_fasting_day(date_str), "overall_status": "NO_DATA", "summary": "No memory file for this date."})
            continue
        
        text = memory_file.read_text()
        all_readings = parse_bp_table(text)
        # Filter to only readings matching this date
        readings = [r for r in all_readings if r["date"] == date_str]
        analysis = analyze_day(date_str, readings)
        all_analyses.append(analysis)

    if args.as_json:
        print(json.dumps(all_analyses, indent=2))
        return

    # Print reports
    for analysis in all_analyses:
        print(format_report(analysis))
        print()

    # Multi-day trend
    if len(all_analyses) > 1:
        print("─" * 40)
        print("📈 Trend Analysis")
        sys_vals = [(a["date"], a.get("avg_systolic")) for a in all_analyses if a.get("avg_systolic")]
        if len(sys_vals) >= 2:
            first_sys = sys_vals[0][1]
            last_sys = sys_vals[-1][1]
            delta = last_sys - first_sys
            if delta < -5:
                print(f"Systolic: ↓ {abs(delta)} mmHg drop over {len(sys_vals)} days — excellent fasting response")
            elif delta < 0:
                print(f"Systolic: ↓ {abs(delta)} mmHg — small drop, tracking in right direction")
            elif delta > 5:
                print(f"Systolic: ↑ {delta} mmHg rise — unexpected during fast, flag for coaching review")
            else:
                print(f"Systolic: → stable ({first_sys}→{last_sys} mmHg)")


if __name__ == "__main__":
    main()
