import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Owner Sales Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from data import load_data
from styles import inject_styles, shell_header
from views.home import show_home
from views.manager import show_manager
from views.rep_detail import show_rep_detail
from views.rep_search import show_rep_search
from views.rep_brief import show_rep_brief

calls, patterns, reps, restaurants = load_data()

if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_rep" not in st.session_state:
    st.session_state.selected_rep = None
if "selected_restaurant" not in st.session_state:
    st.session_state.selected_restaurant = None
if "brief_generated" not in st.session_state:
    st.session_state.brief_generated = False
if "brief_data" not in st.session_state:
    st.session_state.brief_data = None
if "generate_brief" not in st.session_state:
    st.session_state.generate_brief = False
if "is_new_restaurant" not in st.session_state:
    st.session_state.is_new_restaurant = False
if "is_followup" not in st.session_state:
    st.session_state.is_followup = False
if "prior_calls" not in st.session_state:
    st.session_state.prior_calls = []
if "similar_restaurants" not in st.session_state:
    st.session_state.similar_restaurants = []
if "show_new_restaurant_form" not in st.session_state:
    st.session_state.show_new_restaurant_form = False
if "rep_filter" not in st.session_state:
    st.session_state.rep_filter = "all"

inject_styles()

view = st.session_state.view

# Reset rep deep-dive filter when leaving the manager page
if st.session_state.get("_prev_view") == "manager" and view != "manager":
    st.session_state.rep_filter = "all"
st.session_state._prev_view = view

if view == "home":
    show_home(calls, patterns, reps, restaurants)
else:
    shell_header(view)
    if view == "manager":
        show_manager(calls, patterns, reps)
    elif view == "rep_detail":
        show_rep_detail(calls, reps)
    elif view == "rep_search":
        show_rep_search(calls, restaurants)
    elif view == "rep_brief":
        if not st.session_state.selected_restaurant:
            st.session_state.view = "rep_search"
            st.rerun()
        else:
            show_rep_brief(calls, patterns)
