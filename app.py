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
prod_w = st.sidebar.number_input("Part Width (mm)", min_value=1, value=110, step=1, help="Horizontal flat width (e.g. base depth)")
prod_h = st.sidebar.number_input("Part Height (mm)", min_value=1, value=40, step=1, help="Vertical thickness (how high it stands when flat)")

# Product Weight
st.sidebar.markdown("#### Part Weight (kg)")
prod_wt = st.sidebar.number_input("Weight per Part (kg)", min_value=0.01, value=0.25, step=0.05)

# --- VISUAL INPUT METHOD SELECTOR ---
st.sidebar.markdown("---")
st.sidebar.header("📸 Part Visual Reference")
upload_method = st.sidebar.radio("Select Visual Reference Method:", ["Multi-Angle 2D Photos", "3D CAD Model (.STL)"])

uploaded_top = None
uploaded_front = None
uploaded_side = None
uploaded_stl = None

if upload_method == "Multi-Angle 2D Photos":
    uploaded_top = st.sidebar.file_uploader("Upload TOP View (Length x Width)", type=["png", "jpg", "jpeg"])
    uploaded_front = st.sidebar.file_uploader("Upload FRONT View (Length x Height)", type=["png", "jpg", "jpeg"])
    uploaded_side = st.sidebar.file_uploader("Upload SIDE View (Width x Height)", type=["png", "jpg", "jpeg"])
else:
    uploaded_stl = st.sidebar.file_uploader("Upload 3D CAD File (.STL)", type=["stl"])

st.sidebar.markdown("---")
st.sidebar.header("📏 Divider & Clearance Spacing")

# Margins and Clearances (Directly from manager discussion)
clear_side = st.sidebar.slider("Sides Clearance buffer (mm)", min_value=0, max_value=20, value=2, help="Clearance at the wall edges (lengthwise and widthwise)")
clear_height = st.sidebar.slider("Height Clearance buffer (mm)", min_value=0, max_value=20, value=4, help="Clearance at the top height edge")

sep_xy = st.sidebar.slider("Separator X/Y Thickness (mm)", min_value=0, max_value=10, value=2, help="Thickness of the horizontal dividers")
sep_z = st.sidebar.slider("Separator Z Thickness (mm)", min_value=0, max_value=10, value=4, help="Thickness of the vertical shelf dividers")

# Enforce stable flat orientation
strict_flat = st.sidebar.checkbox("Strict Flat Packing (Highly Recommended)", value=True, help="Force the part to remain flat on its base (height stays at 40 mm) so it does not tip over in transit.")

sort_criteria = st.sidebar.selectbox("Rank Box Options By:", ["Volumetric Efficiency (%)", "Number of Parts per Box", "Box Price (€)"])


# --- RECOMMENDATION SYSTEM MATHEMATICS ---
def calculate_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h):
    if strict_flat:
        orientations = [
            (p_l, p_w, p_h),
            (p_w, p_l, p_h)
        ]
    else:
        orientations = [
            (p_l, p_w, p_h), (p_l, p_h, p_w),
            (p_w, p_l, p_h), (p_w, p_h, p_l),
            (p_h, p_l, p_w), (p_h, p_w, p_l)
        ]
    
    best_qty = 0
    best_config = None
    best_grid_layout = (0, 0, 0)
    
    for px, py, pz in orientations:
        nx = max(0, int((box_int_l - (2 * clear_side) + sep_xy) // (px + sep_xy)))
        ny = max(0, int((box_int_w - (2 * clear_side) + sep_xy) // (py + sep_xy)))
        nz = max(0, int((box_int_h - clear_height + sep_z) // (pz + sep_z)))
        
        total_parts = nx * ny * nz
        if total_parts > best_qty:
            best_qty = total_parts
            best_config = (px, py, pz)
            best_grid_layout = (nx, ny, nz)
            
    return best_qty, best_config, best_grid_layout


# Helper to identify the physical placement style
def determine_placement_style(p_l, p_w, p_h, oz):
    dims = sorted([p_l, p_w, p_h]) # [40, 110, 170]
    if int(oz) == int(dims[0]):
        return "🟢 FLAT / HORIZONTAL (Resting on wide base, most stable)"
    elif int(oz) == int(dims[1]):
        return "⚠️ STANDING ON SIDE / EDGE"
    else:
        return "🚨 STANDING VERTICAL / ON END (Unstable, prone to tipping)"


# Dynamic empty weight estimation of the FEFCO 0201 flat sheets
def estimate_box_weight(ext_l, ext_w, ext_h, quality):
    if pd.isna(ext_l) or pd.isna(ext_w) or pd.isna(ext_h):
        return 0.15
    sheet_l_m = (2 * (ext_l + ext_w) + 40) / 1000.0
    sheet_w_m = (ext_h + ext_w) / 1000.0
    flat_area = sheet_l_m * sheet_w_m
    
    grammage_map = {'1.20B': 0.40, '1.20C': 0.45, '2.30EB': 0.70, '2.30BC': 0.85}
    g = grammage_map.get(str(quality).strip(), 0.50)
    return flat_area * g


# --- EXECUTE CALCULATION ENGINE ---
results = []
single_part_vol = prod_l * prod_w * prod_h

for idx, row in df_inventory.iterrows():
    box_int_l = row['Int.Length [mm]']
    box_int_w = row['Width [mm]']
    box_int_h = row['Height [mm]']
    ext_l = row['Ext. Length [mm]']
    ext_w = row['Ext.Width [mm]']
    ext_h = row['Ext. Height [mm]']
    
    if pd.isna(box_int_l) or pd.isna(box_int_w) or pd.isna(box_int_h):
       
