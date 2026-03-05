import streamlit as st

# ─────────────────────────────────────────────
# CALL THIS ONCE at the top of app.py:
#   from styles import inject_all_styles
#   inject_all_styles()
# ─────────────────────────────────────────────
def render_main_title():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    </style>
    <div style="text-align: center; margin-bottom: 24px;">
        <div style="
            display: inline-block;
            font-family: 'Share Tech Mono', monospace;
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #2cb86d, #b2f0d9, #2cb86d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 4px;
            text-transform: uppercase;
            filter: drop-shadow(0 0 8px rgba(44,184,109,0.7)) drop-shadow(0 0 20px rgba(44,184,109,0.4));
        ">⬡ Inventory Management System</div>
        <div style="
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            background: linear-gradient(90deg, #4dba80, #b2f0d9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 3px;
            margin-top: 6px;
            opacity: 0.8;
        ">REALTIME · CONNECTED · LIVE</div>
    </div>
    """, unsafe_allow_html=True)
def inject_all_styles():
    _base_theme()
    _title_styles()
    _sidebar_heading_styles()
    _button_styles()
    _table_area_styles()

def render_sidebar_group_label(text: str):
    st.sidebar.markdown(f"""
    <div style="
        font-family: 'Share Tech Mono', monospace;
        font-size: 16px;
        letter-spacing: 5px;
        color: #4dba80;
        text-transform: uppercase;
        opacity: 0.6;
        padding-left: 4px;
        margin-top: 14px;
        margin-bottom: 4px;
        border-left: 2px solid #2cb86d;
        padding-left: 8px;
    ">{text}</div>
    """, unsafe_allow_html=True)
# ─────────────────────────────────────────────
# 1. BASE THEME
# ─────────────────────────────────────────────
def _base_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600;800&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Exo 2', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 2. TITLE — centered, neon green glow
# ─────────────────────────────────────────────
def _title_styles():
    st.markdown("""
    <style>
    /* Center the main page title */
    [data-testid="stAppViewContainer"] > section > div > div > div > h1 {
        text-align: center;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 2.4rem !important;
        color: #b2f0d9 !important;
        text-shadow: 0 0 12px #2cb86d, 0 0 28px rgba(44,184,109,0.5);
        letter-spacing: 3px;
        padding-bottom: 10px;
        border-bottom: 1px solid #2cb86d33;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. SIDEBAR EXPANDER HEADINGS
#    Each expander gets a colored label injected
#    via the summary element CSS
# ─────────────────────────────────────────────
def _sidebar_heading_styles():
    st.markdown("""
    <style>
    /* All sidebar expander headers */
    [data-testid="stSidebar"] details summary p {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        letter-spacing: 2px !important;
        color: #b2f0d9 !important;
        text-shadow: 0 0 6px #2cb86d;
        text-transform: uppercase;
    }

    /* Expander border glow */
    [data-testid="stSidebar"] details {
        border: 1px solid #2cb86d33 !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        background: rgba(44,184,109,0.03) !important;
        transition: border 0.2s ease;
    }
    [data-testid="stSidebar"] details[open] {
        border: 1px solid #2cb86d88 !important;
        box-shadow: 0 0 12px rgba(44,184,109,0.15);
    }

    /* Sidebar section label — call render_sidebar_label() to use */
    .sidebar-section-label {
        font-family: 'Share Tech Mono', monospace;
        font-size: 10px;
        letter-spacing: 2.5px;
        color: #4dba80;
        text-transform: uppercase;
        opacity: 0.7;
        margin-bottom: 8px;
        padding-left: 2px;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 4. BUTTONS
# ─────────────────────────────────────────────
def _button_styles():
    st.markdown("""
    <style>

    /* ── Default (secondary) buttons ── */
    [data-testid="stButton"] button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #2cb86d88 !important;
        color: #b2f0d9 !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
        transition: all 0.2s ease !important;
        padding: 6px 16px !important;
    }
    [data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #2cb86d !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(44,184,109,0.4) !important;
        background: rgba(44,184,109,0.08) !important;
    }

    /* ── Primary buttons ── */
    [data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(145deg, #2cb86d, #03361b) !important;
        border: 1px solid #2cb86d !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
        box-shadow: 0 0 10px rgba(44,184,109,0.3) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 0 18px rgba(44,184,109,0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Danger / delete buttons — red variant ── */
    /* Usage: wrap in st.container() with key then target via nth-child,
       OR just use type="primary" for delete and rely on context */

    /* ── Download button ── */
    [data-testid="stDownloadButton"] button {
        background: transparent !important;
        border: 1px solid #2cb86d !important;
        color: #b2f0d9 !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: rgba(44,184,109,0.1) !important;
        box-shadow: 0 0 12px rgba(44,184,109,0.4) !important;
    }

    /* ── Refresh Table button — right aligned ── */
    div[data-testid="stButton"]:has(button[kind="secondary"]) {
        display: flex;
        justify-content: flex-end;
    }

    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 5. TABLE AREA LABEL
# ─────────────────────────────────────────────
def _table_area_styles():
    st.markdown("""
    <style>
    /* Section heading above table */
    .table-section-heading {
        font-family: 'Share Tech Mono', monospace;
        font-size: 16px;
        letter-spacing: 2.5px;
        color: #4dba80;
        text-transform: uppercase;
        border-left: 3px solid #2cb86d;
        padding-left: 10px;
        margin-bottom: 6px;
        text-shadow: 0 0 6px rgba(44,184,109,0.4);
    }
    </style>
    """, unsafe_allow_html=True)
    st.divider()


# ─────────────────────────────────────────────
# HELPER — renders a styled section label
# Usage: render_section_label("Product Table")
# ─────────────────────────────────────────────
def render_section_label(text: str):
    st.markdown(f'<div class="table-section-heading">{text}</div>', unsafe_allow_html=True)