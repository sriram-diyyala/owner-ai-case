import anthropic
import pandas as pd
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── RUN FLAGS ────────────────────────────────────────────────
# Set True to skip a step and reuse existing output files.
# To re-run only Step 2: set SKIP_STEP_1 = True, SKIP_STEP_3 = True
SKIP_STEP_1 = True
SKIP_STEP_3 = False

calls = pd.read_csv("data/call_transcripts.csv")
calls.columns = [c.lower() for c in calls.columns]

# ── BEHAVIOR SCORE WEIGHTS ───────────────────────────────────
# Each signal scored 0-10 independently, then weighted to produce
# a composite. Weights reflect domain knowledge about what drives
# demo booking — to be calibrated via regression at 1000+ calls.

SIGNAL_WEIGHTS = {
    "reached_dm":         0.15,
    "asked_discovery":    0.20,
    "objection_handling": 0.20,
    "clear_next_step":    0.15,
    "talk_ratio_score":   0.10,
    "personalization":    0.10,
    "rapport_building":   0.10,
}

signal_keys = list(SIGNAL_WEIGHTS.keys())


def compute_behavior_score(analysis: dict) -> dict:
    scores = {}
    scores["reached_dm"] = 10.0 if analysis.get("reached_dm") else 0.0

    if analysis.get("asked_discovery_questions"):
        n_q = len(analysis.get("discovery_questions_used", []))
        scores["asked_discovery"] = min(10.0, 6.0 + n_q * 1.5)
    else:
        scores["asked_discovery"] = 0.0

    oh_map = {"strong": 10.0, "moderate": 6.0, "weak": 2.0, "none": 5.0}
    scores["objection_handling"] = oh_map.get(analysis.get("objection_handling", "none"), 5.0)
    scores["clear_next_step"] = 10.0 if analysis.get("clear_next_step") else 0.0

    tr = analysis.get("talk_ratio", 50)
    if 40 <= tr <= 55:
        scores["talk_ratio_score"] = 10.0
    elif 35 <= tr <= 65:
        scores["talk_ratio_score"] = 7.0
    elif 25 <= tr <= 75:
        scores["talk_ratio_score"] = 4.0
    else:
        scores["talk_ratio_score"] = 1.0

    p_map = {"high": 10.0, "medium": 6.0, "low": 2.0}
    scores["personalization"] = p_map.get(analysis.get("personalization", "low"), 2.0)

    r_map = {"strong": 10.0, "moderate": 6.0, "weak": 2.0}
    scores["rapport_building"] = r_map.get(analysis.get("rapport_building", "weak"), 2.0)

    composite = round(sum(scores[s] * w for s, w in SIGNAL_WEIGHTS.items()), 1)
    return {"behavior_score": composite, "score_breakdown": scores, "score_weights": SIGNAL_WEIGHTS}


# ── SHARED CONTEXT ───────────────────────────────────────────

OWNER_CONTEXT = """
Owner.com helps independent restaurants compete with chains via:
1. Native online ordering — cuts 20-30% DoorDash/Uber Eats commission fees
2. White-labeled loyalty app — restaurant owns the customer relationship
3. Automated marketing — email/SMS to drive repeat orders
4. SEO/Google ranking tools — local search visibility

Sales motion: outbound cold calling to independent restaurant owners.
Reps: open with social proof, pitch one angle, navigate gatekeepers, handle objections, close for 15-min demo.
Context: 120+ dials/day, avg productive call 3-5 min, demo_booked = success.
Spanish calls exist — flag and evaluate separately.
"""


def pct(n, d):
    return "0%" if d == 0 else f"{round(100*n/d)}%"


def avg(values):
    return 0 if not values else round(sum(values) / len(values), 1)


def _build_segment_angle_matrix(real_calls):
    rows = []
    cuisines = [c for c in pd.Series([r.get("cuisine_type") for r in real_calls]).value_counts().head(6).index if c != "unknown"]
    angles = ["fee_savings", "google_ranking", "online_ordering", "demo_request_followup", "relationship_followup"]
    for cuisine in cuisines:
        for angle in angles:
            seg = [r for r in real_calls if r.get("cuisine_type") == cuisine and r.get("opening_angle") == angle]
            if len(seg) >= 3:
                conv = round(100 * sum(1 for r in seg if r["call_outcome"] == "demo_booked") / len(seg))
                rows.append(f"  {cuisine:<15} x {angle:<25} → {conv}% ({len(seg)} calls)")
    return "\n".join(rows) if rows else "  Insufficient data (need 3+ calls per cell)"


# ── STEP 1 ───────────────────────────────────────────────────

def analyze_call(row):
    prompt = f"""You are a sales call analyst for Owner.com.

{OWNER_CONTEXT}

CALL:
- ID: {row['call_id']} | Outcome: {row['call_outcome']} | Duration: {row['call_duration_min']} min
- Rep: {row['rep_id']} ({row['rep_tenure']}) | Restaurant: {row['cuisine_type']} / {row['restaurant_type']}
- Short call: {row['call_duration_min'] < 2}

TRANSCRIPT:
{row['transcript']}

Score what ACTUALLY happened. talk_ratio = % of words spoken by rep.
discovery_questions_used = ONLY questions revealing prospect situation/needs/pain.
objections_raised = ONLY genuine pushbacks.
value_established_early = did rep establish relevance to THIS restaurant within 60 seconds?
follow_up_indicators = did prospect signal future openness?

Return ONLY valid JSON:
{{
    "language": "english" or "spanish" or "other",
    "call_type": "cold_call" or "follow_up" or "voicemail" or "wrong_person" or "auto_attendant" or "callback_scheduled" or "unknown",
    "reached_dm": true or false,
    "talk_ratio": integer 0-100,
    "used_social_proof": true or false,
    "social_proof_restaurant": "name or null",
    "opening_angle": "fee_savings" or "google_ranking" or "online_ordering" or "demo_request_followup" or "relationship_followup" or "other",
    "asked_discovery_questions": true or false,
    "discovery_questions_used": ["exact text", ...],
    "objections_raised": ["exact text", ...],
    "objection_handling": "strong" or "moderate" or "weak" or "none",
    "objection_handling_detail": "one sentence or null",
    "personalization": "high" or "medium" or "low",
    "personalization_detail": "what rep personalized or null",
    "rapport_building": "strong" or "moderate" or "weak",
    "graceful_exit": true or false,
    "clear_next_step": true or false,
    "next_step_detail": "what the next step was or null",
    "energy_level": "high" or "medium" or "low",
    "gatekeeper_navigation": "excellent" or "good" or "poor" or "not_applicable",
    "pitch_timing": "pitched_too_early" or "pitched_after_discovery" or "no_pitch" or "not_applicable",
    "value_established_early": true or false,
    "value_established_early_detail": "what rep said or null",
    "follow_up_indicators": true or false,
    "biggest_strength": "one specific sentence citing what rep said or did",
    "biggest_gap": "one specific sentence citing what rep missed",
    "coaching_moment": "one sentence a manager says in coaching about this call",
    "summary": "two sentences: what happened and what determined the outcome"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    analysis = json.loads(raw.strip())
    analysis.update(compute_behavior_score(analysis))
    return analysis


if not SKIP_STEP_1:
    print("=" * 60)
    print("STEP 1: Analyzing all calls...")
    print("=" * 60)
    results = []
    errors = []
    for i, row in calls.iterrows():
        try:
            analysis = analyze_call(row)
            for field in ["call_id", "rep_id", "rep_tenure", "call_outcome", "call_duration_min", "cuisine_type", "restaurant_type", "num_locations"]:
                analysis[field] = row[field]
            analysis["is_short_call"] = row["call_duration_min"] < 2
            analysis["is_unknown_cuisine"] = row["cuisine_type"] == "unknown"
            results.append(analysis)
            print(f"  ✓ {row['call_id']} ({i+1}/{len(calls)}) score:{analysis.get('behavior_score','?')} | {row['call_outcome']} | {analysis.get('call_type','?')}")
            time.sleep(0.3)
        except Exception as e:
            errors.append({"call_id": row["call_id"], "error": str(e)})
            print(f"  ✗ {row['call_id']} — ERROR: {e}")
    with open("data/call_analysis_raw.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. {len(results)} analyzed, {len(errors)} errors.")
else:
    print("STEP 1: Skipped — loading existing call_analysis_raw.json")
    with open("data/call_analysis_raw.json") as f:
        results = json.load(f)
    errors = []
    print(f"  Loaded {len(results)} calls.")


# ── STEP 2 ───────────────────────────────────────────────────

print("\n" + "=" * 60)
print("STEP 2: Building playbook patterns...")
print("=" * 60)

real_calls = [r for r in results if r.get("call_type") not in ["auto_attendant", "voicemail"] and r.get("language") == "english"]
booked = [r for r in real_calls if r["call_outcome"] == "demo_booked"]
not_booked = [r for r in real_calls if r["call_outcome"] == "not_booked"]

booked_signal_avgs = {k: avg([r.get("score_breakdown", {}).get(k, 0) for r in booked]) for k in signal_keys}
not_booked_signal_avgs = {k: avg([r.get("score_breakdown", {}).get(k, 0) for r in not_booked]) for k in signal_keys}
tenure_df = pd.DataFrame(real_calls).groupby(["rep_tenure", "call_outcome"]).size().unstack(fill_value=0)

pattern_prompt = f"""You are the head of sales intelligence at Owner.com, analyzing {len(real_calls)} real outbound sales calls.

{OWNER_CONTEXT}

DATASET:
- Real conversations: {len(real_calls)} | Booked: {len(booked)} ({pct(len(booked),len(real_calls))}) | Not booked: {len(not_booked)}
- Avg duration booked: {avg([r['call_duration_min'] for r in booked])} min | Not booked: {avg([r['call_duration_min'] for r in not_booked])} min

BEHAVIOR SIGNAL BREAKDOWN:
Signal                  | Booked | Not Booked | Delta
reached_dm             | {booked_signal_avgs.get('reached_dm',0):.1f}   | {not_booked_signal_avgs.get('reached_dm',0):.1f}       | {booked_signal_avgs.get('reached_dm',0)-not_booked_signal_avgs.get('reached_dm',0):+.1f}
asked_discovery        | {booked_signal_avgs.get('asked_discovery',0):.1f}   | {not_booked_signal_avgs.get('asked_discovery',0):.1f}       | {booked_signal_avgs.get('asked_discovery',0)-not_booked_signal_avgs.get('asked_discovery',0):+.1f}
objection_handling     | {booked_signal_avgs.get('objection_handling',0):.1f}   | {not_booked_signal_avgs.get('objection_handling',0):.1f}       | {booked_signal_avgs.get('objection_handling',0)-not_booked_signal_avgs.get('objection_handling',0):+.1f}
clear_next_step        | {booked_signal_avgs.get('clear_next_step',0):.1f}   | {not_booked_signal_avgs.get('clear_next_step',0):.1f}       | {booked_signal_avgs.get('clear_next_step',0)-not_booked_signal_avgs.get('clear_next_step',0):+.1f}
talk_ratio_score       | {booked_signal_avgs.get('talk_ratio_score',0):.1f}   | {not_booked_signal_avgs.get('talk_ratio_score',0):.1f}       | {booked_signal_avgs.get('talk_ratio_score',0)-not_booked_signal_avgs.get('talk_ratio_score',0):+.1f}
personalization        | {booked_signal_avgs.get('personalization',0):.1f}   | {not_booked_signal_avgs.get('personalization',0):.1f}       | {booked_signal_avgs.get('personalization',0)-not_booked_signal_avgs.get('personalization',0):+.1f}
rapport_building       | {booked_signal_avgs.get('rapport_building',0):.1f}   | {not_booked_signal_avgs.get('rapport_building',0):.1f}       | {booked_signal_avgs.get('rapport_building',0)-not_booked_signal_avgs.get('rapport_building',0):+.1f}

OPENING ANGLES — Booked: {pd.Series([r.get('opening_angle') for r in booked]).value_counts().to_dict()}
OPENING ANGLES — Not booked: {pd.Series([r.get('opening_angle') for r in not_booked]).value_counts().to_dict()}

TOP OBJECTIONS — Booked: {pd.Series([o for r in booked for o in r.get('objections_raised',[])]).value_counts().head(8).to_dict()}
TOP OBJECTIONS — Not booked: {pd.Series([o for r in not_booked for o in r.get('objections_raised',[])]).value_counts().head(8).to_dict()}

DISCOVERY: Booked {pct(sum(1 for r in booked if r.get('asked_discovery_questions')),len(booked))} | Not booked {pct(sum(1 for r in not_booked if r.get('asked_discovery_questions')),len(not_booked))}
SOCIAL PROOF: Booked {pct(sum(1 for r in booked if r.get('used_social_proof')),len(booked))} | Not booked {pct(sum(1 for r in not_booked if r.get('used_social_proof')),len(not_booked))}
PITCH AFTER DISCOVERY: Booked {pct(sum(1 for r in booked if r.get('pitch_timing')=='pitched_after_discovery'),len(booked))} | Pitched too early not booked {pct(sum(1 for r in not_booked if r.get('pitch_timing')=='pitched_too_early'),len(not_booked))}
CLEAR NEXT STEP: Booked {pct(sum(1 for r in booked if r.get('clear_next_step')),len(booked))} | Not booked {pct(sum(1 for r in not_booked if r.get('clear_next_step')),len(not_booked))}
VALUE EARLY: Booked {pct(sum(1 for r in booked if r.get('value_established_early')),len(booked))} | Not booked {pct(sum(1 for r in not_booked if r.get('value_established_early')),len(not_booked))}

TENURE:
{tenure_df.to_string()}

HIGH-BEHAVIOR NOT-BOOKED (score >= 7, still failed):
Count: {len([r for r in not_booked if r.get('behavior_score',0) >= 7])}
Objections: {pd.Series([o for r in not_booked if r.get('behavior_score',0) >= 7 for o in r.get('objections_raised',[])]).value_counts().head(5).to_dict()}

SEGMENT x ANGLE MATRIX:
{_build_segment_angle_matrix(real_calls)}

FOLLOW-UP SIGNALS: {pct(sum(1 for r in not_booked if r.get('follow_up_indicators')),len(not_booked))} of not-booked calls showed follow-up interest

STATISTICAL AND METHODOLOGICAL GUARDRAILS — apply ALL before surfacing any finding:

1. SIGNIFICANCE: Delta >= 15 percentage points AND smaller group >= 10 calls required.
   If pattern exists but doesn't meet bar: label "early signal — needs more data at scale."
   Do NOT include in three_things_we_didnt_know.

2. CAUSALITY CHECK: For every finding ask — could causality be reversed?
   Could a confound (rep experience, call duration, territory) explain both X and Y?
   If yes: frame as "Hypothesis: X may cause Y. Mechanism: [explain]. To validate: [what to test]."
   Do NOT state as confirmed causal fact.

3. SALES METHODOLOGY CHECK: If finding contradicts B2B sales best practices
   (SPIN, Challenger, consultative selling, MEDDIC), do NOT discard — but require
   20+ pt delta AND explicitly state: "Contradicts standard methodology. Explanation
   for restaurant cold calling context: [specific reason]."

4. ACTIONABILITY GATE: Every finding in three_things_we_didnt_know must answer
   "What should a rep do differently on their NEXT call?"
   If no clear behavioral implication: exclude it.

Return ONLY valid JSON:
{{
    "top_winning_behaviors": [
        {{
            "behavior": "3-5 word name",
            "insight": "one sentence: what it is, why it works, the mechanism",
            "booked_rate": "X of Y calls booked",
            "evidence_stat": "specific number from data above"
        }}
    ],
    "top_objections": [
        {{
            "objection": "objection category name",
            "frequency": "X% of calls",
            "best_response": "specific response approach that works",
            "example_rep_behavior": "what a top rep actually says"
        }}
    ],
    "opening_angle_analysis": {{
        "best_angle": "angle name",
        "best_angle_conversion": "X%",
        "insight": "why it works psychologically for restaurant owners",
        "worst_angle": "angle name",
        "worst_angle_conversion": "X%",
        "worst_insight": "why it underperforms and what it triggers"
    }},
    "tenure_insight": "one paragraph: what does tenure data actually show?",
    "duration_insight": "one paragraph: what does call duration tell us?",
    "three_things_we_didnt_know": [
        {{
            "title": "4-8 word punchy causal headline",
            "detail": "2-3 sentences. Specific numbers. Causal mechanism or honest hypothesis acknowledging confounds. What manager should change. What rep does differently tomorrow."
        }},
        {{
            "title": "4-8 word punchy causal headline",
            "detail": "2-3 sentences. Numbers. Mechanism or hypothesis. What changes."
        }},
        {{
            "title": "4-8 word punchy causal headline",
            "detail": "2-3 sentences. Numbers. Mechanism or hypothesis. What changes."
        }}
    ],
    "segment_angle_insights": [
        {{
            "cuisine": "cuisine type",
            "best_angle": "opening angle",
            "conversion_rate": "X%",
            "insight": "why this angle works for this segment"
        }}
    ],
    "high_behavior_not_booked": {{
        "count": "number",
        "pattern": "what these calls have in common",
        "gtm_implication": "product-market fit gap, pricing, or timing? What does GTM team do with this?"
    }},
    "follow_up_opportunity": {{
        "count": "number",
        "pct_of_not_booked": "X%",
        "implication": "what a follow-up sequencing system captures"
    }}
}}"""

pattern_response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=3000,
    messages=[{"role": "user", "content": pattern_prompt}],
)

raw = pattern_response.content[0].text.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
playbook_patterns = json.loads(raw.strip())

playbook_patterns["behavior_score_methodology"] = {
    "description": "Composite of 7 signals. Weights = domain knowledge; calibrate via regression at 1000+ calls.",
    "signals": SIGNAL_WEIGHTS,
    "scoring_notes": {
        "talk_ratio": "Optimal 40-55% rep talking. Outside 25-75% = score 1.",
        "asked_discovery": "Binary + quality: +1.5pts per question, max 10.",
        "objection_handling": "strong=10, moderate=6, weak=2, none=5.",
        "reached_dm": "Binary prerequisite.",
        "clear_next_step": "Binary explicit ask.",
        "personalization": "high=10, medium=6, low=2.",
        "rapport_building": "strong=10, moderate=6, weak=2.",
    },
}

with open("data/playbook_patterns.json", "w") as f:
    json.dump(playbook_patterns, f, indent=2)

print("Playbook patterns saved.")
print("\nTHREE THINGS WE DIDN'T KNOW:")
for i, ins in enumerate(playbook_patterns.get("three_things_we_didnt_know", []), 1):
    if isinstance(ins, dict):
        print(f"  {i}. {ins.get('title','')}")
        print(f"     {ins.get('detail','')}")
    else:
        print(f"  {i}. {ins}")

print("\nSEGMENT x ANGLE:")
for s in playbook_patterns.get("segment_angle_insights", []):
    print(f"  {s.get('cuisine')} x {s.get('best_angle')} → {s.get('conversion_rate')}")

hb = playbook_patterns.get("high_behavior_not_booked", {})
print(f"\nHIGH-BEHAVIOR NOT-BOOKED: {hb.get('count')} calls | {hb.get('gtm_implication','')}")

fu = playbook_patterns.get("follow_up_opportunity", {})
print(f"FOLLOW-UP OPPORTUNITY: {fu.get('count')} calls ({fu.get('pct_of_not_booked')}) | {fu.get('implication','')}")


# ── STEP 3 ───────────────────────────────────────────────────

if not SKIP_STEP_3:
    print("\n" + "=" * 60)
    print("STEP 3: Building rep profiles...")
    print("=" * 60)

    rep_profiles = []
    for rep_id in sorted(set(r["rep_id"] for r in results)):
        rep_calls = [r for r in results if r["rep_id"] == rep_id]
        rep_real = [r for r in rep_calls if r.get("call_type") not in ["auto_attendant","voicemail"] and r.get("language") == "english"]
        rep_booked = [r for r in rep_real if r["call_outcome"] == "demo_booked"]

        if not rep_calls:
            continue

        tenure = rep_calls[0].get("rep_tenure", "unknown")
        avg_score = avg([r.get("behavior_score", 0) for r in rep_real])
        conversion_rate = len(rep_booked) / max(len(rep_real), 1)
        avg_duration = avg([r.get("call_duration_min", 0) for r in rep_calls])
        best_call = max(rep_real, key=lambda x: x.get("behavior_score", 0)) if rep_real else None
        rep_signal_avgs = {k: avg([r.get("score_breakdown", {}).get(k, 0) for r in rep_real]) for k in signal_keys}
        weakest_signal = min(rep_signal_avgs, key=rep_signal_avgs.get) if rep_signal_avgs else "unknown"
        coaching_moments = [r.get("coaching_moment","") for r in rep_real if r.get("coaching_moment")][:5]

        coaching_prompt = f"""Sales coach at Owner.com, weekly 1:1 with rep {rep_id}.

{OWNER_CONTEXT}

REP DATA:
- Tenure: {tenure} | Calls: {len(rep_calls)} | Real convos: {len(rep_real)} | Booked: {len(rep_booked)}
- Conversion: {conversion_rate:.0%} (team median ~33%) | Avg score: {avg_score:.1f}/10
- Signal breakdown: {json.dumps(rep_signal_avgs)}
- Weakest signal: {weakest_signal} ({rep_signal_avgs.get(weakest_signal,0):.1f})
- Angles used: {pd.Series([r.get('opening_angle') for r in rep_real]).value_counts().to_dict()}
- Strengths: {[r.get('biggest_strength','') for r in rep_real[:5]]}
- Gaps: {[r.get('biggest_gap','') for r in rep_real[:5]]}
- Coaching moments: {coaching_moments}

RULES: Be specific to THIS rep. coaching_rec = one verbatim manager sentence.
gap = recurring pattern across calls, not one-off.
priority: high if conv<25% AND calls>=8; low if conv>50%; else medium.

Return ONLY valid JSON:
{{
    "strength": "one sentence citing recurring strength",
    "gap": "one sentence citing recurring weakness pattern",
    "coaching_rec": "one verbatim manager sentence targeting {weakest_signal}",
    "focus_metric": "{weakest_signal}",
    "priority": "high" or "medium" or "low",
    "best_call_to_review": "one sentence on why {best_call['call_id'] if best_call else 'N/A'} is worth reviewing"
}}"""

        coaching_response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": coaching_prompt}],
        )
        raw = coaching_response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        coaching = json.loads(raw.strip())

        rep_profiles.append({
            "rep_id": rep_id, "tenure": tenure,
            "total_calls": len(rep_calls), "real_conversations": len(rep_real),
            "demos_booked": len(rep_booked), "conversion_rate": round(conversion_rate, 3),
            "avg_behavior_score": avg_score, "avg_duration_min": avg_duration,
            "best_call_id": best_call["call_id"] if best_call else None,
            "best_call_score": best_call.get("behavior_score") if best_call else None,
            "signal_breakdown": rep_signal_avgs, "weakest_signal": weakest_signal,
            "strength": coaching.get("strength"), "gap": coaching.get("gap"),
            "coaching_rec": coaching.get("coaching_rec"),
            "focus_metric": coaching.get("focus_metric", weakest_signal),
            "priority": coaching.get("priority"),
            "best_call_rationale": coaching.get("best_call_to_review"),
        })
        print(f"  ✓ {rep_id} | {tenure} | {avg_score:.1f} score | {conversion_rate:.0%} conv | weakest: {weakest_signal} | {coaching.get('priority')}")
        time.sleep(0.3)

    with open("data/rep_profiles.json", "w") as f:
        json.dump(rep_profiles, f, indent=2)
    print(f"\nDone. {len(rep_profiles)} rep profiles built.")

else:
    print("\nSTEP 3: Skipped — using existing rep_profiles.json")


# ── SUMMARY ─────────────────────────────────────────────────

print("\n" + "=" * 60)
print("ALL DONE")
print("=" * 60)
print("  data/call_analysis_raw.json  — per-call scores + 7-signal breakdown")
print("  data/playbook_patterns.json  — causal patterns + GTM insights + methodology")
print("  data/rep_profiles.json       — rep scorecards + weakest signal + coaching rec")
print("\nBehavior score weights:")
for s, w in SIGNAL_WEIGHTS.items():
    print(f"  {s:<22} {w:.0%}")