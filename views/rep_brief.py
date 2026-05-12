import streamlit as st
import anthropic
import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def show_rep_brief(calls, patterns):
    restaurant = st.session_state.get("selected_restaurant", {})
    cuisine = restaurant.get("cuisine_type", "unknown")
    biz_type = restaurant.get("business_type", "unknown")
    num_loc = int(restaurant.get("num_locations", 1))
    loc_text = "1 location" if num_loc == 1 else f"{num_loc} locations"

    prior_calls_data = st.session_state.get("prior_calls", [])
    has_prior = bool(prior_calls_data)
    is_followup = has_prior  # Fix 1: auto-detect, no radio

    def _back():
        if st.button("← Back to search", key="back_to_search"):
            for key in ("is_new_restaurant", "is_followup", "prior_calls",
                        "similar_restaurants", "brief_data", "generate_brief", "brief_generated"):
                st.session_state.pop(key, None)
            st.session_state.view = "rep_search"
            st.rerun()

    def _header_card():
        st.markdown(
            f'<div class="brief-section-card" style="margin-bottom:24px;">'
            f'<div style="font-size:24px; font-weight:600; letter-spacing:-0.02em;">{restaurant.get("name","")}</div>'
            f'<div style="font-size:14px; color:var(--muted-foreground); margin-top:4px; display:flex; gap:12px; flex-wrap:wrap;">'
            f'<span>\U0001f4cd {restaurant.get("city","")}, {restaurant.get("state","")}</span>'
            f'<span>·</span>'
            f'<span>{cuisine} · {biz_type.replace("_"," ").title()}</span>'
            f'<span>·</span>'
            f'<span>{loc_text}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── BRIEF OUTPUT MODE ──────────────────────────────────────────────────────
    if st.session_state.get("generate_brief") or st.session_state.get("brief_data"):
        if st.session_state.get("generate_brief"):
            brief = _generate_brief(
                restaurant, cuisine, biz_type, is_followup, "", calls, patterns,
                similar_restaurants=st.session_state.get("similar_restaurants", []),
                prior_calls=prior_calls_data,
            )
            st.session_state.brief_data = brief
            st.session_state.generate_brief = False  # Fix 3: don't re-trigger on refresh
        else:
            brief = st.session_state.brief_data

        _back()
        _header_card()
        if brief:
            _render_brief(brief, calls, patterns, cuisine, biz_type, is_followup)
        return

    # ── PREP MODE ──────────────────────────────────────────────────────────────
    _back()
    _header_card()

    # New restaurant context card
    if st.session_state.get("is_new_restaurant"):
        similar = st.session_state.get("similar_restaurants", [])
        names = ", ".join(s.get("name", "") for s in similar if s.get("name"))
        if names:
            sim_n = len(similar)
            sim_suffix = "s" if sim_n != 1 else ""
            st.markdown(
                f'<div class="brief-section-card" style="border-color:rgba(26,107,60,0.3);background:rgba(26,107,60,0.04);margin-bottom:16px;">'
                f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:var(--primary);margin-bottom:8px;">✦ New restaurant</div>'
                f'<div style="font-size:14px;line-height:1.6;">This restaurant is not in our dataset. Brief is grounded in <strong>{sim_n}</strong> similar restaurant{sim_suffix} from our data: <em>{names}</em>.</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Prior call history context card
    if has_prior:
        n = len(prior_calls_data)
        n_suffix = "s" if n != 1 else ""
        prior_html = (
            f'<div class="brief-section-card" style="border-color:rgba(176,120,0,0.3);background:rgba(176,120,0,0.04);margin-bottom:16px;">'
            f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:var(--warning);margin-bottom:12px;">↺ Prior context — {n} previous call{n_suffix}</div>'
        )
        for c in prior_calls_data[:3]:
            outcome = "✅ Booked" if c.get("call_outcome") == "demo_booked" else "❌ Not booked"
            objections = ", ".join(c.get("objections_raised", [])[:2]) or "None noted"
            summary = c.get("summary", "")
            summary_short = summary[:130] + "…" if len(summary) > 130 else summary
            prior_html += (
                f'<div style="border-top:1px solid rgba(176,120,0,0.2);padding-top:10px;margin-top:10px;font-size:13px;line-height:1.6;">'
                f'<span style="font-weight:600;">{c.get("rep_id","")}</span> · {outcome}<br>'
                f'<span style="color:var(--muted-foreground);">Objections: {objections}</span><br>'
                f'<span style="color:var(--muted-foreground);">{summary_short}</span>'
                f'</div>'
            )
        prior_html += "</div>"
        st.markdown(prior_html, unsafe_allow_html=True)

    # Fix 1 + Fix 3: no radio, no text area — just the generate button
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("✦ Generate brief", type="primary", use_container_width=True, key="generate_btn"):
            st.session_state.generate_brief = True
            st.rerun()


def _generate_brief(
    restaurant, cuisine, biz_type, is_followup, prior_notes, calls, patterns,
    similar_restaurants=None, prior_calls=None
):
    similar_calls = [
        c for c in calls
        if c.get("cuisine_type") == cuisine or c.get("restaurant_type") == biz_type
    ]
    similar_booked = [c for c in similar_calls if c["call_outcome"] == "demo_booked"]

    playbook_context = f"""
Playbook data from {len(similar_calls)} similar calls ({cuisine} / {biz_type}):
- Conversion rate for this segment: {len(similar_booked)/max(len(similar_calls),1):.0%}
- Best opening angle: {patterns.get('opening_angle_analysis', {}).get('best_angle', '')}
- Top winning behaviors: {[b['behavior'] for b in patterns.get('top_winning_behaviors', [])[:3]]}
- Top objections: {[o['objection'] for o in patterns.get('top_objections', [])[:3]]}
"""

    new_rest_context = ""
    if similar_restaurants:
        names = ", ".join(s.get("name", "") for s in similar_restaurants if s.get("name"))
        new_rest_context = (
            f"\nThis restaurant is NOT in our database. Ground the brief in calls to similar "
            f"{cuisine} {biz_type.replace('_', ' ')} restaurants in our dataset: {names}.\n"
        )

    prior_calls_context = ""
    if prior_calls:
        lines = [f"This restaurant has been called {len(prior_calls)} time(s) before:"]
        for c in prior_calls[:3]:
            outcome = "booked" if c.get("call_outcome") == "demo_booked" else "not booked"
            objections = ", ".join(c.get("objections_raised", [])[:2]) or "none"
            lines.append(
                f"- {c.get('rep_id')}: {outcome}, objections raised: {objections}, "
                f"summary: {c.get('summary', '')[:100]}"
            )
        lines.append(
            "IMPORTANT: The brief must include a 'followup_reframe' field that explicitly says "
            "'Last call tried X — this time try Y' with a concrete different angle or approach."
        )
        prior_calls_context = "\n" + "\n".join(lines) + "\n"

    online_val = "Yes" if restaurant.get("website_url") else "No"
    followup_field = (
        ",'followup_reframe': 'Last call tried X — this time try Y with a concrete different approach'"
        if is_followup or prior_calls else ""
    )

    prompt = f"""You are helping a sales rep at Owner.com prepare for a call. Owner.com helps independent restaurants compete with large chains by giving them their own website, native online ordering, loyalty programs, and automated marketing — cutting 20-30% DoorDash/Uber Eats commission fees by bringing ordering in-house.

Restaurant:
- Name: {restaurant.get('name')}
- Location: {restaurant.get('city')}, {restaurant.get('state')}
- Cuisine: {cuisine}
- Type: {biz_type}
- Locations: {restaurant.get('num_locations', 1)}
- Website: {restaurant.get('website_url', 'none')}

Call type: {"Follow-up" if is_followup else "First cold call"}
{new_rest_context}{prior_calls_context}
{playbook_context}

Return ONLY valid JSON, no markdown:
{{
    "one_thing": "the single most important thing to remember — 1-2 sentences max",
    "gatekeeper_opener": "exact words to say if staff picks up — natural and specific to this restaurant",
    "dm_opener": "exact words to say if owner/decision maker picks up — specific to their situation",
    "angle_headline": "the single best opening angle for this restaurant",
    "angle_evidence": "one sentence citing playbook data supporting this angle",
    "pain_points": ["pain 1", "pain 2", "pain 3"],
    "discovery_questions": ["question 1", "question 2", "question 3"],
    "objections": [
        {{"objection": "objection text", "response": "one-line response"}},
        {{"objection": "objection text", "response": "one-line response"}},
        {{"objection": "objection text", "response": "one-line response"}}
    ]
    {followup_field}
}}"""

    with st.spinner("Generating brief from playbook data…"):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())


def _render_brief(brief, calls, patterns, cuisine, biz_type, is_followup):
    sp = '<div style="height:20px"></div>'

    # One thing — hero card
    st.markdown(f"""
    <div class="brief-one-thing">
        <div class="brief-one-thing-eyebrow">✦ The one thing to remember</div>
        <div class="brief-one-thing-text">{brief.get('one_thing','')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(sp, unsafe_allow_html=True)

    # Openers side by side
    col_gk, col_dm = st.columns(2)
    with col_gk:
        st.markdown(f"""
        <div class="opener-card">
            <div class="opener-label">
                <span class="opener-icon">🛡</span>
                Gatekeeper opener
            </div>
            <div class="opener-script">{brief.get('gatekeeper_opener','')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_dm:
        st.markdown(f"""
        <div class="opener-card">
            <div class="opener-label">
                <span class="opener-icon">👤</span>
                Decision maker opener
            </div>
            <div class="opener-script">{brief.get('dm_opener','')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(sp, unsafe_allow_html=True)

    if is_followup and brief.get("followup_reframe"):
        st.markdown(f"""
        <div class="angle-card" style="border-color: color-mix(in oklab, var(--warning) 40%, transparent); background: color-mix(in oklab, var(--warning) 5%, transparent);">
            <div class="brief-section-label" style="color: var(--warning-foreground);">Follow-up reframe</div>
            <div style="font-size:15px; line-height:1.6;">{brief.get('followup_reframe','')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(sp, unsafe_allow_html=True)

    # Angle
    st.markdown(f"""
    <div class="angle-card">
        <div class="brief-section-label">Best angle</div>
        <div class="angle-headline">{brief.get('angle_headline','')}</div>
        <div class="angle-evidence">📊 {brief.get('angle_evidence','')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(sp, unsafe_allow_html=True)

    # Pain points + Discovery questions side by side
    col_pain, col_disc = st.columns(2)
    with col_pain:
        pain_html = '<div class="brief-section-card"><div class="brief-section-label">Pain points</div>'
        for p in brief.get("pain_points", []):
            pain_html += f'<div class="pain-item"><div class="pain-dot"></div><div>{p}</div></div>'
        pain_html += "</div>"
        st.markdown(pain_html, unsafe_allow_html=True)

    with col_disc:
        disc_html = '<div class="brief-section-card"><div class="brief-section-label">Discovery questions</div>'
        for i, q in enumerate(brief.get("discovery_questions", []), 1):
            disc_html += f'<div class="discovery-item"><div class="discovery-num">{i}.</div><div>{q}</div></div>'
        disc_html += "</div>"
        st.markdown(disc_html, unsafe_allow_html=True)

    st.markdown(sp, unsafe_allow_html=True)

    # Objections
    obj_html = '<div class="brief-section-card"><div class="brief-section-label">Likely objections + responses</div><div>'
    for obj in brief.get("objections", []):
        obj_html += (
            f'<div class="objection-row">'
            f'<div class="objection-q">"{obj.get("objection","")}"</div>'
            f'<div class="objection-a">{obj.get("response","")}</div>'
            f'</div>'
        )
    obj_html += "</div></div>"
    st.markdown(obj_html, unsafe_allow_html=True)
