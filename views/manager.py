import streamlit as st
import pandas as pd
from data import get_team_metrics, get_objection_stats, get_action_banner


def show_manager(calls, patterns, reps):
    m = get_team_metrics(calls, reps)
    banner = get_action_banner(calls, reps, patterns)
    objections = get_objection_stats(calls, patterns)

    st.markdown("""
    <div class="page-wrap">
        <div class="page-header">
            <div class="page-eyebrow">Manager view</div>
            <div class="page-title">Team intelligence</div>
            <div class="page-sub">Pre-computed nightly from {count} analyzed calls.</div>
        </div>
    """.replace("{count}", f"{m['calls_analyzed']:,}"), unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Team dashboard", "Rep deep-dive"])

    with tab1:
        _team_dashboard(calls, patterns, reps, m, banner, objections)

    with tab2:
        _rep_grid(reps)

    st.markdown("</div>", unsafe_allow_html=True)


def _team_dashboard(calls, patterns, reps, m, banner, objections):
    # Action banner
    if banner:
        st.markdown(f"""
        <div class="action-banner">
            <div class="banner-eyebrow">⚡ Highest-impact action this week</div>
            <div class="banner-headline">{banner['headline']}</div>
            <div class="banner-detail">{banner['detail']}</div>
            <div class="banner-pills">
                <span class="banner-pill">{banner['reps_impacted']} reps impacted</span>
                <span class="banner-pill">Est. {banner['estimated_lift']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Metrics
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Calls analyzed</div><div class="metric-value">{m["calls_analyzed"]:,}</div></div>', unsafe_allow_html=True)
    with mc2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Demo conversion</div><div class="metric-value">{m["conversion_rate"]}%</div></div>', unsafe_allow_html=True)
    with mc3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg behavior score</div><div class="metric-value">{m["avg_behavior_score"]}</div><div class="metric-sub">composite, 1–10</div></div>', unsafe_allow_html=True)
    with mc4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Booked-call score</div><div class="metric-value">{m["booked_call_score"]}</div><div class="metric-sub">benchmark for coaching</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Insights
    st.markdown("""
    <div class="section-header">
        <div class="section-title">What we didn't know</div>
        <div class="section-sub">Org-wide patterns only visible at scale.</div>
    </div>
    """, unsafe_allow_html=True)

    insights = patterns.get("three_things_we_didnt_know", [])
    evidences = [
        f"Based on {m['calls_analyzed']} calls analyzed",
        f"Based on {m['real_calls']} real conversations",
        f"Based on {m['booked']} booked demos",
    ]
    titles = [i.split("—")[0].strip() if "—" in i else i[:60] + "..." for i in insights]
    details = [i.split("—")[1].strip() if "—" in i else i for i in insights]

    cols = st.columns(3)
    for i, (col, insight) in enumerate(zip(cols, insights)):
        with col:
            title = titles[i] if i < len(titles) else f"Finding {i+1}"
            detail = details[i] if i < len(details) else insight
            evidence = evidences[i] if i < len(evidences) else ""
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-eyebrow">↑ Insight</div>
                <div class="insight-title">{title}</div>
                <div class="insight-detail">{detail}</div>
                <div class="insight-evidence">{evidence}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        # Winning behaviors
        st.markdown("""
        <div class="section-header">
            <div class="section-title">What works</div>
            <div class="section-sub">Behaviors correlated with booked demos.</div>
        </div>
        """, unsafe_allow_html=True)

        behaviors_html = '<div class="list-card">'
        for b in patterns.get("top_winning_behaviors", []):
            behaviors_html += f"""
            <div class="list-card-row">
                <div>
                    <div class="list-row-main">{b.get('behavior','')}</div>
                    <div class="list-row-sub">{b.get('evidence_stat','')}</div>
                </div>
                <span class="lift-badge">{b.get('booked_rate','')}</span>
            </div>"""
        behaviors_html += "</div>"
        st.markdown(behaviors_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Opening angles
        st.markdown("""
        <div class="section-header">
            <div class="section-title">Opening angles</div>
            <div class="section-sub">Best and worst performing openers.</div>
        </div>
        """, unsafe_allow_html=True)

        angle = patterns.get("opening_angle_analysis", {})
        angles_data = [
            {"angle": angle.get("best_angle", ""), "rate": "Best", "note": angle.get("insight", ""), "good": True},
            {"angle": angle.get("worst_angle", ""), "rate": "Underperforms", "note": angle.get("worst_insight", ""), "good": False},
        ]
        angles_html = '<div class="list-card">'
        for a in angles_data:
            color_class = "good" if a["good"] else "bad"
            angles_html += f"""
            <div class="list-card-row">
                <div>
                    <div class="list-row-main">{a['angle']}</div>
                    <div class="list-row-sub">{a['note'][:80]}...</div>
                </div>
                <span class="conversion-value {color_class}">{a['rate']}</span>
            </div>"""
        angles_html += "</div>"
        st.markdown(angles_html, unsafe_allow_html=True)

    with col_right:
        # Objection map
        st.markdown("""
        <div class="section-header">
            <div class="section-title">Objection map</div>
            <div class="section-sub">Most common objections and the responses that work.</div>
        </div>
        """, unsafe_allow_html=True)

        obj_html = """
        <table class="obj-table">
            <thead><tr>
                <th>Objection</th>
                <th>Best response</th>
                <th class="right">Win w/</th>
                <th class="right">Win w/o</th>
            </tr></thead>
            <tbody>"""

        for obj in objections:
            win_with = obj.get("win_rate_with", 0)
            win_without = obj.get("win_rate_without", 0)
            obj_html += f"""
            <tr>
                <td>
                    <div class="obj-main">{obj.get('objection','')}</div>
                    <div class="obj-freq">{obj.get('frequency','')}</div>
                </td>
                <td class="obj-response">"{obj.get('best_response','')}"</td>
                <td class="right"><span class="win-rate good">{win_with}%</span></td>
                <td class="right"><span class="win-rate bad">{win_without}%</span></td>
            </tr>"""

        obj_html += "</tbody></table>"
        st.markdown(obj_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tenure insight
        st.markdown("""
        <div class="section-header">
            <div class="section-title">Tenure insight</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="brief-section-card">
            <div style="font-size:14px; color: var(--muted-foreground); line-height:1.6;">
                {patterns.get('tenure_insight','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Coaching queue
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Coaching queue</div>
        <div class="section-sub">Sorted by impact, not alphabet. Click any rep to open their deep-dive.</div>
    </div>
    """, unsafe_allow_html=True)

    sorted_reps = sorted(
        reps,
        key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1)
    )

    st.markdown('<div class="coaching-queue">', unsafe_allow_html=True)
    for rep in sorted_reps:
        priority = rep.get("priority", "medium")
        badge_class = f"badge-{priority}"
        priority_icon = {"high": "⚠", "medium": "·", "low": "✓"}.get(priority, "·")

        col1, col2, col3, col4 = st.columns([3, 5, 2, 1])
        with col1:
            st.markdown(f"""
            <div style="padding: 12px 0 12px 20px;">
                <span class="badge {badge_class}">{priority_icon} {priority}</span>
                <div class="queue-rep-name" style="margin-top:6px;">{rep['rep_id']}</div>
                <div class="queue-rep-meta">{rep.get('tenure','').title()} · {rep.get('total_calls',0)} calls</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="padding: 12px 0; font-size: 13px; color: var(--muted-foreground); line-height: 1.5;">
                {rep.get('gap','')}
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="padding: 12px 0; text-align: right;">
                <div class="queue-score">{rep.get('avg_behavior_score','')}</div>
                <div class="queue-score-label">behavior</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("<div style='padding: 8px 20px 0 0;'>", unsafe_allow_html=True)
            if st.button("→", key=f"queue_{rep['rep_id']}", help=f"Open {rep['rep_id']} deep-dive"):
                st.session_state.selected_rep = rep["rep_id"]
                st.session_state.view = "rep_detail"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<hr style="margin:0; border-color: var(--border);">', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _rep_grid(reps):
    """Card grid of all reps — click to open deep-dive."""
    st.markdown("""
    <div class="rep-grid">
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, rep in enumerate(sorted(reps, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority","medium"), 1))):
        with cols[i % 3]:
            priority = rep.get("priority", "medium")
            badge_class = f"badge-{priority}"
            st.markdown(f"""
            <div class="rep-card">
                <div class="rep-card-header">
                    <div>
                        <div class="rep-card-name">{rep['rep_id']}</div>
                        <div class="rep-card-meta">{rep.get('total_calls',0)} calls · {rep.get('tenure','').title()}</div>
                    </div>
                    <span class="badge {badge_class}">{priority}</span>
                </div>
                <div class="mini-stats">
                    <div class="mini-stat">
                        <div class="mini-stat-value">{rep.get('avg_behavior_score','')}</div>
                        <div class="mini-stat-label">Score</div>
                    </div>
                    <div class="mini-stat">
                        <div class="mini-stat-value">{rep.get('conversion_rate',0):.0%}</div>
                        <div class="mini-stat-label">Conv %</div>
                    </div>
                    <div class="mini-stat">
                        <div class="mini-stat-value">{rep.get('demos_booked',0)}</div>
                        <div class="mini-stat-label">Booked</div>
                    </div>
                </div>
                <div class="rep-card-gap">{rep.get('gap','')}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"View deep-dive →", key=f"grid_{rep['rep_id']}", use_container_width=True):
                st.session_state.selected_rep = rep["rep_id"]
                st.session_state.view = "rep_detail"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)