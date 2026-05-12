import streamlit as st


def inject_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] { display: none; }
.stDeployButton { display: none; }

:root {
    --background: #f4f7f5;
    --foreground: #0a0f0d;
    --card: #ffffff;
    --primary: #1a6b3c;
    --primary-light: #22883f;
    --primary-foreground: #ffffff;
    --secondary: #e8f5ed;
    --secondary-foreground: #1a6b3c;
    --muted-foreground: #5a6e63;
    --success: #1a6b3c;
    --warning: #b07800;
    --warning-bg: #fff8e8;
    --destructive: #c53030;
    --destructive-bg: #fdecea;
    --border: #d4e4da;
    --border-light: #e5edea;
    --radius: 0.625rem;
    --gradient-hero: linear-gradient(135deg, #0f3d20 0%, #1a6b3c 50%, #22883f 100%);
    --shadow-elevated: 0 10px 30px -12px rgba(26,107,60,0.25);
    --shadow-card: 0 1px 2px rgba(10,15,13,0.06), 0 1px 3px rgba(10,15,13,0.04);
}

html, body, [class*="css"] {
    font-family: 'Inter', ui-sans-serif, system-ui, sans-serif !important;
    background-color: var(--background) !important;
    color: var(--foreground) !important;
    -webkit-font-smoothing: antialiased;
}

html, body { overflow-x: hidden !important; max-width: 100% !important; }
h1, h2, h3, h4 { letter-spacing: -0.02em !important; }

section[data-testid="stSidebar"] { display: none; }

.main { padding: 0 !important; }

.main .block-container,
[data-testid="stMainBlockContainer"] {
    padding: 2rem 3rem !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

.main .block-container > div:first-child {
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
}

section.main > div > div > div[data-testid="stVerticalBlock"],
section[data-testid="stMain"] {
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
}

/* Page content wrapper */
.page-wrap {
    padding: 32px 5%;
}

/* Nav row wrapper — empty marker div, collapse it */
.nav-row-wrap, .nav-row-inner { display: none; }

/* Nav header — target the Streamlit column block immediately after the nav marker */
[data-testid="stMarkdownContainer"]:has(.nav-row-wrap) + [data-testid="stHorizontalBlock"] {
    background: var(--card) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 8px 5% !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 100 !important;
    align-items: center !important;
}

/* Logo button — first column in the nav block, transparent/no-border */
[data-testid="stMarkdownContainer"]:has(.nav-row-wrap) + [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child div.stButton > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 4px 0 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    color: var(--foreground) !important;
    text-align: left !important;
}
[data-testid="stMarkdownContainer"]:has(.nav-row-wrap) + [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child div.stButton > button:hover {
    background: transparent !important;
    border: none !important;
    color: var(--primary) !important;
}

/* Hero */
.hero-section { background: var(--gradient-hero); color: var(--primary-foreground); }
.hero-inner { max-width: 1400px; margin: 0 auto; padding: 64px 40px 120px 40px; }
.hero-eyebrow {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.12em; opacity: 0.75; margin-bottom: 16px;
}
.hero-headline {
    font-size: 56px; font-weight: 700; line-height: 1.05;
    letter-spacing: -0.03em; max-width: 750px; margin-bottom: 20px;
}
.hero-sub { font-size: 18px; opacity: 0.85; max-width: 560px; line-height: 1.6; }

.role-cards-grid {
    max-width: 1100px; margin: -72px auto 0 auto; padding: 0 40px;
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
}
.role-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 32px; box-shadow: var(--shadow-elevated);
}
.role-card-label {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--secondary); color: var(--secondary-foreground);
    border-radius: 999px; padding: 4px 12px; font-size: 12px; font-weight: 500;
    margin-bottom: 20px;
}
.role-card-title {
    font-size: 24px; font-weight: 700; color: var(--foreground);
    margin-bottom: 12px; letter-spacing: -0.02em;
}
.role-card-body { font-size: 14px; color: var(--muted-foreground); line-height: 1.6; margin-bottom: 24px; }

.stats-bar { max-width: 1100px; margin: 32px auto 64px auto; padding: 0 40px; }
.stats-bar-inner {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 32px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px;
}
.stat-value {
    font-family: 'JetBrains Mono', monospace; font-size: 32px; font-weight: 600;
    letter-spacing: -0.02em; color: var(--foreground);
}
.stat-label { font-size: 14px; color: var(--muted-foreground); margin-top: 4px; }

.page-eyebrow {
    font-size: 11px; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.12em; color: var(--muted-foreground); margin-bottom: 4px;
}
.page-title { font-size: 32px; font-weight: 700; color: var(--foreground); letter-spacing: -0.02em; }
.page-sub { font-size: 14px; color: var(--muted-foreground); margin-top: 4px; }
.section-title { font-size: 18px; font-weight: 600; }
.section-sub { font-size: 14px; color: var(--muted-foreground); margin-top: 2px; }

.metric-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-card);
}
.metric-label {
    font-size: 11px; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--muted-foreground); margin-bottom: 10px;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 600;
    color: var(--foreground); letter-spacing: -0.02em;
}
.metric-delta {
    display: inline-block; font-size: 11px; font-weight: 600;
    padding: 2px 8px; border-radius: 999px; margin-left: 8px;
    background: var(--secondary); color: var(--success);
}
.metric-sub { font-size: 12px; color: var(--muted-foreground); margin-top: 4px; }

/* Metric info tooltip */
.metric-info {
    display: inline-block;
    position: relative;
    cursor: help;
    font-size: 11px;
    color: var(--muted-foreground);
    opacity: 0.55;
    margin-left: 5px;
    vertical-align: middle;
    line-height: 1;
}
.metric-info::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: #1a1f1c;
    color: #ffffff;
    font-size: 12px;
    font-weight: 400;
    text-transform: none;
    letter-spacing: 0;
    padding: 8px 12px;
    border-radius: 7px;
    width: 250px;
    z-index: 9999;
    text-align: left;
    line-height: 1.5;
    white-space: normal;
    box-shadow: 0 4px 16px rgba(0,0,0,0.22);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s ease;
}
.metric-info:hover::after { opacity: 1; }

.action-banner {
    background: var(--gradient-hero); color: var(--primary-foreground);
    border-radius: 14px; padding: 24px 28px; box-shadow: var(--shadow-elevated);
}
.banner-eyebrow {
    display: flex; align-items: center; gap: 8px;
    font-size: 11px; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.12em; opacity: 0.75; margin-bottom: 10px;
}
.banner-icon { background: rgba(255,255,255,0.15); border-radius: 6px; padding: 4px 6px; font-size: 12px; }
.banner-headline { font-size: 22px; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.02em; }
.banner-detail { font-size: 14px; opacity: 0.85; line-height: 1.55; margin-bottom: 18px; max-width: 720px; }
.banner-pills { display: flex; gap: 10px; flex-wrap: wrap; }
.banner-pill {
    border: 1px solid rgba(255,255,255,0.25); background: rgba(255,255,255,0.12);
    border-radius: 999px; padding: 4px 12px; font-size: 12px; font-weight: 500;
}

.insight-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card);
    height: 100%;
}
.insight-eyebrow {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--primary); margin-bottom: 10px;
}
.insight-title { font-size: 16px; font-weight: 700; line-height: 1.3; margin-bottom: 10px; }
.insight-detail { font-size: 14px; color: var(--muted-foreground); line-height: 1.55; margin-bottom: 10px; }
.insight-evidence { font-size: 12px; color: var(--muted-foreground); opacity: 0.75; font-family: 'JetBrains Mono', monospace; }

.list-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); box-shadow: var(--shadow-card); overflow: hidden;
}
.list-card-row {
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
    padding: 14px 20px; border-top: 1px solid var(--border-light);
}
.list-card-row:first-child { border-top: none; }
.list-row-main { font-size: 14px; font-weight: 500; }
.list-row-sub { font-size: 12px; color: var(--muted-foreground); margin-top: 2px; }
.lift-badge {
    background: var(--secondary); color: var(--success);
    border-radius: 999px; padding: 3px 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; white-space: nowrap;
}

.obj-table {
    width: 100%; background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); box-shadow: var(--shadow-card);
    border-collapse: separate; border-spacing: 0; overflow: hidden;
}
.obj-table thead tr { background: var(--secondary); }
.obj-table th {
    padding: 10px 18px; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--secondary-foreground); text-align: left;
}
.obj-table th.right { text-align: right; }
.obj-table td { padding: 14px 18px; font-size: 13px; border-top: 1px solid var(--border-light); vertical-align: top; }
.obj-table td.right { text-align: right; }
.obj-main { font-weight: 500; }
.obj-freq { font-size: 11px; color: var(--muted-foreground); margin-top: 2px; }
.obj-response { color: var(--muted-foreground); font-style: italic; }
.obj-rep { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--foreground); }
.win-rate { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; }
.win-rate.good { color: var(--success); }
.win-rate.bad { color: var(--destructive); }
.win-rate.neutral { color: var(--muted-foreground); }

.badge {
    display: inline-flex; align-items: center; gap: 4px;
    border-radius: 999px; padding: 3px 10px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; white-space: nowrap;
}
.badge-high { background: var(--destructive-bg); color: var(--destructive); }
.badge-medium { background: var(--warning-bg); color: var(--warning); }
.badge-low { background: var(--secondary); color: var(--success); }

.coach-card { border-radius: var(--radius); border: 1px solid; padding: 22px; height: 100%; display: flex; flex-direction: column; }
.coach-card.success { border-color: rgba(26,107,60,0.3); background: rgba(26,107,60,0.04); }
.coach-card.warning { border-color: rgba(176,120,0,0.4); background: rgba(176,120,0,0.04); }
.coach-card.primary { border-color: rgba(26,107,60,0.25); background: rgba(26,107,60,0.06); }
.coach-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.coach-card-icon { border-radius: 6px; padding: 4px 8px; font-size: 14px; }
.coach-card-icon.success { background: rgba(26,107,60,0.12); color: var(--success); }
.coach-card-icon.warning { background: rgba(176,120,0,0.15); color: var(--warning); }
.coach-card-icon.primary { background: rgba(26,107,60,0.12); color: var(--primary); }
.coach-card-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-foreground); }
.coach-card-body { font-size: 14px; line-height: 1.6; }

.rep-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card); height: 100%;
}
.rep-card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 18px; }
.rep-card-name { font-size: 15px; font-weight: 700; }
.rep-card-meta { font-size: 12px; color: var(--muted-foreground); margin-top: 2px; }
.mini-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 18px; }
.mini-stat { background: var(--secondary); border-radius: 8px; padding: 10px; text-align: center; }
.mini-stat-value { font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 700; }
.mini-stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-foreground); margin-top: 2px; }
.rep-card-gap { font-size: 12px; color: var(--muted-foreground); line-height: 1.5; margin-bottom: 18px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* Performance cards — top/bottom rep summaries on dashboard */
.perf-card { border-radius: var(--radius); border: 1px solid; padding: 18px; height: 100%; display: flex; flex-direction: column; }
.perf-card.success { border-color: rgba(26,107,60,0.3); background: rgba(26,107,60,0.04); }
.perf-card.warning { border-color: rgba(176,120,0,0.4); background: rgba(176,120,0,0.04); }
.perf-card-name { font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.perf-card-stats { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.perf-stat {
    background: var(--secondary); color: var(--secondary-foreground);
    border-radius: 999px; padding: 2px 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;
}
.perf-card-text { font-size: 13px; color: var(--muted-foreground); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

/* Equal-height card rows — stretch columns to match tallest card */
[data-testid="stHorizontalBlock"]:has(.perf-card),
[data-testid="stHorizontalBlock"]:has(.coach-card) {
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"]:has(.perf-card) > [data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.coach-card) > [data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stHorizontalBlock"]:has(.perf-card) > [data-testid="column"] > div,
[data-testid="stHorizontalBlock"]:has(.coach-card) > [data-testid="column"] > div {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stHorizontalBlock"]:has(.perf-card) .perf-card,
[data-testid="stHorizontalBlock"]:has(.coach-card) .coach-card {
    flex: 1 !important;
}

/* Category cards — rep search empty state */
.category-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card); margin-bottom: 12px;
}
.category-card-icon { font-size: 24px; margin-bottom: 12px; }
.category-card-title { font-size: 16px; font-weight: 700; margin-bottom: 8px; color: var(--foreground); }
.category-card-body { font-size: 13px; color: var(--muted-foreground); line-height: 1.55; margin-bottom: 16px; }

.restaurant-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card); height: 100%;
}
.restaurant-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 16px; }
.restaurant-name { font-size: 15px; font-weight: 700; }
.restaurant-location { font-size: 12px; color: var(--muted-foreground); margin-top: 4px; }
.restaurant-rating { background: var(--secondary); color: var(--secondary-foreground); border-radius: 6px; padding: 4px 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 18px; }
.tag { border-radius: 999px; border: 1px solid var(--border); background: var(--card); color: var(--muted-foreground); padding: 3px 10px; font-size: 11px; font-weight: 500; }
.tag.success { border-color: rgba(26,107,60,0.3); background: var(--secondary); color: var(--success); }
.tag.warning { border-color: rgba(176,120,0,0.4); background: var(--warning-bg); color: var(--warning); }

.brief-one-thing { background: var(--gradient-hero); color: var(--primary-foreground); border-radius: 14px; padding: 24px 28px; box-shadow: var(--shadow-elevated); }
.brief-one-thing-eyebrow { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.12em; opacity: 0.75; margin-bottom: 14px; }
.brief-one-thing-text { font-size: 22px; font-weight: 700; line-height: 1.35; letter-spacing: -0.02em; }
.opener-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card); height: 100%; }
.opener-label { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-foreground); margin-bottom: 14px; }
.opener-icon { background: var(--secondary); color: var(--secondary-foreground); border-radius: 6px; padding: 4px 8px; font-size: 12px; }
.opener-script { font-size: 15px; line-height: 1.6; }
.angle-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card); }
.angle-headline { font-size: 18px; font-weight: 700; margin: 6px 0; }
.angle-evidence { font-size: 12px; color: var(--muted-foreground); margin-top: 4px; font-family: 'JetBrains Mono', monospace; }
.brief-section-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-card); height: 100%; }
.brief-section-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-foreground); margin-bottom: 14px; }
.pain-item { display: flex; gap: 10px; padding: 8px 0; font-size: 14px; }
.pain-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--destructive); margin-top: 7px; flex-shrink: 0; }
.discovery-item { display: flex; gap: 10px; padding: 8px 0; font-size: 14px; }
.discovery-num { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--muted-foreground); padding-top: 2px; flex-shrink: 0; }
.objection-row { display: grid; grid-template-columns: 220px 1fr; gap: 16px; padding: 14px 0; border-top: 1px solid var(--border-light); font-size: 14px; }
.objection-row:first-child { border-top: none; padding-top: 0; }
.objection-q { font-weight: 500; }
.objection-a { color: var(--muted-foreground); }

/* Streamlit overrides */
.stTabs [data-baseweb="tab-list"] { gap: 0; background: transparent; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 0 !important;
    padding: 10px 20px !important; font-size: 14px !important; font-weight: 500 !important;
    color: var(--muted-foreground) !important; border: none !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
    background: transparent !important;
}

/* Manager page header bar — white strip between nav and tab content */
[data-testid="stMarkdownContainer"]:has(.mgr-header-marker) {
    background: var(--card) !important;
    padding: 24px 5% 16px 5% !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
[data-testid="stMarkdownContainer"]:has(.mgr-header-marker) + [data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--card) !important;
    padding-left: 5% !important;
    padding-right: 5% !important;
    box-shadow: 0 1px 3px rgba(10,15,13,0.06) !important;
}

/* Rep page header bar */
[data-testid="stMarkdownContainer"]:has(.rep-header-marker) {
    background: var(--card) !important;
    padding: 24px 5% !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    border-bottom: 1px solid var(--border) !important;
}

div.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 14px !important;
}
div.stButton > button[kind="primary"] {
    background: var(--primary) !important; border-color: var(--primary) !important; color: white !important;
}
div.stButton > button[kind="primary"]:hover {
    background: var(--primary-light) !important; border-color: var(--primary-light) !important;
}
div.stButton > button[kind="secondary"] {
    background: var(--card) !important; border-color: var(--border) !important; color: var(--foreground) !important;
}


.stTextInput > div > div > input { border-color: var(--border) !important; border-radius: 8px !important; background: var(--card) !important; font-family: 'Inter', sans-serif !important; font-size: 15px !important; }
.stTextArea > div > div > textarea { border-color: var(--border) !important; border-radius: 8px !important; background: var(--card) !important; font-family: 'Inter', sans-serif !important; }
[data-testid="metric-container"] { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; box-shadow: var(--shadow-card); }
.stDataFrame { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
</style>
""", unsafe_allow_html=True)


def shell_header(active_view):
    """Persistent nav header — logo (clickable) on left, Manager/Rep on right."""
    st.markdown('<div class="nav-row-wrap"><div class="nav-row-inner">', unsafe_allow_html=True)

    col_logo, col_spacer, col_mgr, col_rep = st.columns([5, 4, 1.5, 1.5])

    with col_logo:
        if st.button("✦  Owner Sales Intelligence",
                     key="logo_home",
                     type="secondary",
                     use_container_width=False):
            st.session_state.view = "home"
            st.rerun()

    with col_mgr:
        is_mgr = active_view in ["manager", "rep_detail"]
        if st.button("Analyze", key="nav_manager", use_container_width=True,
                     type="primary" if is_mgr else "secondary"):
            st.session_state.view = "manager"
            st.rerun()

    with col_rep:
        is_rep = active_view in ["rep_search", "rep_brief"]
        if st.button("Prep", key="nav_rep", use_container_width=True,
                     type="primary" if is_rep else "secondary"):
            st.session_state.view = "rep_search"
            st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)