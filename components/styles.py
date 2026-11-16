import streamlit as st

def inject_bsh_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700;800&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
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
    </style>
    """, unsafe_allow_html=True)
