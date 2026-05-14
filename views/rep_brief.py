import concurrent.futures
import streamlit as st
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Constants ────────────────────────────────────────────────
RESEARCH_TIMEOUT_SECS = 25     # hard wall-clock limit for web research
RESEARCH_MAX_TOKENS   = 300   # keeps research cost ~$0.001 per call
BRIEF_MAX_TOKENS      = 1500  # full brief generation budget


# ── Helpers ──────────────────────────────────────────────────

def _empty_intel(freshness: str = "unavailable") -> dict:
    return {
        "on_doordash": None, "on_uber_eats": None, "has_own_ordering": None,
        "google_rating": None, "review_count": None, "num_locations": None,
        "recent_news": None, "customer_themes": None, "sales_angle_hint": None,
        "data_freshness": freshness,
    }


def research_restaurant(name: str, city: str, state: str = "", cuisine: str = "") -> dict:
    """
    Use Claude + web search to research a restaurant before brief generation.
    Hard timeout: 8 seconds. Max tokens: 300. Fails gracefully — brief still
    generates without intel if research times out or errors.
    """
    location = f"{city}, {state}" if state else city

    prompt = f"""Research this restaurant for a sales rep at Owner.com.

Restaurant: {name} — {location}{f' — {cuisine}' if cuisine else ''}

Find only what's verifiable. Return ONLY valid JSON, no markdown:
{{
    "on_doordash": true or false or null,
    "on_uber_eats": true or false or null,
    "has_own_ordering": true or false or null,
    "google_rating": number or null,
    "review_count": number or null,
    "num_locations": number or null,
    "recent_news": "one sentence or null",
    "customer_themes": "one sentence or null",
    "sales_angle_hint": "one sentence on best Owner.com angle for this restaurant",
    "data_freshness": "web_search"
}}"""

    def _call_api() -> str:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=RESEARCH_MAX_TOKENS,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if hasattr(block, "text")
        )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_api)
            try:
                full_text = future.result(timeout=RESEARCH_TIMEOUT_SECS)
            except concurrent.futures.TimeoutError:
                print(f"research_restaurant timed out after {RESEARCH_TIMEOUT_SECS}s")
                return _empty_intel("timeout")

        raw = full_text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])

    except Exception as e:
        print(f"research_restaurant error: {e}")

    return _empty_intel()


def _render_intel_card(intel: dict, restaurant_name: str):
    """Render live web research card. Silently skips if no data."""
    if not intel or intel.get("data_freshness") in ("unavailable", "timeout"):
        return

    lines = []
    if intel.get("on_doordash") is True:
        lines.append("📦 Currently on DoorDash — fee savings angle is live")
    elif intel.get("on_doordash") is False:
        lines.append("📦 Not on DoorDash — explore their current delivery setup")
    if intel.get("on_uber_eats") is True:
        lines.append("🚗 Active on Uber Eats — commission leak is real")
    if intel.get("has_own_ordering") is True:
        lines.append("🌐 Has own website ordering — pitch on reducing commission dependency")
    elif intel.get("has_own_ordering") is False:
        lines.append("🌐 No own ordering found — strong case for Owner.com's core product")
    if intel.get("google_rating"):
        lines.append(f"⭐ Google rating: {intel['google_rating']}")
    if intel.get("recent_news"):
        lines.append(f"📰 Recent: {intel['recent_news']}")
    if intel.get("customer_themes"):
        lines.append(f"💬 Customers say: {intel['customer_themes']}")
    if intel.get("sales_angle_hint"):
        lines.append(f"🎯 Suggested angle: {intel['sales_angle_hint']}")

    if not lines:
        return

    items_html = "".join(
        f'<div style="padding:6px 0;border-top:1px solid rgba(26,107,60,0.1);'
        f'font-size:13px;line-height:1.5;">{line}</div>'
        for line in lines
    )
    st.markdown(
        f'<div class="brief-section-card" style="border-color:rgba(26,107,60,0.3);'
        f'background:rgba(26,107,60,0.03);margin-bottom:16px;">'
        f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:var(--primary);margin-bottom:8px;">'
        f'🔍 Live web research — {restaurant_name}</div>'
        f'{items_html}</div>',
        unsafe_allow_html=True,
    )


# ── Main view ────────────────────────────────────────────────

def show_rep_brief(calls, patterns):
    restaurant       = st.session_state.get("selected_restaurant", {})
    cuisine          = restaurant.get("cuisine_type", "unknown")
    biz_type         = restaurant.get("business_type", "unknown")
    num_loc          = int(restaurant.get("num_locations", 1))
    loc_text         = "1 location" if num_loc == 1 else f"{num_loc} locations"
    prior_calls_data = st.session_state.get("prior_calls", [])
    has_prior        = bool(prior_calls_data)
    is_followup      = has_prior

    def _back():
        if st.button("← Back to search", key="back_to_search"):
            for key in ("is_new_restaurant", "is_followup", "prior_calls",
                        "similar_restaurants", "brief_data", "generate_brief",
                        "brief_generated", "restaurant_intel"):
                st.session_state.pop(key, None)
            st.session_state.view = "rep_search"
            st.rerun()

    def _header_card():
        st.markdown(
            f'<div class="brief-section-card" style="margin-bottom:24px;">'
            f'<div style="font-size:24px;font-weight:600;letter-spacing:-0.02em;">'
            f'{restaurant.get("name","")}</div>'
            f'<div style="font-size:14px;color:var(--muted-foreground);margin-top:4px;'
            f'display:flex;gap:12px;flex-wrap:wrap;">'
            f'<span>\U0001f4cd {restaurant.get("city","")}, {restaurant.get("state","")}</span>'
            f'<span>·</span>'
            f'<span>{cuisine} · {biz_type.replace("_"," ").title()}</span>'
            f'<span>·</span>'
            f'<span>{loc_text}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── BRIEF OUTPUT MODE ──────────────────────────────────
    if st.session_state.get("generate_brief") or st.session_state.get("brief_data"):

        if st.session_state.get("generate_brief"):
            # Web research — cached per restaurant, 8-second timeout
            intel = st.session_state.get("restaurant_intel")
            if intel is None:
                with st.spinner(
                    f"Researching {restaurant.get('name', 'restaurant')} online…"
                ):
                    intel = research_restaurant(
                        name=restaurant.get("name", ""),
                        city=restaurant.get("city", ""),
                        state=restaurant.get("state", ""),
                        cuisine=cuisine,
                    )
                st.session_state.restaurant_intel = intel

            brief = _generate_brief(
                restaurant, cuisine, biz_type, is_followup, calls, patterns,
                similar_restaurants=st.session_state.get("similar_restaurants", []),
                prior_calls=prior_calls_data,
                restaurant_intel=intel,
            )
            st.session_state.brief_data   = brief
            st.session_state.generate_brief = False

        else:
            brief = st.session_state.brief_data
            intel = st.session_state.get("restaurant_intel", {})

        _back()
        _header_card()
        _render_intel_card(intel, restaurant.get("name", ""))
        if brief:
            _render_brief(brief, is_followup)
        return

    # ── PREP MODE (before generation) ──────────────────────
    _back()
    _header_card()

    # New restaurant card
    if st.session_state.get("is_new_restaurant"):
        similar = st.session_state.get("similar_restaurants", [])
        names   = ", ".join(s.get("name", "") for s in similar if s.get("name"))
        if names:
            sim_n      = len(similar)
            sim_suffix = "s" if sim_n != 1 else ""
            st.markdown(
                f'<div class="brief-section-card" style="border-color:rgba(26,107,60,0.3);'
                f'background:rgba(26,107,60,0.04);margin-bottom:16px;">'
                f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:var(--primary);margin-bottom:8px;">✦ New restaurant</div>'
                f'<div style="font-size:14px;line-height:1.6;">Not in our dataset. '
                f'Brief grounded in <strong>{sim_n}</strong> similar restaurant{sim_suffix}: '
                f'<em>{names}</em>.</div></div>',
                unsafe_allow_html=True,
            )

    # Prior call history card
    if has_prior:
        n          = len(prior_calls_data)
        n_suffix   = "s" if n != 1 else ""
        prior_html = (
            f'<div class="brief-section-card" style="border-color:rgba(176,120,0,0.3);'
            f'background:rgba(176,120,0,0.04);margin-bottom:16px;">'
            f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:0.08em;color:var(--warning);margin-bottom:12px;">'
            f'↺ Prior context — {n} previous call{n_suffix}</div>'
        )
        for c in prior_calls_data[:3]:
            outcome       = "✅ Booked" if c.get("call_outcome") == "demo_booked" else "❌ Not booked"
            objections    = ", ".join(c.get("objections_raised", [])[:2]) or "None noted"
            summary       = c.get("summary", "")
            summary_short = summary[:130] + "…" if len(summary) > 130 else summary
            prior_html   += (
                f'<div style="border-top:1px solid rgba(176,120,0,0.2);padding-top:10px;'
                f'margin-top:10px;font-size:13px;line-height:1.6;">'
                f'<span style="font-weight:600;">{c.get("rep_id","")}</span> · {outcome}<br>'
                f'<span style="color:var(--muted-foreground);">Objections: {objections}</span><br>'
                f'<span style="color:var(--muted-foreground);">{summary_short}</span></div>'
            )
        prior_html += "</div>"
        st.markdown(prior_html, unsafe_allow_html=True)

    # Generate button
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button(
            "✦ Generate brief", type="primary",
            use_container_width=True, key="generate_btn"
        ):
            st.session_state.generate_brief = True
            st.rerun()


# ── Brief generation ─────────────────────────────────────────

def _generate_brief(
    restaurant, cuisine, biz_type, is_followup, calls, patterns,
    similar_restaurants=None, prior_calls=None, restaurant_intel=None,
):
    similar_calls  = [
        c for c in calls
        if c.get("cuisine_type") == cuisine or c.get("restaurant_type") == biz_type
    ]
    similar_booked = [c for c in similar_calls if c["call_outcome"] == "demo_booked"]

    playbook_context = (
        f"\nPlaybook data from {len(similar_calls)} similar calls ({cuisine} / {biz_type}):\n"
        f"- Segment conversion: {len(similar_booked)/max(len(similar_calls),1):.0%}\n"
        f"- Best angle: {patterns.get('opening_angle_analysis',{}).get('best_angle','')}\n"
        f"- Top behaviors: {[b['behavior'] for b in patterns.get('top_winning_behaviors',[])[:2]]}\n"
        f"- Top objections: {[o['objection'] for o in patterns.get('top_objections',[])[:3]]}\n"
    )

    new_rest_context = ""
    if similar_restaurants:
        names            = ", ".join(s.get("name","") for s in similar_restaurants if s.get("name"))
        new_rest_context = (
            f"\nNot in database — ground brief in similar {cuisine} "
            f"{biz_type.replace('_',' ')} restaurants: {names}.\n"
        )

    prior_calls_context = ""
    if prior_calls:
        lines = [f"Called {len(prior_calls)} time(s) before:"]
        for c in prior_calls[:3]:
            outcome    = "booked" if c.get("call_outcome") == "demo_booked" else "not booked"
            objections = ", ".join(c.get("objections_raised",[])[:2]) or "none"
            lines.append(
                f"- {c.get('rep_id')}: {outcome}, objections: {objections}, "
                f"summary: {c.get('summary','')[:100]}"
            )
        lines.append(
            "Include a followup_reframe: 'Last call tried X — this time try Y'."
        )
        prior_calls_context = "\n" + "\n".join(lines) + "\n"

    web_intel_context = ""
    if restaurant_intel and restaurant_intel.get("data_freshness") == "web_search":
        intel_lines = ["Live web research:"]
        if restaurant_intel.get("on_doordash") is True:
            intel_lines.append("- On DoorDash (paying ~20-30% commission)")
        if restaurant_intel.get("on_uber_eats") is True:
            intel_lines.append("- On Uber Eats (paying commission)")
        if restaurant_intel.get("has_own_ordering") is False:
            intel_lines.append("- No own ordering — strong Owner.com case")
        if restaurant_intel.get("has_own_ordering") is True:
            intel_lines.append("- Has own ordering — pitch commission reduction")
        if restaurant_intel.get("recent_news"):
            intel_lines.append(f"- Recent news: {restaurant_intel['recent_news']}")
        if restaurant_intel.get("customer_themes"):
            intel_lines.append(f"- Customers say: {restaurant_intel['customer_themes']}")
        if restaurant_intel.get("sales_angle_hint"):
            intel_lines.append(f"- Best angle: {restaurant_intel['sales_angle_hint']}")
        if len(intel_lines) > 1:
            web_intel_context = (
                "\n" + "\n".join(intel_lines) +
                "\nUse this to make the brief specific to their actual situation.\n"
            )

    followup_field = (
        ",'followup_reframe':'Last call tried X — this time try Y with a concrete different approach'"
        if is_followup or prior_calls else ""
    )

    prompt = f"""Sales rep at Owner.com preparing for a call. Owner.com helps independent restaurants cut 20-30% DoorDash/Uber Eats commission fees via native online ordering, loyalty, and automated marketing.

Restaurant: {restaurant.get('name')} | {restaurant.get('city')}, {restaurant.get('state')} | {cuisine} {biz_type} | {restaurant.get('num_locations',1)} location(s)
Call type: {"Follow-up" if is_followup else "First cold call"}
{new_rest_context}{prior_calls_context}{web_intel_context}{playbook_context}
Return ONLY valid JSON:
{{"one_thing":"1-2 sentences — use live intel if available","gatekeeper_opener":"exact words for staff","dm_opener":"exact words for owner — reference live intel if useful","angle_headline":"best angle based on playbook + live intel","angle_evidence":"one sentence citing data or intel","pain_points":["p1","p2","p3"],"discovery_questions":["q1","q2","q3"],"objections":[{{"objection":"text","response":"one-line"}},{{"objection":"text","response":"one-line"}},{{"objection":"text","response":"one-line"}}]{followup_field}}}"""

    import time

    with st.spinner("Generating brief from playbook data…"):
        response = None
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=BRIEF_MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                )
                break
            except anthropic.RateLimitError:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    st.error("Brief generation is temporarily rate limited. Please try again in 30 seconds.")
                    return None

        if response is None:
            return None

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())


# ── Brief rendering ──────────────────────────────────────────

def _render_brief(brief: dict, is_followup: bool):
    sp = '<div style="height:20px"></div>'

    # Hero card
    st.markdown(
        f'<div class="brief-one-thing">'
        f'<div class="brief-one-thing-eyebrow">✦ The one thing to remember</div>'
        f'<div class="brief-one-thing-text">{brief.get("one_thing","")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(sp, unsafe_allow_html=True)

    # Openers
    col_gk, col_dm = st.columns(2)
    with col_gk:
        st.markdown(
            f'<div class="opener-card">'
            f'<div class="opener-label"><span class="opener-icon">🛡</span>Gatekeeper opener</div>'
            f'<div class="opener-script">{brief.get("gatekeeper_opener","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_dm:
        st.markdown(
            f'<div class="opener-card">'
            f'<div class="opener-label"><span class="opener-icon">👤</span>Decision maker opener</div>'
            f'<div class="opener-script">{brief.get("dm_opener","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown(sp, unsafe_allow_html=True)

    # Follow-up reframe
    if is_followup and brief.get("followup_reframe"):
        st.markdown(
            f'<div class="angle-card" style="border-color:color-mix(in oklab,var(--warning) 40%,transparent);'
            f'background:color-mix(in oklab,var(--warning) 5%,transparent);">'
            f'<div class="brief-section-label" style="color:var(--warning-foreground);">Follow-up reframe</div>'
            f'<div style="font-size:15px;line-height:1.6;">{brief.get("followup_reframe","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(sp, unsafe_allow_html=True)

    # Best angle
    st.markdown(
        f'<div class="angle-card">'
        f'<div class="brief-section-label">Best angle</div>'
        f'<div class="angle-headline">{brief.get("angle_headline","")}</div>'
        f'<div class="angle-evidence">📊 {brief.get("angle_evidence","")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(sp, unsafe_allow_html=True)

    # Pain points + Discovery questions
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