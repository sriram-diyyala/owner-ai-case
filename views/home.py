import streamlit as st
from data import get_team_metrics


def show_home(calls, patterns, reps, restaurants):
    m = get_team_metrics(calls, reps)

    # Hero
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f3d20 0%, #1a6b3c 50%, #22883f 100%); color: white; width: 100vw; box-sizing: border-box; padding: 64px 10% 120px 10%; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%); margin-top: -2rem;">            
        <div style="font-size:12px; font-weight:500; text-transform:uppercase; letter-spacing:0.12em; opacity:0.75; margin-bottom:16px;">
            ✦ OWNER SALES INTELLIGENCE
        </div>
        <div style="font-size:56px; font-weight:700; line-height:1.05; letter-spacing:-0.03em; max-width:750px; margin-bottom:20px;">
            Know what works.<br>Prep what's next.
        </div>
        <div style="font-size:18px; opacity:0.85; max-width:560px; line-height:1.6;">
            Owner Sales Intelligence analyzes every sales call to surface what's working
            across the team — and grounds every pre-call brief in real evidence from
            similar calls.
        </div>
        <div style="margin-top:28px; font-size:13px; font-weight:500; opacity:0.7; letter-spacing:0.01em;">
            Currently analyzing {m['calls_analyzed']} calls · {len(restaurants)} restaurants · {len(reps)} reps
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* Position the row — overlap the hero from below */
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] {
        max-width: 1100px !important;
        margin: -72px auto 0 auto !important;
        gap: 24px !important;
        padding: 0 5% !important;
        position: relative !important;
        z-index: 10 !important;
        align-items: stretch !important;
    }

    /* Both columns — white elevated cards, equal height */
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        background: white !important;
        border: 1px solid #d4e4da !important;
        border-radius: 14px !important;
        padding: 32px !important;
        box-shadow: 0 20px 50px -12px rgba(10,15,13,0.25), 0 4px 12px rgba(10,15,13,0.08) !important;        
        display: flex !important;
        flex-direction: column !important;
        box-sizing: border-box !important;
    }

    /* Inner block fills column so button sits at natural bottom */
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] > [data-testid="column"] > div {
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }


     /* Filled CTA buttons */
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] div.stButton > button {
    background: #1a6b3c !important;
    border: 1px solid #1a6b3c !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    box-shadow: none !important;
    width: 100% !important;
    border-radius: 8px !important;
    }
    [data-testid="stMarkdownContainer"]:has(.home-cards-marker) + [data-testid="stHorizontalBlock"] div.stButton > button:hover {
        background: #22883f !important;
        border-color: #22883f !important;
    }           

    </style>
    <div class="home-cards-marker"></div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("""
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
        if st.button("Analyze team calls →", key="home_manager"):
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
        if st.button("Prep for my next call →", key="home_rep"):
            st.session_state.view = "rep_search"
            st.rerun()

