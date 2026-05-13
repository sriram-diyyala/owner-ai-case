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
    div[data-testid="column"] div.stButton > button[kind="primary"] {
        border-top-left-radius: 0 !important;
        border-top-right-radius: 0 !important;
        border-top: none !important;
        margin-top: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top: -80px; position: relative; z-index: 10; padding: 0 4%;">', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(f"""
        <div style="background:white; border:1.5px solid #d4e4da; border-radius:16px; border-bottom-left-radius:0; border-bottom-right-radius:0; border-bottom:none; padding:32px; box-shadow:0 8px 32px rgba(10,15,13,0.12); min-height:280px; margin-bottom:-14px;">
            <div style="display:inline-flex; align-items:center; gap:6px; background:#e8f5ed; color:#1a6b3c; border-radius:999px; padding:4px 12px; font-size:12px; font-weight:500; margin-bottom:20px;">
                📊 I'm a manager
            </div>
            <div style="font-size:24px; font-weight:700; color:#0a0f0d; margin-bottom:12px; letter-spacing:-0.02em;">
                Show me what I don't know.
            </div>
            <div style="font-size:14px; color:#5a6e63; line-height:1.6; margin-bottom:28px;">
                Org-wide patterns, who to coach this week, the one gap that matters per rep — sorted by impact, not alphabet.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Analyze team calls →", key="home_manager", use_container_width=True, type="primary"):
            st.session_state.view = "manager"
            st.rerun()

    with col2:
        st.markdown(f"""
        <div style="background:white; border:1.5px solid #d4e4da; border-radius:16px; border-bottom-left-radius:0; border-bottom-right-radius:0; border-bottom:none; padding:32px; box-shadow:0 8px 32px rgba(10,15,13,0.12); min-height:280px; margin-bottom:-14px;">
            <div style="display:inline-flex; align-items:center; gap:6px; background:#e8f5ed; color:#1a6b3c; border-radius:999px; padding:4px 12px; font-size:12px; font-weight:500; margin-bottom:20px;">
                📞 I'm a rep
            </div>
            <div style="font-size:24px; font-weight:700; color:#0a0f0d; margin-bottom:12px; letter-spacing:-0.02em;">
                I have a call in 5. Get me ready.
            </div>
            <div style="font-size:14px; color:#5a6e63; line-height:1.6; margin-bottom:28px;">
                Search the restaurant. Generate a one-page brief grounded in {len(calls)} analyzed calls. Gatekeeper opener, decision maker opener, top objections — ready in seconds.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Prep for my next call →", key="home_rep", use_container_width=True, type="primary"):
            st.session_state.view = "rep_search"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

