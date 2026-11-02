import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import base64

# Set up page layout and appearance
st.set_page_config(
    page_title="Packaging Density & Box Recommender Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern corporate look
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0056b3;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        min-height: 110px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    .guide-box {
        background-color: #e9ecef;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ced4da;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Packaging Density & Interactive Box Recommender")
st.markdown("### Grid-Based Product Accommodation & Operator Safety Tool")
st.write("This tool calculates the maximum number of parts that can fit inside our company's standard boxes with partition separators.")

# Bulletproof database reader
@st.cache_data
def load_database():
    possible_files = ['1.xlsx', '1.xlsx_Sheet1_Sheet1.csv']
    df = None
    loaded_file = None
    
    for file in possible_files:
        if os.path.exists(file):
            loaded_file = file
            if file.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            break
            
    if df is None:
        raise FileNotFoundError("Could not find box database file.")
        
    df = df.dropna(subset=['BoxSize']).copy()
    
    # Safely convert key numeric columns
    numeric_cols = [
        'Ext. Length [mm]', 'Ext.Width [mm]', 'Ext. Height [mm]',
        'Int.Length [mm]', 'Width [mm]', 'Height [mm]', 'Max. Load [kg]'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Standardize PL as Box Contract Price in Euros (€)
    df['Box Price (€)'] = pd.to_numeric(df['PL'], errors='coerce').fillna(0.0)
    return df, loaded_file

try:
    df_inventory, filename_loaded = load_database()
    st.success(f"Connected to Cardboard Database: `{filename_loaded}`")
except Exception as e:
    st.error("⚠️ Database connection failed!")
    st.info("Please place your cardboard database file named `1.xlsx` in this folder:")
    st.code(os.getcwd())
    st.stop()


# --- SIDEBAR: OPERATOR INPUTS ---
st.sidebar.header("⚙️ Product Specifications")

# Product Physical Dimensions
st.sidebar.markdown("#### Part Dimensions (mm)")
prod_l = st.sidebar.number_input("Part Length (mm)", min_value=1, value=170, step=1, help="Horizontal flat length (e.g. ear-to-ear span)")
prod_w = st.sidebar.number_input("Part Width (mm)", min_value=1, val
