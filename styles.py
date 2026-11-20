# ==============================================================================
# 1. PAGE CONFIGURATION & ENTERPRISE DESIGN SYSTEM (CSS)
# ==============================================================================
# styles.py
import streamlit as st

def inject_corporate_theme():
# CUSTOM THEME-PROOF STYLING (Light/Dark themes supported perfectly)
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    /* Executive SaaS Header */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 22px 28px;
        border-radius: 14px;
        color: #ffffff;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .app-header h1 {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff !important;
    }
    .app-header p {
        font-size: 13px;
        color: #94a3b8;
        margin: 5px 0 0 0;
    }
    /* Modern KPI Cards */
    .metric-box {
        background-color: var(--background-color);
        padding: 16px 18px;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-left: 5px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        min-height: 110px;
        color: var(--text-color);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 18px -4px rgba(0,0,0,0.08);
    }
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    .guide-box {
        background-color: var(--background-color);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        color: var(--text-color);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
    }
    .warning-box {
        background-color: rgba(245, 159, 0, 0.12);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #f59f00;
        margin-bottom: 15px;
        color: var(--text-color);
    }
    .danger-box {
        background-color: rgba(239, 68, 68, 0.12);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ef4444;
        margin-bottom: 15px;
        color: var(--text-color);
    }
    .success-box {
        background-color: rgba(34, 197, 94, 0.12);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #22c55e;
        margin-bottom: 15px;
        color: var(--text-color);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 18px;
        font-weight: 600;
        font-size: 14px;
    }
    .comparison-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .comp-card {
        background-color: var(--background-color);
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid rgba(148, 163, 184, 0.25);
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .comp-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 18px -4px rgba(0,0,0,0.08);
    }
    .comp-card.hero {
        border: 2px solid #2563eb;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.12);
        position: relative;
        background-color: rgba(37, 99, 235, 0.015);
    }
    .hero-badge {
        position: absolute;
        top: -12px;
        right: 22px;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white !important;
        font-size: 10px;
        font-weight: 800;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
    }
    .card-header {
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        padding-bottom: 12px;
        margin-bottom: 15px;
    }
    .card-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.01em;
    }
    .card-header .dims {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 14px;
    }
    .metric-row .label {
        color: #64748b;
    }
    .metric-row .val {
        font-weight: 700;
    }
    .val.win {
        color: #22c55e !important;
    }
    .val.danger {
        color: #ef4444 !important;
    }
    .val.saving {
        background-color: rgba(34, 197, 94, 0.15);
        color: #22c55e !important;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)