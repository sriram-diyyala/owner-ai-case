import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Owner AI — Sales Intelligence",
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

inject_styles()

view = st.session_state.view

if view == "home":
    show_home(calls, patterns, reps, restaurants)
else:
    shell_header(view)
    if view == "manager":
        show_manager(calls, patterns, reps)
    elif view == "rep_detail":
        show_rep_detail(calls, reps)
    elif view == "rep_search":
        show_rep_search(restaurants)
    elif view == "rep_brief":
        if not st.session_state.selected_restaurant:
            st.session_state.view = "rep_search"
            st.rerun()
        else:
            show_rep_brief(calls, patterns)
