import re
import streamlit as st
import plotly.express as px
from data import get_team_metrics, get_objection_stats, get_action_banner, get_opening_angle_stats


def to_third_person(text):
    if not text:
        return text
    replacements = [
        ("You're ", "Rep is "),
        ("You are ", "Rep is "),
        ("You consistently ", "Rep consistently "),
        ("You excel ", "Rep excels "),
        ("You repeatedly ", "Rep repeatedly "),
        ("You struggle", "Rep struggles"),
        ("You dominate", "Rep dominates"),
        ("You jump", "Rep jumps"),
        ("You fail", "Rep fails"),
        ("You tend", "Rep tends"),
        ("You often", "Rep often"),
        ("You rarely", "Rep rarely"),
        ("You always", "Rep always"),
        ("You never", "Rep never"),
        ("You miss", "Rep misses"),
        ("You pitch", "Rep pitches"),
        ("You ask", "Rep asks"),
        ("You build", "Rep builds"),
        ("You deliver", "Rep delivers"),
        ("You handle", "Rep handles"),
        ("Your ", "Their "),
    ]
    for second, third in replacements:
        if text.startswith(second):
            text = third + text[len(second):]
            break
    return text


def show_manager(calls, patterns, reps):
    m = get_team_metrics(calls, reps)
    banner = get_action_banner(calls, reps, patterns)
    objections = get_objection_stats(calls, patterns)
    angle_stats = get_opening_angle_stats(calls)

    st.markdown("""
    <div class="mgr-header-marker">
        <div class="page-title">Team intelligence</div>
        <div class="page-sub">Patterns from every call, coaching priorities ranked by impact.</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Team dashboard", "Rep deep-dive"])

    with tab1:
        _team_dashboard(calls, patterns, reps, m, banner, objections, angle_stats)

    with tab2:
        _rep_grid(reps)


def _team_dashboard(calls, patterns, reps, m, banner, objections, angle_stats):
    # Action banner
    if banner:
        st.markdown(f"""
        <div class="action-banner">            
            <div class="banner-eyebrow">⚡ Highest-impact action this week</div>
            <div class="banner-headline">{banner['headline']}</div>
            <div class="banner-detail" style="max-width:100%;">{banner['detail']}</div>
            <div class="banner-pills">
                <span class="banner-pill">{banner['reps_impacted']} reps impacted</span>
                <span class="banner-pill">Est. {banner['estimated_lift']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    # Metrics — 3 cards (call count already in page subtitle)
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Demo conversion</div><div class="metric-value">{m["conversion_rate"]}%</div></div>', unsafe_allow_html=True)
    with mc2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg behavior score<span class="metric-info" data-tooltip="Composite score (1–10) combining talk ratio, energy, discovery questions asked, objection handling, personalization, rapport, clear next step, and call energy. Higher = stronger rep behavior on this call.">ⓘ</span></div><div class="metric-value">{m["avg_behavior_score"]}</div></div>', unsafe_allow_html=True)
    with mc3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Booked-call score<span class="metric-info" data-tooltip="Average behavior score across all calls that booked a demo. Used as the benchmark — coaching brings reps closer to this score.">ⓘ</span></div><div class="metric-value">{m["booked_call_score"]}</div></div>', unsafe_allow_html=True)

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

    cols = st.columns(3)
    for i, (col, insight) in enumerate(zip(cols, insights)):
        with col:
            if isinstance(insight, dict):
                title = insight.get("title", f"Finding {i+1}")
                detail = insight.get("detail", "")
            else:
                title = insight.split("—")[0].strip() if "—" in insight else insight[:60] + "..."
                detail = insight.split("—")[1].strip() if "—" in insight else insight
            _parts = [p.strip() for p in re.split(r'\.\s+', detail.strip()) if p.strip()]
            _normed = [p if p.endswith(('.', '!', '?')) else p + '.' for p in _parts]
            if len(_normed) >= 3:
                _header = " ".join(_normed[:2])
                _bullet_parts = _normed[2:5]
            elif len(_normed) == 2:
                _header = _normed[0]
                _bullet_parts = [_normed[1]]
            else:
                _header = detail
                _bullet_parts = []
            _bullet_items = "".join(f"<li>{b}</li>" for b in _bullet_parts)
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-eyebrow">↑ Insight</div>
                <div class="insight-title">{title}</div>
                <div class="insight-lead">{_header}</div>
                <ul class="insight-bullets">
                    {_bullet_items}
                </ul>
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
            behavior = b.get("behavior") or "—"
            evidence = b.get("evidence_stat") or b.get("insight") or ""
            booked_rate = b.get("booked_rate") or "—"
            behaviors_html += f"""
            <div class="list-card-row">
                <div>
                    <div class="list-row-main">{behavior}</div>
                    <div class="list-row-sub">{evidence}</div>
                </div>
                <span class="lift-badge">{booked_rate}</span>
            </div>"""
        behaviors_html += "</div>"
        st.markdown(behaviors_html, unsafe_allow_html=True)

    with col_right:
        # Opening angles
        st.markdown("""
        <div class="section-header">
            <div class="section-title">Opening angles</div>
            <div class="section-sub">Conversion rate by opener — 5+ calls, sorted by conversion.</div>
        </div>
        """, unsafe_allow_html=True)

        angles_html = '<div class="list-card">'
        for a in angle_stats:
            conv = a["conversion_rate"]
            if conv >= 35:
                rate_color = "var(--success)"
            elif conv >= 20:
                rate_color = "var(--foreground)"
            else:
                rate_color = "var(--destructive)"
            sub = f"{a['count']} calls"
            if a["best_for"]:
                sub += f" · best for {a['best_for']}"
            angles_html += f"""
            <div class="list-card-row">
                <div>
                    <div class="list-row-main">{a['human_label']}</div>
                    <div class="list-row-sub">{sub}</div>
                </div>
                <span style="font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:700; color:{rate_color}; white-space:nowrap;">{conv}%</span>
            </div>"""
        angles_html += "</div>"
        st.markdown(angles_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Objection map — full width
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Objection map</div>
        <div class="section-sub">Most common objections, top handler, and win rates by response quality.</div>
    </div>
    """, unsafe_allow_html=True)

    obj_html = """
    <table class="obj-table">
        <thead><tr>
            <th>Objection</th>
            <th>Best response</th>
            <th>Top rep</th>
            <th class="right">Win rate</th>
        </tr></thead>
        <tbody>"""

    for obj in objections:
        win_with = obj.get("win_rate_with", "—")
        with_display = f"{win_with}%" if isinstance(win_with, int) else win_with
        appearances = obj.get("total_appearances", 0)
        freq_text = obj.get("frequency") or ""
        freq_label = f"{freq_text} · {appearances} calls" if appearances else freq_text
        best_response = obj.get("best_response") or obj.get("example_rep_behavior") or ""
        top_rep = obj.get("top_rep", "—")
        obj_html += f"""
        <tr>
            <td>
                <div class="obj-main">{obj.get('objection','')}</div>
                <div class="obj-freq">{freq_label}</div>
            </td>
            <td class="obj-response">"{best_response}"</td>
            <td class="obj-rep">{top_rep}</td>
            <td class="right"><span class="win-rate good">{with_display}</span></td>
        </tr>"""

    obj_html += "</tbody></table>"
    st.markdown(obj_html, unsafe_allow_html=True)


def _render_rep_cards(rep_list, key_prefix="grid"):
    cols = st.columns(3)
    for i, rep in enumerate(rep_list):
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
                <div class="rep-card-gap">{to_third_person(rep.get('gap',''))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View deep-dive →", key=f"{key_prefix}_{rep['rep_id']}", use_container_width=True):
                st.session_state.selected_rep = rep["rep_id"]
                st.session_state.view = "rep_detail"
                st.rerun()


def _rep_grid(reps):
    search = st.text_input(
        "Search reps",
        placeholder="Search by rep ID, name, or tenure…",
        label_visibility="collapsed",
    )

    # Filter chips
    if "rep_filter" not in st.session_state:
        st.session_state.rep_filter = "all"

    chips = [
        ("all", "All"),
        ("high_priority", "High priority"),
        ("new_tenure", "New tenure"),
        ("low_conversion", "Low conversion"),
    ]
    chip_cols = st.columns(len(chips))
    for col, (key, label) in zip(chip_cols, chips):
        with col:
            is_active = st.session_state.rep_filter == key
            if st.button(label, key=f"chip_{key}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state.rep_filter = key
                st.rerun()

    active_filter = st.session_state.rep_filter

    def _apply_filter(rep_list):
        if active_filter == "high_priority":
            return [r for r in rep_list if r.get("priority") == "high"]
        elif active_filter == "new_tenure":
            return [r for r in rep_list if r.get("tenure", "").lower() == "new"]
        elif active_filter == "low_conversion":
            return [r for r in rep_list if r.get("conversion_rate", 0) < 0.25]
        return rep_list

    # Apply search text first, then chip filter on top
    working = list(reps)
    if search:
        q = search.lower()
        working = [r for r in working if q in r["rep_id"].lower() or q in r.get("tenure", "").lower()]

    # Non-"all" chip: show full filtered grid, hide curated sections
    if active_filter != "all":
        filtered = _apply_filter(working)
        n = len(filtered)
        st.caption(f"{n} rep{'s' if n != 1 else ''} match this filter")
        _render_rep_cards(filtered, key_prefix="filtered")
        return

    # "All" chip + search active: show search results, skip curated sections
    if search:
        n = len(working)
        st.caption(f"{n} rep{'s' if n != 1 else ''} found")
        _render_rep_cards(working, key_prefix="search")
        return

    # Default view (All + no search): scatter → coach this week → top reps → view all

    # Team performance scatter
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Team performance map</div>
        <div class="section-sub">Click any rep to open their coaching profile. Dot size = call volume.</div>
    </div>
    """, unsafe_allow_html=True)

    scatter_rows = [
        {
            "Rep": r["rep_id"],
            "Behavior Score": r.get("avg_behavior_score", 0),
            "Conversion Rate (%)": round(r.get("conversion_rate", 0) * 100, 1),
            "Total Calls": max(r.get("total_calls", 1), 1),
            "Priority": r.get("priority", "medium"),
            "Gap": r.get("gap", ""),
            "Coaching Rec": r.get("coaching_rec", ""),
        }
        for r in reps
    ]
    fig = px.scatter(
        scatter_rows,
        x="Behavior Score",
        y="Conversion Rate (%)",
        size="Total Calls",
        color="Priority",
        color_discrete_map={"high": "#c53030", "medium": "#b07800", "low": "#1a6b3c"},
        text="Rep",
        size_max=30,
        category_orders={"Priority": ["high", "medium", "low"]},
        custom_data=["Gap", "Coaching Rec", "Rep"],
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        hovertemplate="<b>%{customdata[2]}</b><br>Score: %{x} | Conv: %{y}%<extra></extra>",
    )

    fig.update_traces(marker=dict(line=dict(width=1, color="white")))

    fig.add_shape(type="rect", x0=5.5, x1=8, y0=33, y1=115, fillcolor="rgba(26,107,60,0.05)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=4, x1=5.5, y0=33, y1=115, fillcolor="rgba(176,120,0,0.05)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, x1=8, y0=0, y1=33, fillcolor="rgba(59,130,246,0.05)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=4, x1=5.5, y0=0, y1=33, fillcolor="rgba(197,48,48,0.05)", line_width=0, layer="below")

    fig.add_shape(type="line", x0=5.5, x1=5.5, y0=0, y1=115, line=dict(color="#d4e4da", width=1, dash="dash"))
    fig.add_shape(type="line", x0=4, x1=8, y0=33, y1=33, line=dict(color="#d4e4da", width=1, dash="dash"))

    fig.add_annotation(x=7.8, y=108, text="✦ Clone", showarrow=False, font=dict(size=11, color="#1a6b3c"), opacity=0.7)
    fig.add_annotation(x=4.3, y=108, text="⚠ Fragile", showarrow=False, font=dict(size=11, color="#b07800"), opacity=0.7)
    fig.add_annotation(x=7.8, y=3, text="↑ Unlock", showarrow=False, font=dict(size=11, color="#3b82f6"), opacity=0.7)
    fig.add_annotation(x=4.3, y=3, text="🎯 Coach now", showarrow=False, font=dict(size=11, color="#c53030"), opacity=0.7)

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter, sans-serif",
        xaxis=dict(range=[4, 8], title="Avg behavior score (0–10)", gridcolor="#e5edea", zeroline=False),
        yaxis=dict(range=[-8, 115], title="Conversion rate (%)", gridcolor="#e5edea", zeroline=False),
        height=520,
        margin=dict(l=40, r=40, t=20, b=60),
        showlegend=True,
        legend=dict(
            title="Coaching priority",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
    )

    selected = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="team_scatter")
    if selected and selected.get("selection", {}).get("points"):
        point = selected["selection"]["points"][0]
        rep_name = point.get("text") or scatter_rows[point["point_index"]]["Rep"]
        st.session_state.selected_rep = rep_name
        st.session_state.view = "rep_detail"
        st.rerun()

    st.caption("X axis: avg behavior score across all calls (composite of 7 signals). Y axis: demo conversion rate. Reference lines at team median behavior score (5.5) and team avg conversion (33%).")

    st.markdown("<br>", unsafe_allow_html=True)

    # Coach this week
    high_priority = [r for r in reps if r.get("priority") == "high"]
    coach_week = sorted(high_priority, key=lambda x: x.get("avg_behavior_score", 0))[:3]

    if coach_week:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">Coach this week</div>
            <div class="section-sub">High-priority reps ranked by lowest behavior score — biggest impact first.</div>
        </div>
        """, unsafe_allow_html=True)
        coach_cols = st.columns(len(coach_week))
        for col, rep in zip(coach_cols, coach_week):
            with col:
                st.markdown(f"""
                <div class="perf-card warning">
                    <div class="perf-card-name">{rep['rep_id']}</div>
                    <div class="perf-card-stats">
                        <span class="perf-stat">{rep.get('avg_behavior_score', '')} score</span>
                        <span class="perf-stat">{rep.get('conversion_rate', 0):.0%} conv.</span>
                    </div>
                    <div class="perf-card-text">{to_third_person(rep.get('gap', ''))}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
                if st.button("View →", key=f"coach_{rep['rep_id']}", use_container_width=True):
                    st.session_state.selected_rep = rep["rep_id"]
                    st.session_state.view = "rep_detail"
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    # Top reps — clone their behavior
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Top reps — clone their behavior</div>
        <div class="section-sub">Highest behavior score — at least 5 calls.</div>
    </div>
    """, unsafe_allow_html=True)

    qualifying = [r for r in reps if r.get("total_calls", 0) >= 5]
    top3 = sorted(qualifying, key=lambda x: x.get("avg_behavior_score", 0), reverse=True)[:3]
    top_cols = st.columns(len(top3)) if top3 else st.columns(1)
    for col, rep in zip(top_cols, top3):
        with col:
            st.markdown(f"""
            <div class="perf-card success">
                <div class="perf-card-name">{rep['rep_id']}</div>
                <div class="perf-card-stats">
                    <span class="perf-stat">{rep.get('avg_behavior_score', '')} score</span>
                    <span class="perf-stat">{rep.get('conversion_rate', 0):.0%} conv.</span>
                </div>
                <div class="perf-card-text">{to_third_person(rep.get('strength', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            if st.button("View →", key=f"top_{rep['rep_id']}", use_container_width=True):
                st.session_state.selected_rep = rep["rep_id"]
                st.session_state.view = "rep_detail"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("View all reps", expanded=False):
        sorted_reps = sorted(reps, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1))
        _render_rep_cards(sorted_reps, key_prefix="all")