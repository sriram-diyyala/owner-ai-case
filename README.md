# Owner Sales Intelligence

A sales intelligence system built for Owner.com's Applied AI Lead case study. Analyzes 150 real outbound sales call transcripts using Claude to surface coaching patterns for managers and generate evidence-grounded pre-call briefs for reps.

---

## What This Does

Owner's sales team makes 120+ dials per day to independent restaurant owners. Every call contains signal — who the rep reached, what they pitched, how the prospect responded, what objections came up, whether a demo was booked. That signal currently disappears after the call ends.

This system captures it, compresses it into a living playbook, and routes it back to two audiences:

- **Managers** get org-wide patterns invisible at the individual call level: which behaviors predict demos, which objections are handled best by which reps, where the whole team has a systemic gap
- **Reps** get a one-page pre-call brief for any restaurant — grounded in similar calls from the playbook, enriched with live web research, and adapted for whether this is a first contact or a follow-up

---

## Architecture

```
call_transcripts.csv (150 calls)
        ↓
build_playbook.py (runs once — Claude API, ~$1.50, ~15 min)
        ↓
data/ JSON files (pre-computed, version-controlled)
  ├── call_analysis_raw.json    — per-call behavior scores + 7-signal breakdown
  ├── playbook_patterns.json    — org-wide patterns, insights, GTM analysis
  └── rep_profiles.json         — per-rep scorecards + coaching recs
        ↓
app.py (Streamlit — reads JSON instantly, no API calls)
        ↓
Live Claude API call (only for rep brief generation + web research)
```

**Why pre-compute?** Running 150 calls through Claude on every page load would cost ~$1.50 and take 15 minutes. Pre-computing once makes the manager dashboard instant. At 10,000 calls, this becomes a nightly batch job — the architecture is the same.

---

## Setup

### Prerequisites
- Python 3.9+
- Anthropic API key (required for live brief generation and web research)

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/owner-ai-case.git
cd owner-ai-case

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here
```

### Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. The pre-computed JSON files are included — no pipeline run needed.

---

## Running the Analysis Pipeline

The JSON files in `data/` are already generated and committed. You only need to run `build_playbook.py` if you want to re-analyze the calls or add new data.

```bash
# Run the full pipeline (all 3 steps — ~15 min, ~$1.50)
python3 build_playbook.py

# Re-run only the pattern detection (Step 2 — ~30 sec, ~$0.10)
# Edit build_playbook.py: set SKIP_STEP_1 = True, SKIP_STEP_3 = True
python3 build_playbook.py

# Re-run only rep profiles (Step 3 — ~2 min, ~$0.20)
# Edit build_playbook.py: set SKIP_STEP_1 = True, SKIP_STEP_2 = True
python3 build_playbook.py
```

---

## Behavior Score Methodology

Each call is scored on 7 independently measured signals, then combined into a composite 1–10 score:

| Signal | Weight | How it's measured |
|---|---|---|
| Reached decision maker | 15% | Binary — did rep get the owner on the line? |
| Asked discovery questions | 20% | Binary + quality bonus (+1.5pts per question, max 10) |
| Objection handling | 20% | strong=10, moderate=6, weak=2, none=5 |
| Clear next step | 15% | Binary — was there an explicit ask for a next action? |
| Talk ratio | 10% | Optimal range 40–55% rep talking; outside 25–75% = score 1 |
| Personalization | 10% | high=10, medium=6, low=2 |
| Rapport building | 10% | strong=10, moderate=6, weak=2 |

**Why these weights?** They reflect domain knowledge about what drives demo booking. The right next step is running a logistic regression on 1,000+ calls to calibrate them empirically — the methodology is documented so that work is already scoped.

**Why compute in Python, not ask Claude for a score?** A single holistic score from Claude is a black box. Computing it from 7 independently scored signals makes the score transparent, debuggable, and adjustable. It also means a manager can see *which* signal is weakest for a rep — not just that their score is low.

---

## File Structure

```
owner-ai-case/
├── app.py                    # Streamlit router — view switching, session state
├── data.py                   # Data loading, metrics, banner logic, objection matching
├── styles.py                 # CSS injection, nav header component
├── build_playbook.py         # One-time pipeline: transcripts → JSON playbook
├── requirements.txt
├── .env.example
├── data/
│   ├── call_transcripts.csv  # 150 real Owner.com sales calls
│   ├── restaurants.csv       # 138 restaurant records
│   ├── call_analysis_raw.json
│   ├── playbook_patterns.json
│   └── rep_profiles.json
└── views/
    ├── home.py               # Landing page — role cards
    ├── manager.py            # Team dashboard + rep deep-dive
    ├── rep_detail.py         # Individual rep scorecard
    ├── rep_search.py         # Restaurant search + category browsing
    └── rep_brief.py          # Brief generation + web research
```

---

## Key Design Decisions

**Streamlit over React** — The goal was to ship real intelligence on real data, not a polished mock. Streamlit let the build focus on the pipeline, the scoring methodology, and the insight quality rather than frontend infrastructure.

**Pre-compute vs live API** — Manager dashboard reads pre-computed JSON (instant). Rep brief calls Claude live (real-time feel, grounded in the playbook). This split mirrors how a production system would work: nightly batch for analytics, on-demand for personalized outputs.

**Web research for briefs** — Before generating each brief, the system calls Claude with web search enabled to find whether the restaurant is on DoorDash/Uber Eats, has own ordering, and any recent news. This makes even first-contact briefs hyper-specific to the restaurant's actual situation. Timeout: 25 seconds. Fails gracefully — brief still generates without intel.

**Statistical guardrails on patterns** — The pattern detection prompt requires 15+ percentage point delta AND 10+ calls in the smaller group before surfacing a finding. Findings that contradict sales methodology require 20+ point delta and explicit acknowledgment of the contradiction. This prevents Claude from surfacing noise as signal.

---

## Environment Variables

```
ANTHROPIC_API_KEY=your_key_here
```

Web search is used for restaurant research in the rep brief. Requires an Anthropic API key with web search access enabled.
