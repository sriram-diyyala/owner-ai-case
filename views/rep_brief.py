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

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    if st.button("← Back to search", key="back_to_search"):
        st.session_state.view = "rep_search"
        st.rerun()

    # Restaurant header card
    cuisine = restaurant.get("cuisine_type", "unknown")
    biz_type = restaurant.get("business_type", "unknown")
    has_website = pd.notna(restaurant.get("website_url", "")) and str(restaurant.get("website_url", "")).strip()
    num_loc = int(restaurant.get("num_locations", 1))

    st.markdown(f"""
    <div class="brief-section-card" style="margin-bottom: 24px;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:16px; margin-bottom:16px;">
            <div>
                <div style="font-size:24px; font-weight:600; letter-spacing:-0.02em;">{restaurant.get('name','')}</div>
                <div style="font-size:14px; color:var(--muted-foreground); margin-top:4px; display:flex; gap:12px; flex-wrap:wrap;">
                    <span>📍 {restaurant.get('city','')}, {restaurant.get('state','')}</span>
                    <span>·</span>
                    <span>{cuisine} · {biz_type.replace('_',' ').title()}</span>
                    <span>·</span>
                    <span>{num_loc} location{'s' if num_loc != 1 else ''}</span>
                </div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
    """, unsafe_allow_html=True)

    # Call type toggle + generate button
    col_type, col_btn = st.columns([3, 1])
    with col_type:
        call_type = st.radio(
            "Call type",
            ["New call — first contact", "Follow-up — prior history"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with col_btn:
        generate = st.button("✦ Generate brief", type="primary", use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    is_followup = "Follow-up" in call_type
    prior_notes = ""
    if is_followup:
        prior_notes = st.text_area(
            "Notes from last call",
            placeholder="e.g. Owner busy, asked to call back Thursday. Open to recovering DoorDash fees but said competitor rep already pitched.",
            height=80,
            label_visibility="collapsed",
        )

    if generate or st.session_state.get("brief_generated"):
        if generate:
            st.session_state.brief_generated = True
            st.session_state.brief_data = None  # force regeneration

        if st.session_state.get("brief_data") is None or generate:
            brief = _generate_brief(restaurant, cuisine, biz_type, is_followup, prior_notes, calls, patterns)
            st.session_state.brief_data = brief
        else:
            brief = st.session_state.brief_data

        if brief:
            _render_brief(brief, calls, patterns, cuisine, biz_type, is_followup)

    st.markdown("</div>", unsafe_allow_html=True)


def _generate_brief(restaurant, cuisine, biz_type, is_followup, prior_notes, calls, patterns):
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

    prompt = f"""You are helping a sales rep at Owner.com prepare for a call. Owner.com helps independent restaurants compete with large chains by giving them their own website, native online ordering, loyalty programs, and automated marketing — cutting 20-30% DoorDash/Uber Eats commission fees by bringing ordering in-house.

Restaurant:
- Name: {restaurant.get('name')}
- Location: {restaurant.get('city')}, {restaurant.get('state')}
- Cuisine: {cuisine}
- Type: {biz_type}
- Locations: {restaurant.get('num_locations', 1)}
- Website: {restaurant.get('website_url', 'none')}

Call type: {"Follow-up" if is_followup else "First cold call"}
{"Prior call notes: " + prior_notes if prior_notes else ""}

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
    ],
    "snapshot": {{
        "name": "{restaurant.get('name')}",
        "location": "{restaurant.get('city')}, {restaurant.get('state')}",
        "cuisine": "{cuisine}",
        "type": "{biz_type}",
        "online": "{'Yes' if restaurant.get('website_url') else 'No'}"
    }}
    {",'followup_reframe': 'how to reframe based on prior notes — specific and actionable'" if is_followup else ""}
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
    similar_calls = [
        c for c in calls
        if c.get("cuisine_type") == cuisine or c.get("restaurant_type") == biz_type
    ]

    # One thing — hero card
    st.markdown(f"""
    <div class="brief-one-thing">
        <div class="brief-one-thing-eyebrow">✦ The one thing to remember</div>
        <div class="brief-one-thing-text">{brief.get('one_thing','')}</div>
    </div>
    """, unsafe_allow_html=True)

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

    if is_followup and brief.get("followup_reframe"):
        st.markdown(f"""
        <div class="angle-card" style="margin-top:16px; border-color: color-mix(in oklab, var(--warning) 40%, transparent); background: color-mix(in oklab, var(--warning) 5%, transparent);">
            <div class="brief-section-label" style="color: var(--warning-foreground);">Follow-up reframe</div>
            <div style="font-size:15px; line-height:1.6;">{brief.get('followup_reframe','')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Angle
    st.markdown(f"""
    <div class="angle-card">
        <div class="brief-section-label">Best angle</div>
        <div class="angle-headline">{brief.get('angle_headline','')}</div>
        <div class="angle-evidence">📊 {brief.get('angle_evidence','')}</div>
    </div>
    """, unsafe_allow_html=True)

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

    # Objections
    obj_html = '<div class="brief-section-card"><div class="brief-section-label">Likely objections + responses</div><div>'
    for obj in brief.get("objections", []):
        obj_html += f"""
        <div class="objection-row">
            <div class="objection-q">"{obj.get('objection','')}"</div>
            <div class="objection-a">{obj.get('response','')}</div>
        </div>"""
    obj_html += "</div></div>"
    st.markdown(obj_html, unsafe_allow_html=True)

    # Snapshot footer
    snap = brief.get("snapshot", {})
    st.markdown(f"""
    <div class="snapshot-footer">
        <span>📞</span>
        <div>
            <div style="font-weight:500; color:var(--foreground); margin-bottom:4px;">Snapshot</div>
            {snap.get('name','')} · {snap.get('location','')} · {snap.get('cuisine','')} · {snap.get('type','').replace('_',' ').title()} · Online ordering: {snap.get('online','')}
            <br>Brief grounded in {len(similar_calls)} similar calls from Owner's playbook.
        </div>
    </div>
    """, unsafe_allow_html=True)