import html as _html
import streamlit as st
import pandas as pd
from data import get_restaurant_call_history, get_warm_pipeline


def _reset_warm_page():
    st.session_state.warm_page = 0
    st.session_state.warm_selected_id = None


def show_rep_search(calls, restaurants):
    if "search_category" not in st.session_state:
        st.session_state.search_category = None
    if "search_chip" not in st.session_state:
        st.session_state.search_chip = None
    if "show_new_restaurant_form" not in st.session_state:
        st.session_state.show_new_restaurant_form = False
    if "new_restaurant_name" not in st.session_state:
        st.session_state.new_restaurant_name = ""

    call_history = get_restaurant_call_history(calls)

    st.markdown("""
    <div class="rep-header-marker">
        <div class="page-title">Get ready for your next call.</div>
        <div class="page-sub">Search a restaurant, choose call type, generate a brief grounded in analyzed calls.</div>
    </div>
    """, unsafe_allow_html=True)

    # New restaurant form replaces all other content when active
    if st.session_state.show_new_restaurant_form:
        if st.button("← Back to search", key="back_from_new_rest"):
            st.session_state.show_new_restaurant_form = False
            st.rerun()
        _new_restaurant_form(restaurants)
        return

    tab1, tab2 = st.tabs(["Search restaurants", "Warm pipeline"])

    with tab1:
        search = st.text_input(
            "Search",
            placeholder="🔍  Search by restaurant name, city, or cuisine…",
            label_visibility="collapsed",
        )

        if search and len(search) >= 2:
            st.session_state.search_category = None
            st.session_state.search_chip = None
            q = search.lower()
            filtered = restaurants[
                restaurants["name"].str.lower().str.contains(q, na=False) |
                restaurants["city"].str.lower().str.contains(q, na=False) |
                restaurants["cuisine_type"].str.lower().str.contains(q, na=False)
            ]
            if len(filtered) == 0:
                safe_search = _html.escape(search)
                st.markdown(f"""
                <div style="text-align:center; padding: 56px 32px;">
                    <div style="font-size:18px; font-weight:600; color:var(--foreground); margin-bottom:8px;">
                        &ldquo;{safe_search}&rdquo; not found in our database
                    </div>
                    <div style="font-size:14px; color:var(--muted-foreground); margin-bottom:24px;">
                        Generate a brief grounded in similar calls from our dataset.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                _, center_col, _ = st.columns([1, 2, 1])
                with center_col:
                    if st.button(
                        f"＋ Start brief for {search}",
                        key="quick_new_rest",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.new_restaurant_name = search
                        st.session_state.show_new_restaurant_form = True
                        st.rerun()
            else:
                st.caption(f"{len(filtered)} restaurant{'s' if len(filtered) != 1 else ''} found")
                _render_restaurant_grid(filtered, call_history)
                if len(filtered) < 3:
                    _not_found_cta()
        else:
            category = st.session_state.search_category

            if category is None:
                _render_category_cards()
            else:
                if st.button("← All categories", key="cat_back"):
                    st.session_state.search_category = None
                    st.session_state.search_chip = None
                    st.rerun()

                if category == "has_website":
                    mask = restaurants["website_url"].notna() & (restaurants["website_url"].str.strip() != "")
                    filtered = restaurants[mask]
                    st.caption(f"{len(filtered)} restaurants with an existing website")
                    _render_restaurant_grid(filtered, call_history)

                elif category == "no_website":
                    mask = restaurants["website_url"].isna() | (restaurants["website_url"].str.strip() == "")
                    filtered = restaurants[mask]
                    st.caption(f"{len(filtered)} restaurants with no website yet")
                    _render_restaurant_grid(filtered, call_history)

                elif category == "cuisine":
                    cuisines = sorted(
                        c for c in restaurants["cuisine_type"].dropna().unique() if c and c != "unknown"
                    )
                    active = st.session_state.search_chip
                    _render_chips(cuisines, active, "chip_cuisine_")
                    if active:
                        filtered = restaurants[restaurants["cuisine_type"] == active]
                        st.caption(f"{len(filtered)} {active} restaurant{'s' if len(filtered) != 1 else ''}")
                        _render_restaurant_grid(filtered, call_history)
                    else:
                        st.caption("Select a cuisine type above to see restaurants.")

                elif category == "city":
                    top_cities = restaurants["city"].value_counts().head(16).index.tolist()
                    active = st.session_state.search_chip
                    _render_chips(top_cities, active, "chip_city_")
                    if active:
                        filtered = restaurants[restaurants["city"] == active]
                        st.caption(f"{len(filtered)} restaurant{'s' if len(filtered) != 1 else ''} in {active}")
                        _render_restaurant_grid(filtered, call_history)
                    else:
                        st.caption("Select a city above to see restaurants.")

    with tab2:
        _render_warm_pipeline(calls, restaurants)


def _render_warm_pipeline(calls, restaurants):
    warm_rows = get_warm_pipeline(calls, restaurants)

    # Session state init
    for key, default in [
        ("warm_filter_cuisine", "All"),
        ("warm_filter_score", "All"),
        ("warm_filter_rep", "All"),
        ("warm_page", 0),
        ("warm_selected_id", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Build filter option lists from warm_rows
    cuisines_avail = sorted({
        r["cuisine_type"].replace("_", " ").title()
        for r in warm_rows
        if r["cuisine_type"] and r["cuisine_type"] not in ("unknown", "")
    })
    reps_avail = sorted({r["rep_id"] for r in warm_rows if r["rep_id"]})
    cuisine_opts = ["All"] + cuisines_avail
    score_opts = ["All", "7+", "6+", "5+"]
    rep_opts = ["All"] + reps_avail

    cuisine_f = st.session_state.warm_filter_cuisine
    score_f = st.session_state.warm_filter_score
    rep_f = st.session_state.warm_filter_rep

    # Apply filters (needed for hero count before rendering filters)
    filtered_rows = warm_rows
    if cuisine_f != "All":
        filtered_rows = [r for r in filtered_rows if r["cuisine_type"].replace("_", " ").title() == cuisine_f]
    if score_f != "All":
        min_score = int(score_f.rstrip("+"))
        filtered_rows = [r for r in filtered_rows if r["behavior_score"] >= min_score]
    if rep_f != "All":
        filtered_rows = [r for r in filtered_rows if r["rep_id"] == rep_f]

    n = len(filtered_rows)

    # 1. HERO BANNER — top of tab
    st.markdown(f"""
    <div class="warm-pipeline-hero">
        <div class="warm-pipeline-hero-left">
            <div class="warm-pipeline-hero-eyebrow">🔥 Highest-leverage calls this week</div>
            <div class="warm-pipeline-hero-headline">These prospects already said yes to the conversation.</div>
            <div class="warm-pipeline-hero-sub">They didn't book — but they didn't say no either. A better angle, better timing, or a different rep could close these. Start here before cold dialing.</div>
        </div>
        <div class="warm-pipeline-hero-stat">
            <div class="warm-pipeline-hero-number">{n}</div>
            <div class="warm-pipeline-hero-label">warm prospects<br>ready to re-engage</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. FILTER CONTROLS — below hero
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        st.selectbox("Cuisine", cuisine_opts, key="warm_filter_cuisine", on_change=_reset_warm_page)
    with fc2:
        st.selectbox("Min score", score_opts, key="warm_filter_score", on_change=_reset_warm_page)
    with fc3:
        st.selectbox("Rep", rep_opts, key="warm_filter_rep", on_change=_reset_warm_page)
    with fc4:
        st.caption(f"**{n}** prospect{'s' if n != 1 else ''} match")

    if not filtered_rows:
        st.markdown("""
        <div style="text-align:center; padding: 64px; border: 1px dashed var(--border);
                    border-radius: var(--radius); color: var(--muted-foreground); font-size: 14px;">
            No prospects match the current filters.
        </div>
        """, unsafe_allow_html=True)
        return

    # 3. PAGINATED CARD GRID
    per_page = 3
    total_pages = max(1, (n + per_page - 1) // per_page)
    current_page = min(st.session_state.warm_page, total_pages - 1)
    st.session_state.warm_page = current_page
    page_rows = filtered_rows[current_page * per_page : (current_page + 1) * per_page]

    cols = st.columns(3)
    for i, row in enumerate(page_rows):
        restaurant_name = _html.escape(str(row.get("restaurant_name", row["call_id"])))
        cuisine = _html.escape(row["cuisine_type"].replace("_", " ").title())
        rep_id = _html.escape(str(row["rep_id"]))
        score = row["behavior_score"]
        objections_raw = row["objections"]
        obj_text = _html.escape(", ".join(objections_raw) if objections_raw else "No objections noted")
        reframe_raw = row.get("follow_up_note", "")
        reframe = _html.escape(str(reframe_raw)) if reframe_raw else ""
        reframe_html = f'<div class="warm-grid-reframe">↪ {reframe}</div>' if reframe else ""

        with cols[i]:
            st.markdown(f"""
            <div class="warm-grid-card">
                <div>
                    <div class="warm-grid-cuisine">{restaurant_name} · {cuisine}</div>
                    <div class="warm-grid-meta">
                        {rep_id} &nbsp;·&nbsp;
                        <span class="warm-score-badge">{score}</span>
                    </div>
                    <div class="warm-grid-objection">{obj_text}</div>
                    {reframe_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View brief →", key=f"warm_view_{current_page}_{i}", use_container_width=True, type="secondary"):
                st.session_state.warm_selected_id = row["call_id"]
                st.rerun()

    # 4. PAGINATION CONTROLS
    col_prev, col_mid, col_next = st.columns([1, 2, 1])
    with col_prev:
        st.markdown('<div style="display:flex;justify-content:flex-start;">', unsafe_allow_html=True)
        if current_page > 0:
            if st.button("← Previous", key="warm_prev", type="secondary"):
                st.session_state.warm_page = current_page - 1
                st.session_state.warm_selected_id = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_mid:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px; font-size:13px; color:#6B7280;'>"
            f"Page {current_page + 1} of {total_pages} &nbsp;·&nbsp; {n} prospects</div>",
            unsafe_allow_html=True,
        )
    with col_next:
        st.markdown('<div style="display:flex;justify-content:flex-end;">', unsafe_allow_html=True)
        if current_page < total_pages - 1:
            if st.button("Next →", key="warm_next", type="primary"):
                st.session_state.warm_page = current_page + 1
                st.session_state.warm_selected_id = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Detail panel
    selected_id = st.session_state.get("warm_selected_id")
    if selected_id:
        sel = next((r for r in warm_rows if r["call_id"] == selected_id), None)
        if sel:
            cuisine = _html.escape(sel["cuisine_type"].replace("_", " ").title())
            rest_type = _html.escape(sel["restaurant_type"].replace("_", " ").title())
            rep_id = _html.escape(str(sel["rep_id"]))
            score = sel["behavior_score"]
            objections_raw = sel["objections"]
            obj_text = _html.escape(", ".join(objections_raw) if objections_raw else "None noted")
            summary = _html.escape(str(sel["summary"]))
            follow_up_note = _html.escape(str(sel["follow_up_note"]))

            st.markdown(f"""
            <div class="warm-detail-panel">
                <div class="warm-detail-header">{cuisine} · {rest_type}</div>
                <div class="warm-detail-meta">Last called by {rep_id} · Score: {score}/10</div>
                <div class="warm-detail-objections">Objections raised: {obj_text}</div>
                <div class="warm-detail-summary">{summary}</div>
                <div class="warm-detail-note">{follow_up_note}</div>
            </div>
            """, unsafe_allow_html=True)

            dc1, dc2 = st.columns([2, 1])
            with dc1:
                if st.button("✦ Generate follow-up brief →", key="warm_generate", type="primary"):
                    st.session_state.selected_restaurant = {
                        "name": sel["restaurant_name"],
                        "cuisine_type": sel["cuisine_type"],
                        "business_type": sel["restaurant_type"],
                        "city": sel["city"],
                        "state": sel["state"],
                        "num_locations": sel["num_locations"],
                        "website_url": sel["website_url"],
                    }
                    st.session_state.prior_calls = sel["prior_calls"]
                    st.session_state.is_new_restaurant = False
                    st.session_state.is_followup = True
                    st.session_state.brief_generated = False
                    st.session_state.brief_data = None
                    st.session_state.pop("restaurant_intel", None)
                    st.session_state.generate_brief = False
                    st.session_state.view = "rep_brief"
                    st.rerun()
            with dc2:
                if st.button("✕ Dismiss", key="warm_dismiss"):
                    st.session_state.warm_selected_id = None
                    st.rerun()


# contextual CTA — only shown inline when search returns <3 results
def _not_found_cta():
    st.markdown("""
    <div style="border: 1px dashed var(--border); border-radius: var(--radius);
                padding: 20px 22px; margin-top: 8px;">
        <div style="font-size:15px; font-weight:600; color:var(--foreground); margin-bottom:6px;">Not finding it?</div>
        <div style="font-size:13px; color:var(--muted-foreground); margin-bottom:12px;">
            Add a new restaurant to generate a brief grounded in similar calls.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(
        "＋ Prep for a new restaurant",
        key="open_new_rest_form",
        type="secondary",
    ):
        st.session_state.show_new_restaurant_form = True
        st.rerun()


def _new_restaurant_form(restaurants):
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Prep for a new restaurant</div>
        <div class="section-sub">Brief will be grounded in calls to similar restaurants in our dataset.</div>
    </div>
    """, unsafe_allow_html=True)

    validation_errors = st.session_state.get("form_validation_errors", [])
    if validation_errors:
        st.warning(f"Please fill in: {', '.join(validation_errors)}")

    cuisine_options = ["— select cuisine —"] + sorted(
        c for c in restaurants["cuisine_type"].dropna().unique() if c not in ("unknown", "")
    ) + ["Other"]
    business_options = ["full_service", "quick_service", "cafe", "bakery", "other"]

    prefill_name = st.session_state.pop("new_restaurant_name", "")
    if prefill_name:
        st.session_state["_nrf_name"] = prefill_name
    with st.form("new_restaurant_form"):
        name = st.text_input("Restaurant name *", key="_nrf_name")
        col_city, col_state = st.columns([3, 1])
        with col_city:
            city = st.text_input("City *")
        with col_state:
            state = st.text_input("State * (2-letter)", max_chars=2, placeholder="CA")
        cuisine = st.selectbox("Cuisine type *", cuisine_options)
        biz_type = st.selectbox(
            "Business type",
            business_options,
            format_func=lambda x: x.replace("_", " ").title(),
        )
        has_website = st.radio("Has website?", ["Yes", "No", "Not sure"], horizontal=True)
        num_locations = st.number_input("Number of locations", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("Generate brief →", type="primary", use_container_width=True)

    if submitted:
        missing = []
        if not name.strip():
            missing.append("restaurant name")
        if not city.strip():
            missing.append("city")
        if not state.strip():
            missing.append("state")
        if cuisine == "— select cuisine —":
            missing.append("cuisine type")

        if missing:
            st.session_state.form_validation_errors = missing
            st.rerun()
        else:
            st.session_state.pop("form_validation_errors", None)
            rest_dict = {
                "restaurant_id": f"new_{abs(hash(name.strip() + city.strip())) % 10000:04d}",
                "name": name.strip(),
                "city": city.strip(),
                "state": state.strip().upper()[:2],
                "cuisine_type": cuisine if cuisine != "Other" else "unknown",
                "business_type": biz_type,
                "website_url": "yes" if has_website == "Yes" else "",
                "num_locations": int(num_locations),
            }

            cuisine_val = rest_dict["cuisine_type"]
            biz_val = rest_dict["business_type"]
            both = restaurants[
                (restaurants["cuisine_type"] == cuisine_val) &
                (restaurants["business_type"] == biz_val)
            ]
            if len(both) >= 1:
                similar = both.sample(min(3, len(both)), random_state=42).to_dict("records")
            else:
                same_cuisine = restaurants[restaurants["cuisine_type"] == cuisine_val]
                similar = (
                    same_cuisine.sample(min(3, len(same_cuisine)), random_state=42).to_dict("records")
                    if len(same_cuisine) > 0 else []
                )

            st.session_state.selected_restaurant = rest_dict
            st.session_state.similar_restaurants = similar
            st.session_state.is_new_restaurant = True
            st.session_state.is_followup = False
            st.session_state.prior_calls = []
            st.session_state.show_new_restaurant_form = False
            st.session_state.brief_generated = False
            st.session_state.brief_data = None
            st.session_state.generate_brief = False
            st.session_state.view = "rep_brief"
            st.rerun()


def _render_chips(items, active, key_prefix):
    per_row = 5
    for row_start in range(0, len(items), per_row):
        row_items = items[row_start:row_start + per_row]
        chip_cols = st.columns(len(row_items))
        for j, item in enumerate(row_items):
            with chip_cols[j]:
                is_active = active == item
                if st.button(
                    item,
                    key=f"{key_prefix}{item}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.search_chip = None if is_active else item
                    st.rerun()


def _render_category_cards():
    categories = [
        {
            "key": "cuisine",
            "icon": "🍜",
            "title": "By cuisine type",
            "body": "Browse restaurants by food category — Mexican, Italian, Asian, and more.",
        },
        {
            "key": "city",
            "icon": "📍",
            "title": "By city",
            "body": "Filter to restaurants in a specific market you're working.",
        },
        {
            "key": "has_website",
            "icon": "🌐",
            "title": "Has online ordering already",
            "body": "Restaurants with an existing website — ready to upgrade to commission-free ordering.",
        },
        {
            "key": "no_website",
            "icon": "⚡",
            "title": "No website yet",
            "body": "Highest urgency — no online presence means all delivery revenue goes to platforms.",
        },
    ]

    row1 = st.columns(2, gap="medium")
    row2 = st.columns(2, gap="medium")
    for col, cat in zip([*row1, *row2], categories):
        with col:
            st.markdown(f"""
            <div class="category-card">
                <div class="category-card-icon">{cat['icon']}</div>
                <div class="category-card-title">{cat['title']}</div>
                <div class="category-card-body">{cat['body']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Browse →", key=f"cat_{cat['key']}", use_container_width=True):
                st.session_state.search_category = cat["key"]
                st.session_state.search_chip = None
                st.rerun()


def _render_restaurant_grid(filtered, call_history=None):
    if call_history is None:
        call_history = {}

    if len(filtered) == 0:
        st.markdown("""
        <div style="text-align:center; padding: 64px; border: 1px dashed var(--border);
                    border-radius: var(--radius); color: var(--muted-foreground); font-size: 14px;">
            No matches. Try a different filter.
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("""
    <div style="display:flex; gap:16px; align-items:center; margin-bottom:12px; font-size:12px; color:#5a6e63;">
        <span style="display:inline-flex; align-items:center; gap:6px;">
            <span style="width:12px; height:12px; border-radius:3px; border:2px solid #1a6b3c; display:inline-block;"></span>
            Prior call history
        </span>
        <span style="display:inline-flex; align-items:center; gap:6px;">
            <span style="width:12px; height:12px; border-radius:3px; border:1.5px solid #d4e4da; display:inline-block;"></span>
            No prior contact
        </span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (_, r) in enumerate(filtered.head(30).iterrows()):
        with cols[i % 3]:
            name = _html.escape(str(r.get("name", "")))
            city = _html.escape(str(r.get("city", "")))
            state = _html.escape(str(r.get("state", "")))
            cuisine = _html.escape(str(r.get("cuisine_type", "")))
            biz_type = _html.escape(str(r.get("business_type", "")).replace("_", " ").title())
            cuisine_short = cuisine[:3].upper()

            has_website = pd.notna(r.get("website_url", "")) and str(r.get("website_url", "")).strip()
            online_tag_class = "success" if has_website else "warning"
            online_label = "Has website" if has_website else "No website"

            num_loc = int(r.get("num_locations", 1))
            loc_label = "1 location" if num_loc == 1 else f"{num_loc} locations"

            rest_id = str(r.get("restaurant_id", ""))
            prior = call_history.get(rest_id, [])
            n_prior = len(prior)

            card_style = "border: 1.5px solid rgba(26,107,60,0.35);" if n_prior > 0 else ""
            history_badge = (
                '<span class="tag" style="background:rgba(26,107,60,0.1);'
                'color:var(--primary);border-color:rgba(26,107,60,0.3);">'
                f'\U0001f4de Contacted {n_prior}×</span>'
            ) if n_prior > 0 else ""

            card_html = (
                f'<div class="restaurant-card" style="{card_style}">'
                  f'<div class="restaurant-card-header">'
                    f'<div>'
                      f'<div class="restaurant-name">{name}</div>'
                      f'<div class="restaurant-location">\U0001f4cd {city}, {state}</div>'
                    f'</div>'
                    f'<div class="restaurant-rating">★ {cuisine_short}</div>'
                  f'</div>'
                  f'<div class="tags">'
                    f'<span class="tag">{cuisine}</span>'
                    f'<span class="tag">{biz_type}</span>'
                    f'<span class="tag {online_tag_class}">{online_label}</span>'
                    f'<span class="tag">{loc_label}</span>'
                    f'{history_badge}'
                  f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            if st.button("Select", key=f"rest_{i}", use_container_width=True, type="secondary"):
                st.session_state.selected_restaurant = r.to_dict()
                st.session_state.is_new_restaurant = False
                st.session_state.similar_restaurants = []
                st.session_state.prior_calls = prior
                st.session_state.is_followup = n_prior > 0
                st.session_state.brief_generated = False
                st.session_state.brief_data = None
                st.session_state.generate_brief = False
                st.session_state.view = "rep_brief"
                st.rerun()
