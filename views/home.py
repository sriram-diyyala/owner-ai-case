import streamlit as st
from data import get_team_metrics


def show_home(calls, patterns, reps, restaurants):
    m = get_team_metrics(calls, reps)

    # Hero
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f3d20 0%, #1a6b3c 50%, #22883f 100%); color: white;">
        <div style="max-width: 1400px; margin: 0 auto; padding: 64px 40px 120px 40px;">
            <div style="font-size:12px; font-weight:500; text-transform:uppercase; letter-spacing:0.12em; opacity:0.75; margin-bottom:16px;">
                ✦ Owner AI
            </div>
            <div style="font-size:56px; font-weight:700; line-height:1.05; letter-spacing:-0.03em; max-width:750px; margin-bottom:20px;">
                Every sales call,<br>feeding every next call.
            </div>
            <div style="font-size:18px; opacity:0.85; max-width:560px; line-height:1.6;">
                Owner AI extracts the institutional knowledge buried in your team's transcripts
                and routes it back to reps and managers before it matters — the right brief
                before the dial, the right coaching before the week.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS for the card wrappers — applied to Streamlit's column containers.
    # The marker div lives inside a stMarkdownContainer; the columns block is its
    # adjacent sibling in the DOM, so we use :has() to bridge that boundary.
    st.markdown("""
    <style>
    /* Constrain and overlap the hero — targets the stHorizontalBlock after our marker */
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] {
        max-width: 1020px !important;
        margin: -72px auto 0 auto !important;
        gap: 24px !important;
        position: relative !important;
        z-index: 10 !important;
    }

    /* White elevated card on each column */
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        background: white !important;
        border: 1px solid #d4e4da !important;
        border-radius: 14px !important;
        padding: 32px !important;
        box-shadow: 0 10px 30px -12px rgba(26,107,60,0.25) !important;
    }
    </style>
    <div class="home-cards-marker"></div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown(f"""
        <div style="display:inline-flex; align-items:center; gap:6px; background:#e8f5ed; color:#1a6b3c; border-radius:999px; padding:4px 12px; font-size:12px; font-weight:500; margin-bottom:20px;">
            📊 I'm a manager
        </div>
        <div style="font-size:24px; font-weight:700; color:#0a0f0d; margin-bottom:12px; letter-spacing:-0.02em;">
            Show me what I don't know.
        </div>
        <div style="font-size:14px; color:#5a6e63; line-height:1.6; margin-bottom:24px;">
            Org-wide patterns, who to coach this week, the one gap that matters per rep — sorted by impact, not alphabet.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open team dashboard →", type="primary", use_container_width=True, key="home_manager"):
            st.session_state.view = "manager"
            st.rerun()

    with col2:
        st.markdown(f"""
        <div style="display:inline-flex; align-items:center; gap:6px; background:#e8f5ed; color:#1a6b3c; border-radius:999px; padding:4px 12px; font-size:12px; font-weight:500; margin-bottom:20px;">
            📞 I'm a rep
        </div>
        <div style="font-size:24px; font-weight:700; color:#0a0f0d; margin-bottom:12px; letter-spacing:-0.02em;">
            I have a call in 5. Get me ready.
        </div>
        <div style="font-size:14px; color:#5a6e63; line-height:1.6; margin-bottom:24px;">
            Search the restaurant. Generate a one-page brief grounded in {len(calls)} analyzed calls. Gatekeeper opener, decision maker opener, top objections — ready in seconds.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate a pre-call brief →", type="primary", use_container_width=True, key="home_rep"):
            st.session_state.view = "rep_search"
            st.rerun()

    # Stats bar
    st.markdown(f"""
    <div style="max-width:1100px; margin: 48px auto 64px auto; padding: 0 40px;">
        <div style="background: white; border: 1px solid #d4e4da; border-radius: 12px; padding: 32px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px;">
            <div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:32px; font-weight:600; letter-spacing:-0.02em; color:#0a0f0d;">{m['calls_analyzed']:,}</div>
                <div style="font-size:14px; color:#5a6e63; margin-top:4px;">Calls analyzed</div>
            </div>
            <div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:32px; font-weight:600; letter-spacing:-0.02em; color:#0a0f0d;">{m['conversion_rate']}%</div>
                <div style="font-size:14px; color:#5a6e63; margin-top:4px;">Demo conversion rate</div>
            </div>
            <div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:32px; font-weight:600; letter-spacing:-0.02em; color:#0a0f0d;">{m['avg_behavior_score']} / 10</div>
                <div style="font-size:14px; color:#5a6e63; margin-top:4px;">Team avg behavior score</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)