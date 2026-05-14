import html as _html
import streamlit as st
import pandas as pd
from data import get_restaurant_call_history


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

    # Fix 1: white header bar matching manager page style
    st.markdown("""
    <div class="rep-header-marker">
        <div class="page-title">Get ready for your next call.</div>
        <div class="page-sub">Search a restaurant, choose call type, generate a brief grounded in analyzed calls.</div>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input(
        "Search",
        placeholder="🔍  Search by restaurant name, city, or cuisine…",
        label_visibility="collapsed",
    )

    # New restaurant form replaces all other content when active
    if st.session_state.show_new_restaurant_form:
        if st.button("← Back to search", key="back_from_new_rest"):
            st.session_state.show_new_restaurant_form = False
            st.rerun()
        _new_restaurant_form(restaurants)
        return

    # Text search
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
            # Fix 2: inline CTA when fewer than 3 results
            if len(filtered) < 3:
                _not_found_cta()
        return

    category = st.session_state.search_category

    # Empty state — no search, no category selected
    if category is None:
        _render_category_cards()
        return

    # Category selected — back link + filtered content
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


# Fix 2: contextual CTA — only shown inline when search returns <3 results
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

    # Fix 2: show validation warning at top, before the form renders
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
    """Render a list of items as toggle-button chips, 5 per row."""
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
    """2×2 grid of category entry points shown on empty state."""
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
    """Restaurant card grid with call history badges."""
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

    # Fix 2: legend above the grid
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
            # Pre-compute all values — no inline expressions inside the HTML string
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

            # Build the complete card HTML as a single string, then render once
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
