"""Re-runs only step 2 of build_playbook.py (pattern detection).
Reads call_analysis_raw.json; writes playbook_patterns.json.
"""
import anthropic
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

with open('data/call_analysis_raw.json') as f:
    results = json.load(f)

real_calls = [r for r in results if r.get('call_type') not in ['auto_attendant', 'voicemail']]
booked = [r for r in real_calls if r['call_outcome'] == 'demo_booked']
not_booked = [r for r in real_calls if r['call_outcome'] == 'not_booked']

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

print("Running step 2: pattern detection...")
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": pattern_prompt}]
)

raw = response.content[0].text.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
playbook_patterns = json.loads(raw.strip())

with open('data/playbook_patterns.json', 'w') as f:
    json.dump(playbook_patterns, f, indent=2)

print("playbook_patterns.json updated.\n")
print("THREE THINGS WE DIDN'T KNOW:")
for i, insight in enumerate(playbook_patterns.get('three_things_we_didnt_know', []), 1):
    if isinstance(insight, dict):
        print(f"  {i}. {insight['title']} — {insight['detail']}")
    else:
        print(f"  {i}. {insight}")
