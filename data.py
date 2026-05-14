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
    words = re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}


def _keywords_overlap(pattern_words, raw_words):
    for pw in pattern_words:
        for rw in raw_words:
            if pw == rw:
                return True
            if len(pw) >= 4 and len(rw) >= 4 and pw[:4] == rw[:4]:
                return True
    return False


def get_objection_stats(calls, patterns):
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]
    enriched = []
    for obj_data in patterns.get("top_objections", []):
        pattern_kws = _content_words(obj_data.get("objection", ""))

        with_obj = []
        for c in real:
            for raw_obj in c.get("objections_raised", []):
                if _keywords_overlap(pattern_kws, _content_words(raw_obj)):
                    with_obj.append(c)
                    break

        handled_well = [c for c in with_obj if c.get("objection_handling") in ["strong", "moderate"]]

        if len(handled_well) >= 2:
            rate = len([c for c in handled_well if c["call_outcome"] == "demo_booked"]) / len(handled_well)
            win_with = round(rate * 100)
        else:
            win_with = "—"

        best_call = max(
            (c for c in with_obj if c.get("objection_handling") in ("strong", "moderate") and c.get("rep_id")),
            key=lambda c: c.get("behavior_score", 0),
            default=None,
        )
        top_rep = best_call["rep_id"] if best_call else "—"

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


# ── Dynamic banner copy templates ────────────────────────────
# Each signal has: headline, current_state, why_it_matters, the_fix
# All strings use {n} for affected count, {total} for total reps,
# {lift} for estimated lift, {rec} for the top rep's coaching rec.

_BANNER_TEMPLATES = {
    "talk_ratio_score": {
        "headline": "Your team is talking prospects out of demos",
        "current_state": "{n} of {total} reps dominate their calls, speaking 65%+ of the time. Prospects barely get a word in before hearing the pitch.",
        "why_it_matters": "Calls where reps hit the 40–55% talk range convert at nearly 2x the rate. Reps who listen more book more — the data is unambiguous.",
        "the_fix": "This week: have every rep pull one recent call, count their talk ratio, and set a personal target of under 55%. Add talk ratio to your weekly coaching scorecard.",
    },
    "asked_discovery": {
        "headline": "Your team is pitching blind — no discovery, no demos",
        "current_state": "{n} of {total} reps skip discovery questions and go straight to the pitch. They're presenting solutions to problems they haven't confirmed exist.",
        "why_it_matters": "Calls with at least one discovery question before the pitch convert significantly higher. Restaurant owners respond when reps show they understand their specific situation.",
        "the_fix": "This week: make one discovery question mandatory before any pitch. Coach the team to open with 'Quick question before I tell you what we do — are you currently on DoorDash or Uber Eats?",
    },
    "objection_handling": {
        "headline": "Your team folds when prospects push back",
        "current_state": "{n} of {total} reps handle objections weakly — either accepting the 'no' immediately or pivoting awkwardly instead of probing deeper.",
        "why_it_matters": "Strong objection handling converts at 3–4x the rate of weak handling on the same objection. The objection is often the opening, not the close.",
        "the_fix": "This week: role-play the top 3 objections from the data — 'not interested,' 'already have a website,' 'too busy.' Coach reps to respond with a question, not a counter-pitch.",
    },
    "clear_next_step": {
        "headline": "Your team leaves calls without booking anything",
        "current_state": "{n} of {total} reps end calls without a clear next step. No date, no time, no commitment — just 'I'll follow up.'",
        "why_it_matters": "Calls with a specific next step booked on the call convert dramatically higher than calls that end with vague follow-up promises. Vague follow-ups die in inboxes.",
        "the_fix": "This week: make the ask mandatory. Coach every rep to say 'I have Tuesday at 2pm or Wednesday at 10am — which works better for a 15-minute look?' before hanging up.",
    },
    "personalization": {
        "headline": "Your team is running generic scripts on unique restaurants",
        "current_state": "{n} of {total} reps pitch the same way to every restaurant regardless of cuisine, size, or situation. Owners can hear the script.",
        "why_it_matters": "High-personalization calls convert at significantly higher rates. Restaurant owners are entrepreneurs — they respond to reps who have clearly looked at their specific business.",
        "the_fix": "This week: require reps to reference one specific thing about the restaurant before pitching — their cuisine, their delivery platform, a competitor down the street. One sentence of personalization changes the whole tone.",
    },
    "rapport_building": {
        "headline": "Your team jumps to pitch before building any trust",
        "current_state": "{n} of {total} reps skip rapport entirely and launch into questions or pitches within the first 20 seconds. Calls feel transactional from the start.",
        "why_it_matters": "Cold calls to restaurant owners interrupt their workday. A single acknowledgment — 'I know you're probably mid-lunch rush' — changes the dynamic. Rapport isn't small talk, it's permission.",
        "the_fix": "This week: coach every rep to open with one line that shows awareness of the owner's world before asking anything. 10 seconds of empathy buys 3 minutes of attention.",
    },
    "reached_dm": {
        "headline": "Your team is coaching gatekeepers instead of owners",
        "current_state": "{n} of {total} reps are failing to reach the actual decision maker on most calls. They're pitching staff who can't say yes.",
        "why_it_matters": "You can't book a demo without the owner. Every call that ends with a gatekeeper is a wasted dial — no matter how good the pitch was.",
        "the_fix": "This week: run a gatekeeper navigation drill. Coach the team to say 'Is [owner name] usually in around this time?' rather than launching the pitch at whoever picks up. Own the conversation before you give it.",
    },
}

_DEFAULT_TEMPLATE = {
    "headline": "{n} reps share the same gap — {label}",
    "current_state": "{n} of {total} reps score lowest on {label}. This is the single most common weakness across the team.",
    "why_it_matters": "Fixing this one behavior consistently is the highest-leverage coaching investment this week based on call volume and conversion gap.",
    "the_fix": "Focus your 1:1s this week on {label}.",
}


def get_action_banner(calls, reps, patterns):
    """Surface the highest-leverage team-wide coaching pattern this week."""
    real = [c for c in calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]

    # Most common weakest signal across all reps
    weakness_counter = Counter(
        r.get("weakest_signal", "") for r in reps if r.get("weakest_signal")
    )
    top_weakness, affected_count = weakness_counter.most_common(1)[0]

    # Affected reps sorted by priority then call volume
    affected_reps = sorted(
        [r for r in reps if r.get("weakest_signal") == top_weakness],
        key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1),
            -x.get("total_calls", 0),
        ),
    )

    # Lift across all affected reps
    median_calls = [c for c in real if c.get("behavior_score", 0) >= 7]
    median_booked = [c for c in median_calls if c["call_outcome"] == "demo_booked"]
    median_conversion = len(median_booked) / max(len(median_calls), 1)

    total_lift = 0.0
    for rep in affected_reps:
        weekly_calls = rep.get("total_calls", 0) / 4
        current_demos = weekly_calls * rep.get("conversion_rate", 0)
        potential_demos = weekly_calls * median_conversion
        lift_raw = max(potential_demos - current_demos, 0)
        total_lift += round(lift_raw * 2) / 2
    total_lift = min(round(total_lift * 2) / 2, 15.0)
    if total_lift < 0.5:
        total_lift = 1.0

    weakness_labels = {
        "talk_ratio_score": "talking too much on calls",
        "asked_discovery": "skipping discovery questions",
        "objection_handling": "weak objection handling",
        "clear_next_step": "not closing for a next step",
        "personalization": "using generic pitches",
        "rapport_building": "skipping rapport before pitching",
        "reached_dm": "not reaching decision makers",
    }
    weakness_label = weakness_labels.get(top_weakness, top_weakness.replace("_", " "))

    # Pull template
    tmpl = _BANNER_TEMPLATES.get(top_weakness, _DEFAULT_TEMPLATE)

    def _fill(s):
        return s.format(
            n=affected_count,
            total=len(reps),
            lift=f"+{total_lift:g}",
            label=weakness_label,
        )

    headline = _fill(tmpl["headline"])
    current_state = _fill(tmpl["current_state"])
    why_it_matters = _fill(tmpl["why_it_matters"])
    the_fix = _fill(tmpl["the_fix"])

    # Structured HTML detail — three bullets
    detail = (
        f'<ul style="margin:10px 0 0 0; padding-left:18px; opacity:0.92; line-height:1.6;">'
        f'<li style="margin-bottom:8px;"><strong>What\'s happening:</strong> {current_state}</li>'
        f'<li style="margin-bottom:8px;"><strong>Why it matters:</strong> {why_it_matters}</li>'
        f'<li style="margin-bottom:0;"><strong>The fix:</strong> {the_fix}</li>'
        f'</ul>'
    )

    return {
        "headline": headline,
        "detail": detail,
        "reps_impacted": affected_count,
        "estimated_lift": f"+{total_lift:g} demos/week",
        "affected_reps": [],
        "top_weakness": top_weakness,
        "is_html_detail": True,
    }

def research_restaurant(name: str, city: str, state: str = "", cuisine: str = "") -> dict:
    """
    Use Claude with web search to research a restaurant before generating a brief.
    Returns structured intel that gets injected into the brief prompt.
    Works for both new restaurants (no call history) and existing ones (enhances context).
    """
    import anthropic
    import os
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    location = f"{city}, {state}" if state else city

    prompt = f"""Research this restaurant and return structured intel for a sales rep at Owner.com who is about to call them.

Restaurant: {name}
Location: {location}
{f'Cuisine: {cuisine}' if cuisine else ''}

Find and return ONLY what you can verify from search results:
1. Are they currently on DoorDash, Uber Eats, or other delivery platforms?
2. Do they have their own website with online ordering?
3. Google rating and approximate number of reviews
4. Number of locations
5. Any recent news, expansions, or changes (last 6 months)
6. What customers say about them (1-2 themes from reviews)

Return ONLY valid JSON, no markdown:
{{
    "on_doordash": true or false or null,
    "on_uber_eats": true or false or null,
    "has_own_ordering": true or false or null,
    "google_rating": float or null,
    "review_count": integer or null,
    "num_locations": integer or null,
    "recent_news": "one sentence summary of anything notable, or null",
    "customer_themes": "one sentence on what customers say, or null",
    "sales_angle_hint": "one sentence on the most relevant Owner.com angle given what you found",
    "data_freshness": "web_search"
}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from response (may include tool_use blocks)
        full_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_text += block.text

        # Parse JSON from response
        raw = full_text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        # Find JSON object in response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])

    except Exception as e:
        print(f"research_restaurant error: {e}")

    # Fallback — return empty intel rather than crashing
    return {
        "on_doordash": None,
        "on_uber_eats": None,
        "has_own_ordering": None,
        "google_rating": None,
        "review_count": None,
        "num_locations": None,
        "recent_news": None,
        "customer_themes": None,
        "sales_angle_hint": None,
        "data_freshness": "unavailable",
    }