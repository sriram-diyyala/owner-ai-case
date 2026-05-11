import json
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    with open("call_analysis_raw.json") as f:
        calls = json.load(f)
    with open("playbook_patterns.json") as f:
        patterns = json.load(f)
    with open("rep_profiles.json") as f:
        reps = json.load(f)
    restaurants = pd.read_csv("restaurants.csv")
    restaurants.columns = [c.lower() for c in restaurants.columns]
    return calls, patterns, reps, restaurants


def get_team_metrics(calls, reps):
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]
    booked = [c for c in real if c["call_outcome"] == "demo_booked"]
    avg_score_all = sum(c.get("behavior_score", 0) for c in real) / max(len(real), 1)
    avg_score_booked = sum(c.get("behavior_score", 0) for c in booked) / max(len(booked), 1)
    conversion = len(booked) / max(len(real), 1)
    high_priority = len([r for r in reps if r.get("priority") == "high"])
    return {
        "calls_analyzed": len(calls),
        "real_calls": len(real),
        "booked": len(booked),
        "conversion_rate": round(conversion * 100, 1),
        "avg_behavior_score": round(avg_score_all, 1),
        "booked_call_score": round(avg_score_booked, 1),
        "high_priority_reps": high_priority,
        "reps_count": len(reps),
    }


def get_objection_stats(calls, patterns):
    """Add win-rate-with vs win-rate-without to objection map."""
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]
    enriched = []
    for obj_data in patterns.get("top_objections", []):
        objection = obj_data.get("objection", "").lower()
        with_obj = [
            c for c in real
            if any(objection[:20] in o.lower() for o in c.get("objections_raised", []))
        ]
        handled_well = [
            c for c in with_obj
            if c.get("objection_handling") in ["strong", "moderate"]
        ]
        not_handled = [
            c for c in with_obj
            if c.get("objection_handling") in ["weak", "none"]
        ]
        win_with = (
            len([c for c in handled_well if c["call_outcome"] == "demo_booked"]) / max(len(handled_well), 1)
        )
        win_without = (
            len([c for c in not_handled if c["call_outcome"] == "demo_booked"]) / max(len(not_handled), 1)
        )
        enriched.append({
            **obj_data,
            "win_rate_with": round(win_with * 100),
            "win_rate_without": round(win_without * 100),
            "total_appearances": len(with_obj),
        })
    return enriched


def get_action_banner(calls, reps, patterns):
    """Compute the highest-impact coaching action this week."""
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]
    booked = [c for c in real if c["call_outcome"] == "demo_booked"]
    conversion = len(booked) / max(len(real), 1)

    high_priority = sorted(
        [r for r in reps if r.get("priority") == "high"],
        key=lambda x: x.get("total_calls", 0),
        reverse=True,
    )
    top = high_priority[0] if high_priority else None
    if not top:
        return None

    # Estimate lift: if this rep hit median conversion, how many more demos/week?
    median_conversion = conversion
    rep_calls_per_week = top.get("total_calls", 0) / 4  # rough weekly estimate
    current_demos = rep_calls_per_week * top.get("conversion_rate", 0)
    potential_demos = rep_calls_per_week * median_conversion
    lift = max(0, round(potential_demos - current_demos, 1))

    return {
        "rep_id": top["rep_id"],
        "focus": top.get("focus_metric", "").replace("_", " "),
        "headline": f"Coach {top['rep_id']} on {top.get('focus_metric','').replace('_',' ')} — highest impact this week",
        "detail": top.get("coaching_rec", ""),
        "reps_impacted": len(high_priority),
        "estimated_lift": f"+{lift:.0f} demos/week",
    }
