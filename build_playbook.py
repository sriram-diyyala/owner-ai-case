import anthropic
import pandas as pd
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

calls = pd.read_csv('data/call_transcripts.csv')
calls.columns = [c.lower() for c in calls.columns]

# ── STEP 1: ANALYZE EVERY CALL ──────────────────────────────

def analyze_call(row):
    is_short = row['call_duration_min'] < 2
    
    prompt = f"""You are analyzing a sales call for Owner.com, a platform that helps independent restaurants compete with chains by giving them their own website, native online ordering, loyalty apps, and automated marketing — cutting out 30% DoorDash/Uber Eats commission fees.

Call metadata:
- Call ID: {row['call_id']}
- Outcome: {row['call_outcome']}
- Duration: {row['call_duration_min']} minutes
- Rep ID: {row['rep_id']}
- Rep tenure: {row['rep_tenure']}
- Cuisine type: {row['cuisine_type']}
- Restaurant type: {row['restaurant_type']}
- Short call flag: {is_short}

Transcript:
{row['transcript']}

Analyze this call carefully. Even short calls contain signal about rep behavior.

Return ONLY a valid JSON object with exactly these fields:
{{
    "language": "english" or "spanish" or "other",
    "call_type": "cold_call", "follow_up", "voicemail", "wrong_person", "auto_attendant", or "unknown",
    "reached_dm": true or false,
    "talk_ratio": integer 0-100 (estimated % rep was talking),
    "used_social_proof": true or false (did rep mention a nearby restaurant they work with),
    "opening_angle": "fee_savings", "google_ranking", "online_ordering", "demo_request_followup", "relationship_followup", or "other",
    "asked_discovery_questions": true or false,
    "discovery_questions_used": [list of actual discovery questions the rep asked, empty if none],
    "objections_raised": [list of objections the prospect raised, empty if none],
    "objection_handling": "strong", "moderate", "weak", or "none",
    "personalization": "high", "medium", or "low",
    "rapport_building": "strong", "moderate", or "weak",
    "graceful_exit": true or false (did rep handle rejection or early end professionally),
    "clear_next_step": true or false (was there a clear next action at end of call),
    "energy_level": "high", "medium", or "low",
    "behavior_score": integer 1-10 (overall rep behavior quality, not outcome),
    "biggest_strength": "one sentence describing what the rep did best",
    "biggest_gap": "one sentence describing the rep's biggest missed opportunity",
    "summary": "two sentence summary of what happened on this call"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


print("=" * 60)
print("STEP 1: Analyzing all 150 calls...")
print("=" * 60)

results = []
errors = []

for i, row in calls.iterrows():
    try:
        analysis = analyze_call(row)
        analysis['call_id'] = row['call_id']
        analysis['rep_id'] = row['rep_id']
        analysis['rep_tenure'] = row['rep_tenure']
        analysis['call_outcome'] = row['call_outcome']
        analysis['call_duration_min'] = row['call_duration_min']
        analysis['cuisine_type'] = row['cuisine_type']
        analysis['restaurant_type'] = row['restaurant_type']
        analysis['num_locations'] = row['num_locations']
        analysis['is_short_call'] = row['call_duration_min'] < 2
        analysis['is_unknown_cuisine'] = row['cuisine_type'] == 'unknown'
        results.append(analysis)
        print(f"  ✓ {row['call_id']} ({i+1}/150) — score: {analysis.get('behavior_score','?')} | outcome: {row['call_outcome']}")
        time.sleep(0.3)
    except Exception as e:
        errors.append({'call_id': row['call_id'], 'error': str(e)})
        print(f"  ✗ {row['call_id']} — ERROR: {e}")

# Save raw results
with open('data/call_analysis_raw.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nDone. {len(results)} calls analyzed, {len(errors)} errors.")
if errors:
    print("Errors:", errors)

# ── STEP 2: BUILD PLAYBOOK PATTERNS ─────────────────────────

print("\n" + "=" * 60)
print("STEP 2: Building playbook patterns...")
print("=" * 60)

# Filter to real conversations with known outcomes
real_calls = [r for r in results if r.get('call_type') not in ['auto_attendant', 'voicemail']]
booked = [r for r in real_calls if r['call_outcome'] == 'demo_booked']
not_booked = [r for r in real_calls if r['call_outcome'] == 'not_booked']

# Build pattern summary for Claude to analyze
pattern_prompt = f"""You are analyzing {len(real_calls)} sales calls for Owner.com to extract patterns that explain what separates successful calls (demo booked) from unsuccessful ones.

DEMO BOOKED CALLS ({len(booked)} total):
- Avg behavior score: {sum(r.get('behavior_score',0) for r in booked)/max(len(booked),1):.1f}
- Avg duration: {sum(r.get('call_duration_min',0) for r in booked)/max(len(booked),1):.1f} min
- Used social proof: {sum(1 for r in booked if r.get('used_social_proof'))} of {len(booked)}
- Asked discovery questions: {sum(1 for r in booked if r.get('asked_discovery_questions'))} of {len(booked)}
- Had clear next step: {sum(1 for r in booked if r.get('clear_next_step'))} of {len(booked)}
- Opening angles: {pd.Series([r.get('opening_angle') for r in booked]).value_counts().to_dict()}
- Objection handling: {pd.Series([r.get('objection_handling') for r in booked]).value_counts().to_dict()}
- Top objections raised: {pd.Series([o for r in booked for o in r.get('objections_raised',[])]).value_counts().head(10).to_dict()}

NOT BOOKED CALLS ({len(not_booked)} total):
- Avg behavior score: {sum(r.get('behavior_score',0) for r in not_booked)/max(len(not_booked),1):.1f}
- Avg duration: {sum(r.get('call_duration_min',0) for r in not_booked)/max(len(not_booked),1):.1f} min
- Used social proof: {sum(1 for r in not_booked if r.get('used_social_proof'))} of {len(not_booked)}
- Asked discovery questions: {sum(1 for r in not_booked if r.get('asked_discovery_questions'))} of {len(not_booked)}
- Had clear next step: {sum(1 for r in not_booked if r.get('clear_next_step'))} of {len(not_booked)}
- Opening angles: {pd.Series([r.get('opening_angle') for r in not_booked]).value_counts().to_dict()}
- Objection handling: {pd.Series([r.get('objection_handling') for r in not_booked]).value_counts().to_dict()}
- Top objections raised: {pd.Series([o for r in not_booked for o in r.get('objections_raised',[])]).value_counts().head(10).to_dict()}

TENURE BREAKDOWN:
{pd.DataFrame(real_calls).groupby(['rep_tenure','call_outcome']).size().to_string()}

Based on this data, generate a playbook pattern analysis. Return ONLY valid JSON:
{{
    "top_winning_behaviors": [
        {{
            "behavior": "behavior name",
            "insight": "one sentence explaining what this behavior is and why it works",
            "booked_rate": "X of Y calls with this behavior booked demo",
            "evidence_stat": "specific number from the data"
        }}
    ],
    "top_objections": [
        {{
            "objection": "objection text",
            "frequency": "how often it appears",
            "best_response": "one sentence on how top reps handle this",
            "example_rep_behavior": "what good looks like"
        }}
    ],
    "opening_angle_analysis": {{
        "best_angle": "angle name",
        "insight": "why this angle works best",
        "worst_angle": "angle name",
        "worst_insight": "why this angle underperforms"
    }},
    "tenure_insight": "one paragraph on what the tenure data actually shows — is experience the differentiator?",
    "duration_insight": "one paragraph on what call duration tells us about successful calls",
    "three_things_we_didnt_know": [
        {{"title": "Short punchy title (4-7 words)", "detail": "One sentence with the specific numbers and why it's counterintuitive"}},
        {{"title": "Short punchy title (4-7 words)", "detail": "One sentence with the specific numbers and why it's counterintuitive"}},
        {{"title": "Short punchy title (4-7 words)", "detail": "One sentence with the specific numbers and why it's counterintuitive"}}
    ]
}}"""

pattern_response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": pattern_prompt}]
)

raw = pattern_response.content[0].text.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
playbook_patterns = json.loads(raw.strip())

with open('data/playbook_patterns.json', 'w') as f:
    json.dump(playbook_patterns, f, indent=2)

print("Playbook patterns built.")
print("\nTHREE THINGS WE DIDN'T KNOW:")
for i, insight in enumerate(playbook_patterns.get('three_things_we_didnt_know', []), 1):
    print(f"  {i}. {insight}")

# ── STEP 3: BUILD REP PROFILES ───────────────────────────────

print("\n" + "=" * 60)
print("STEP 3: Building rep profiles...")
print("=" * 60)

rep_profiles = []
rep_ids = list(set(r['rep_id'] for r in results))

for rep_id in sorted(rep_ids):
    rep_calls = [r for r in results if r['rep_id'] == rep_id]
    rep_real = [r for r in rep_calls if r.get('call_type') not in ['auto_attendant','voicemail']]
    rep_booked = [r for r in rep_real if r['call_outcome'] == 'demo_booked']
    
    if not rep_calls:
        continue

    tenure = rep_calls[0].get('rep_tenure', 'unknown')
    avg_score = sum(r.get('behavior_score', 0) for r in rep_real) / max(len(rep_real), 1)
    conversion_rate = len(rep_booked) / max(len(rep_real), 1)
    avg_duration = sum(r.get('call_duration_min', 0) for r in rep_calls) / max(len(rep_calls), 1)
    
    # Find best call
    best_call = max(rep_real, key=lambda x: x.get('behavior_score', 0)) if rep_real else None
    
    # Get coaching rec from Claude
    coaching_prompt = f"""You are a sales coach for Owner.com analyzing rep {rep_id}.

Rep stats:
- Tenure: {tenure}
- Total calls: {len(rep_calls)}
- Real conversations: {len(rep_real)}
- Demos booked: {len(rep_booked)}
- Conversion rate: {conversion_rate:.0%}
- Avg behavior score: {avg_score:.1f}/10
- Avg call duration: {avg_duration:.1f} min

Strengths observed: {[r.get('biggest_strength','') for r in rep_real[:5]]}
Gaps observed: {[r.get('biggest_gap','') for r in rep_real[:5]]}
Opening angles used: {pd.Series([r.get('opening_angle') for r in rep_real]).value_counts().to_dict()}
Discovery questions asked: {sum(1 for r in rep_real if r.get('asked_discovery_questions'))} of {len(rep_real)} calls

Return ONLY valid JSON:
{{
    "strength": "their single biggest strength in one sentence",
    "gap": "their single most impactful gap in one sentence", 
    "coaching_rec": "one specific, concrete, actionable thing to do differently on next call",
    "focus_metric": "talk_ratio" or "discovery_questions" or "objection_handling" or "personalization" or "closing",
    "priority": "high", "medium", or "low" (coaching urgency based on call volume and gap size)
}}"""

    coaching_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": coaching_prompt}]
    )
    
    raw = coaching_response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    coaching = json.loads(raw.strip())
    
    profile = {
        'rep_id': rep_id,
        'tenure': tenure,
        'total_calls': len(rep_calls),
        'real_conversations': len(rep_real),
        'demos_booked': len(rep_booked),
        'conversion_rate': round(conversion_rate, 3),
        'avg_behavior_score': round(avg_score, 1),
        'avg_duration_min': round(avg_duration, 1),
        'best_call_id': best_call['call_id'] if best_call else None,
        'best_call_score': best_call.get('behavior_score') if best_call else None,
        'strength': coaching.get('strength'),
        'gap': coaching.get('gap'),
        'coaching_rec': coaching.get('coaching_rec'),
        'focus_metric': coaching.get('focus_metric'),
        'priority': coaching.get('priority')
    }
    rep_profiles.append(profile)
    print(f"  ✓ {rep_id} | tenure: {tenure} | score: {avg_score:.1f} | conversion: {conversion_rate:.0%} | priority: {coaching.get('priority')}")
    time.sleep(0.3)

with open('data/rep_profiles.json', 'w') as f:
    json.dump(rep_profiles, f, indent=2)

print(f"\nDone. {len(rep_profiles)} rep profiles built.")

# ── SUMMARY ─────────────────────────────────────────────────

print("\n" + "=" * 60)
print("ALL DONE — FILES CREATED:")
print("=" * 60)
print("  call_analysis_raw.json  — per-call behavior scores and tags")
print("  playbook_patterns.json  — org-wide patterns and insights")
print("  rep_profiles.json       — per-rep scorecards and coaching recs")
print("\nNext step: load these into Streamlit and build the UI.")