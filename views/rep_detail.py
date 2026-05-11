import streamlit as st
import pandas as pd


def show_rep_detail(calls, reps):
    rep_id = st.session_state.get("selected_rep")
    rep = next((r for r in reps if r["rep_id"] == rep_id), None)

    if not rep:
        st.error("Rep not found.")
        return

    rep_calls = [c for c in calls if c["rep_id"] == rep_id]
    rep_real = [c for c in rep_calls if c.get("call_type") not in ["auto_attendant", "voicemail"]]

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    if st.button("← Back to dashboard", key="back_to_manager"):
        st.session_state.view = "manager"
        st.rerun()

    # Page header
    st.markdown(f"""
    <div class="page-header">
        <div class="page-eyebrow">Rep deep-dive</div>
        <div class="page-title">{rep['rep_id']}</div>
        <div class="page-sub">
            {rep.get('tenure','').title()} tenure · {rep.get('total_calls',0)} total calls ·
            best call <span style="font-family: 'JetBrains Mono', monospace;">{rep.get('best_call_id','')}</span>
            ({rep.get('best_call_score','')}/10)
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    trend = rep.get("avg_behavior_score", 0) - 5.5  # relative to baseline
    trend_sign = "+" if trend >= 0 else ""
    trend_tone = "success" if trend >= 0 else "warning"

    st.markdown(f"""
    <div class="metric-grid-4">
        <div class="metric-card">
            <div class="metric-label">Behavior score</div>
            <div class="metric-value">{rep.get('avg_behavior_score','')}</div>
            <div class="metric-delta {trend_tone}">{trend_sign}{trend:.1f} vs baseline</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Demos booked</div>
            <div class="metric-value">{rep.get('demos_booked',0)}</div>
            <div class="metric-sub">{rep.get('total_calls',0)} total calls</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Conversion rate</div>
            <div class="metric-value">{rep.get('conversion_rate',0):.0%}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Best call score</div>
            <div class="metric-value">{rep.get('best_call_score','')}</div>
            <div class="metric-sub" style="font-family:'JetBrains Mono',monospace;">{rep.get('best_call_id','')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Coach cards
    st.markdown(f"""
    <div class="coach-grid">
        <div class="coach-card success">
            <div class="coach-card-header">
                <span class="coach-card-icon success">↑</span>
                <span class="coach-card-label">Strength</span>
            </div>
            <div class="coach-card-body">{rep.get('strength','')}</div>
        </div>
        <div class="coach-card warning">
            <div class="coach-card-header">
                <span class="coach-card-icon warning">⊙</span>
                <span class="coach-card-label">Single biggest gap</span>
            </div>
            <div class="coach-card-body">{rep.get('gap','')}</div>
        </div>
        <div class="coach-card primary">
            <div class="coach-card-header">
                <span class="coach-card-icon primary">✦</span>
                <span class="coach-card-label">Coaching recommendation</span>
            </div>
            <div class="coach-card-body">{rep.get('coaching_rec','')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Call history
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Call history</div>
    </div>
    """, unsafe_allow_html=True)

    filter_col, _ = st.columns([2, 5])
    with filter_col:
        outcome_filter = st.radio(
            "Filter",
            ["All", "Booked", "Not booked"],
            horizontal=True,
            label_visibility="collapsed",
        )

    filtered = rep_real
    if outcome_filter == "Booked":
        filtered = [c for c in rep_real if c["call_outcome"] == "demo_booked"]
    elif outcome_filter == "Not booked":
        filtered = [c for c in rep_real if c["call_outcome"] == "not_booked"]

    if filtered:
        rows = []
        for c in filtered:
            outcome_label = "✅ Booked" if c["call_outcome"] == "demo_booked" else "❌ Not booked"
            rows.append({
                "Call": c["call_id"],
                "Restaurant": c.get("restaurant_type", "").replace("_", " ").title(),
                "Angle": c.get("opening_angle", "").replace("_", " "),
                "Score": f"{c.get('behavior_score','')}/10",
                "Talk %": f"{c.get('talk_ratio',0)}%",
                "Discovery Qs": "✓" if c.get("asked_discovery_questions") else "✗",
                "Next step": "✓" if c.get("clear_next_step") else "✗",
                "Outcome": outcome_label,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No calls match this filter.")

    st.markdown("</div>", unsafe_allow_html=True)