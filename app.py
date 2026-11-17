import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import base64
import plotly.graph_objects as go
import itertools
import json
from urllib import request

# ==============================================================================
# 1. PAGE CONFIGURATION & ENTERPRISE DESIGN SYSTEM (CSS)
# ==============================================================================
st.set_page_config(
    page_title="Packaging Density & Box Recommender Tool",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme-Proof Styling: Supports Light and Dark themes perfectly
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
    .info-card {
        background-color: rgba(37, 99, 235, 0.08);
        padding: 14px 16px;
        border-radius: 10px;
        border-left: 4px solid #2563eb;
        margin-bottom: 15px;
        font-size: 13px;
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
        padding: 2px 8px; border-radius: 6px; font-size: 13px;
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

    numeric_cols = [
        'Ext. Length [mm]', 'Ext.Width [mm]', 'Ext. Height [mm]',
        'Int.Length [mm]', 'Width [mm]', 'Height [mm]', 'Max. Load [kg]'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
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
# 3. BENCHMARK PILOT TEST CASES DEFINITION & HELPERS
# ==============================================================================
PILOT_TEST_CASES = {
    "-- Custom / Manual --": {
        "l": 170.0, "w": 110.0, "h": 40.0, "wt": 0.25,
        "material": "Select Material...", "method": "Uniform", "nest_offset": 20.0, "is_small": False
    },
    "TC-1: Industrial Hex Screws & Bolts (Random Bulk)": {
        "l": 12.0, "w": 12.0, "h": 60.0, "wt": 0.015,
        "material": "Mild Steel", "method": "Random (Bulk Pour)", "nest_offset": 0.0, "is_small": True
    },
    "TC-2: Precision Control Valves (Uniform Grid)": {
        "l": 45.0, "w": 35.0, "h": 30.0, "wt": 0.120,
        "material": "Mild Steel", "method": "Uniform", "nest_offset": 0.0, "is_small": False
    },
    "TC-3: Deep-Drawn Metal Stamping Parts (Uniform Grid)": {
        "l": 180.0, "w": 90.0, "h": 40.0, "wt": 0.350,
        "material": "Mild Steel", "method": "Uniform", "nest_offset": 0.0, "is_small": False
    },
    "TC-4: Injection Moulded Shells / Tubs (Stackable Nesting)": {
        "l": 210.0, "w": 150.0, "h": 80.0, "wt": 0.180,
        "material": "Polypropylene (PP)", "method": "Stackable (Nesting)", "nest_offset": 25.0, "is_small": False
    },
    "TC-5: Aluminum Die-Cast Housing (Heavy / Aesthetic Uniform)": {
        "l": 140.0, "w": 120.0, "h": 70.0, "wt": 0.650,
        "material": "Aluminum", "method": "Uniform", "nest_offset": 0.0, "is_small": False
    }
}

def log_feedback_locally(entry):
    feedback_file = "feedback_log.csv"
    df_new = pd.DataFrame([entry])
    if not os.path.exists(feedback_file):
        df_new.to_csv(feedback_file, index=False)
    else:
        df_new.to_csv(feedback_file, mode='a', header=False, index=False)

# ==============================================================================
# 4. RECOMMENDATION SYSTEM MATHEMATICS & PACKING ENGINES
# ==============================================================================
@st.cache_data
def calculate_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h, rule, 
                      clear_side, clear_height, sep_xy, sep_z, 
                      enforce_lot=False, lot_multiplier=24,
                      order_method="Uniform", nest_offset=20.0, bulk_density=55.0,
                      max_box_payload=15.0, part_weight=0.25):

    single_part_vol = max(1.0, p_l * p_w * p_h)

    # -------------------------------------------------------------
    # METHOD 1: RANDOM (BULK POUR) PACKING
    # -------------------------------------------------------------
    if order_method == "Random (Bulk Pour)":
        usable_vol = max(0.0, (box_int_l - 2 * clear_side) * (box_int_w - 2 * clear_side) * (box_int_h - clear_height))
        effective_capacity_vol = (usable_vol * (bulk_density / 100.0))
        qty_by_vol = int(effective_capacity_vol // single_part_vol)

        # Ergonomic handheld weight safety limit (15 kg max)
        effective_payload_limit = min(float(max_box_payload), 15.0)
        qty_by_weight = int(effective_payload_limit // part_weight) if part_weight > 0 else qty_by_vol

        best_qty = max(1, min(qty_by_vol, qty_by_weight))
        if enforce_lot and best_qty >= lot_multiplier:
            best_qty = (best_qty // lot_multiplier) * lot_multiplier

        return best_qty, (p_l, p_w, p_h), (0, 0, 0), qty_by_vol

    # -------------------------------------------------------------
    # METHOD 2 & 3: UNIFORM OR STACKABLE (NESTING)
    # -------------------------------------------------------------
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
    best_config = (p_l, p_w, p_h)
    best_grid_layout = (0, 0, 0)

    for px, py, pz in orientations:
        nx = max(0, int((box_int_l - (2 * clear_side) + sep_xy) // (px + sep_xy)))
        ny = max(0, int((box_int_w - (2 * clear_side) + sep_xy) // (py + sep_xy)))

        if order_method == "Stackable (Nesting)":
            avail_h = box_int_h - clear_height
            if avail_h < pz:
                nz = 0
            else:
                effective_step = max(5.0, nest_offset + sep_z)
                nz = 1 + int((avail_h - pz) // effective_step)
        else:
            nz = max(0, int((box_int_h - clear_height + sep_z) // (pz + sep_z)))

        total_parts = nx * ny * nz
        if total_parts > best_qty:
            best_qty = total_parts
            best_config = (px, py, pz)
            best_grid_layout = (nx, ny, nz)

    raw_max = best_qty
    if enforce_lot and best_qty >= lot_multiplier:
        aligned_qty = (best_qty // lot_multiplier) * lot_multiplier
        return aligned_qty, best_config, best_grid_layout, raw_max

    return best_qty, best_config, best_grid_layout, raw_max

def determine_placement_style(p_l, p_w, p_h, oz, method="Uniform"):
    if method == "Random (Bulk Pour)":
        return "🟡 RANDOM BULK FILL (Disorganized pour, unsegregated parts)"
    elif method == "Stackable (Nesting)":
        return "🔵 STACKABLE NESTING (Interlocking hollow cavity stacking)"
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

def get_live_box_metrics(row, weight_per_part, single_part_vol, active_method):
    box_spec = row["Box ID / Specification"]
    qty_key = f"manual_qty_{box_spec}"
    default_max_qty = int(row["No of Parts per Box"])
    active_qty = int(st.session_state.get(qty_key, default_max_qty))

    ext_l = row.get("Ext. Length [mm]")
    ext_w = row.get("Ext.Width [mm]") if "Ext.Width [mm]" in row else row.get("Ext. Width [mm]")
    ext_h = row.get("Ext. Height [mm]")

    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row.get("Flute Type") or row.get("Quality"))
    live_total_weight = round((active_qty * weight_per_part) + box_weight, 2)

    int_l = row.get("Int.Length [mm]") if "Int.Length [mm]" in row else row.get("Int. Length [mm]")
    int_w = row.get("Width [mm]") if "Width [mm]" in row else row.get("Int. Width [mm]")
    int_h = row.get("Height [mm]") if "Height [mm]" in row else row.get("Int. Height [mm]")

    box_internal_vol = max(1.0, int_l * int_w * int_h)
    live_vol_efficiency = round(((active_qty * single_part_vol) / box_internal_vol) * 100, 2)

    return active_qty, live_total_weight, live_vol_efficiency

def calculate_pallet_stacking(pallet_l, pallet_w, ext_l, ext_w, ext_h, box_wt, pcs_box, pallet_tare=23.0, max_h=826.0, max_wt=600.0):
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

def get_resolved_directive_row(df, l, w, h, q):
    match = df[(df['Ext. Length [mm]'] == l) & (df['Ext.Width [mm]'] == w) & (df['Ext. Height [mm]'] == h) & (df['Quality'].astype(str).str.strip() == q)]
    if not match.empty:
        row = match.iloc[0].copy()
        row["Box ID / Specification"] = f"{row['BoxSize']} [{str(row['Quality']).strip()}]"
        return row, True

    match_tol = df[(abs(df['Ext. Length [mm]'] - l) <= 10) & (abs(df['Ext.Width [mm]'] - w) <= 10) & (df['Quality'].astype(str).str.strip() == q)]
    if not match_tol.empty:
        row_mod = match_tol.iloc[0].copy()
        row_mod['Ext. Length [mm]'] = l
        row_mod['Ext.Width [mm]'] = w
        row_mod['Ext. Height [mm]'] = h
        row_mod['Int.Length [mm]'] = max(10.0, l - 15.0)
        row_mod['Width [mm]'] = max(10.0, w - 15.0)
        row_mod['Height [mm]'] = max(10.0, h - 10.0)
        row_mod["Box ID / Specification"] = f"{row_mod['BoxSize']} [{str(row_mod['Quality']).strip()}]"
        return row_mod, True

    thick = 10 if "2.30" in q else 6
    box_size_key = f"DIR-SPEC-{int(l)}x{int(w)}x{int(h)}"
    fallback_series = pd.Series({
        'BoxSize': box_size_key,
        'Quality': q,
        'Quality Class': q,
        'Ext. Length [mm]': l,
        'Ext.Width [mm]': w,
        'Ext. Height [mm]': h,
        'Int.Length [mm]': max(10.0, l - 2*thick),
        'Width [mm]': max(10.0, w - 2*thick),
        'Height [mm]': max(10.0, h - thick),
        'Max. Load [kg]': 15.0,
        'PL': 1.55 if l > 450 else 0.95,
        'Box Price (€)': 1.55 if l > 450 else 0.95,
        'Flute Type': q,
        'Int. Length [mm]': max(10.0, l - 2*thick),
        'Int. Width [mm]': max(10.0, w - 2*thick),
        'Int. Height [mm]': max(10.0, h - thick),
        'Box ID / Specification': f"{box_size_key} [{q}]"
    })
    return fallback_series, False

# ==============================================================================
# 5. SIDEBAR: OPERATOR INPUTS, BENCHMARK PRESETS & CLASSIFIER
# ==============================================================================
st.sidebar.header("⚙️ Optimization Strategy")
sort_criteria = st.sidebar.selectbox(
    "Rank Box Options By:", 
    [
        "Multi-Criteria Priority (Vol % ➔ Weight ➔ Qty)",
        "Volumetric Efficiency (%)", 
        "Number of Parts per Box", 
        "Box Price (€)",
        "Ergonomic Color Tier"
    ],
    help="Default priority uses weighted index: Volumetric Efficiency (60%) ➔ Weight Compliance (25%) ➔ Quantity Yield (15%)."
)

# -------------------------------------------------------------
# BENCHMARK PILOT TEST CASES (PRESET HANDLER)
# -------------------------------------------------------------
def on_pilot_preset_change():
    selected = st.session_state["pilot_preset_dropdown"]
    if selected != "-- Custom / Manual --":
        p_data = PILOT_TEST_CASES[selected]
        st.session_state["spec_prod_l"] = float(p_data["l"])
        st.session_state["spec_prod_w"] = float(p_data["w"])
        st.session_state["spec_prod_h"] = float(p_data["h"])
        st.session_state["spec_prod_wt"] = float(p_data["wt"])
        st.session_state["spec_material"] = p_data["material"]
        st.session_state["order_method_selector"] = p_data["method"]
        st.session_state["nest_offset_input"] = float(p_data["nest_offset"])
        st.session_state["active_cad_mesh"] = None

with st.sidebar.expander("🧪 Benchmark Pilot Test Cases", expanded=True):
    preset_choice = st.selectbox(
        "Load Pre-Configured Benchmark Test Case:",
        options=list(PILOT_TEST_CASES.keys()),
        index=0,
        key="pilot_preset_dropdown",
        on_change=on_pilot_preset_change
    )
    if preset_choice != "-- Custom / Manual --":
        st.caption(f"⚡ Loaded parameters for **{preset_choice.split(':')[0]}**.")

# Initialize widget session state defaults if absent
if "spec_prod_l" not in st.session_state: st.session_state["spec_prod_l"] = 170.0
if "spec_prod_w" not in st.session_state: st.session_state["spec_prod_w"] = 110.0
if "spec_prod_h" not in st.session_state: st.session_state["spec_prod_h"] = 40.0
if "spec_prod_wt" not in st.session_state: st.session_state["spec_prod_wt"] = 0.25
if "spec_material" not in st.session_state: st.session_state["spec_material"] = "Select Material..."
if "order_method_selector" not in st.session_state: st.session_state["order_method_selector"] = "Uniform"
if "nest_offset_input" not in st.session_state: st.session_state["nest_offset_input"] = 20.0
if "active_cad_mesh" not in st.session_state: st.session_state["active_cad_mesh"] = None

# -------------------------------------------------------------
# PRODUCT SPECIFICATIONS & CAD UPLOADER
# -------------------------------------------------------------
MATERIAL_DENSITIES = {
    "Assembly (Multi-Material/Manual Weight)": "manual",  
    "ABS Plastic": 1.04,
    "PLA Plastic": 1.24,
    "Polypropylene (PP)": 0.90,
    "Polycarbonate (PC)": 1.20,
    "Aluminum": 2.70,
    "Mild Steel": 7.85,
    "Stainless Steel": 8.00
}

with st.sidebar.expander("📂 Product Specifications & CAD", expanded=False):
    uploaded_stl = st.file_uploader("Upload 3D CAD File (.STL, .STEP, .STP)", type=["stl", "step", "stp"])
    material_selected = True  
    assembly_mode = False

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

            if mesh_cad.vertices.size > 0:
                st.session_state["active_cad_mesh"] = mesh_cad
                bounds = mesh_cad.bounding_box.extents
                dims = sorted(bounds)
                auto_h = round(dims[0], 1)
                auto_w = round(dims[1], 1)
                auto_l = round(dims[2], 1)

                cad_volume = max(mesh_cad.volume, 0.001)
                is_cm_scale = auto_l < 50.0
                if is_cm_scale:
                    auto_l *= 10.0; auto_w *= 10.0; auto_h *= 10.0
                    cad_volume *= 1000.0  

                st.session_state["spec_prod_l"] = float(auto_l)
                st.session_state["spec_prod_w"] = float(auto_w)
                st.session_state["spec_prod_h"] = float(auto_h)
                st.success(f"📐 Extracted: {auto_l}x{auto_w}x{auto_h} mm")
        except Exception as e_cad:
            st.warning(f"Error reading CAD mesh: {e_cad}")

    mat_options = ["Select Material..."] + list(MATERIAL_DENSITIES.keys())
    current_mat = st.session_state["spec_material"]
    mat_index = mat_options.index(current_mat) if current_mat in mat_options else 0
    selected_material = st.selectbox("Select Part Material:", options=mat_options, index=mat_index, key="spec_material")

    if selected_material == "Select Material...":
        material_selected = False
    elif selected_material == "Assembly (Multi-Material/Manual Weight)":
        assembly_mode = True
    else:
        density = MATERIAL_DENSITIES[selected_material]
        calc_vol = st.session_state["spec_prod_l"] * st.session_state["spec_prod_w"] * st.session_state["spec_prod_h"] * 1e-6
        st.session_state["spec_prod_wt"] = round(calc_vol * density, 3)

    prod_l = st.number_input("Part Length (mm)", min_value=1.0, step=1.0, key="spec_prod_l")
    prod_w = st.number_input("Part Width (mm)", min_value=1.0, step=1.0, key="spec_prod_w")
    prod_h = st.number_input("Part Height (mm)", min_value=1.0, step=1.0, key="spec_prod_h")
    prod_wt = st.number_input("Part Weight (kg)", min_value=0.001, step=0.01, format="%.3f", key="spec_prod_wt")

# -------------------------------------------------------------
# AUTONOMOUS METHODOLOGY CLASSIFIER & ORDER CONTROLS
# -------------------------------------------------------------
part_bbox_vol = max(1.0, prod_l * prod_w * prod_h)
mesh_cad = st.session_state.get("active_cad_mesh")
if mesh_cad is not None and hasattr(mesh_cad, "volume") and mesh_cad.volume > 0:
    cavity_index = max(0.0, min(100.0, (1.0 - (mesh_cad.volume / part_bbox_vol)) * 100.0))
else:
    cavity_index = 0.0

is_tiny_hardware = (prod_l <= 35.0 and prod_w <= 35.0 and prod_wt <= 0.04)

if is_tiny_hardware:
    ai_recommendation = "Random (Bulk Pour)"
    ai_reason = "Small hardware/fastener geometry (weight & size best suited for bulk pouring)."
elif cavity_index > 45.0 or (prod_h < 0.35 * max(prod_l, prod_w) and preset_choice.startswith("TC-4")):
    ai_recommendation = "Stackable (Nesting)"
    ai_reason = f"High internal hollow cavity detected (Cavity Index: {cavity_index:.1f}%)."
else:
    ai_recommendation = "Uniform"
    ai_reason = "Solid/rigid aesthetic or precision component requiring orthogonal divider protection."

with st.sidebar.expander("⚙️ Order Methodology & Nesting Controls", expanded=True):
    st.markdown(f"""
    <div class="info-card">
        <b>🤖 Autonomous Analysis Recommendation:</b><br>
        <span style="font-weight:700; color:#2563eb; font-size:14px;">{ai_recommendation}</span><br>
        <span style="color:#64748b; font-size:11px;">{ai_reason}</span>
    </div>
    """, unsafe_allow_html=True)

    method_options = ["Uniform", "Stackable (Nesting)", "Random (Bulk Pour)"]
    current_method = st.session_state.get("order_method_selector", ai_recommendation)
    active_order_method = st.selectbox(
        "Active Order Methodology (Operator Override):",
        options=method_options,
        index=method_options.index(current_method) if current_method in method_options else 0,
        key="order_method_selector",
        help="Select packing physics. Choose 'Random' for screws/bolts, 'Stackable' for hollow nesting, or 'Uniform' for grid partitions."
    )

    nest_offset_val = 20.0
    bulk_fill_density = 55.0
    if active_order_method == "Stackable (Nesting)":
        nest_offset_val = st.slider(
            "Nesting Step / Offset Depth (mm):",
            min_value=2.0, max_value=max(10.0, float(prod_h)),
            value=float(min(st.session_state.get("nest_offset_input", 20.0), prod_h)),
            step=1.0,
            help="Protrusion height when one part is nested inside another."
        )
    elif active_order_method == "Random (Bulk Pour)":
        bulk_fill_density = st.slider(
            "Bulk Fill Packing Density (%):",
            min_value=35.0, max_value=70.0, value=55.0, step=1.0,
            help="Empirical packing fraction for randomized loose parts (typically 50-60%)."
        )
        st.caption("ℹ️ Orientation rules are automatically disabled for random bulk pouring.")

    if active_order_method != "Random (Bulk Pour)":
        orientation_rule = st.selectbox(
            "Select Packing Orientation:",
            ["Automatic (Highest Quantity)", "Force Flat Packing Only", "Force Standing on Edge", "Force Standing Vertical"]
        )
    else:
        orientation_rule = "Automatic (Highest Quantity)"

with st.sidebar.expander("📂 Packaging Directives & Tolerances", expanded=False):
    max_box_weight_limit = st.number_input("Max Manual Box Weight Limit (kg)", min_value=5.0, max_value=30.0, value=13.0, step=0.5)
    max_pallet_weight_limit = st.number_input("Max Gross Pallet Weight Limit (kg)", min_value=100.0, max_value=1500.0, value=600.0, step=25.0)
    max_pallet_height_limit = st.number_input("Max Total Pallet Stack Height (mm)", min_value=500.0, max_value=1500.0, value=970.0, step=10.0)

    enforce_box_dim_cap = st.checkbox("Enforce Custom Box Dimension Limits", value=False)
    if enforce_box_dim_cap:
        limit_l = st.number_input("Max External Length (mm)", min_value=100.0, max_value=2000.0, value=600.0, step=10.0)
        limit_w = st.number_input("Max External Width (mm)", min_value=100.0, max_value=400.0, value=400.0, step=10.0)
        limit_h = st.number_input("Max External Height (mm)", min_value=50.0, max_value=2000.0, value=270.0, step=10.0)

    st.markdown("#### 🏭 Production LOT Alignment")
    lot_alignment_enabled = st.checkbox("Align Box Quantity to LOT Multiples", value=False)
    lot_step = 24
    if lot_alignment_enabled:
        lot_step = st.selectbox("Select Production LOT Multiplier:", options=[24, 48, 72], index=0)

    st.markdown("#### 📏 Clearance Spacers")
    clear_side = st.slider("Sides Buffer (mm)", min_value=0, max_value=20, value=2)
    clear_height = st.slider("Height Buffer (mm)", min_value=0, max_value=20, value=4)
    sep_xy = st.slider("Separator X/Y (mm)", min_value=0, max_value=10, value=2)
    sep_z = st.slider("Separator Z (mm)", min_value=0, max_value=10, value=4)

with st.sidebar.expander("📋 Packaging Directive Ref Boxes", expanded=False):
    alt1_l = st.number_input("Alt I Ext. Length (mm)", value=400.0, step=10.0)
    alt1_w = st.number_input("Alt I Ext. Width (mm)", value=300.0, step=10.0)
    alt1_h = st.number_input("Alt I Ext. Height (mm)", value=220.0, step=10.0)
    alt1_q = st.selectbox("Alt I Quality Class", ["2.30EB", "2.30BC", "1.20C", "1.20B"], index=1)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    alt2_l = st.number_input("Alt II Ext. Length (mm)", value=600.0, step=10.0)
    alt2_w = st.number_input("Alt II Ext. Width (mm)", value=400.0, step=10.0)
    alt2_h = st.number_input("Alt II Ext. Height (mm)", value=200.0, step=10.0)
    alt2_q = st.selectbox("Alt II Quality Class", ["2.30EB", "2.30BC", "1.20C", "1.20B"], index=0)

# ==============================================================================
# 6. EXECUTE CALCULATION ENGINE WITH SMALL-PARTS BOX BOUNDARY
# ==============================================================================
results = []
single_part_vol = max(1.0, prod_l * prod_w * prod_h)
is_small_hardware_mode = (active_order_method == "Random (Bulk Pour)") or (prod_l <= 35.0 and prod_w <= 35.0)

for idx, row in df_inventory.iterrows():
    box_int_l = row['Int.Length [mm]']
    box_int_w = row['Width [mm]']
    box_int_h = row['Height [mm]']
    ext_l = row['Ext. Length [mm]']
    ext_w = row['Ext.Width [mm]']
    ext_h = row['Ext. Height [mm]']
    max_load_cap = row.get('Max. Load [kg]', 15.0)

    if pd.isna(box_int_l) or pd.isna(box_int_w) or pd.isna(box_int_h):
        continue

    # ELIMINATE OVERSIZED PALLET-CRATES (800x600) FOR SCREWS / SMALL BULK HARDWARE
    if is_small_hardware_mode:
        if ext_l > 420.0 or ext_w > 320.0 or ext_h > 260.0:
            continue

    if enforce_box_dim_cap:
        ext_dims_sorted = sorted([ext_l, ext_w])
        req_dims_sorted = sorted([limit_l, limit_w])
        if ext_dims_sorted[1] > req_dims_sorted[1] or ext_dims_sorted[0] > req_dims_sorted[0] or ext_h > limit_h:
            continue

    parts_count, pack_orient, grid_layout, raw_max_qty = calculate_packing(
        box_int_l, box_int_w, box_int_h, 
        prod_l, prod_w, prod_h,
        orientation_rule,
        clear_side, clear_height, sep_xy, sep_z,
        lot_alignment_enabled, lot_step,
        order_method=active_order_method,
        nest_offset=nest_offset_val,
        bulk_density=bulk_fill_density,
        max_box_payload=max_load_cap,
        part_weight=prod_wt
    )
    if parts_count <= 0:
        continue

    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row['Quality'])
    total_payload_wt = parts_count * prod_wt
    total_package_weight = total_payload_wt + box_weight

    if total_payload_wt > max_load_cap:
        continue

    box_internal_vol = box_int_l * box_int_w * box_int_h
    occupied_volume = parts_count * single_part_vol
    vol_efficiency = min(100.0, (occupied_volume / box_internal_vol) * 100.0)
    air_space_percent = max(0.0, 100.0 - vol_efficiency)

    if total_package_weight < 13.0:
        weight_tier = "🟢 1. Green (<13 kg)"
        tier_rank = 1
    elif total_package_weight <= 17.0:
        weight_tier = "🟠 2. Orange (13-17 kg)"
        tier_rank = 2
    else:
        weight_tier = "🔴 3. Red (>17 kg)"
        tier_rank = 3

    q_class = str(row['Quality']).strip()
    box_spec_label = f"{row['BoxSize']} [{q_class}]"

    results.append({
        "Weight Status": weight_tier,
        "Box ID / Specification": box_spec_label,
        "Box Size Key": row['BoxSize'],
        "Box Footprint (Ext)": f"{int(ext_l)}x{int(ext_w)} mm",
        "Flute Type": q_class,             
        "Quality Class": q_class,           
        "Total Weight (kg)": round(total_package_weight, 2),
        "Internal Dimensions": f"{int(box_int_l)}x{int(box_int_w)}x{int(box_int_h)} mm",
        "Ext. Height [mm]": ext_h,
        "No of Parts per Box": parts_count,  
        "Max Geometric Fit": raw_max_qty,
        "Optimal Grid Layout": f"{grid_layout[0]}x{grid_layout[1]}x{grid_layout[2]} (X x Y x Z)" if active_order_method != "Random (Bulk Pour)" else "Loose Bulk Pour",
        "Optimal Orientation": f"{int(pack_orient[0])}x{int(pack_orient[1])}x{int(pack_orient[2])} mm" if active_order_method != "Random (Bulk Pour)" else "Disorganized / Poured",
        "Volumetric Efficiency (%)": round(vol_efficiency, 2),
        "Remaining Air Space (%)": round(air_space_percent, 1),
        "Box Price (€)": row['Box Price (€)'],
        "Tier Rank": tier_rank,

        "Int. Length [mm]": box_int_l, "Int.Length [mm]": box_int_l,
        "Int. Width [mm]": box_int_w, "Width [mm]": box_int_w,
        "Int. Height [mm]": box_int_h, "Height [mm]": box_int_h,
        "Ext. Length [mm]": ext_l, "Ext. Width [mm]": ext_w, "Ext.Width [mm]": ext_w,

        "_nx": grid_layout[0], "_ny": grid_layout[1], "_nz": grid_layout[2],
        "_ox": pack_orient[0], "_oy": pack_orient[1], "_oz": pack_orient[2],
        "_box_vol": box_internal_vol
    })

# ==============================================================================
# 7. RANKING ENGINE & PRIORITY SCORE COMPILATION
# ==============================================================================
if results:
    res_df = pd.DataFrame(results)
    max_vol = res_df["Volumetric Efficiency (%)"].max() if res_df["Volumetric Efficiency (%)"].max() > 0 else 1.0
    max_qty = res_df["No of Parts per Box"].max() if res_df["No of Parts per Box"].max() > 0 else 1.0

    def calculate_priority_score(row):
        v_score = row["Volumetric Efficiency (%)"] / max_vol
        wt = row["Total Weight (kg)"]
        if wt < max_box_weight_limit:
            w_score = 1.0  
        elif wt <= 17.0:
            w_score = 0.6  
        else:
            w_score = 0.1  
        q_score = row["No of Parts per Box"] / max_qty

        score = (0.60 * v_score) + (0.25 * w_score) + (0.15 * q_score)
        if is_small_hardware_mode and (row["Ext. Length [mm]"] > 400 or row["Ext. Width [mm]"] > 300):
            score *= 0.3
        return score

    res_df["Priority Score"] = res_df.apply(calculate_priority_score, axis=1)

    if sort_criteria == "Multi-Criteria Priority (Vol % ➔ Weight ➔ Qty)":
        sort_by_cols = ["Priority Score", "Total Weight (kg)", "Box Price (€)"]
        ascending_rules = [False, True, True]
    elif sort_criteria == "Volumetric Efficiency (%)":
        sort_by_cols = ["Volumetric Efficiency (%)", "Tier Rank", "Box Price (€)"]
        ascending_rules = [False, True, True]
    elif sort_criteria == "Number of Parts per Box":
        sort_by_cols = ["No of Parts per Box", "Tier Rank", "Box Price (€)"]
        ascending_rules = [False, True, True]
    elif sort_criteria == "Box Price (€)":
        sort_by_cols = ["Box Price (€)", "Tier Rank", "No of Parts per Box"]
        ascending_rules = [True, True, False]
    else:  
        sort_by_cols = ["Tier Rank", "Volumetric Efficiency (%)", "Box Price (€)"]
        ascending_rules = [True, False, True]

    sorted_df = res_df.sort_values(by=sort_by_cols, ascending=ascending_rules).reset_index(drop=True)
    available_boxes = list(sorted_df["Box ID / Specification"].values)
    current_best_box = available_boxes[0] if available_boxes else None

    if "previous_best_box" not in st.session_state:
        st.session_state["previous_best_box"] = current_best_box
        st.session_state["global_selected_box"] = current_best_box
    elif st.session_state["previous_best_box"] != current_best_box:
        st.session_state["global_selected_box"] = current_best_box
        st.session_state["previous_best_box"] = current_best_box

    if "global_selected_box" not in st.session_state or st.session_state["global_selected_box"] not in available_boxes:
        st.session_state["global_selected_box"] = current_best_box

    def sync_from_tab1(): st.session_state["global_selected_box"] = st.session_state["tab1_box_selector"]
    def sync_from_tab2(): st.session_state["global_selected_box"] = st.session_state["tab2_box_selector"]
    def sync_from_tab3(): st.session_state["global_selected_box"] = st.session_state["tab3_box_selector"]

    st.session_state["tab1_box_selector"] = st.session_state["global_selected_box"]
    st.session_state["tab2_box_selector"] = st.session_state["global_selected_box"]
    st.session_state["tab3_box_selector"] = st.session_state["global_selected_box"]

    def get_safe_index(available_list, selected_val):
        try: return available_list.index(selected_val)
        except (ValueError, KeyError): return 0

    viz_box_rank1 = sorted_df.iloc[0] if not sorted_df.empty else None
    viz_box_active = sorted_df[sorted_df["Box ID / Specification"] == st.session_state["global_selected_box"]].iloc[0] if not sorted_df.empty else None

    col_title, col_safety_header = st.columns([7, 3])
    with col_title:
        st.markdown(f"""
            <div class='app-header'>
                <h1>📦 BSH Packaging Density & Box Recommender</h1>
                <p>Order Methodology: <b>{active_order_method}</b> | Optimization Mode: {sort_criteria}</p>
            </div>
        """, unsafe_allow_html=True)
    with col_safety_header:
        if viz_box_rank1 is not None:
            r1_active_qty, r1_active_wt, _ = get_live_box_metrics(viz_box_rank1, prod_wt, single_part_vol, active_order_method)
            if r1_active_wt > 17.0:
                st.markdown(f"""
                    <div style='background-color:rgba(239, 68, 68, 0.15); border-left:5px solid #ef4444; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#ef4444; font-size:16px;'>🚨 3. Heavy Load (&gt;17 kg)</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>{r1_active_wt} kg (Forklift Required)</span><br>
                        <span style='font-size:11px;'>Exceeds ergonomic manual limit. Permitted only with mechanical lift aids.</span>
                    </div>
                """, unsafe_allow_html=True)
            elif r1_active_wt >= max_box_weight_limit:
                st.markdown(f"""
                    <div style='background-color:rgba(245, 159, 0, 0.15); border-left:5px solid #f59f00; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#f59f00; font-size:16px;'>🟠 2. Moderate Weight ({max_box_weight_limit}-17 kg)</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>{r1_active_wt} kg (Elevated Weight)</span><br>
                        <span style='font-size:11px;'>Slightly above standard {max_box_weight_limit} kg manual directive. Two-person lift recommended.</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color:rgba(34, 197, 94, 0.15); border-left:5px solid #22c55e; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#22c55e; font-size:16px;'>🟢 1. Light / Safe Weight (&lt;{max_box_weight_limit} kg)</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>Safe at {r1_active_wt} kg</span><br>
                        <span style='font-size:11px;'>Conforms strictly to Packaging Directive (&lt;{max_box_weight_limit} kg). Single-operator manual safe.</span>
                    </div>
                """, unsafe_allow_html=True)

    st.success(f"Connected to Cardboard Database: `{filename_loaded}` | Qualifying Options: {len(sorted_df)} | Active Pilot Profile: 🏷️ {preset_choice}")

    r1_live_qty, r1_live_wt, r1_live_eff = get_live_box_metrics(viz_box_rank1, prod_wt, single_part_vol, active_order_method)
    st.subheader("💡 Best Matched Packing Insights (Rank-1 Box)")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                <b>👑 Best Recommendation</b><br>
                <span style='font-size:11px; font-weight:bold; color:#0056b3;'>
                    {viz_box_rank1['Box ID / Specification']}<br>
                    <span style='color:#dc3545;'>[Flute: {viz_box_rank1['Flute Type']}]</span>
                </span>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box'><b>📦 Live Parts Loaded</b><br><span style='font-size:24px; font-weight:bold; color:#28a745;'>{r1_live_qty} Pcs</span></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-box'><b>📊 Vol. Efficiency</b><br><span style='font-size:24px; font-weight:bold; color:#ffc107;'>{r1_live_eff}%</span></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-box'><b>⚖️ Live Weight</b><br><span style='font-size:24px; font-weight:bold; color:#17a2b8;'>{r1_live_wt} kg</span></div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='metric-box'><b>💰 Box Price</b><br><span style='font-size:24px; font-weight:bold; color:#e83e8c;'>€ {viz_box_rank1['Box Price (€)']:.2f}</span></div>", unsafe_allow_html=True)

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
        st.subheader("🏆 Cardboard Packaging Recommendations")
        all_unique_flutes = sorted(list(sorted_df["Flute Type"].dropna().unique()))
        col_excel_filter, col_export_hub = st.columns([6, 4])
        with col_excel_filter:
            with st.popover("🔽 Filter Table by Flute (Excel-Style Dropdown)", use_container_width=False):
                st.markdown("<b>Filter from 'Flute Type':</b>", unsafe_allow_html=True)
                select_all = st.checkbox("(Select All)", value=True, key="excel_select_all")
                selected_flutes = []
                for fl in all_unique_flutes:
                    is_checked = st.checkbox(f"☑ {fl}", value=select_all, key=f"filter_flute_{fl}")
                    if is_checked: selected_flutes.append(fl)

        filtered_df = sorted_df[sorted_df["Flute Type"].isin(selected_flutes)].copy() if selected_flutes else sorted_df.copy()
        keep_columns = [
            "Box ID / Specification", "Box Footprint (Ext)", "Flute Type",
            "Total Weight (kg)", "No of Parts per Box", "Volumetric Efficiency (%)",
            "Remaining Air Space (%)", "Box Price (€)"
        ]
        display_df = filtered_df[keep_columns].copy()
        display_df.index = display_df.index + 1

        with col_export_hub:
            export_format = st.selectbox("📥 Export Active Table Data...", ["-- Choose Format --", "Export to Excel (.xlsx)", "Export to CSV (.csv)"], index=0)
            if export_format == "Export to Excel (.xlsx)":
                buffer_xls = io.BytesIO()
                with pd.ExcelWriter(buffer_xls, engine='openpyxl') as writer:
                    display_df.to_excel(writer, sheet_name='Recommended_Boxes', index=True)
                st.download_button(label="🟢 Download Excel File", data=buffer_xls.getvalue(), file_name="Recommended_Boxes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            elif export_format == "Export to CSV (.csv)":
                st.download_button(label="🔵 Download CSV File", data=display_df.to_csv(index=True).encode('utf-8'), file_name="Recommended_Boxes.csv", mime="text/csv", use_container_width=True)

        def highlight_exact_weight_hierarchy(row):
            wt = float(row["Total Weight (kg)"])
            bg = "#d4edda; color: #155724;" if wt < max_box_weight_limit else ("#fff3cd; color: #856404;" if wt <= 17.0 else "#f8d7da; color: #721c24;")
            return [f"background-color: {bg} font-weight: 600;"] * len(row)

        styled_df = display_df.style.apply(highlight_exact_weight_hierarchy, axis=1).format({
            "Box Price (€)": "€ {:.2f}", "Volumetric Efficiency (%)": "{:.2f}%",
            "Remaining Air Space (%)": "{:.1f}%", "Total Weight (kg)": "{:.2f} kg"
        })
        st.dataframe(styled_df, use_container_width=True, height=400)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Step-by-Step Visual Blueprint Loading Map")
        safe_index_t1 = get_safe_index(available_boxes, st.session_state["global_selected_box"])
        selected_box_tab1 = st.selectbox(
            "Select a Cardboard Box to inspect its loading blueprints & 3D models (Synchronized):",
            options=available_boxes, index=safe_index_t1, key="tab1_box_selector", on_change=sync_from_tab1
        )

        nx = int(viz_box_active["_nx"])
        ny = int(viz_box_active["_ny"])
        nz = int(viz_box_active["_nz"])
        ox = int(viz_box_active["_ox"])
        oy = int(viz_box_active["_oy"])
        oz = int(viz_box_active["_oz"])
        box_l = viz_box_active["Int. Length [mm]"]
        box_w = viz_box_active["Int. Width [mm]"]
        ext_l = viz_box_active["Ext. Length [mm]"]
        ext_w = viz_box_active["Ext. Width [mm]"]

        max_possible_parts = int(viz_box_active["Max Geometric Fit"])
        default_packed_parts = int(viz_box_active["No of Parts per Box"])
        qty_state_key = f"manual_qty_{st.session_state['global_selected_box']}"
        if qty_state_key not in st.session_state:
            st.session_state[qty_state_key] = default_packed_parts

        st.markdown("##### 🎛️ Operator Quantity Fine-Tuning")
        col_adj_1, col_adj_2 = st.columns([1, 2])
        with col_adj_1:
            active_quantity = st.number_input(
                f"Loaded Parts per Box (Max Geometric: {max_possible_parts})",
                min_value=1, max_value=max(1, max_possible_parts),
                value=int(min(st.session_state[qty_state_key], max(1, max_possible_parts))),
                step=1, key=f"input_{qty_state_key}"
            )
            st.session_state[qty_state_key] = active_quantity
        with col_adj_2:
            override_weight = round((active_quantity * prod_wt) + estimate_box_weight(ext_l, ext_w, viz_box_active["Ext. Height [mm]"], viz_box_active["Flute Type"]), 2)
            override_efficiency = round(((active_quantity * single_part_vol) / (box_l * box_w * viz_box_active["Int. Height [mm]"])) * 100, 2)
            st.info(f"⚡ Live Package Weight: **{override_weight} kg** | Volumetric Efficiency: **{override_efficiency}%** | Loaded: **{active_quantity} / {max_possible_parts} parts**")

        placement_style = determine_placement_style(prod_l, prod_w, prod_h, oz, method=active_order_method)

        with st.container():
            col_text, col_flat, col_stack = st.columns([2.5, 3, 2.5])
            with col_text:
                st.markdown("<div class='guide-box'><h4><b>🛠️ Packing Instruction</b></h4><hr style='border: 0.5px solid rgba(148,163,184,0.3);'>", unsafe_allow_html=True)
                st.markdown(f"<b>Mode:</b> {placement_style}<br>", unsafe_allow_html=True)
                if active_order_method == "Random (Bulk Pour)":
                    st.markdown(f"""
                    <ul>
                        <li>Pour <b>{active_quantity} parts</b> evenly into the container.</li>
                        <li>Maintain loose bulk fill level below the <b>{int(clear_height)} mm</b> top clearance buffer.</li>
                        <li>Apply mandatory bulk bag liner if required for loose hardware.</li>
                    </ul>
                    """, unsafe_allow_html=True)
                else:
                    parts_per_layer = nx * ny
                    active_layers = int(np.ceil(active_quantity / parts_per_layer)) if parts_per_layer > 0 else 1
                    st.markdown(f"""
                    <b>Floor Grid:</b> {nx} columns x {ny} rows ({parts_per_layer} parts/layer).<br>
                    <b>Vertical Stack:</b> {active_layers} active layer(s).<br>
                    <b>Separators:</b> {sep_xy} mm lateral partitions, {sep_z} mm shelf divider sheets.
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_flat:
                fig, ax = plt.subplots(figsize=(6, 4), facecolor='none')
                ax.set_facecolor('none')
                st_text_color = '#FFFFFF' if st.get_option('theme.base') == 'dark' else '#212529'

                ax.add_patch(patches.Rectangle((0, 0), box_l, box_w, fill=False, edgecolor=st_text_color, linewidth=2.5))
                if active_order_method == "Random (Bulk Pour)":
                    ax.add_patch(patches.Rectangle((clear_side, clear_side), box_l - 2*clear_side, box_w - 2*clear_side, fill=True, facecolor='#fef08a', alpha=0.4, hatch='..'))
                    np.random.seed(42)
                    num_scatter = min(200, active_quantity)
                    rx = np.random.uniform(clear_side + 10, box_l - clear_side - 10, num_scatter)
                    ry = np.random.uniform(clear_side + 10, box_w - clear_side - 10, num_scatter)
                    ax.scatter(rx, ry, color='#d97706', s=16, alpha=0.8)
                    ax.text(box_l/2, box_w/2, f"Bulk Pour Scatter\n({active_quantity} Pcs)", ha='center', va='center', fontsize=11, fontweight='bold', color='#b45309')
                else:
                    parts_per_layer = nx * ny
                    total_grid_w = nx * ox + (nx - 1) * sep_xy
                    total_grid_h = ny * oy + (ny - 1) * sep_xy
                    start_x = clear_side + ((box_l - 2*clear_side - total_grid_w) / 2)
                    start_y = clear_side + ((box_w - 2*clear_side - total_grid_h) / 2)
                    for r in range(ny):
                        for c in range(nx):
                            x_pos = start_x + c * (ox + sep_xy)
                            y_pos = start_y + r * (oy + sep_xy)
                            ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#a5d8ff', edgecolor='#1971c2', linewidth=1.2))
                    ax.text(box_l/2, box_w + 12, f"Grid: {nx}x{ny} per layer", color='#dc3545', fontsize=11, fontweight='bold', ha='center')

                ax.set_xlim(-20, box_l + 20)
                ax.set_ylim(-20, box_w + 25)
                ax.set_aspect('equal')
                ax.axis('off')
                st.pyplot(fig)
                plt.close(fig)

            with col_stack:
                active_layers = int(np.ceil(active_quantity / (nx * ny))) if (nx * ny) > 0 else 1
                fig3d = plt.figure(figsize=(4, 3.5), facecolor='none')
                ax3d = fig3d.add_subplot(111, projection='3d', facecolor='none')
                w_scale = 100
                l_scale = w_scale * (box_l / box_w)
                h_scale = 30
                z_aspect = max(30, active_layers * 15)
                ax3d.set_box_aspect((l_scale, w_scale, z_aspect))

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
                    color = '#fef08a' if active_order_method == "Random (Bulk Pour)" else '#a5d8ff'
                    poly = Poly3DCollection(faces, facecolors=color, edgecolors='#1971c2', linewidths=1.2, alpha=0.7)
                    ax3d.add_collection3d(poly)
                    ax3d.text(-25, 20, z_start + h_scale/2, f"L{layer + 1}", color='#dc3545', fontweight='bold', fontsize=9)

                ax3d.set_xlim(-40, l_scale + 10)
                ax3d.set_ylim(-20, w_scale + 10)
                ax3d.set_zlim(0, active_layers * (h_scale + 5) + 10)
                ax3d.view_init(elev=22, azim=-65)
                ax3d.axis('off')
                plt.title("Stacking Height Map", fontsize=11, fontweight='bold', color=st_text_color)
                st.pyplot(fig3d)
                plt.close(fig3d)

        # -------------------------------------------------------------
        # RESTORED: INTERACTIVE 3D BOX & PART TWIN VIEWPORT (PLOTLY)
        # -------------------------------------------------------------
        st.markdown("<hr style='margin:25px 0; border:0; border-top:1px solid rgba(148,163,184,0.2);'>", unsafe_allow_html=True)
        st.subheader("🔄 Interactive 3D Box & Part Twin Viewport (Rotatable)")
        col_cad, col_packing_3d = st.columns(2)
        with col_cad:
            st.markdown("##### 🔍 Rotatable 3D CAD Part Model")
            mesh_display = st.session_state.get("active_cad_mesh")
            if mesh_display is not None:
                try:
                    v_coords = mesh_display.vertices
                    f_indices = mesh_display.faces
                    fig_cad = go.Figure(data=[
                        go.Mesh3d(
                            x=v_coords[:, 0], y=v_coords[:, 1], z=v_coords[:, 2],
                            i=f_indices[:, 0], j=f_indices[:, 1], k=f_indices[:, 2],
                            color='#d1d5db', opacity=1.0,
                            flatshading=False,
                            lighting=dict(ambient=0.5, diffuse=0.9, roughness=0.15, specular=1.6, fresnel=0.6),
                            name="3D CAD Part"
                        )
                    ])
                    fig_cad.update_layout(
                        scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
                        margin=dict(l=0, r=0, b=0, t=0), height=380
                    )
                    st.plotly_chart(fig_cad, use_container_width=True)
                except Exception as e_plotly:
                    st.info(f"CAD render notice: {e_plotly}")
            else:
                st.info("💡 Upload a 3D CAD file (.STL / .STEP) to activate the interactive 3D digital part twin viewport.")

        with col_packing_3d:
            st.markdown("##### 📦 Rotatable 3D Box Packing Layout")
            try:
                fig_pack = go.Figure()
                def add_wireframe_compartment(fig_scene, x_pos, y_pos, z_pos, dx, dy, dz):
                    cv = np.array([
                        [x_pos, y_pos, z_pos], [x_pos + dx, y_pos, z_pos],
                        [x_pos + dx, y_pos + dy, z_pos], [x_pos, y_pos + dy, z_pos],
                        [x_pos, y_pos, z_pos + dz], [x_pos + dx, y_pos + dz, z_pos + dz],
                        [x_pos + dx, y_pos + dy, z_pos + dz], [x_pos, y_pos + dy, z_pos + dz]
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
                            showlegend=False, hoverinfo='skip'
                        ))

                if active_order_method == "Random (Bulk Pour)":
                    np.random.seed(42)
                    num_scatter_3d = min(150, active_quantity)
                    rx_3d = np.random.uniform(clear_side + 5, box_l - clear_side - 5, num_scatter_3d)
                    ry_3d = np.random.uniform(clear_side + 5, box_w - clear_side - 5, num_scatter_3d)
                    rz_3d = np.random.uniform(5, max(10, viz_box_active["Int. Height [mm]"] - clear_height), num_scatter_3d)
                    fig_pack.add_trace(go.Scatter3d(
                        x=rx_3d, y=ry_3d, z=rz_3d,
                        mode='markers',
                        marker=dict(size=4, color='#f59e0b', opacity=0.8),
                        name="Random Poured Parts"
                    ))
                else:
                    parts_placed = 0
                    for layer in range(active_layers):
                        z_pos = layer * (nest_offset_val if active_order_method == "Stackable (Nesting)" else (oz + sep_z))
                        for r in range(ny):
                            for c in range(nx):
                                if parts_placed >= active_quantity: break
                                x_pos = clear_side + c * (ox + sep_xy)
                                y_pos = clear_side + r * (oy + sep_xy)
                                add_wireframe_compartment(fig_pack, x_pos, y_pos, z_pos, ox, oy, oz)
                                parts_placed += 1

                # Outer Box Boundary Wireframe
                box_v = np.array([
                    [0, 0, 0], [box_l, 0, 0], [box_l, box_w, 0], [0, box_w, 0],
                    [0, 0, viz_box_active["Int. Height [mm]"]], [box_l, 0, viz_box_active["Int. Height [mm]"]],
                    [box_l, box_w, viz_box_active["Int. Height [mm]"]], [0, box_w, viz_box_active["Int. Height [mm]"]]
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
                        mode='lines', line=dict(color='#212529', width=3),
                        showlegend=False, hoverinfo='skip'
                    ))
                fig_pack.update_layout(
                    scene=dict(xaxis_title="Length (mm)", yaxis_title="Width (mm)", zaxis_title="Height (mm)", aspectmode='data'),
                    margin=dict(l=0, r=0, b=0, t=0), height=380
                )
                st.plotly_chart(fig_pack, use_container_width=True)
            except Exception as e_pack_plotly:
                st.warning(f"Error rendering 3D packing viewport: {e_pack_plotly}")

    # ==========================================================================
    # TAB 2: PALLET STACKING OPTIMIZER & COMPARATIVE ANALYSIS
    # ==========================================================================
    with tab_pallet:
        st.subheader("🚛 Multi-Pallet Optimization Engine")
        st.markdown(f"Transport optimization conforming to standard directives: **{max_pallet_height_limit} mm max stack height** and **{max_pallet_weight_limit} kg gross payload**.")

        PALLETS = {
            "EPAL 1 (Standard)": {"l": 1200, "w": 800, "tare": 23.0, "pallet_h": 144.0},
            "EPAL 2 (Industrial)": {"l": 1200, "w": 1000, "tare": 23.0, "pallet_h": 144.0}
        }
        pure_box_max_h = max(200.0, max_pallet_height_limit - 144.0)

        row_alt1, _ = get_resolved_directive_row(df_inventory, alt1_l, alt1_w, alt1_h, alt1_q)
        row_alt2, _ = get_resolved_directive_row(df_inventory, alt2_l, alt2_w, alt2_h, alt2_q)

        qty_alt1, _, _, _ = calculate_packing(
            row_alt1['Int.Length [mm]'], row_alt1['Width [mm]'], row_alt1['Height [mm]'],
            prod_l, prod_w, prod_h, orientation_rule, clear_side, clear_height, sep_xy, sep_z,
            lot_alignment_enabled, lot_step, order_method=active_order_method, nest_offset=nest_offset_val, bulk_density=bulk_fill_density,
            max_box_payload=row_alt1.get('Max. Load [kg]', 15.0), part_weight=prod_wt
        )
        qty_alt2, _, _, _ = calculate_packing(
            row_alt2['Int.Length [mm]'], row_alt2['Width [mm]'], row_alt2['Height [mm]'],
            prod_l, prod_w, prod_h, orientation_rule, clear_side, clear_height, sep_xy, sep_z,
            lot_alignment_enabled, lot_step, order_method=active_order_method, nest_offset=nest_offset_val, bulk_density=bulk_fill_density,
            max_box_payload=row_alt2.get('Max. Load [kg]', 15.0), part_weight=prod_wt
        )

        cvse_pcs, cvse_box_wt, _ = get_live_box_metrics(viz_box_rank1, prod_wt, single_part_vol, active_order_method)
        a1_box_weight = estimate_box_weight(alt1_l, alt1_w, alt1_h, alt1_q)
        a1_box_wt = round((qty_alt1 * prod_wt) + a1_box_weight, 2)
        a2_box_weight = estimate_box_weight(alt2_l, alt2_w, alt2_h, alt2_q)
        a2_box_wt = round((qty_alt2 * prod_wt) + a2_box_weight, 2)

        bt_cvse, _, _, pcs_cvse, wt_cvse, _, _, _ = calculate_pallet_stacking(
            1200, 800, viz_box_rank1["Ext. Length [mm]"], viz_box_rank1["Ext. Width [mm]"], viz_box_rank1["Ext. Height [mm]"], 
            cvse_box_wt, cvse_pcs, max_h=pure_box_max_h
        )
        bt_a1, _, _, pcs_a1, wt_a1, _, _, _ = calculate_pallet_stacking(
            1200, 800, alt1_l, alt1_w, alt1_h, a1_box_wt, qty_alt1, max_h=pure_box_max_h
        )
        bt_a2, _, _, pcs_a2, wt_a2, _, _, _ = calculate_pallet_stacking(
            1200, 800, alt2_l, alt2_w, alt2_h, a2_box_wt, qty_alt2, max_h=pure_box_max_h
        )

        cost_cvse = (bt_cvse * viz_box_rank1["Box Price (€)"]) + 8.00
        cost_a1 = (bt_a1 * row_alt1["Box Price (€)"]) + 8.00
        cost_a2 = (bt_a2 * row_alt2["Box Price (€)"]) + 8.00
        potential_saving_alt1 = max(0.0, cost_a1 - cost_cvse)
        potential_saving_alt2 = max(0.0, cost_a2 - cost_cvse)

        st.markdown("### 📊 Executive Yield & Cost Impact Overview")
        card_col1, card_col2, card_col3 = st.columns(3)
        with card_col1:
            st.markdown(f"""
            <div class="comp-card hero" style="min-height: 360px;">
                <div class="hero-badge">👑 CVSE Recommendation</div>
                <div class="card-header">
                    <h3 style="color: var(--text-color);">{viz_box_rank1['Box ID / Specification']}</h3>
                    <div class="dims">{int(viz_box_rank1['Ext. Length [mm]'])}x{int(viz_box_rank1['Ext. Width [mm]'])}x{int(viz_box_rank1['Ext. Height [mm]'])} mm</div>
                </div>
                <div class="metric-row"><span class="label">Quality</span><span class="val">{viz_box_rank1['Quality Class']}</span></div>
                <div class="metric-row"><span class="label">Parts / Box</span><span class="val">{cvse_pcs} Pcs</span></div>
                <div class="metric-row"><span class="label">Total Pallet Yield</span><span class="val win">{pcs_cvse} Pcs</span></div>
                <div class="metric-row"><span class="label">Gross Weight</span><span class="val">{wt_cvse} kg</span></div>
                <div class="metric-row" style="margin-top:12px; border-top:1px dashed rgba(148,163,184,0.3); padding-top:10px;">
                    <span class="label">Cost / Pallet</span><span class="val">€ {cost_cvse:.2f}</span>
                </div>
                <div class="metric-row"><span class="label">Saving (vs Alt I)</span><span class="val saving">€ {potential_saving_alt1:.2f} Save</span></div>
            </div>
            """, unsafe_allow_html=True)
        with card_col2:
            st.markdown(f"""
            <div class="comp-card" style="min-height: 360px;">
                <div class="card-header">
                    <h3 style="color: var(--text-color);">Directive Alt 1 (SLC 400)</h3>
                    <div class="dims">{int(alt1_l)}x{int(alt1_w)}x{int(alt1_h)} mm</div>
                </div>
                <div class="metric-row"><span class="label">Quality</span><span class="val">{alt1_q}</span></div>
                <div class="metric-row"><span class="label">Parts / Box</span><span class="val">{qty_alt1} Pcs</span></div>
                <div class="metric-row"><span class="label">Total Pallet Yield</span><span class="val">{pcs_a1} Pcs</span></div>
                <div class="metric-row"><span class="label">Gross Weight</span><span class="val">{wt_a1} kg</span></div>
                <div class="metric-row" style="margin-top:12px; border-top:1px dashed rgba(148,163,184,0.3); padding-top:10px;">
                    <span class="label">Cost / Pallet</span><span class="val">€ {cost_a1:.2f}</span>
                </div>
                <div class="metric-row"><span class="label">Saving (vs Alt I)</span><span class="val" style="color: #64748b;">Baseline Reference</span></div>
            </div>
            """, unsafe_allow_html=True)
        with card_col3:
            st.markdown(f"""
            <div class="comp-card" style="min-height: 360px;">
                <div class="card-header">
                    <h3 style="color: var(--text-color);">Directive Alt 2 (SLC 600)</h3>
                    <div class="dims">{int(alt2_l)}x{int(alt2_w)}x{int(alt2_h)} mm</div>
                </div>
                <div class="metric-row"><span class="label">Quality</span><span class="val">{alt2_q}</span></div>
                <div class="metric-row"><span class="label">Parts / Box</span><span class="val">{qty_alt2} Pcs</span></div>
                <div class="metric-row"><span class="label">Total Pallet Yield</span><span class="val">{pcs_a2} Pcs</span></div>
                <div class="metric-row"><span class="label">Gross Weight</span><span class="val">{wt_a2} kg</span></div>
                <div class="metric-row" style="margin-top:12px; border-top:1px dashed rgba(148,163,184,0.3); padding-top:10px;">
                    <span class="label">Cost / Pallet</span><span class="val">€ {cost_a2:.2f}</span>
                </div>
                <div class="metric-row"><span class="label">Comparison</span><span class="val" style="color: #ef4444;">+ € {potential_saving_alt2:.2f} Delta</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='success-box' style='margin-top:20px;'>
            🏆 <b>Decision Winner: {viz_box_rank1['Box ID / Specification']}</b> achieves the highest performance ranking (Score: <b>{viz_box_rank1['Priority Score']:.3f}</b>) under the <b>{active_order_method}</b> methodology without oversized container waste.
        </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # RESTORED: ROTATABLE 3D PALLETIZER VIEW WITH DECK BOARDS
        # -------------------------------------------------------------
        st.markdown("<hr style='margin:25px 0;'>", unsafe_allow_html=True)
        st.markdown("### 📦 Palletization Report & Interactive 3D Stacking Model")

        safe_index_t2 = get_safe_index(available_boxes, st.session_state["global_selected_box"])
        selected_box_t2 = st.selectbox(
            "Select any Cardboard Box to inspect its detailed pallet loading report & rotatable 3D stack (Synchronized):",
            options=available_boxes, index=safe_index_t2, key="tab2_box_selector", on_change=sync_from_tab2
        )
        viz_box_t2 = sorted_df[sorted_df["Box ID / Specification"] == st.session_state["global_selected_box"]].iloc[0]

        active_t2_pcs, active_t2_wt, _ = get_live_box_metrics(viz_box_t2, prod_wt, single_part_vol, active_order_method)
        bx_ext_l = viz_box_t2["Ext. Length [mm]"]
        bx_ext_w = viz_box_t2["Ext. Width [mm]"]
        bx_ext_h = viz_box_t2["Ext. Height [mm]"]

        col_metrics, col_plotly_pallet = st.columns([4, 6])
        with col_metrics:
            st.markdown(f"#### 📋 Stacking Report for **{st.session_state['global_selected_box']}**")
            b_total_1, z_layers_1, _, p_pcs_1, p_wt_1, orient_1, nx_1, ny_1 = calculate_pallet_stacking(
                PALLETS["EPAL 1 (Standard)"]["l"], PALLETS["EPAL 1 (Standard)"]["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, active_t2_wt, active_t2_pcs, PALLETS["EPAL 1 (Standard)"]["tare"], max_h=pure_box_max_h
            )
            b_total_2, z_layers_2, _, p_pcs_2, p_wt_2, orient_2, nx_2, ny_2 = calculate_pallet_stacking(
                PALLETS["EPAL 2 (Industrial)"]["l"], PALLETS["EPAL 2 (Industrial)"]["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, active_t2_wt, active_t2_pcs, PALLETS["EPAL 2 (Industrial)"]["tare"], max_h=pure_box_max_h
            )
            st.markdown(f"""
            <div style='background-color: var(--background-color); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--text-color); border-left: 5px solid #228be6;'>
                <h5 style='margin-top: 0px;'>🥇 EPAL 1 Standard (1200 x 800 mm)</h5>
                <b>Orientation:</b> {orient_1}<br>
                📐 <b>Layer Layout Grid:</b> {nx_1} x {ny_1} (X x Y)<br>
                🪜 <b>Stacking Height:</b> {z_layers_1} vertical layers<br>
                📦 <b>Total Boxes:</b> {b_total_1} units<br>
                ✨ <b>Total Pieces:</b> <b style='color:#2b8a3e;'>{p_pcs_1} Pcs</b><br>
                ⚖️ <b>Gross Weight:</b> <b>{p_wt_1} kg</b> (&lt;{max_pallet_weight_limit} kg limit)
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background-color: var(--background-color); padding: 15px; border-radius: 8px; border: 1px solid var(--text-color); border-left: 5px solid #15aabf;'>
                <h5 style='margin-top: 0px;'>🥈 EPAL 2 Industrial (1200 x 1000 mm)</h5>
                <b>Orientation:</b> {orient_2}<br>
                📐 <b>Layer Layout Grid:</b> {nx_2} x {ny_2} (X x Y)<br>
                🪜 <b>Stacking Height:</b> {z_layers_2} vertical layers<br>
                📦 <b>Total Boxes:</b> {b_total_2} units<br>
                ✨ <b>Total Pieces:</b> <b style='color:#2b8a3e;'>{p_pcs_2} Pcs</b><br>
                ⚖️ <b>Gross Weight:</b> <b>{p_wt_2} kg</b> (&lt;{max_pallet_weight_limit} kg limit)
            </div>
            """, unsafe_allow_html=True)

        with col_plotly_pallet:
            st.markdown("##### 🔄 Rotatable 3D Pallet Stacking Blueprint")
            pallet_sel = st.radio("Choose Pallet Standard:", options=["EPAL 1 (1200x800)", "EPAL 2 (1200x1000)"], horizontal=True)
            active_p_spec = PALLETS["EPAL 1 (Standard)"] if "EPAL 1" in pallet_sel else PALLETS["EPAL 2 (Industrial)"]
            p_boxes, p_layers, p_l_qty, _, _, p_orient, nx_act, ny_act = calculate_pallet_stacking(
                active_p_spec["l"], active_p_spec["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, active_t2_wt, active_t2_pcs, active_p_spec["tare"], max_h=pure_box_max_h
            )
            try:
                fig_pallet_3d = go.Figure()
                pallet_h = active_p_spec["pallet_h"] 

                # Top Wooden Deck
                fig_pallet_3d.add_trace(go.Mesh3d(
                    x=[0, active_p_spec["l"], active_p_spec["l"], 0, 0, active_p_spec["l"], active_p_spec["l"], 0],
                    y=[0, 0, active_p_spec["w"], active_p_spec["w"], 0, 0, active_p_spec["w"], active_p_spec["w"]],
                    z=[122, 122, 122, 122, 144, 144, 144, 144],
                    i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                    j=[1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6],
                    k=[2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5],
                    color='#d2b48c', opacity=0.95, name="Top Deck Boards",
                    flatshading=True, lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1)
                ))

                # Wooden Runners (Blocks)
                runners_y = [
                    (0, 100),
                    (active_p_spec["w"]/2 - 50, active_p_spec["w"]/2 + 50),
                    (active_p_spec["w"] - 100, active_p_spec["w"])
                ]
                for r_idx, (y0, y1) in enumerate(runners_y):
                    fig_pallet_3d.add_trace(go.Mesh3d(
                        x=[0, active_p_spec["l"], active_p_spec["l"], 0, 0, active_p_spec["l"], active_p_spec["l"], 0],
                        y=[y0, y0, y1, y1, y0, y0, y1, y1],
                        z=[22, 22, 22, 22, 122, 122, 122, 122],
                        i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                        j=[1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6],
                        k=[2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5],
                        color='#cd853f', opacity=0.95, name=f"Runner {r_idx+1}",
                        flatshading=True, lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1)
                    ))

                # Bottom Deck Boards
                fig_pallet_3d.add_trace(go.Mesh3d(
                    x=[0, active_p_spec["l"], active_p_spec["l"], 0, 0, active_p_spec["l"], active_p_spec["l"], 0],
                    y=[0, 0, active_p_spec["w"], active_p_spec["w"], 0, 0, active_p_spec["w"], active_p_spec["w"]],
                    z=[0, 0, 0, 0, 22, 22, 22, 22],
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
                    z0 = layer * bx_dz + pallet_h 
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
                                flatshading=True, lighting=dict(ambient=0.6, diffuse=0.8, roughness=0.3, specular=0.15)
                            ))

                fig_pallet_3d.add_trace(go.Scatter3d(
                    x=line_x, y=line_y, z=line_z,
                    mode='lines', line=dict(color='#1864ab', width=2),
                    name="Cardboard Boxes"
                ))
                fig_pallet_3d.update_layout(
                    scene=dict(
                        xaxis=dict(title="Length (mm)", range=[-50, active_p_spec["l"]+50]),
                        yaxis=dict(title="Width (mm)", range=[-50, active_p_spec["w"]+50]),
                        zaxis=dict(title="Height (mm)", range=[0, 1100]),
                        aspectmode='data',
                        camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
                    ),
                    margin=dict(l=0, r=0, b=0, t=0), height=460
                )
                st.plotly_chart(fig_pallet_3d, use_container_width=True)
            except Exception as e_pack_plotly:
                st.warning(f"Error rendering interactive 3D pallet: {e_pack_plotly}")

    # ==========================================================================
    # TAB 3: MCKEE GRAVITY COMPRESSION SAFETY CHECK
    # ==========================================================================
    with tab_compression:
        st.subheader("🗜️ Corrugated Cardboard McKee Compression Strength Checker")
        st.markdown("Validate if bottom-layer cartons resist stacking crush forces under real-world transport climates.")

        col_setup_1, col_setup_2 = st.columns(2)
        with col_setup_1:
            stack_style = st.selectbox("Select Pallet Stacking Configuration:", ["Single Pallet Load", "Double-Stacked Pallets (Pallet-on-Pallet)"])
        with col_setup_2:
            safe_index_t3 = get_safe_index(available_boxes, st.session_state["global_selected_box"])
            selected_box_t3 = st.selectbox("Select Cardboard Box to Inspect Compression:", options=available_boxes, index=safe_index_t3, key="tab3_box_selector", on_change=sync_from_tab3)
            viz_box_t3 = sorted_df[sorted_df["Box ID / Specification"] == st.session_state["global_selected_box"]].iloc[0]

        col_moisture, col_spread, col_fragility = st.columns(3)
        with col_moisture: moisture_sel = st.selectbox("Moisture (Humidity):", ["Dry", "Normal", "Humid", "Wet"], index=1)
        with col_spread: spread_sel = st.selectbox("Load spread:", ["Even", "Uneven", "Center", "Corner"], index=0)
        with col_fragility: fragility_sel = st.selectbox("Fragility:", ["Low", "Medium", "High"], index=1)
        col_storage, col_transport = st.columns(2)
        with col_storage: storage_sel = st.selectbox("Storage Duration:", ["Short (days)", "Medium (weeks)", "Long (months)"], index=1)
        with col_transport: transport_sel = st.selectbox("Transport Handling / Vibration:", ["LTL/FTL Truck", "Parcel shipping", "Air/Sea Cargo"], index=1)

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
        q_class_t3 = str(viz_box_t3.get("Quality Class") or viz_box_t3.get("Flute Type")).strip() 
        props_t3 = QUALITY_PROPERTIES.get(q_class_t3, {"ect": 4.0, "thickness": 3.5, "name": "Custom Grade"})
        ect_val_t3 = props_t3["ect"]
        thickness_val_t3 = props_t3["thickness"]
        q_name_t3 = props_t3["name"]

        box_perimeter_t3 = 2 * ((viz_box_t3.get("Int.Length [mm]") or viz_box_t3.get("Int. Length [mm]")) + (viz_box_t3.get("Width [mm]") or viz_box_t3.get("Int. Width [mm]")))
        bct_n_t3 = 1.82 * ect_val_t3 * np.sqrt(thickness_val_t3 * box_perimeter_t3)
        bct_kg_t3 = round(bct_n_t3 / 9.81, 1) 
        sf_t3 = round(1.5 * f_moisture * f_spread * f_fragility * f_storage * f_transport, 2)
        bct_safe_load_t3 = round(bct_kg_t3 / sf_t3, 1)

        active_t3_pcs, active_t3_wt, _ = get_live_box_metrics(viz_box_t3, prod_wt, single_part_vol, active_order_method)
        _, z_layers_calc_t3, best_layer_qty_t3, _, p_wt_calc_t3, _, _, _ = calculate_pallet_stacking(
            1200, 800, viz_box_t3["Ext. Length [mm]"], viz_box_t3["Ext. Width [mm]"], viz_box_t3["Ext. Height [mm]"], active_t3_wt, active_t3_pcs
        )
        boxes_above_t3 = max(0, z_layers_calc_t3 - 1)
        actual_bottom_load_t3 = round(boxes_above_t3 * active_t3_wt, 1)
        if stack_style == "Double-Stacked Pallets (Pallet-on-Pallet)":
            top_pallet_weight_contribution_t3 = round(p_wt_calc_t3 / max(1, best_layer_qty_t3), 1)
            actual_bottom_load_t3 = round(actual_bottom_load_t3 + top_pallet_weight_contribution_t3, 1)

        col_comp_kpis = st.columns(4)
        with col_comp_kpis[0]: st.metric("Theoretical BCT Strength", f"{bct_kg_t3} kg", help="Ultimate crushing force of a pristine single carton.")
        with col_comp_kpis[1]: st.metric("Combined Safety Factor", f"{sf_t3}x", help="Climate/logistics margin multiplier.")
        with col_comp_kpis[2]: st.metric("Safe Design Capacity", f"{bct_safe_load_t3} kg", help="Derated maximum load allowable on lowest carton.")
        with col_comp_kpis[3]: st.metric("Actual Bottom Load", f"{actual_bottom_load_t3} kg", help="Total physical mass supported by the lowest carton.")

        if actual_bottom_load_t3 <= bct_safe_load_t3:
            st.markdown(f"""
            <div class='success-box'>
                🟢 <b>Safe Stacking Approved:</b> The actual load of <b>{actual_bottom_load_t3} kg</b> is within the design capacity of <b>{bct_safe_load_t3} kg</b>! Cardboard grade <b>{q_class_t3} ({q_name_t3})</b> is structurally secure.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='danger-box'>
                🚨 <b>Warning - Structural Failure Risk:</b> The actual bottom load of <b>{actual_bottom_load_t3} kg</b> exceeds the safe limit of <b>{bct_safe_load_t3} kg</b>! Consider upgrading cardboard quality or reducing stack height.
            </div>
            """, unsafe_allow_html=True)

        # RESTORED: DETAILED MCKEE LATEX MATHEMATICAL BREAKDOWN
        st.markdown("<div class='guide-box'><h5>🧮 Step-by-Step Mathematical Workings (McKee Metric Standard):</h5>"
                    "The Box Compression Test (BCT) is computed dynamically using live units:</div>", unsafe_allow_html=True)
        st.latex(r"\text{BCT (Newtons)} = 1.82 \times \text{ECT} \times \sqrt{t \times P}")
        st.latex(r"\text{BCT (kg)} = \frac{\text{BCT (Newtons)}}{9.81\text{ m/s}^2}")
        st.latex(r"\text{Safe Design Capacity} = \frac{\text{BCT (kg)}}{\text{Combined Safety Factor (SF)}}")
        st.markdown(f"""
        <div class='guide-box' style='margin-top:-20px; border-top-left-radius:0px; border-top-right-radius:0px; border-top:0px;'>
            <b>Active Parameters (Based on {active_t3_pcs} Pcs Loaded):</b>
            <ul>
                <li><b>ECT:</b> Quality class <b>{q_class_t3}</b> baseline is <b>{ect_val_t3} N/mm</b>.</li>
                <li><b>t (Thickness):</b> Quality class <b>{q_class_t3}</b> baseline is <b>{thickness_val_t3} mm</b>.</li>
                <li><b>P (Perimeter):</b> Measured boundary is <b>{int(box_perimeter_t3)} mm</b>.</li>
            </ul>
            <hr style='border: 0.5px solid rgba(148,163,184,0.3);'>
            <b>Live Calculations:</b><br><br>
            <b>1. Pristine Crushing Force:</b> 1.82 × {ect_val_t3} N/mm × √({thickness_val_t3} mm × {int(box_perimeter_t3)} mm) = <b>{bct_n_t3:.2f} Newtons</b><br>
            <b>2. Mass Conversion (kg):</b> {bct_n_t3:.2f} N ÷ 9.81 m/s² = <b>{bct_kg_t3} kg</b><br>
            <b>3. Environmental Safety Limit ({sf_t3}x):</b> {bct_kg_t3} kg ÷ {sf_t3} = <b>{bct_safe_load_t3} kg</b>
        </div>
        """, unsafe_allow_html=True)

# Fail-safe warning display
if not results:
    st.warning("⚠️ No suitable boxes in your database can fit this product under the active weight or dimension parameters.")

# ==============================================================================
# 8. COLLABORATIVE FEEDBACK HUB & ADMIN VIEW PANEL
# ==============================================================================
st.sidebar.markdown("<hr style='margin:15px 0; border:0; border-top:1px solid rgba(148,163,184,0.3);'>", unsafe_allow_html=True)
st.sidebar.subheader("💬 App Feedback Hub")
with st.sidebar.form("feedback_form", clear_on_submit=True):
    user_name = st.text_input("Your Name / Department:", placeholder="e.g., Logistics Engineering")
    rating = st.select_slider("Rate this tool:", options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], value="⭐⭐⭐⭐⭐")
    feedback_text = st.text_area("How can we improve this tool?", placeholder="Enter comments or bug reports...")
    submitted = st.form_submit_button("Submit Feedback", use_container_width=True)

    if submitted:
        if feedback_text.strip() == "":
            st.error("Please enter some feedback comments before submitting.")
        else:
            feedback_entry = {
                "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "User": user_name.strip() if user_name.strip() != "" else "Anonymous Colleague",
                "Rating": rating,
                "Comments": feedback_text.strip()
            }
            log_feedback_locally(feedback_entry)
            st.success("🎉 Feedback logged successfully!")

            try:
                if "teams" in st.secrets and st.secrets["teams"].get("webhook_url"):
                    WEBHOOK_URL = st.secrets["teams"]["webhook_url"]
                    payload = {
                        "type": "message",
                        "attachments": [{
                            "contentType": "application/vnd.microsoft.card.adaptive",
                            "content": {
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "type": "AdaptiveCard", "version": "1.2",
                                "body": [
                                    {"type": "TextBlock", "text": "📦 New App Feedback Received!", "weight": "Bolder", "size": "Medium"},
                                    {"type": "FactSet", "facts": [
                                        {"title": "📅 Timestamp:", "value": feedback_entry["Timestamp"]},
                                        {"title": "👤 Submitted By:", "value": feedback_entry["User"]},
                                        {"title": "⭐ Rating:", "value": feedback_entry["Rating"]}
                                    ]},
                                    {"type": "TextBlock", "text": f"💬 Comments:\n\"{feedback_entry['Comments']}\"", "wrap": True, "italic": True}
                                ]
                            }
                        }]
                    }
                    req = request.Request(url=WEBHOOK_URL, method="POST")
                    req.add_header("Content-Type", "application/json")
                    with request.urlopen(req, data=json.dumps(payload).encode("utf-8")) as response:
                        pass
            except Exception as e_teams:
                print(f"Teams webhook notice: {e_teams}")

st.markdown("<br><br><hr style='border:0; border-top:1px solid rgba(148,163,184,0.2);'>", unsafe_allow_html=True)
with st.expander("🔐 Admin Panel: View Collected Feedback"):
    admin_password = st.text_input("Enter Admin Password to view logs:", type="password", key="admin_pwd_input")
    if admin_password == "BSHAdmin2026":
        feedback_file = "feedback_log.csv"
        if os.path.exists(feedback_file):
            try:
                feed_df = pd.read_csv(feedback_file)
                st.markdown(f"### 📋 Total Submissions: {len(feed_df)}")
                st.dataframe(feed_df, use_container_width=True)
                st.download_button(label="📥 Export Feedback Database to CSV", data=feed_df.to_csv(index=False).encode('utf-8'), file_name="BSH_Tool_Feedback_Export.csv", mime="text/csv", use_container_width=True)
            except Exception as e_read_feed:
                st.error(f"Error reading feedback file: {e_read_feed}")
        else:
            st.info("No feedback has been submitted yet.")
    elif admin_password != "":
        st.error("Incorrect password. Access denied.")
