import streamlit as st
import pandas as pd


def show_rep_search(restaurants):
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Rep view</div>
        <div class="page-title">Get ready for your next call.</div>
        <div class="page-sub">Search a restaurant, choose call type, generate a brief grounded in analyzed calls.</div>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input(
        "Search",
        placeholder="🔍  Search by restaurant name, city, or cuisine…",
        label_visibility="collapsed",
    )

    filtered = restaurants.copy()
    if search and len(search) >= 2:
        q = search.lower()
        filtered = filtered[
            filtered["name"].str.lower().str.contains(q, na=False) |
            filtered["city"].str.lower().str.contains(q, na=False) |
            filtered["cuisine_type"].str.lower().str.contains(q, na=False)
        ]

    st.caption(f"{len(filtered)} restaurant{'s' if len(filtered) != 1 else ''} found")

    if len(filtered) == 0:
        st.markdown("""
        <div style="text-align:center; padding: 64px; border: 1px dashed var(--border); border-radius: var(--radius); color: var(--muted-foreground); font-size: 14px;">
            No matches. Try a city or cuisine.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Restaurant cards in 3-column grid
    cols = st.columns(3)
    for i, (_, r) in enumerate(filtered.head(30).iterrows()):
        with cols[i % 3]:
            has_website = pd.notna(r.get("website_url", "")) and str(r.get("website_url", "")).strip()
            online_tag_class = "success" if has_website else "warning"
            online_label = "Has website" if has_website else "No website"
            num_loc = int(r.get("num_locations", 1))

            st.markdown(f"""
            <div class="restaurant-card">
                <div class="restaurant-card-header">
                    <div>
                        <div class="restaurant-name">{r['name']}</div>
                        <div class="restaurant-location">📍 {r['city']}, {r['state']}</div>
                    </div>
                    <div class="restaurant-rating">
                        ★ {r.get('cuisine_type','')[:3].upper()}
                    </div>
                </div>
                <div class="tags">
                    <span class="tag">{r.get('cuisine_type','')}</span>
                    <span class="tag">{r.get('business_type','').replace('_',' ').title()}</span>
                    <span class="tag {online_tag_class}">{online_label}</span>
                    <span class="tag">{num_loc} location{'s' if num_loc != 1 else ''}</span>
                </div>
                <div class="restaurant-cta">Generate brief →</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Select", key=f"rest_{i}_{r['name'][:10]}", use_container_width=True, type="secondary"):
                st.session_state.selected_restaurant = r.to_dict()
                st.session_state.view = "rep_brief"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)