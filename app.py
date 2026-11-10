import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import base64
import plotly.graph_objects as go
import itertools

# ==============================================================================
# 1. PAGE CONFIGURATION & ENTERPRISE DESIGN SYSTEM (CSS)
# ==============================================================================
st.set_page_config(
    page_title="Packaging Density & Box Recommender Tool",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme-Proof Styling: Uses Streamlit CSS variables to support Light and Dark themes perfectly
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

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

    /* Filter Bar Container */
    .filter-panel {
        background-color: var(--background-color);
        padding: 14px 18px;
        border-radius: 10px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        margin-bottom: 14px;
    }

    /* Tab navigation polish */
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
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BULLETPROOF DATABASE READER
# ==============================================================================
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
except Exception as e:
    st.error("⚠️ Database connection failed!")
    st.info("Please place your cardboard database file named `1.xlsx` in this folder:")
    st.code(os.getcwd())
    st.stop()

# ==============================================================================
# 3. SIDEBAR: OPERATOR INPUTS & PACKAGING DIRECTIVE CONTROLS
# ==============================================================================
st.sidebar.header("⚙️ Product Specifications")
uploaded_stl = st.sidebar.file_uploader("Upload 3D CAD File (.STL, .STEP, .STP)", type=["stl", "step", "stp"])
mesh_cad = None  
auto_l, auto_w, auto_h = 170.0, 110.0, 40.0
calculated_weight_kg = 0.25
material_selected = True  

MATERIAL_DENSITIES = {
    "ABS Plastic": 1.04,
    "PLA Plastic": 1.24,
    "Polypropylene (PP)": 0.90,
    "Polycarbonate (PC)": 1.20,
    "Aluminum": 2.70,
    "Mild Steel": 7.85,
    "Stainless Steel": 8.00
}

if uploaded_stl is not None:
    filename = uploaded_stl.name.lower()
    try:
        import trimesh
        uploaded_stl.seek(0)

        if filename.endswith('.step') or filename.endswith('.stp'):
            import cascadio
            mesh_cad = trimesh.load(uploaded_stl, file_type='step')
        else:
            mesh_cad = trimesh.load(uploaded_stl, file_type='stl')

        bounds = mesh_cad.bounding_box.extents
        dims = sorted(bounds)
        auto_h = round(dims[0], 1)
        auto_w = round(dims[1], 1)
        auto_l = round(dims[2], 1)

        cad_volume = max(mesh_cad.volume, 0.001)

        is_cm_scale = auto_l < 50.0
        if is_cm_scale:
            auto_l *= 10.0
            auto_w *= 10.0
            auto_h *= 10.0
            cad_volume *= 1000.0  

        st.sidebar.success(f"📐 Auto-Extracted Dimensions: {auto_l} x {auto_w} x {auto_h} mm")

        st.sidebar.markdown("#### 🪵 Material Weight Extractor")
        selected_material = st.sidebar.selectbox(
            "Select Part Material:",
            options=["Select Material..."] + list(MATERIAL_DENSITIES.keys()),
            index=0,
            help="Choose the physical material of this component to calculate its exact solid weight."
        )

        if selected_material == "Select Material...":
            material_selected = False
        else:
            density = MATERIAL_DENSITIES[selected_material]
            calculated_weight_kg = round(cad_volume * density * 1e-6, 3)
            st.sidebar.info(f"⚖️ Calculated Solid Weight ({selected_material}): **{calculated_weight_kg} kg**")

    except Exception as e_cad:
        st.sidebar.warning(f"Could not auto-extract CAD dimensions: {e_cad}")

st.sidebar.markdown("#### Part Dimensions (mm)")
prod_l = st.sidebar.number_input("Part Length (mm)", min_value=1.0, value=float(auto_l), step=1.0)
prod_w = st.sidebar.number_input("Part Width (mm)", min_value=1.0, value=float(auto_w), step=1.0)
prod_h = st.sidebar.number_input("Part Height (mm)", min_value=1.0, value=float(auto_h), step=1.0)

st.sidebar.markdown("#### Part Weight (kg)")
prod_wt = st.sidebar.number_input("Weight per Part (kg)", min_value=0.01, value=float(calculated_weight_kg), step=0.05)

st.sidebar.markdown("---")
st.sidebar.header("📋 Packaging Directive Constraints")

max_box_weight_limit = st.sidebar.number_input(
    "Max Manual Box Weight Limit (kg)", 
    min_value=5.0, max_value=30.0, value=13.0, step=0.5,
    help="Directive standard: <13 kg for manual operator handling."
)

max_pallet_weight_limit = st.sidebar.number_input(
    "Max Gross Pallet Weight Limit (kg)", 
    min_value=100.0, max_value=1500.0, value=600.0, step=25.0,
    help="Directive standard: <600 kg total gross pallet load."
)

max_pallet_height_limit = st.sidebar.number_input(
    "Max Total Pallet Stack Height (mm)",
    min_value=500.0, max_value=1500.0, value=970.0, step=10.0,
    help="Directive standard: 970 mm total height (including 144 mm wood pallet)."
)

enforce_box_dim_cap = st.sidebar.checkbox(
    "Enforce Directive Max Box Size (600x400x270 mm)", 
    value=False,
    help="If enabled, filters out boxes with external dimensions exceeding 600(L) x 400(W) x 270(H) mm."
)

st.sidebar.markdown("#### 🏭 Production LOT Alignment")
lot_alignment_enabled = st.sidebar.checkbox(
    "Align Box Quantity to LOT Multiples", 
    value=False, 
    help="Caps the packed parts per box to the highest multiple of standard LOT sizes (e.g., 24 or 48)."
)
lot_step = 24
if lot_alignment_enabled:
    lot_step = st.sidebar.selectbox("Select Production LOT Multiplier:", options=[24, 48, 12], index=0)

st.sidebar.markdown("---")
st.sidebar.header("📏 Divider & Clearance Spacing")
clear_side = st.sidebar.slider("Sides Clearance buffer (mm)", min_value=0, max_value=20, value=2)
clear_height = st.sidebar.slider("Height Clearance buffer (mm)", min_value=0, max_value=20, value=4)
sep_xy = st.sidebar.slider("Separator X/Y Thickness (mm)", min_value=0, max_value=10, value=2)
sep_z = st.sidebar.slider("Separator Z Thickness (mm)", min_value=0, max_value=10, value=4)

orientation_rule = st.sidebar.selectbox(
    "Select Packing Orientation:",
    ["Automatic (Highest Quantity)", "Force Flat Packing Only", "Force Standing on Edge", "Force Standing Vertical"]
)

sort_criteria = st.sidebar.selectbox("Rank Box Options By:", ["Volumetric Efficiency (%)", "Number of Parts per Box", "Box Price (€)"])

if not material_selected:
    st.markdown("""
        <div class='app-header'>
            <h1>📦 Packaging Density & Interactive Box Recommender</h1>
            <p>Grid-Based Product Accommodation, Palletization & McKee Structural Stacking Optimizer</p>
        </div>
    """, unsafe_allow_html=True)
    st.warning("⚠️ **Please select a part material** in the sidebar to recommend boxes.")
    st.stop()

# ==============================================================================
# 4. RECOMMENDATION SYSTEM MATHEMATICS
# ==============================================================================
def calculate_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h, rule, enforce_lot=False, lot_multiplier=24):
    dims = sorted([p_l, p_w, p_h])
    h_dim, w_dim, l_dim = dims[0], dims[1], dims[2]
    if rule == "Force Flat Packing Only":
        orientations = [(l_dim, w_dim, h_dim), (w_dim, l_dim, h_dim)]
    elif rule == "Force Standing on Edge":
        orientations = [(l_dim, h_dim, w_dim), (h_dim, l_dim, w_dim)]
    elif rule == "Force Standing Vertical":
        orientations = [(w_dim, h_dim, l_dim), (h_dim, w_dim, l_dim)]
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

    if enforce_lot and best_qty >= lot_multiplier:
        aligned_qty = (best_qty // lot_multiplier) * lot_multiplier
        return aligned_qty, best_config, best_grid_layout, best_qty

    return best_qty, best_config, best_grid_layout, best_qty

def determine_placement_style(p_l, p_w, p_h, oz):
    dims = sorted([p_l, p_w, p_h])
    if int(oz) == int(dims[0]):
        return "🟢 FLAT / HORIZONTAL (Resting on wide base, most stable)"
    elif int(oz) == int(dims[1]):
        return "⚠️ STANDING ON SIDE / EDGE"
    else:
        return "🚨 STANDING VERTICAL / ON END (Unstable, prone to tipping)"

def estimate_box_weight(ext_l, ext_w, ext_h, quality):
    if pd.isna(ext_l) or pd.isna(ext_w) or pd.isna(ext_h):
        return 0.15
    sheet_l_m = (2 * (ext_l + ext_w) + 40) / 1000.0
    sheet_w_m = (ext_h + ext_w) / 1000.0
    flat_area = sheet_l_m * sheet_w_m

    grammage_map = {'1.20B': 0.40, '1.20C': 0.45, '2.30EB': 0.70, '2.30BC': 0.85}
    g = grammage_map.get(str(quality).strip(), 0.50)
    return flat_area * g

# ==============================================================================
# 5. EXECUTE CALCULATION ENGINE
# ==============================================================================
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
        continue

    # Enforce Directive Max Box Dimension Cap if selected (600x400x270 mm)
    if enforce_box_dim_cap:
        ext_dims_sorted = sorted([ext_l, ext_w])
        if ext_dims_sorted[1] > 600.0 or ext_dims_sorted[0] > 400.0 or ext_h > 270.0:
            continue

    parts_count, pack_orient, grid_layout, raw_max_qty = calculate_packing(
        box_int_l, box_int_w, box_int_h, 
        prod_l, prod_w, prod_h,
        rule=orientation_rule,
        enforce_lot=lot_alignment_enabled,
        lot_multiplier=lot_step
    )

    if parts_count == 0:
        continue

    # Calculate Weights
    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row['Quality'])
    total_payload_wt = parts_count * prod_wt
    total_package_weight = total_payload_wt + box_weight

    # Weight threshold check against User Input Limit (default 13 kg)
    dims_footprint = sorted([ext_l, ext_w])
    is_manual_box = (dims_footprint[0] <= 300.0) and (dims_footprint[1] <= 400.0)

    if is_manual_box and total_package_weight > max_box_weight_limit:
        continue

    # Structural Box Load check
    if total_payload_wt > row['Max. Load [kg]']:
        continue

    # Volumes & Air Spaces
    box_internal_vol = box_int_l * box_int_w * box_int_h
    occupied_volume = parts_count * single_part_vol
    vol_efficiency = (occupied_volume / box_internal_vol) * 100
    air_space_percent = 100.0 - vol_efficiency

    # Ergonomic 3-Tier Weight Hierarchy Classification:
    # 🟢 Green (Light): <= 60% of limit
    # 🟠 Orange (Moderate): 60% - 90% of limit
    # 🔴 Light Red (Heavy): > 90% of limit
    weight_pct = (total_package_weight / max_box_weight_limit) * 100.0
    if weight_pct <= 60.0:
        weight_tier = "🟢 Light (≤60%)"
        tier_rank = 1
    elif weight_pct <= 90.0:
        weight_tier = "🟠 Moderate (60%-90%)"
        tier_rank = 2
    else:
        weight_tier = "🔴 Heavy (>90%)"
        tier_rank = 3

    q_class = str(row['Quality']).strip()
    box_spec_label = f"{row['BoxSize']} [{q_class}]"

    results.append({
        "Box ID / Specification": box_spec_label,
        "Raw Box ID": row['BoxSize'],
        "Box Footprint (Ext)": f"{int(ext_l)}x{int(ext_w)} mm",
        "Quality Class": q_class,
        "Internal Dimensions": f"{int(box_int_l)}x{int(box_int_w)}x{int(box_int_h)} mm",
        "Int. Length [mm]": box_int_l,
        "Int. Width [mm]": box_int_w,
        "Int. Height [mm]": box_int_h,
        "Ext. Length [mm]": ext_l,
        "Ext. Width [mm]": ext_w,
        "Ext. Height [mm]": ext_h,
        "Number of Parts per Box": parts_count,
        "Max Geometric Fit": raw_max_qty,
        "Optimal Grid Layout": f"{grid_layout[0]}x{grid_layout[1]}x{grid_layout[2]} (X x Y x Z)",
        "Optimal Orientation": f"{int(pack_orient[0])}x{int(pack_orient[1])}x{int(pack_orient[2])} mm",
        "Total Weight (kg)": round(total_package_weight, 2),
        "Weight Classification": weight_tier,
        "Tier Rank": tier_rank,
        "Remaining Air Space (%)": round(air_space_percent, 1),
        "Box Price (€)": row['Box Price (€)'],
        "Volumetric Efficiency (%)": round(vol_efficiency, 2),
        "_nx": grid_layout[0],
        "_ny": grid_layout[1],
        "_nz": grid_layout[2],
        "_ox": pack_orient[0],
        "_oy": pack_orient[1],
        "_oz": pack_orient[2],
    })

# ==============================================================================
# 6. RENDER RESULTS & EXECUTIVE KPI DASHBOARD
# ==============================================================================
if results:
    res_df = pd.DataFrame(results)

    # Base Ranking Logic
    if sort_criteria == "Volumetric Efficiency (%)":
        sort_by_cols = ["Volumetric Efficiency (%)", "Box Price (€)", "Total Weight (kg)"]
        ascending_rules = [False, True, True]
    elif sort_criteria == "Number of Parts per Box":
        sort_by_cols = ["Number of Parts per Box", "Box Price (€)", "Total Weight (kg)"]
        ascending_rules = [False, True, True]
    else:
        sort_by_cols = ["Box Price (€)", "Number of Parts per Box", "Total Weight (kg)"]
        ascending_rules = [True, False, True]

    sorted_df = res_df.sort_values(by=sort_by_cols, ascending=ascending_rules).reset_index(drop=True)
    best_box = sorted_df.iloc[0]

    # Universal Session State Synchronization across Tabs 1, 2, and 3
    available_boxes = list(sorted_df["Box ID / Specification"].values)
    if "global_selected_box" not in st.session_state or st.session_state["global_selected_box"] not in available_boxes:
        st.session_state["global_selected_box"] = available_boxes[0]

    def sync_from_tab1():
        val = st.session_state["tab1_box_selector"]
        st.session_state["global_selected_box"] = val
        st.session_state["tab2_box_selector"] = val
        st.session_state["tab3_box_selector"] = val

    def sync_from_tab2():
        val = st.session_state["tab2_box_selector"]
        st.session_state["global_selected_box"] = val
        st.session_state["tab1_box_selector"] = val
        st.session_state["tab3_box_selector"] = val

    def sync_from_tab3():
        val = st.session_state["tab3_box_selector"]
        st.session_state["global_selected_box"] = val
        st.session_state["tab1_box_selector"] = val
        st.session_state["tab2_box_selector"] = val

    for key in ["tab1_box_selector", "tab2_box_selector", "tab3_box_selector"]:
        if key not in st.session_state or st.session_state[key] not in available_boxes:
            st.session_state[key] = st.session_state["global_selected_box"]

    # Top Header Safety Badge Layout
    col_title, col_safety_header = st.columns([7, 3])

    with col_title:
        st.markdown("""
            <div class='app-header'>
                <h1>📦 BSH Packaging Density & Box Recommender</h1>
                <p>Grid-Based Product Accommodation, Packaging Directive Compliance & Multi-Pallet Optimizer</p>
            </div>
        """, unsafe_allow_html=True)

    with col_safety_header:
        total_package_weight = best_box["Total Weight (kg)"]
        ext_l = best_box["Ext. Length [mm]"]
        ext_w = best_box["Ext. Width [mm]"]
        dims_footprint = sorted([ext_l, ext_w])
        is_manual_box = (dims_footprint[0] <= 300.0) and (dims_footprint[1] <= 400.0)

        if total_package_weight > max_box_weight_limit:
            if not is_manual_box:
                st.markdown(f"""
                    <div style='background-color:rgba(224, 49, 49, 0.15); border-left:5px solid #e03131; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#e03131; font-size:16px;'>🚨 Forklift Transport Required</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>{total_package_weight} kg (Bypasses manual limit)</span><br>
                        <span style='font-size:11px;'>Box footprint <b>{int(ext_l)}x{int(ext_w)} mm</b> exceeds manual threshold. Weight &gt; {max_box_weight_limit} kg is <b>permitted</b>.</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color:rgba(224, 49, 49, 0.15); border-left:5px solid #e03131; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#e03131; font-size:16px;'>🚨 Overweight Manual Box</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>{total_package_weight} kg (Exceeds {max_box_weight_limit} kg limit)</span><br>
                        <span style='font-size:11px;'>Box footprint <b>{int(ext_l)}x{int(ext_w)} mm</b> is within manual threshold. Prohibited for manual operator packing!</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background-color:rgba(43, 138, 62, 0.15); border-left:5px solid #2b8a3e; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                    <b style='color:#2b8a3e; font-size:16px;'>🟢 Safe Operational Weight</b><br>
                    <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>Safe at {total_package_weight} kg</span><br>
                    <span style='font-size:11px;'>Box footprint <b>{int(ext_l)}x{int(ext_w)} mm</b> conforms to packaging directive (&lt;{max_box_weight_limit} kg). Approved for Manual Handling.</span>
                </div>
            """, unsafe_allow_html=True)

    st.success(f"Connected to Cardboard Database: `{filename_loaded}` | Qualifying Options: {len(sorted_df)}")

    st.subheader("💡 Best Matched Packing Insights")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                <b>👑 Best Recommendation</b><br>
                <span style='font-size:11px; font-weight:bold; color:#0056b3;'>
                    {best_box['Box ID / Specification']}<br>
                    <span style='color:#dc3545;'>[Flute: {best_box['Quality Class']}]</span>
                </span>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box'><b>📦 Max Parts Fitted</b><br><span style='font-size:24px; font-weight:bold; color:#28a745;'>{int(best_box['Number of Parts per Box'])} Pcs</span></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-box'><b>📊 Vol. Efficiency</b><br><span style='font-size:24px; font-weight:bold; color:#ffc107;'>{best_box['Volumetric Efficiency (%)']}%</span></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-box'><b>⚖️ Total Weight</b><br><span style='font-size:24px; font-weight:bold; color:#17a2b8;'>{best_box['Total Weight (kg)']} kg</span></div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='metric-box'><b>💰 Box Price</b><br><span style='font-size:24px; font-weight:bold; color:#e83e8c;'>€ {best_box['Box Price (€)']:.2f}</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_recommender, tab_pallet, tab_compression = st.tabs([
        "📦 Tab 1: Box Recommender & Individual Loading", 
        "🚛 Tab 2: Pallet Stacking Optimizer (EPAL 1 & EPAL 2)", 
        "🗜️ Tab 3: McKee Gravity Compression Safety Check"
    ])

    # ==========================================================================
    # TAB 1: BOX RECOMMENDER & INDIVIDUAL LOADING
    # ==========================================================================
    with tab_recommender:
        # 1. EXCEL-LIKE INTERACTIVE FILTER ROW
        st.subheader("🏆 Recommended Cardboard Boxes")
        st.markdown("""
            **Ergonomic Color Hierarchy:** 
            🟢 **Light (≤60% weight)** &nbsp;|&nbsp; 
            🟠 **Moderate (60%-90% weight)** &nbsp;|&nbsp; 
            🔴 **Heavy (>90% weight)**
        """)

        with st.expander("🔍 Filter & Search Table Options (Excel-like Filtering)", expanded=False):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                all_flutes_list = sorted(list(sorted_df["Quality Class"].dropna().unique()))
                filter_flutes = st.multiselect("Filter Flute Grade:", options=all_flutes_list, default=all_flutes_list)
            with col_f2:
                all_tiers = ["🟢 Light (≤60%)", "🟠 Moderate (60%-90%)", "🔴 Heavy (>90%)"]
                filter_tiers = st.multiselect("Filter Weight Tier:", options=all_tiers, default=all_tiers)
            with col_f3:
                all_fps = sorted(list(sorted_df["Box Footprint (Ext)"].dropna().unique()))
                filter_footprints = st.multiselect("Filter Footprint:", options=all_fps, default=all_fps)
            with col_f4:
                search_query = st.text_input("Search Box Name:", placeholder="e.g. 600x400")

        # Apply In-Table Filters
        working_df = sorted_df.copy()
        if filter_flutes:
            working_df = working_df[working_df["Quality Class"].isin(filter_flutes)]
        if filter_tiers:
            working_df = working_df[working_df["Weight Classification"].isin(filter_tiers)]
        if filter_footprints:
            working_df = working_df[working_df["Box Footprint (Ext)"].isin(filter_footprints)]
        if search_query:
            working_df = working_df[working_df["Box ID / Specification"].str.contains(search_query, case=False, na=False)]

        if working_df.empty:
            st.warning("No boxes match the applied table filters. Please broaden your selection.")
            st.stop()

        display_df = working_df.drop(columns=[
            "_nx", "_ny", "_nz", "_ox", "_oy", "_oz", 
            "Raw Box ID", "Int. Length [mm]", "Int. Width [mm]", "Int. Height [mm]", 
            "Ext. Length [mm]", "Ext. Width [mm]", "Tier Rank"
        ]).reset_index(drop=True)
        display_df.index = display_df.index + 1

        col_header_sub, col_export_hub = st.columns([7, 3])
        with col_header_sub:
            st.caption(f"Showing **{len(display_df)}** qualified boxes matching your criteria.")

        with col_export_hub:
            export_format = st.selectbox(
                "📥 Export Table Data...",
                ["-- Choose Format --", "Export to Excel (.xlsx)", "Export to CSV (.csv)"],
                index=0,
                key="export_selector_hub",
                help="Download the recommendations directly to your machine."
            )

            if export_format == "Export to Excel (.xlsx)":
                buffer_xls = io.BytesIO()
                with pd.ExcelWriter(buffer_xls, engine='openpyxl') as writer:
                    display_df.to_excel(writer, sheet_name='Recommended_Boxes', index=True)
                xls_data = buffer_xls.getvalue()
                st.download_button(
                    label="🟢 Click to Download Excel Sheet",
                    data=xls_data,
                    file_name="BSH_Recommended_Boxes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            elif export_format == "Export to CSV (.csv)":
                csv_data = display_df.to_csv(index=True).encode('utf-8')
                st.download_button(
                    label="🔵 Click to Download CSV File",
                    data=csv_data,
                    file_name="BSH_Recommended_Boxes.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # Crisp High-Contrast Table Styling (High contrast text, soft tinted badge highlights)
        def highlight_weight_tier_clean(row):
            tier = str(row["Weight Classification"])
            if "Light" in tier or "🟢" in tier:
                bg = "background-color: rgba(34, 197, 94, 0.12);"
            elif "Moderate" in tier or "🟠" in tier:
                bg = "background-color: rgba(245, 159, 0, 0.12);"
            else:
                bg = "background-color: rgba(239, 68, 68, 0.12);"
            return [f"{bg} color: var(--text-color); font-weight: 500;"] * len(row)

        styled_df = display_df.style.apply(highlight_weight_tier_clean, axis=1).format({
            "Box Price (€)": "€ {:.2f}",
            "Volumetric Efficiency (%)": "{:.2f}%",
            "Remaining Air Space (%)": "{:.1f}%",
            "Total Weight (kg)": "{:.2f} kg"
        })

        st.dataframe(styled_df, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Step-by-Step Visual Blueprint Loading Map")

        # Synchronized Box Selection Dropdown
        selected_box_tab1 = st.selectbox(
            "Select a Cardboard Box to inspect its loading blueprints & 3D models (Synchronized):",
            options=available_boxes,
            key="tab1_box_selector",
            on_change=sync_from_tab1
        )
        st.session_state["global_selected_box"] = selected_box_tab1
        viz_box = sorted_df[sorted_df["Box ID / Specification"] == st.session_state["global_selected_box"]].iloc[0]

        nx = int(viz_box["_nx"])
        ny = int(viz_box["_ny"])
        nz = int(viz_box["_nz"])
        ox = int(viz_box["_ox"])
        oy = int(viz_box["_oy"])
        oz = int(viz_box["_oz"])
        box_l = viz_box["Int. Length [mm]"]
        box_w = viz_box["Int. Width [mm]"]
        ext_l = viz_box["Ext. Length [mm]"]
        ext_w = viz_box["Ext. Width [mm]"]

        # Manual Quantity Override / Fine-Tuning Stepper
        max_possible_parts = int(viz_box["Max Geometric Fit"])
        default_packed_parts = int(viz_box["Number of Parts per Box"])

        # Retain fine-tuned quantity across session state
        qty_state_key = f"manual_qty_{st.session_state['global_selected_box']}"
        if qty_state_key not in st.session_state:
            st.session_state[qty_state_key] = default_packed_parts

        st.markdown("##### 🎛️ Operator Quantity Fine-Tuning (Updates Diagrams & Pallet Calculations)")
        col_adj_1, col_adj_2 = st.columns([1, 2])
        with col_adj_1:
            active_quantity = st.number_input(
                f"Loaded Parts per Box (Max Geometric: {max_possible_parts})",
                min_value=1,
                max_value=max_possible_parts,
                value=int(st.session_state[qty_state_key]),
                step=1,
                key=f"input_{qty_state_key}",
                help="Fine-tune or override the number of parts. All 2D floor plans, 3D views, and pallet weights adapt automatically."
            )
            st.session_state[qty_state_key] = active_quantity

        with col_adj_2:
            override_weight = round((active_quantity * prod_wt) + estimate_box_weight(ext_l, ext_w, viz_box["Ext. Height [mm]"], viz_box["Quality Class"]), 2)
            override_efficiency = round(((active_quantity * single_part_vol) / (box_l * box_w * viz_box["Int. Height [mm]"])) * 100, 2)
            st.info(f"⚡ Live Recalculated Package Weight: **{override_weight} kg** | Volumetric Efficiency: **{override_efficiency}%** | Loaded: **{active_quantity} / {max_possible_parts} parts**")

        placement_style = determine_placement_style(prod_l, prod_w, prod_h, oz)
        is_standing = oz > min(prod_l, prod_w, prod_h)
        if is_standing and nz == 1:
            req_height_2_layers = (oz * 2) + sep_z + clear_height
            st.markdown(f"""
                <div class='warning-box'>
                    💡 <b>Alternative Orientation Tip:</b> You are packing the parts <b>standing on edge/vertical</b>. 
                    While this fits more parts on the floor grid, you can only pack <b>1 single layer</b> because this box height ({int(viz_box['Int. Height [mm]'])} mm) is too short. 
                    <br>👉 To stack <b>2 layers</b> in this standing orientation, you would need to ask procurement for a taller box with an internal height of at least <b>{int(req_height_2_layers)} mm</b>.
                </div>
            """, unsafe_allow_html=True)

        with st.container():
            col_text, col_flat, col_stack = st.columns([2.5, 3, 2.5])

            with col_text:
                st.markdown("<div class='guide-box'><h4><b>🛠️ 3-Step Packing Instruction</b></h4><hr style='border: 0.5px solid rgba(148,163,184,0.3);'>", unsafe_allow_html=True)

                st.markdown(f"""
                <b>Step 1: Orient the Part</b><br>
                Place each individual part according to this orientation:<br>
                <i>{placement_style}</i>
                <ul>
                    <li>📐 <b>Lengthwise (Left-to-Right):</b> {ox} mm</li>
                    <li>📐 <b>Widthwise (Front-to-Back):</b> {oy} mm</li>
                    <li>📐 <b>Height (pointing UP):</b> {oz} mm</li>
                </ul>
                """, unsafe_allow_html=True)

                parts_per_layer = nx * ny
                active_layers = int(np.ceil(active_quantity / parts_per_layer)) if parts_per_layer > 0 else 1

                st.markdown(f"""
                <b>Step 2: Arrange the Floor Grid</b><br>
                Lay down a grid of <b>{nx} columns</b> and <b>{ny} rows</b>.
                <ul>
                    <li>Capacity per complete layer: <b>{parts_per_layer} parts</b>.</li>
                    <li>Active layer count: <b>{active_layers} layer(s)</b>.</li>
                    <li>Place {sep_xy}mm partition grids between parts.</li>
                </ul>
                """, unsafe_allow_html=True)

                if active_layers > 1:
                    st.markdown(f"""
                    <b>Step 3: Stacking Vertical Layers</b><br>
                    <ul>
                        <li>Place a flat {sep_z}mm divider sheet over completed layers.</li>
                        <li>Build a total of <b>{active_layers} vertical layers</b> (reaching <b>{active_quantity} loaded parts</b>).</li>
                    </ul>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <b>Step 3: Finish Packing</b><br>
                    All <b>{active_quantity} parts</b> fit into <b>1 single floor layer</b>. No vertical shelf dividers are needed. 
                    <br>Seal the box and apply the mandatory single box label!
                    """, unsafe_allow_html=True)

                dims_footprint_sel = sorted([ext_l, ext_w])
                is_manual_box_sel = (dims_footprint_sel[0] <= 300.0) and (dims_footprint_sel[1] <= 400.0)

                if override_weight > max_box_weight_limit:
                    if not is_manual_box_sel:
                        st.markdown(f"<p style='color:#2b8a3e; font-weight:bold; margin-top:10px;'>🟢 Operational Weight: {override_weight} kg (Permitted: Box footprint {int(ext_l)}x{int(ext_w)} mm exceeds manual threshold)</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:#e03131; font-weight:bold; margin-top:10px;'>🚨 Operational Weight: {override_weight} kg (Overweight manual packing error! Exceeds {max_box_weight_limit} kg directive)</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#2b8a3e; font-weight:bold; margin-top:10px;'>🟢 Operational Weight: Safe at {override_weight} kg (Conforms to &lt;{max_box_weight_limit} kg limit)</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_flat:
                # DYNAMIC 2D FLOOR GRID PLAN: Reflects manual quantity fine-tuning!
                st_text_color = '#FFFFFF' if st.get_option('theme.base') == 'dark' else '#212529'
                fig, ax = plt.subplots(figsize=(6, 4), facecolor='none')
                ax.set_facecolor('none')

                ax.add_patch(patches.Rectangle((0, 0), box_l, box_w, fill=False, edgecolor=st_text_color, linewidth=2.5, label='Box Wall'))
                ax.add_patch(patches.Rectangle((0, 0), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.3))
                ax.add_patch(patches.Rectangle((0, box_w - clear_side), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.3))
                ax.add_patch(patches.Rectangle((0, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.3))
                ax.add_patch(patches.Rectangle((box_l - clear_side, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.3))

                total_grid_w = nx * ox + (nx - 1) * sep_xy
                total_grid_h = ny * oy + (ny - 1) * sep_xy
                leftover_x = (box_l - 2 * clear_side) - total_grid_w
                leftover_y = (box_w - 2 * clear_side) - total_grid_h

                start_x_offset = clear_side + (leftover_x / 2)
                start_y_offset = clear_side + (leftover_y / 2)

                # Visual tracking of active vs empty slots based on active_quantity
                # Parts fill bottom-up: layer 1 takes min(active_quantity, nx*ny)
                layer1_filled = min(active_quantity, nx * ny)

                slot_counter = 0
                for r in range(ny):
                    y_pos = start_y_offset + r * (oy + sep_xy)
                    for c in range(nx):
                        x_pos = start_x_offset + c * (ox + sep_xy)
                        slot_counter += 1
                        if slot_counter <= layer1_filled:
                            # Populated compartment
                            ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#a5d8ff', edgecolor='#1971c2', linewidth=1.2))
                            ax.text(x_pos + ox/2, y_pos + oy/2, f"{c+1}, {r+1}", ha='center', va='center', fontsize=8, color='#0f4c81', fontweight='bold')
                        else:
                            # Empty / Unfilled compartment due to operator reduction
                            ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='rgba(200,200,200,0.15)', edgecolor='#94a3b8', linewidth=1.0, linestyle='--'))
                            ax.text(x_pos + ox/2, y_pos + oy/2, "Empty", ha='center', va='center', fontsize=7, color='#94a3b8', fontstyle='italic')

                ax.annotate('', xy=(0, -25), xytext=(box_l, -25), arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
                ax.text(box_l/2, -45, f"{int(ext_l)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center')

                ax.annotate('', xy=(box_l + 25, 0), xytext=(box_l + 25, box_w), arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
                ax.text(box_l + 45, box_w/2, f"{int(ext_w)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center', va='center', rotation=-90)

                ax.text(box_l/2, box_w + 15, f"Floor Grid: {nx}x{ny} | Active Layers: {active_layers}", color='#dc3545', fontsize=12, fontweight='bold', ha='center')

                ax.set_xlim(-40, box_l + 80)
                ax.set_ylim(-60, box_w + 35)
                ax.set_aspect('equal')
                ax.axis('off')
                st.pyplot(fig)
                plt.close(fig)

            with col_stack:
                # DYNAMIC 3D VERTICAL STACKING BLUEPRINT: Reflects active layers based on quantity!
                fig3d = plt.figure(figsize=(4, 3.5), facecolor='none')
                ax3d = fig3d.add_subplot(111, projection='3d', facecolor='none')
                w_scale = 100
                l_scale = w_scale * (box_l / box_w)
                h_scale = 30
                z_aspect = max(30, active_layers * 15)
                ax3d.set_box_aspect((l_scale, w_scale, z_aspect))
                lbl_font = 9 if active_layers > 6 else 12

                for layer in range(active_layers):
                    z_start = layer * (h_scale + 5)
                    v = np.array([
                        [0, 0, z_start], [l_scale, 0, z_start], [l_scale, w_scale, z_start], [0, w_scale, z_start],
                        [0, 0, z_start + h_scale], [l_scale, 0, z_start + h_scale], [l_scale, w_scale, z_start + h_scale], [0, w_scale, z_start + h_scale]
                    ])
                    faces = [
                        [v[0], v[1], v[5], v[4]], [v[1], v[2], v[6], v[5]], [v[2], v[3], v[7], v[6]],
                        [v[3], v[0], v[4], v[7]], [v[4], v[5], v[6], v[7]], [v[0], v[1], v[2], v[3]]
                    ]
                    color = '#a5d8ff' if layer < active_layers - 1 else '#74c0fc'
                    poly = Poly3DCollection(faces, facecolors=color, edgecolors='#1971c2', linewidths=1.5, alpha=0.8)
                    ax3d.add_collection3d(poly)

                    ax3d.text(-35, 20, z_start + h_scale/2, f"L{layer + 1}", color='#dc3545', fontweight='bold', fontsize=lbl_font, ha='right', va='center', zorder=100)
                    ax3d.plot([-30, 0], [10, 0], [z_start + h_scale/2, z_start + h_scale/2], color='#dc3545', linestyle=':', linewidth=1)

                ax3d.set_xlim(-50, l_scale + 10)
                ax3d.set_ylim(-20, w_scale + 10)
                ax3d.set_zlim(0, active_layers * (h_scale + 5) + 10)
                ax3d.view_init(elev=22, azim=-65)
                ax3d.axis('off')

                plt.title(f"Vertical Blueprint ({active_layers} Layers)", fontsize=11, fontweight='bold', color=st_text_color, pad=10)
                st.pyplot(fig3d)
                plt.close(fig3d)

        # DYNAMIC INTERACTIVE 3D DIGITAL TWIN VIEWPORT
        st.markdown("<hr style='margin:25px 0; border:0; border-top:1px solid rgba(148,163,184,0.2);'>", unsafe_allow_html=True)
        st.subheader("🔄 Interactive 3D Box & Part Twin Viewport (Rotatable)")
        col_cad, col_packing_3d = st.columns(2)

        with col_cad:
            st.markdown("##### 🔍 Rotatable 3D CAD Part Model")
            if mesh_cad is not None:
                try:
                    v_coords = mesh_cad.vertices
                    f_indices = mesh_cad.faces
                    x_v, y_v, z_v = v_coords[:, 0], v_coords[:, 1], v_coords[:, 2]
                    i_f, j_f, k_f = f_indices[:, 0], f_indices[:, 1], f_indices[:, 2]

                    fig_cad = go.Figure(data=[
                        go.Mesh3d(
                            x=x_v, y=y_v, z=z_v,
                            i=i_f, j=j_f, k=k_f,
                            color='#d1d5db',
                            opacity=1.0,
                            flatshading=False,
                            lighting=dict(ambient=0.5, diffuse=0.9, roughness=0.15, specular=1.6, fresnel=0.6),
                            lightposition=dict(x=1000, y=1000, z=1500),
                            name="3D CAD Part"
                        )
                    ])
                    fig_cad.update_layout(
                        scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
                        margin=dict(l=0, r=0, b=0, t=0),
                        height=380
                    )
                    st.plotly_chart(fig_cad, use_container_width=True)
                except Exception as e_plotly:
                    st.info("Upload your 3D CAD (.STL/.STEP) file to activate the rotatable 3D digital twin viewer!")
            else:
                st.info("💡 Please upload a 3D CAD (.STL/.STEP) file in the sidebar to activate this rotatable digital twin viewer!")

        with col_packing_3d:
            st.markdown("##### 📦 Rotatable 3D Box Packing Layout")
            try:
                fig_pack = go.Figure()

                def add_wireframe_compartment(fig_scene, x_pos, y_pos, z_pos, dx, dy, dz):
                    cv = np.array([
                        [x_pos, y_pos, z_pos], [x_pos + dx, y_pos, z_pos],
                        [x_pos + dx, y_pos + dy, z_pos], [x_pos, y_pos + dy, z_pos],
                        [x_pos, y_pos, z_pos + dz], [x_pos + dx, y_pos, z_pos + dz],
                        [x_pos + dx, y_pos, z_pos + dz], [x_pos, y_pos + dy, z_pos + dz]
                    ])
                    edges_c = [
                        (0, 1), (1, 2), (2, 3), (3, 0),
                        (4, 5), (5, 6), (6, 7), (7, 4),
                        (0, 4), (1, 5), (2, 6), (3, 7)
                    ]
                    for edge in edges_c:
                        fig_scene.add_trace(go.Scatter3d(
                            x=[cv[edge[0]][0], cv[edge[1]][0]],
                            y=[cv[edge[0]][1], cv[edge[1]][1]],
                            z=[cv[edge[0]][2], cv[edge[1]][2]],
                            mode='lines',
                            line=dict(color='rgba(150, 150, 150, 0.4)', width=2),
                            showlegend=False,
                            hoverinfo='skip'
                        ))

                def add_plotly_mesh_part(fig_scene, x_pos, y_pos, z_pos, dx, dy, dz, raw_v, raw_f, text_str):
                    min_v = np.min(raw_v, axis=0)
                    max_v = np.max(raw_v, axis=0)
                    raw_extent = max_v - min_v

                    best_perm = None
                    min_error = float('inf')
                    for perm in itertools.permutations([0, 1, 2]):
                        perm_extent = raw_extent[list(perm)]
                        ratios = np.array([dx, dy, dz]) / perm_extent
                        error = np.std(ratios)
                        if error < min_error:
                            min_error = error
                            best_perm = perm

                    v_aligned = (raw_v - min_v)[:, list(best_perm)]
                    aligned_extent = raw_extent[list(best_perm)]
                    scale_factor = np.min(np.array([dx, dy, dz]) / aligned_extent)
                    v_scaled = v_aligned * scale_factor
                    scaled_extent = aligned_extent * scale_factor

                    gap_x = dx - scaled_extent[0]
                    gap_y = dy - scaled_extent[1]
                    gap_z = dz - scaled_extent[2]
                    v_final = v_scaled + np.array([x_pos + gap_x/2, y_pos + gap_y/2, z_pos + gap_z/2])

                    fig_scene.add_trace(go.Mesh3d(
                        x=v_final[:, 0], y=v_final[:, 1], z=v_final[:, 2],
                        i=raw_f[:, 0], j=raw_f[:, 1], k=raw_f[:, 2],
                        color='#74c0fc', opacity=1.0,
                        flatshading=False,
                        lighting=dict(ambient=0.5, diffuse=0.9, specular=1.2, roughness=0.15, fresnel=0.5),
                        name=text_str, hoverinfo="text", text=text_str, showlegend=False
                    ))

                total_grid_w = nx * ox + (nx - 1) * sep_xy
                total_grid_h = ny * oy + (ny - 1) * sep_xy
                leftover_x = (box_l - 2 * clear_side) - total_grid_w
                leftover_y = (box_w - 2 * clear_side) - total_grid_h
                start_x_offset = clear_side + (leftover_x / 2)
                start_y_offset = clear_side + (leftover_y / 2)

                # Dynamically fill 3D CAD parts according to active_quantity
                parts_placed = 0
                for layer in range(active_layers):
                    z_pos = layer * (oz + sep_z)
                    for r in range(ny):
                        y_pos = start_y_offset + r * (oy + sep_xy)
                        for c in range(nx):
                            if parts_placed >= active_quantity:
                                break
                            x_pos = start_x_offset + c * (ox + sep_xy)
                            add_wireframe_compartment(fig_pack, x_pos, y_pos, z_pos, ox, oy, oz)
                            if mesh_cad is not None and parts_placed < 10:  # Render up to 10 solid mesh models for high framerate
                                add_plotly_mesh_part(
                                    fig_pack, x_pos, y_pos, z_pos, ox, oy, oz, 
                                    mesh_cad.vertices, mesh_cad.faces, 
                                    f"Part #{parts_placed+1} @ Layer {layer+1}"
                                )
                            parts_placed += 1

                box_v = np.array([
                    [0, 0, 0], [box_l, 0, 0], [box_l, box_w, 0], [0, box_w, 0],
                    [0, 0, viz_box["Int. Height [mm]"]], [box_l, 0, viz_box["Int. Height [mm]"]],
                    [box_l, box_w, viz_box["Int. Height [mm]"]], [0, box_w, viz_box["Int. Height [mm]"]]
                ])
                edges = [
                    (0, 1), (1, 2), (2, 3), (3, 0),
                    (4, 5), (5, 6), (6, 7), (7, 4),
                    (0, 4), (1, 5), (2, 6), (3, 7)
                ]
                for edge in edges:
                    fig_pack.add_trace(go.Scatter3d(
                        x=[box_v[edge[0]][0], box_v[edge[1]][0]],
                        y=[box_v[edge[0]][1], box_v[edge[1]][1]],
                        z=[box_v[edge[0]][2], box_v[edge[1]][2]],
                        mode='lines',
                        line=dict(color='#212529', width=4),
                        showlegend=False,
                        hoverinfo='skip'
                    ))

                fig_pack.update_layout(
                    scene=dict(xaxis_title="Length (mm)", yaxis_title="Width (mm)", zaxis_title="Height (mm)", aspectmode='data'),
                    margin=dict(l=0, r=0, b=0, t=0),
                    height=380
                )
                st.plotly_chart(fig_pack, use_container_width=True)
            except Exception as e_pack_plotly:
                st.warning(f"Error rendering interactive 3D box packing model: {e_pack_plotly}")

    # ==========================================================================
    # TAB 2: PALLET STACKING OPTIMIZER & COMPARATIVE ANALYSIS
    # ==========================================================================
    with tab_pallet:
        st.subheader("🚛 Multi-Pallet Optimization Engine")
        st.markdown(f"Pallet transport optimization aligned to packaging directive: **{max_pallet_height_limit} mm max height** and **{max_pallet_weight_limit} kg gross weight limit**.")

        # EPAL Pallets Dimensions (in mm) with 144mm EUR Pallet base
        PALLETS = {
            "EPAL 1 (Standard)": {"l": 1200, "w": 800, "tare": 23.0, "pallet_h": 144.0},
            "EPAL 2 (Industrial)": {"l": 1200, "w": 1000, "tare": 23.0, "pallet_h": 144.0}
        }

        # Available pure stacking height for boxes (Total max height minus wood pallet)
        pure_box_max_h = max(200.0, max_pallet_height_limit - 144.0)

        def calculate_pallet_stacking(pallet_l, pallet_w, ext_l, ext_w, ext_h, box_wt, pcs_box, pallet_tare=23.0, max_h=pure_box_max_h, max_wt=max_pallet_weight_limit):
            nx_a, ny_a = int(pallet_l // ext_l), int(pallet_w // ext_w)
            layers_a = nx_a * ny_a
            nx_b, ny_b = int(pallet_l // ext_w), int(pallet_w // ext_l)
            layers_b = nx_b * ny_b

            best_layer_qty = max(layers_a, layers_b)
            best_orient = "Lengthwise (L-parallel)" if layers_a >= layers_b else "Widthwise (W-parallel)"
            nx_best = nx_a if layers_a >= layers_b else nx_b
            ny_best = ny_a if layers_a >= layers_b else ny_b

            nz = max(1, int(max_h // ext_h))
            total_boxes = best_layer_qty * nz
            total_weight = total_boxes * box_wt + pallet_tare

            while total_weight > max_wt and nz > 1:
                nz -= 1
                total_boxes = best_layer_qty * nz
                total_weight = total_boxes * box_wt + pallet_tare

            total_pcs = total_boxes * pcs_box
            return total_boxes, nz, best_layer_qty, total_pcs, round(total_weight, 2), best_orient, nx_best, ny_best

        # 1. AUTOMATED COMPARATIVE MATRIX
        st.markdown("### ⚖️ Automated Stacking Comparison")
        st.markdown(f"This matrix compares options on a standard EPAL 1 Pallet under the active **{max_pallet_weight_limit} kg** and **{max_pallet_height_limit} mm** constraints:")

        ranked_df_copy = sorted_df.copy()
        ranked_df_copy['Footprint Area'] = ranked_df_copy['Ext. Length [mm]'] * ranked_df_copy['Ext. Width [mm]']
        sorted_by_footprint = ranked_df_copy.sort_values(by='Footprint Area')

        if len(sorted_by_footprint) >= 2:
            small_row = sorted_by_footprint.iloc[0]
            small_name = small_row["Box ID / Specification"]
            top1_row = ranked_df_copy.iloc[0]
            top1_name = top1_row["Box ID / Specification"]
            top2_row = ranked_df_copy.iloc[1] if len(ranked_df_copy) >= 2 else None
            top2_name = top2_row["Box ID / Specification"] if top2_row is not None else "N/A"
            top3_row = ranked_df_copy.iloc[2] if len(ranked_df_copy) >= 3 else None
            top3_name = top3_row["Box ID / Specification"] if top3_row is not None else "N/A"

            bt_s, _, _, pcs_s, wt_s, _, _, _ = calculate_pallet_stacking(1200, 800, small_row["Ext. Length [mm]"], small_row["Ext. Width [mm]"], small_row["Ext. Height [mm]"], small_row["Total Weight (kg)"], int(small_row["Number of Parts per Box"]))
            bt_1, _, _, pcs_1, wt_1, _, _, _ = calculate_pallet_stacking(1200, 800, top1_row["Ext. Length [mm]"], top1_row["Ext. Width [mm]"], top1_row["Ext. Height [mm]"], top1_row["Total Weight (kg)"], int(top1_row["Number of Parts per Box"]))

            if top2_row is not None:
                bt_2, _, _, pcs_2, wt_2, _, _, _ = calculate_pallet_stacking(1200, 800, top2_row["Ext. Length [mm]"], top2_row["Ext. Width [mm]"], top2_row["Ext. Height [mm]"], top2_row["Total Weight (kg)"], int(top2_row["Number of Parts per Box"]))
            else:
                bt_2, pcs_2, wt_2 = "N/A", 0, "N/A"

            if top3_row is not None:
                bt_3, _, _, pcs_3, wt_3, _, _, _ = calculate_pallet_stacking(1200, 800, top3_row["Ext. Length [mm]"], top3_row["Ext. Width [mm]"], top3_row["Ext. Height [mm]"], top3_row["Total Weight (kg)"], int(top3_row["Number of Parts per Box"]))
            else:
                bt_3, pcs_3, wt_3 = "N/A", 0, "N/A"

            pcs_vals = [pcs_s, pcs_1, pcs_2, pcs_3]
            labels_map = {
                pcs_s: (small_name, "Smallest Footprint Box"),
                pcs_1: (top1_name, "Top 1 Best Box"),
                pcs_2: (top2_name, "Top 2 Best Box"),
                pcs_3: (top3_name, "Top 3 Best Box")
            }
            max_yield = max(pcs_vals)
            winner_box_id, winner_label = labels_map[max_yield]

            st.markdown(f"""
            <div class='success-box'>
                🏆 <b>Automated Yield Decision Winner:</b> The <b>{winner_label} ({winner_box_id})</b> is the optimal choice!<br>
                It delivers <b style='color:#2b8a3e;'>{max_yield} total pieces</b> per standard EPAL 1 pallet, adhering to the &lt;{max_pallet_weight_limit} kg limit.
            </div>
            """, unsafe_allow_html=True)

            price_s = (bt_s * small_row["Box Price (€)"]) + 8.00
            price_1 = (bt_1 * top1_row["Box Price (€)"]) + 8.00
            price_2 = (bt_2 * top2_row["Box Price (€)"]) + 8.00 if top2_row is not None else 0.00
            price_3 = (bt_3 * top3_row["Box Price (€)"]) + 8.00 if top3_row is not None else 0.00

            comp_df = pd.DataFrame([
                {"Metric Profile": "Box Specification ID", "Smallest Box (Top 10)": small_name, "Top 1 Best Box": top1_name, "Top 2 Best Box": top2_name, "Top 3 Best Box": top3_name},
                {"Metric Profile": "Cardboard Flute Quality", "Smallest Box (Top 10)": small_row['Quality Class'], "Top 1 Best Box": top1_row['Quality Class'], "Top 2 Best Box": top2_row['Quality Class'] if top2_row is not None else "N/A", "Top 3 Best Box": top3_row['Quality Class'] if top3_row is not None else "N/A"},
                {"Metric Profile": "External Footprint Dimensions", "Smallest Box (Top 10)": f"{int(small_row['Ext. Length [mm]'])}x{int(small_row['Ext. Width [mm]'])} mm", "Top 1 Best Box": f"{int(top1_row['Ext. Length [mm]'])}x{int(top1_row['Ext. Width [mm]'])} mm", "Top 2 Best Box": f"{int(top2_row['Ext. Length [mm]'])}x{int(top2_row['Ext. Width [mm]'])} mm" if top2_row is not None else "N/A", "Top 3 Best Box": f"{int(top3_row['Ext. Length [mm]'])}x{int(top3_row['Ext. Width [mm]'])} mm" if top3_row is not None else "N/A"},
                {"Metric Profile": "Optimal Packing Orientation", "Smallest Box (Top 10)": determine_placement_style(prod_l, prod_w, prod_h, small_row["_oz"]), "Top 1 Best Box": determine_placement_style(prod_l, prod_w, prod_h, top1_row["_oz"]), "Top 2 Best Box": determine_placement_style(prod_l, prod_w, prod_h, top2_row["_oz"]) if top2_row is not None else "N/A", "Top 3 Best Box": determine_placement_style(prod_l, prod_w, prod_h, top3_row["_oz"]) if top3_row is not None else "N/A"},
                {"Metric Profile": "Parts Loaded (Per Box)", "Smallest Box (Top 10)": f"{int(small_row['Number of Parts per Box'])} Pcs", "Top 1 Best Box": f"{int(top1_row['Number of Parts per Box'])} Pcs", "Top 2 Best Box": f"{int(top2_row['Number of Parts per Box'])} Pcs" if top2_row is not None else "N/A", "Top 3 Best Box": f"{int(top3_row['Number of Parts per Box'])} Pcs" if top3_row is not None else "N/A"},
                {"Metric Profile": "Boxes Loaded (Per Pallet)", "Smallest Box (Top 10)": f"{bt_s} boxes", "Top 1 Best Box": f"{bt_1} boxes", "Top 2 Best Box": f"{bt_2} boxes" if top2_row is not None else "N/A", "Top 3 Best Box": f"{bt_3} boxes" if top3_row is not None else "N/A"},
                {"Metric Profile": "Total Pieces (Per Pallet)", "Smallest Box (Top 10)": f"{pcs_s} Pcs", "Top 1 Best Box": f"{pcs_1} Pcs", "Top 2 Best Box": f"{pcs_2} Pcs" if top2_row is not None else "N/A", "Top 3 Best Box": f"{pcs_3} Pcs" if top3_row is not None else "N/A"},
                {"Metric Profile": "Pallet Weight (inc. 23kg Tare)", "Smallest Box (Top 10)": f"{wt_s} kg", "Top 1 Best Box": f"{wt_1} kg", "Top 2 Best Box": f"{wt_2} kg" if top2_row is not None else "N/A", "Top 3 Best Box": f"{wt_3} kg" if top3_row is not None else "N/A"},
                {"Metric Profile": "Overall Cost (Boxes + 8€ EPAL 1)", "Smallest Box (Top 10)": f"€ {price_s:.2f}", "Top 1 Best Box": f"€ {price_1:.2f}", "Top 2 Best Box": f"€ {price_2:.2f}" if top2_row is not None else "N/A", "Top 3 Best Box": f"€ {price_3:.2f}" if top3_row is not None else "N/A"}
            ])
            st.table(comp_df)
        else:
            st.info("💡 Multiple unique box sizes are required in the inventory database to generate a comparative analysis.")

        st.markdown("<hr style='margin:25px 0; border:0; border-top:1px solid rgba(148,163,184,0.2);'>", unsafe_allow_html=True)

        # 2. INDIVIDUAL STACKING REPORT & INTERACTIVE 3D PALLETIZER
        st.markdown(f"### 📦 Palletization Report & Interactive 3D Stacking Model")

        selected_box_t2 = st.selectbox(
            "Select any Cardboard Box to inspect its detailed pallet loading report & rotatable 3D stack (Synchronized):",
            options=available_boxes,
            key="tab2_box_selector",
            on_change=sync_from_tab2
        )
        st.session_state["global_selected_box"] = selected_box_t2

        viz_box_t2 = sorted_df[sorted_df["Box ID / Specification"] == st.session_state["global_selected_box"]].iloc[0]
        bx_ext_l = viz_box_t2["Ext. Length [mm]"]
        bx_ext_w = viz_box_t2["Ext. Width [mm]"]
        bx_ext_h = viz_box_t2["Ext. Height [mm]"]

        # Dynamically pull the operator fine-tuned box weight and parts count!
        t2_qty_key = f"manual_qty_{st.session_state['global_selected_box']}"
        active_t2_pcs = int(st.session_state.get(t2_qty_key, viz_box_t2["Number of Parts per Box"]))
        active_t2_wt = round((active_t2_pcs * prod_wt) + estimate_box_weight(bx_ext_l, bx_ext_w, bx_ext_h, viz_box_t2["Quality Class"]), 2)

        col_metrics, col_plotly_pallet = st.columns([4, 6])

        with col_metrics:
            st.markdown(f"#### 📋 Stacking Report for **{st.session_state['global_selected_box']}**")
            st.caption(f"Calculations reflect active configuration: **{active_t2_pcs} pcs/box** @ **{active_t2_wt} kg/box**")

            b_total_1, z_layers_1, _, p_pcs_1, p_wt_1, orient_1, nx_1, ny_1 = calculate_pallet_stacking(
                PALLETS["EPAL 1 (Standard)"]["l"], PALLETS["EPAL 1 (Standard)"]["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, active_t2_wt, active_t2_pcs, PALLETS["EPAL 1 (Standard)"]["tare"]
            )
            b_total_2, z_layers_2, _, p_pcs_2, p_wt_2, orient_2, nx_2, ny_2 = calculate_pallet_stacking(
                PALLETS["EPAL 2 (Industrial)"]["l"], PALLETS["EPAL 2 (Industrial)"]["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, active_t2_wt, active_t2_pcs, PALLETS["EPAL 2 (Industrial)"]["tare"]
            )

            st.markdown(f"""
            <div style='background-color: var(--background-color); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--text-color); border-left: 5px solid #228be6;'>
                <h5 style='margin-top: 0px;'>🥇 EPAL 1 standard (1200 x 800 mm)</h5>
                <b>Orientation:</b> {orient_1}<br>
                📐 <b>Layer Layout Grid:</b> {nx_1} x {ny_1} (X x Y)<br>
                🪜 <b>Stacking Height (Vertical Layers):</b> {z_layers_1} layers<br>
                📦 <b>Total Boxes:</b> {b_total_1} units<br>
                ✨ <b>Total Pieces:</b> <b style='color:#2b8a3e;'>{p_pcs_1} Pcs</b><br>
                ⚖️ <b>Pallet Weight:</b> <b>{p_wt_1} kg</b> (&lt;{max_pallet_weight_limit} kg directive)
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style='background-color: var(--background-color); padding: 15px; border-radius: 8px; border: 1px solid var(--text-color); border-left: 5px solid #15aabf;'>
                <h5 style='margin-top: 0px;'>🥈 EPAL 2 Industrial (1200 x 1000 mm)</h5>
                <b>Orientation:</b> {orient_2}<br>
                📐 <b>Layer Layout Grid:</b> {nx_2} x {ny_2} (X x Y)<br>
                🪜 <b>Stacking Height (Vertical Layers):</b> {z_layers_2} layers<br>
                📦 <b>Total Boxes:</b> {b_total_2} units<br>
                ✨ <b>Total Pieces:</b> <b style='color:#2b8a3e;'>{p_pcs_2} Pcs</b><br>
                ⚖️ <b>Pallet Weight:</b> <b>{p_wt_2} kg</b> (&lt;{max_pallet_weight_limit} kg directive)
            </div>
            """, unsafe_allow_html=True)

        with col_plotly_pallet:
            st.markdown("##### 🔄 High-Definition Rotatable 3D Palletizer View")
            pallet_sel = st.radio("Choose Stacking Blueprint Pallet View:", options=["EPAL 1 (1200x800)", "EPAL 2 (1200x1000)"], horizontal=True)
            active_p_spec = PALLETS["EPAL 1 (Standard)"] if "EPAL 1" in pallet_sel else PALLETS["EPAL 2 (Industrial)"]

            p_boxes, p_layers, p_l_qty, _, _, p_orient, nx_act, ny_act = calculate_pallet_stacking(
                active_p_spec["l"], active_p_spec["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, active_t2_wt, active_t2_pcs, active_p_spec["tare"]
            )

            try:
                fig_pallet_3d = go.Figure()

                # Wooden Pallet Base (144mm EUR standard)
                fig_pallet_3d.add_trace(go.Mesh3d(
                    x=[0, active_p_spec["l"], active_p_spec["l"], 0, 0, active_p_spec["l"], active_p_spec["l"], 0],
                    y=[0, 0, active_p_spec["w"], active_p_spec["w"], 0, 0, active_p_spec["w"], active_p_spec["w"]],
                    z=[-22, -22, -22, -22, 0, 0, 0, 0],
                    i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                    j=[1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6],
                    k=[2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5],
                    color='#d2b48c', opacity=0.95, name="Top Deck Boards",
                    flatshading=True, lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1)
                ))

                runners_y = [
                    (0, 100),
                    (active_p_spec["w"]/2 - 50, active_p_spec["w"]/2 + 50),
                    (active_p_spec["w"] - 100, active_p_spec["w"])
                ]
                for r_idx, (y0, y1) in enumerate(runners_y):
                    fig_pallet_3d.add_trace(go.Mesh3d(
                        x=[0, active_p_spec["l"], active_p_spec["l"], 0, 0, active_p_spec["l"], active_p_spec["l"], 0],
                        y=[y0, y0, y1, y1, y0, y0, y1, y1],
                        z=[-122, -122, -122, -122, -22, -22, -22, -22],
                        i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                        j=[1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6],
                        k=[2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5],
                        color='#cd853f', opacity=0.95, name=f"Runner {r_idx+1}",
                        flatshading=True, lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1)
                    ))

                fig_pallet_3d.add_trace(go.Mesh3d(
                    x=[0, active_p_spec["l"], active_p_spec["l"], 0, 0, active_p_spec["l"], active_p_spec["l"], 0],
                    y=[0, 0, active_p_spec["w"], active_p_spec["w"], 0, 0, active_p_spec["w"], active_p_spec["w"]],
                    z=[-144, -144, -144, -144, -122, -122, -122, -122],
                    i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                    j=[1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6],
                    k=[2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5],
                    color='#d2b48c', opacity=0.95, name="Bottom Boards",
                    flatshading=True, lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1)
                ))

                bx_dx = bx_ext_l if p_orient == "Lengthwise (L-parallel)" else bx_ext_w
                bx_dy = bx_ext_w if p_orient == "Lengthwise (L-parallel)" else bx_ext_l
                bx_dz = bx_ext_h

                start_x = (active_p_spec["l"] - nx_act * bx_dx) / 2
                start_y = (active_p_spec["w"] - ny_act * bx_dy) / 2

                line_x, line_y, line_z = [], [], []
                colors_gradient = ["#1c7ed6", "#228be6", "#339af0", "#4dabf7", "#74c0fc", "#a5d8ff"]

                for layer in range(p_layers):
                    z0 = layer * bx_dz
                    z1 = z0 + bx_dz
                    color = colors_gradient[layer % len(colors_gradient)]
                    for r in range(ny_act):
                        y0 = start_y + r * bx_dy
                        y1 = y0 + bx_dy
                        for c in range(nx_act):
                            x0 = start_x + c * bx_dx
                            x1 = x0 + bx_dx

                            edges = [
                                ((x0, y0, z0), (x1, y0, z0)), ((x1, y0, z0), (x1, y1, z0)),
                                ((x1, y1, z0), (x0, y1, z0)), ((x0, y1, z0), (x0, y0, z0)),
                                ((x0, y0, z1), (x1, y0, z1)), ((x1, y0, z1), (x1, y1, z1)),
                                ((x1, y1, z1), (x0, y1, z1)), ((x0, y1, z1), (x0, y0, z1)),
                                ((x0, y0, z0), (x0, y0, z1)), ((x1, y0, z0), (x1, y0, z1)),
                                ((x1, y1, z0), (x1, y1, z1)), ((x0, y1, z0), (x0, y1, z1))
                            ]
                            for p1, p2 in edges:
                                line_x.extend([p1[0], p2[0], None])
                                line_y.extend([p1[1], p2[1], None])
                                line_z.extend([p1[2], p2[2], None])

                            fig_pallet_3d.add_trace(go.Mesh3d(
                                x=[x0, x1, x1, x0, x0, x1, x1, x0],
                                y=[y0, y0, y1, y1, y0, y0, y1, y1],
                                z=[z0, z0, z0, z0, z1, z1, z1, z1],
                                i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                                j=[1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6],
                                k=[2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5],
                                color=color, opacity=0.55, showlegend=False, hoverinfo='skip',
                                flatshading=True,
                                lighting=dict(ambient=0.6, diffuse=0.8, roughness=0.3, specular=0.15)
                            ))

                fig_pallet_3d.add_trace(go.Scatter3d(
                    x=line_x, y=line_y, z=line_z,
                    mode='lines',
                    line=dict(color='#1864ab', width=2),
                    name="Cardboard Boxes"
                ))

                fig_pallet_3d.update_layout(
                    scene=dict(
                        xaxis=dict(title="Length (mm)", range=[-50, active_p_spec["l"]+50], gridcolor='lightgray'),
                        yaxis=dict(title="Width (mm)", range=[-50, active_p_spec["w"]+50], gridcolor='lightgray'),
                        zaxis=dict(title="Height (mm)", range=[-150, 1100], gridcolor='lightgray'),
                        aspectmode='data',
                        camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
                    ),
                    margin=dict(l=0, r=0, b=0, t=0),
                    height=500
                )
                st.plotly_chart(fig_pallet_3d, use_container_width=True)
            except Exception as e_pall_plotly:
                st.warning(f"Error rendering interactive 3D pallet view: {e_pall_plotly}")

    # ==========================================================================
    # TAB 3: MCKEE GRAVITY COMPRESSION SAFETY CHECK
    # ==========================================================================
    with tab_compression:
        st.subheader("🗜️ Corrugated Cardboard McKee Compression Strength Checker")
        st.markdown(f"Validate if the bottom cardboard box can handle the heavy vertical static loads from the stack above on a **{max_pallet_height_limit} mm** pallet layout.")

        st.markdown("#### ⚙️ Stacking Setup")
        col_setup_1, col_setup_2 = st.columns(2)

        with col_setup_1:
            stack_style = st.selectbox(
                "Select Pallet Stacking Configuration:",
                ["Single Pallet Load", "Double-Stacked Pallets (Pallet-on-Pallet)"],
                help="Single Pallet checks local column load. Double Stacking adds the entire gross weight of the top pallet onto the bottom boxes."
            )

        with col_setup_2:
            selected_box_t3 = st.selectbox(
                "Select Box Type to inspect compression strength (Synchronized):",
                options=available_boxes,
                key="tab3_box_selector",
                on_change=sync_from_tab3
            )
            st.session_state["global_selected_box"] = selected_box_t3

        viz_box_t3 = sorted_df[sorted_df["Box ID / Specification"] == st.session_state["global_selected_box"]].iloc[0]

        st.markdown("#### 🪵 3. Load, Environment & Logistics Parameters")
        col_moisture, col_spread, col_fragility = st.columns(3)
        with col_moisture:
            moisture_sel = st.selectbox("Moisture (Humidity):", ["Dry", "Normal", "Humid", "Wet"], index=1, help="Humidity weakens boxes over time.")
        with col_spread:
            spread_sel = st.selectbox("Load spread:", ["Even", "Uneven", "Center", "Corner"], index=0)
        with col_fragility:
            fragility_sel = st.selectbox("Fragility:", ["Low", "Medium", "High"], index=1)

        col_storage, col_transport = st.columns(2)
        with col_storage:
            storage_sel = st.selectbox("Storage Duration:", ["Short (days)", "Medium (weeks)", "Long (months)"], index=1)
        with col_transport:
            transport_sel = st.selectbox("Transport Handling / Vibration:", ["LTL/FTL Truck", "Parcel shipping", "Air/Sea Cargo"], index=1)

        f_moisture = {"Dry": 1.0, "Normal": 1.1, "Humid": 1.3, "Wet": 1.6}[moisture_sel]
        f_spread = {"Even": 1.0, "Uneven": 1.2, "Center": 1.35, "Corner": 1.5}[spread_sel]
        f_fragility = {"Low": 1.0, "Medium": 1.15, "High": 1.3}[fragility_sel]
        f_storage = {"Short (days)": 1.0, "Medium (weeks)": 1.25, "Long (months)": 1.5}[storage_sel]
        f_transport = {"LTL/FTL Truck": 1.0, "Parcel shipping": 1.3, "Air/Sea Cargo": 1.4}[transport_sel]

        QUALITY_PROPERTIES = {
            "1.20B": {"ect": 3.0, "thickness": 3.0, "name": "Single Wall - B Flute"},
            "1.20C": {"ect": 3.8, "thickness": 4.0, "name": "Single Wall - C Flute"},
            "2.30EB": {"ect": 5.5, "thickness": 4.5, "name": "Double Wall - EB Flute"},
            "2.30BC": {"ect": 7.5, "thickness": 6.5, "name": "Double Wall - BC Flute"}
        }

        q_class_t3 = str(viz_box_t3["Quality Class"]).strip()
        props_t3 = QUALITY_PROPERTIES.get(q_class_t3, {"ect": 4.0, "thickness": 3.5, "name": "Custom / Unknown Grade"})

        ect_val_t3 = props_t3["ect"]
        thickness_val_t3 = props_t3["thickness"]
        q_name_t3 = props_t3["name"]

        box_perimeter_t3 = 2 * (viz_box_t3["Int. Length [mm]"] + viz_box_t3["Int. Width [mm]"])
        bct_n_t3 = 1.82 * ect_val_t3 * np.sqrt(thickness_val_t3 * box_perimeter_t3)
        bct_kg_t3 = round(bct_n_t3 / 9.81, 1) 

        sf_t3 = round(1.5 * f_moisture * f_spread * f_fragility * f_storage * f_transport, 2)
        bct_safe_load_t3 = round(bct_kg_t3 / sf_t3, 1)

        bx_ext_l_t3 = viz_box_t3["Ext. Length [mm]"]
        bx_ext_w_t3 = viz_box_t3["Ext. Width [mm]"]
        bx_ext_h_t3 = viz_box_t3["Ext. Height [mm]"]

        # Pull operator fine-tuned box weight for McKee compression check!
        t3_qty_key = f"manual_qty_{st.session_state['global_selected_box']}"
        active_t3_pcs = int(st.session_state.get(t3_qty_key, viz_box_t3["Number of Parts per Box"]))
        active_t3_wt = round((active_t3_pcs * prod_wt) + estimate_box_weight(bx_ext_l_t3, bx_ext_w_t3, bx_ext_h_t3, viz_box_t3["Quality Class"]), 2)

        _, z_layers_calc_t3, best_layer_qty_t3, _, p_wt_calc_t3, _, _, _ = calculate_pallet_stacking(1200, 800, bx_ext_l_t3, bx_ext_w_t3, bx_ext_h_t3, active_t3_wt, active_t3_pcs)
        boxes_above_t3 = max(0, z_layers_calc_t3 - 1)
        actual_bottom_load_t3 = round(boxes_above_t3 * active_t3_wt, 1)

        if stack_style == "Double-Stacked Pallets (Pallet-on-Pallet)":
            top_pallet_weight_contribution_t3 = round(p_wt_calc_t3 / max(1, best_layer_qty_t3), 1)
            actual_bottom_load_t3 = round(actual_bottom_load_t3 + top_pallet_weight_contribution_t3, 1)

        col_comp_kpis = st.columns(4)
        with col_comp_kpis[0]:
            st.metric("💪 Theoretical Box BCT Strength", f"{bct_kg_t3} kg", help="Ultimate crushing force of a single box.")
        with col_comp_kpis[1]:
            st.metric("🛡️ Combined Safety Factor (SF)", f"{sf_t3}x", help="Dynamic stacking margin calculated based on climate, storage, and handling conditions.")
        with col_comp_kpis[2]:
            st.metric("🔒 Safe Design Capacity", f"{bct_safe_load_t3} kg", help=f"Maximum allowed load applying a {sf_t3}x safety threshold.")
        with col_comp_kpis[3]:
            st.metric("🏋️ Actual Load on Bottom Box", f"{actual_bottom_load_t3} kg", help="Total static weight supported by the lowest box on the stack.")

        st.markdown("#### 🔍 Structural Safety Verdict:")
        if actual_bottom_load_t3 == 0:
            st.markdown(f"""
            <div class='success-box'>
                <b>🟢 Safe (Single Layer Stack):</b> There are no other layers stacked above this box on the pallet. Compression failure is mathematically impossible.
            </div>
            """, unsafe_allow_html=True)
        elif actual_bottom_load_t3 <= bct_safe_load_t3:
            st.markdown(f"""
            <div class='success-box'>
                <b>🟢 Safe Stacking Approved:</b> The actual load of <b>{actual_bottom_load_t3} kg</b> is within the safe limit of <b>{bct_safe_load_t3} kg</b>. 
                Cardboard quality class <b>{q_class_t3} ({q_name_t3})</b> is structurally sufficient for the bottom layers of this stack under current environment variables!
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='danger-box'>
                <b>🚨 Warning - Structural Failure Risk:</b> The actual load of <b>{actual_bottom_load_t3} kg</b> exceeds the safe stacked design capacity of <b>{bct_safe_load_t3} kg</b> under these environmental conditions!<br>
                <b>Recommendation:</b><br>
                1. Upgrade the cardboard to a stronger grade (e.g., <b>2.30BC Double-Wall</b>).<br>
                2. Decrease the stacking height on the pallet (reduce the number of layers).<br>
                3. Use corner-board protectors to reinforce structural load paths.
            </div>
            """, unsafe_allow_html=True)

        # RESTORED STEP-BY-STEP MATHEMATICAL WORKINGS (MCKEE STANDARD)
        st.markdown("<div class='guide-box'><h5>🧮 Step-by-Step Mathematical Workings (McKee Metric Standard):</h5>"
                    "The Box Compression Test (BCT) is computed dynamically using metric units:</div>", unsafe_allow_html=True)

        st.latex(r"\text{BCT (Newtons)} = 1.82 \times \text{ECT} \times \sqrt{t \times P}")
        st.latex(r"\text{BCT (kg)} = \frac{\text{BCT (Newtons)}}{9.81 \text{ m/s}^2}")
        st.latex(r"\text{Safe Design Capacity} = \frac{\text{BCT (kg)}}{\text{Combined Safety Factor (SF)}}")

        st.markdown(f"""
        <div class='guide-box' style='margin-top:-20px; border-top-left-radius:0px; border-top-right-radius:0px; border-top:0px;'>
            <b>Active Box Parameters:</b>
            <ul>
                <li><b>ECT (Edge Crush Test):</b> Quality class <b>{q_class_t3}</b> baseline is <b>{ect_val_t3} N/mm</b>.</li>
                <li><b>t (Thickness):</b> Quality class <b>{q_class_t3}</b> baseline is <b>{thickness_val_t3} mm</b>.</li>
                <li><b>P (Perimeter):</b> Measured boundary is <b>{int(box_perimeter_t3)} mm</b> (Lengthwise wall perimeter).</li>
            </ul>
            <hr style='border: 0.5px solid rgba(148,163,184,0.3);'>
            <b>Step-by-Step Calculations:</b><br><br>
            <b>1. Pristine Crushing Force:</b><br>
            1.82 × {ect_val_t3} N/mm × √({thickness_val_t3} mm × {int(box_perimeter_t3)} mm) = <b>{bct_n_t3:.2f} Newtons</b><br><br>
            <b>2. Mass Conversion (kg):</b><br>
            {bct_n_t3:.2f} N ÷ 9.81 m/s² = <b>{bct_kg_t3} kg</b><br><br>
            <b>3. Stacking Environment Safety Limit applied ({sf_t3}x):</b><br>
            {bct_kg_t3} kg ÷ {sf_t3} = <b>{bct_safe_load_t3} kg</b> (Safe Design Capacity)
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("⚠️ No suitable boxes in your database can fit this product under the active weight or dimension parameters.")
