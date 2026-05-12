import json
import re
from collections import defaultdict, Counter
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    with open("data/call_analysis_raw.json") as f:
        calls = json.load(f)
    with open("data/playbook_patterns.json") as f:
        patterns = json.load(f)
    with open("data/rep_profiles.json") as f:
        reps = json.load(f)
    restaurants = pd.read_csv("data/restaurants.csv")
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


_STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "of", "to", "for", "and", "or", "but",
    "with", "at", "by", "from", "as", "on", "up", "be", "was", "are", "were",
    "we", "they", "you", "i", "me", "my", "your", "their", "this", "that",
    "not", "no", "can", "will", "do", "did", "have", "has", "had", "been",
    "before", "after", "when", "if", "about", "already", "still", "just",
    "more", "most", "some", "any", "all", "our", "which", "what", "how",
    "get", "got", "would", "could", "should", "need", "want", "use",
    "right", "now", "very", "also", "only", "even", "like",
}


def _content_words(text):
    """Lowercase alpha words longer than 3 chars, stopwords removed."""
    words = re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}


def _keywords_overlap(pattern_words, raw_words):
    """True if any pair shares an exact match or a 4-char prefix (handles plurals/-ing/-ed)."""
    for pw in pattern_words:
        for rw in raw_words:
            if pw == rw:
                return True
            if len(pw) >= 4 and len(rw) >= 4 and pw[:4] == rw[:4]:
                return True
    return False


def get_objection_stats(calls, patterns):
    """Win-rate-with vs win-rate-without for each playbook objection.

    Matches pattern summaries to raw objections_raised via keyword overlap rather
    than substring — the pattern text is paraphrased while raw values are verbatim.
    Shows '—' instead of a percentage when fewer than 3 calls match a bucket
    (too sparse for a reliable stat).
    """
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]
    enriched = []
    for obj_data in patterns.get("top_objections", []):
        pattern_kws = _content_words(obj_data.get("objection", ""))

        with_obj = []
        for c in real:
            for raw_obj in c.get("objections_raised", []):
                if _keywords_overlap(pattern_kws, _content_words(raw_obj)):
                    with_obj.append(c)
                    break  # count each call once

        handled_well = [c for c in with_obj if c.get("objection_handling") in ["strong", "moderate"]]
        not_handled = [c for c in with_obj if c.get("objection_handling") in ["weak", "none"]]

        if len(handled_well) >= 3:
            rate = len([c for c in handled_well if c["call_outcome"] == "demo_booked"]) / len(handled_well)
            win_with = round(rate * 100)
        else:
            win_with = "—"

        # Top rep: highest avg behavior score among reps with 2+ strong-handling calls for this objection
        strong_calls = [c for c in with_obj if c.get("objection_handling") == "strong"]
        rep_scores: dict = {}
        for c in strong_calls:
            rid = c.get("rep_id")
            if rid:
                rep_scores.setdefault(rid, []).append(c.get("behavior_score", 0))
        qualifying = {rid: sum(s) / len(s) for rid, s in rep_scores.items() if len(s) >= 2}
        top_rep = max(qualifying, key=qualifying.get) if qualifying else "—"

        enriched.append({
            **obj_data,
            "win_rate_with": win_with,
            "total_appearances": len(with_obj),
            "top_rep": top_rep,
        })
    return enriched


_ANGLE_LABELS = {
    "demo_request_followup": "Demo request follow-up",
    "fee_savings": "Recover DoorDash commission",
    "google_ranking": "Google ranking pitch",
    "online_ordering": "Online ordering you control",
    "relationship_followup": "Warm relationship follow-up",
    "other": "Other angle",
}


def get_opening_angle_stats(calls):
    """Per-angle conversion stats for real calls, 5+ sample, sorted by conversion desc."""
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]

    angle_calls: dict = defaultdict(list)
    for c in real:
        angle_calls[c.get("opening_angle", "other")].append(c)

    rows = []
    for angle, angle_list in angle_calls.items():
        if len(angle_list) < 5 or angle == "other":
            continue
        booked = [c for c in angle_list if c.get("call_outcome") == "demo_booked"]
        conv = round(len(booked) / len(angle_list) * 100)

        cuisines = [
            c.get("cuisine_type", "")
            for c in angle_list
            if c.get("cuisine_type") not in ("", "unknown", None)
        ]
        top2 = [k for k, _ in Counter(cuisines).most_common(2)]

        rows.append({
            "angle": angle,
            "human_label": _ANGLE_LABELS.get(angle, angle.replace("_", " ").title()),
            "count": len(angle_list),
            "conversion_rate": conv,
            "best_for": " & ".join(top2) if top2 else "",
        })

    return sorted(rows, key=lambda x: -x["conversion_rate"])


@st.cache_data
def get_restaurant_call_history(_calls):
    """Map restaurant_id -> list of call analysis dicts, via rest_xxx patterns in transcripts.

    Uses underscore-prefixed arg so Streamlit skips hashing the large list.
    """
    calls_csv = pd.read_csv("data/call_transcripts.csv")
    calls_csv.columns = [c.lower() for c in calls_csv.columns]

    call_by_id = {c["call_id"]: c for c in _calls}

    rest_to_calls: dict = {}
    for _, row in calls_csv.iterrows():
        call_id = row["call_id"]
        call_dict = call_by_id.get(call_id)
        if not call_dict:
            continue
        for rest_id in set(re.findall(r"rest_\d+", str(row.get("transcript", "")))):
            rest_to_calls.setdefault(rest_id, [])
            if not any(c["call_id"] == call_id for c in rest_to_calls[rest_id]):
                rest_to_calls[rest_id].append(call_dict)

    return rest_to_calls


def get_action_banner(calls, reps, patterns):
    """Compute the highest-impact coaching action this week."""
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]

    high_priority = sorted(
        [r for r in reps if r.get("priority") == "high"],
        key=lambda x: x.get("total_calls", 0),
        reverse=True,
    )
    top = high_priority[0] if high_priority else None
    if not top:
        return None

    # Conversion rate at median behavior (score ≥ 7) — a realistic target for coached reps
    median_calls = [c for c in real if c.get("behavior_score", 0) >= 7]
    median_booked = [c for c in median_calls if c["call_outcome"] == "demo_booked"]
    median_conversion = len(median_booked) / max(len(median_calls), 1)

    weekly_calls = top.get("total_calls", 0) / 4
    current_demos = weekly_calls * top.get("conversion_rate", 0)
    potential_demos = weekly_calls * median_conversion

    # Round to nearest 0.5; always show at least +1 (rep is the bottleneck); cap at 10
    lift_raw = potential_demos - current_demos
    lift = round(lift_raw * 2) / 2
    if lift < 0.5:
        lift = 1.0
    lift = min(lift, 10.0)

    return {
        "rep_id": top["rep_id"],
        "focus": top.get("focus_metric", "").replace("_", " "),
        "headline": f"Coach {top['rep_id']} on {top.get('focus_metric','').replace('_',' ')} — highest impact this week",
        "detail": top.get("coaching_rec", ""),
        "reps_impacted": len(high_priority),
        "estimated_lift": f"+{lift:g} demos/week",
    }
