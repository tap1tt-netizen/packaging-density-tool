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
    page_title="BSH Packaging Density & Pallet Optimizer",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern SaaS Styling (Inspired by Productive.io, Stackfield & iQuoteXpress)
st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top App Bar Styling */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .app-header h1 {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff !important;
    }
    .app-header p {
        font-size: 14px;
        color: #94a3b8;
        margin: 6px 0 0 0;
    }

    /* Modern KPI Cards */
    .metric-card {
        background: var(--background-color);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
        min-height: 115px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        border-color: #3b82f6;
    }
    .metric-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 4px;
    }
    .metric-val {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 11px;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Status Pill Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-success {
        background-color: rgba(34, 197, 94, 0.15);
        color: #16a34a;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #d97706;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-danger {
        background-color: rgba(239, 68, 68, 0.15);
        color: #dc2626;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-info {
        background-color: rgba(59, 130, 246, 0.15);
        color: #2563eb;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    /* Container Cards */
    .saas-card {
        background: var(--background-color);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    .saas-card-title {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Instruction Step Circles */
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: #2563eb;
        color: #ffffff;
        font-size: 12px;
        font-weight: 700;
        margin-right: 8px;
    }

    /* Clean Streamlit Tab Nav */
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
# 2. DATABASE LOADER ENGINE
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
# 3. SIDEBAR: OPERATOR INPUT ENGINE
# ==============================================================================
st.sidebar.markdown("### ⚙️ Product Parameters")
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

        st.sidebar.success(f"Auto-Extracted Dimensions: {auto_l} × {auto_w} × {auto_h} mm")

        st.sidebar.markdown("#### 🪵 Material Density Extractor")
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
st.sidebar.markdown("### 📏 Divider & Tolerances")
clear_side = st.sidebar.slider("Sides Clearance buffer (mm)", min_value=0, max_value=20, value=2)
clear_height = st.sidebar.slider("Height Clearance buffer (mm)", min_value=0, max_value=20, value=4)
sep_xy = st.sidebar.slider("Separator X/Y Thickness (mm)", min_value=0, max_value=10, value=2)
sep_z = st.sidebar.slider("Separator Z Thickness (mm)", min_value=0, max_value=10, value=4)

orientation_rule = st.sidebar.selectbox(
    "Packing Orientation Rule:",
    ["Automatic (Highest Quantity)", "Force Flat Packing Only", "Force Standing on Edge", "Force Standing Vertical"]
)

sort_criteria = st.sidebar.selectbox(
    "Rank Box Options By:", 
    ["Volumetric Efficiency (%)", "Number of Parts per Box", "Box Price (€)"]
)

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
# 4. CALCULATION ENGINE
# ==============================================================================
def calculate_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h, rule):
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

    return best_qty, best_config, best_grid_layout

def determine_placement_style(p_l, p_w, p_h, oz):
    dims = sorted([p_l, p_w, p_h])
    if int(oz) == int(dims[0]):
        return "🟢 Flat / Horizontal (Resting on wide base, most stable)"
    elif int(oz) == int(dims[1]):
        return "⚠️ Standing on Side / Edge"
    else:
        return "🚨 Standing Vertical / On End (Prone to tipping)"

def estimate_box_weight(ext_l, ext_w, ext_h, quality):
    if pd.isna(ext_l) or pd.isna(ext_w) or pd.isna(ext_h):
        return 0.15
    sheet_l_m = (2 * (ext_l + ext_w) + 40) / 1000.0
    sheet_w_m = (ext_h + ext_w) / 1000.0
    flat_area = sheet_l_m * sheet_w_m
    grammage_map = {'1.20B': 0.40, '1.20C': 0.45, '2.30EB': 0.70, '2.30BC': 0.85}
    g = grammage_map.get(str(quality).strip(), 0.50)
    return flat_area * g

# Run Solver
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

    parts_count, pack_orient, grid_layout = calculate_packing(
        box_int_l, box_int_w, box_int_h, 
        prod_l, prod_w, prod_h,
        rule=orientation_rule
    )

    if parts_count == 0:
        continue

    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row['Quality'])
    total_payload_wt = parts_count * prod_wt
    total_package_weight = total_payload_wt + box_weight

    # Safety Check: 15kg limit on manual handling footprint (<=400x300mm)
    dims_footprint = sorted([ext_l, ext_w])
    is_manual_box = (dims_footprint[0] <= 300.0) and (dims_footprint[1] <= 400.0)
    if is_manual_box and total_package_weight > 15.0:
        continue

    if total_payload_wt > row['Max. Load [kg]']:
        continue

    box_internal_vol = box_int_l * box_int_w * box_int_h
    occupied_volume = parts_count * single_part_vol
    vol_efficiency = (occupied_volume / box_internal_vol) * 100
    air_space_percent = 100.0 - vol_efficiency

    results.append({
        "Box ID / Specification": row['BoxSize'],
        "Box Footprint (Ext)": f"{int(ext_l)}×{int(ext_w)} mm",
        "Quality Class": row['Quality'],
        "Internal Dimensions": f"{int(box_int_l)}×{int(box_int_w)}×{int(box_int_h)} mm",
        "Int. Length [mm]": box_int_l,
        "Int. Width [mm]": box_int_w,
        "Int. Height [mm]": box_int_h,
        "Ext. Length [mm]": ext_l,
        "Ext. Width [mm]": ext_w,
        "Ext. Height [mm]": ext_h,
        "Number of Parts per Box": parts_count,
        "Optimal Grid Layout": f"{grid_layout[0]}×{grid_layout[1]}×{grid_layout[2]} (X×Y×Z)",
        "Optimal Orientation": f"{int(pack_orient[0])}×{int(pack_orient[1])}×{int(pack_orient[2])} mm",
        "Total Weight (kg)": round(total_package_weight, 2),
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
# 5. DASHBOARD HEADER & KPI PANELS
# ==============================================================================
if results:
    res_df = pd.DataFrame(results)

    if sort_criteria == "Volumetric Efficiency (%)":
        sort_by_cols = ["Volumetric Efficiency (%)", "Box Price (€)", "Total Weight (kg)"]
        ascending_rules = [False, True, True]
    elif sort_criteria == "Number of Parts per Box":
        sort_by_cols = ["Number of Parts per Box", "Box Price (€)", "Total Weight (kg)"]
        ascending_rules = [False, True, True]
    else:
        sort_by_cols = ["Box Price (€)", "Number of Parts per Box", "Total Weight (kg)"]
        ascending_rules = [True, False, True]

    ranked_df = res_df.sort_values(by=sort_by_cols, ascending=ascending_rules).head(10).reset_index(drop=True)
    ranked_df.index = ranked_df.index + 1
    best_box = ranked_df.iloc[0]

    # Modern Enterprise Header
    total_pkg_wt = best_box["Total Weight (kg)"]
    ext_l_best = best_box["Ext. Length [mm]"]
    ext_w_best = best_box["Ext. Width [mm]"]
    dims_footprint_best = sorted([ext_l_best, ext_w_best])
    is_manual_best = (dims_footprint_best[0] <= 300.0) and (dims_footprint_best[1] <= 400.0)

    if total_pkg_wt > 15.0 and not is_manual_best:
        safety_status_html = f"<span class='badge badge-warning'>⚡ Forklift Transport ({total_pkg_wt} kg)</span>"
    elif total_pkg_wt > 15.0 and is_manual_best:
        safety_status_html = f"<span class='badge badge-danger'>🚨 Overweight Manual ({total_pkg_wt} kg)</span>"
    else:
        safety_status_html = f"<span class='badge badge-success'>🟢 Ergonomic Safe ({total_pkg_wt} kg)</span>"

    st.markdown(f"""
        <div class='app-header'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <h1>📦 Packaging Density & Box Recommender</h1>
                    <p>BSH Logistics & Supply Chain Packing Optimization Engine</p>
                </div>
                <div>{safety_status_html}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Modern SaaS KPI Metrics Row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid #2563eb;'>
                <div class='metric-title'>Top Recommendation</div>
                <div class='metric-val' style='font-size:18px; color:#2563eb;'>{best_box['Box ID / Specification']}</div>
                <div class='metric-sub' style='color:#64748b;'>Quality: <b>{best_box['Quality Class']}</b></div>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid #16a34a;'>
                <div class='metric-title'>Max Parts Fitted</div>
                <div class='metric-val' style='color:#16a34a;'>{int(best_box['Number of Parts per Box'])} <span style='font-size:16px; font-weight:500;'>pcs</span></div>
                <div class='metric-sub' style='color:#64748b;'>Grid: {best_box['Optimal Grid Layout']}</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid #f59e0b;'>
                <div class='metric-title'>Vol. Efficiency</div>
                <div class='metric-val' style='color:#d97706;'>{best_box['Volumetric Efficiency (%)']}%</div>
                <div class='metric-sub' style='color:#64748b;'>Remaining Air: {best_box['Remaining Air Space (%)']}%</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid #06b6d4;'>
                <div class='metric-title'>Total Weight</div>
                <div class='metric-val' style='color:#0891b2;'>{best_box['Total Weight (kg)']} <span style='font-size:16px; font-weight:500;'>kg</span></div>
                <div class='metric-sub' style='color:#64748b;'>Payload + Tare</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi5:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid #8b5cf6;'>
                <div class='metric-title'>Contract Box Price</div>
                <div class='metric-val' style='color:#7c3aed;'>€ {best_box['Box Price (€)']:.2f}</div>
                <div class='metric-sub' style='color:#64748b;'>Per unit packaging cost</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 6. TABS NAVIGATION
    # ==============================================================================
    tab_recommender, tab_pallet, tab_compression = st.tabs([
        "📦 Box Recommender & Blueprint", 
        "🚛 Multi-Pallet Optimizer (EPAL 1 & 2)", 
        "🗜️ McKee Compression Safety Check"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: BOX RECOMMENDER & INDIVIDUAL LOADING
    # --------------------------------------------------------------------------
    with tab_recommender:
        display_df = ranked_df.drop(columns=[
            "_nx", "_ny", "_nz", "_ox", "_oy", "_oz", 
            "Int. Length [mm]", "Int. Width [mm]", "Int. Height [mm]", 
            "Ext. Length [mm]", "Ext. Width [mm]"
        ])

        col_header, col_export = st.columns([7, 3])
        with col_header:
            st.markdown("#### 🏆 Top 10 Optimized Box Recommendations")
        with col_export:
            export_fmt = st.selectbox(
                "Quick Export Options:",
                ["-- Choose Export Format --", "Export to Excel (.xlsx)", "Export to CSV (.csv)"],
                index=0,
                key="export_box_hub"
            )
            if export_fmt == "Export to Excel (.xlsx)":
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                    display_df.to_excel(writer, sheet_name='Top_10_Boxes', index=True)
                st.download_button(
                    label="📥 Download Excel File",
                    data=buf.getvalue(),
                    file_name="BSH_Top_10_Boxes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            elif export_fmt == "Export to CSV (.csv)":
                csv_bytes = display_df.to_csv(index=True).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV File",
                    data=csv_bytes,
                    file_name="BSH_Top_10_Boxes.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        st.dataframe(
            display_df,
            column_config={
                "Volumetric Efficiency (%)": st.column_config.ProgressColumn(
                    "Volumetric Efficiency",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100,
                    color="blue"
                ),
                "Box Price (€)": st.column_config.NumberColumn(
                    "Box Price",
                    format="€ %.2f"
                )
            },
            use_container_width=True
        )

        st.markdown("<hr style='margin: 25px 0; border: 0; border-top: 1px solid rgba(148, 163, 184, 0.2);'>", unsafe_allow_html=True)

        # Interactive Blueprint Viewer
        st.markdown("#### 📋 Step-by-Step Packing Blueprint & Operator Guide")
        available_boxes = list(ranked_df["Box ID / Specification"].values)
        selected_box_spec = st.selectbox(
            "Select box specification to generate technical packing blueprints:",
            options=available_boxes,
            index=0,
            key="blueprint_selector"
        )

        viz_box = ranked_df[ranked_df["Box ID / Specification"] == selected_box_spec].iloc[0]
        nx, ny, nz = int(viz_box["_nx"]), int(viz_box["_ny"]), int(viz_box["_nz"])
        ox, oy, oz = int(viz_box["_ox"]), int(viz_box["_oy"]), int(viz_box["_oz"])
        box_l, box_w = viz_box["Int. Length [mm]"], viz_box["Int. Width [mm]"]
        ext_l, ext_w = viz_box["Ext. Length [mm]"], viz_box["Ext. Width [mm]"]

        placement_style = determine_placement_style(prod_l, prod_w, prod_h, oz)

        col_instr, col_plan, col_elev = st.columns([2.5, 3, 2.5])

        with col_instr:
            st.markdown(f"""
            <div class='saas-card'>
                <div class='saas-card-title'>🛠️ Operator Instructions</div>
                <p><b><span class='step-number'>1</span> Orient the Part:</b><br>
                <i>{placement_style}</i><br>
                • Length: <b>{ox} mm</b><br>
                • Width: <b>{oy} mm</b><br>
                • Height (Up): <b>{oz} mm</b></p>

                <p><b><span class='step-number'>2</span> Floor Grid Layout:</b><br>
                Place <b>{nx} columns × {ny} rows</b> ({nx * ny} parts per layer).<br>
                Use {sep_xy} mm partition separators between parts.</p>

                <p><b><span class='step-number'>3</span> Vertical Stacking:</b><br>
                {"Lay a flat " + str(sep_z) + " mm divider sheet and repeat for <b>" + str(nz) + " layers</b>." if nz > 1 else "Single layer configuration. No tier sheets required."}</p>

                <div style='margin-top:14px; padding-top:10px; border-top:1px solid rgba(148, 163, 184, 0.2);'>
                    <b>Total Unit Load:</b> {viz_box['Total Weight (kg)']} kg
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_plan:
            st_text_color = '#FFFFFF' if st.get_option('theme.base') == 'dark' else '#1e293b'
            fig, ax = plt.subplots(figsize=(6, 4), facecolor='none')
            ax.set_facecolor('none')

            # Box boundary
            ax.add_patch(patches.Rectangle((0, 0), box_l, box_w, fill=False, edgecolor=st_text_color, linewidth=2))

            # Clearance zones
            ax.add_patch(patches.Rectangle((0, 0), box_l, clear_side, fill=True, color='#94a3b8', alpha=0.2))
            ax.add_patch(patches.Rectangle((0, box_w - clear_side), box_l, clear_side, fill=True, color='#94a3b8', alpha=0.2))
            ax.add_patch(patches.Rectangle((0, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#94a3b8', alpha=0.2))
            ax.add_patch(patches.Rectangle((box_l - clear_side, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#94a3b8', alpha=0.2))

            total_grid_w = nx * ox + (nx - 1) * sep_xy
            total_grid_h = ny * oy + (ny - 1) * sep_xy
            start_x = clear_side + ((box_l - 2 * clear_side) - total_grid_w) / 2
            start_y = clear_side + ((box_w - 2 * clear_side) - total_grid_h) / 2

            for r in range(ny):
                y_pos = start_y + r * (oy + sep_xy)
                for c in range(nx):
                    x_pos = start_x + c * (ox + sep_xy)
                    ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#60a5fa', edgecolor='#2563eb', linewidth=1.2, alpha=0.85))
                    ax.text(x_pos + ox/2, y_pos + oy/2, f"{c+1},{r+1}", ha='center', va='center', fontsize=7, color='#ffffff', fontweight='bold')

            ax.set_xlim(-20, box_l + 20)
            ax.set_ylim(-20, box_w + 20)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.title(f"Floor Plan ({nx}×{ny} Grid)", fontsize=10, fontweight='bold', color=st_text_color)
            st.pyplot(fig)
            plt.close(fig)

        with col_elev:
            fig3d = plt.figure(figsize=(4, 3.5), facecolor='none')
            ax3d = fig3d.add_subplot(111, projection='3d', facecolor='none')
            w_scale = 100
            l_scale = w_scale * (box_l / box_w)
            h_scale = 30
            z_aspect = max(30, nz * 15)
            ax3d.set_box_aspect((l_scale, w_scale, z_aspect))

            for layer in range(nz):
                z_start = layer * (h_scale + 5)
                v = np.array([
                    [0, 0, z_start], [l_scale, 0, z_start], [l_scale, w_scale, z_start], [0, w_scale, z_start],
                    [0, 0, z_start + h_scale], [l_scale, 0, z_start + h_scale], [l_scale, w_scale, z_start + h_scale], [0, w_scale, z_start + h_scale]
                ])
                faces = [
                    [v[0], v[1], v[5], v[4]], [v[1], v[2], v[6], v[5]], [v[2], v[3], v[7], v[6]],
                    [v[3], v[0], v[4], v[7]], [v[4], v[5], v[6], v[7]], [v[0], v[1], v[2], v[3]]
                ]
                poly = Poly3DCollection(faces, facecolors='#38bdf8', edgecolors='#0284c7', linewidths=1.2, alpha=0.7)
                ax3d.add_collection3d(poly)
                ax3d.text(-25, 10, z_start + h_scale/2, f"L{layer + 1}", color='#e11d48', fontweight='bold', fontsize=9)

            ax3d.set_xlim(-30, l_scale + 10)
            ax3d.set_ylim(-10, w_scale + 10)
            ax3d.set_zlim(0, nz * (h_scale + 5) + 10)
            ax3d.view_init(elev=20, azim=-60)
            ax3d.axis('off')
            plt.title("Vertical Stacking Blueprint", fontsize=10, fontweight='bold', color=st_text_color)
            st.pyplot(fig3d)
            plt.close(fig3d)

    # --------------------------------------------------------------------------
    # TAB 2: PALLET STACKING OPTIMIZER
    # --------------------------------------------------------------------------
    with tab_pallet:
        st.markdown("#### 🚛 Multi-Pallet Transport Layout Engine")
        st.caption("Standard height limit: **1000 mm** | Gross payload cap: **1000 kg** (including 23 kg pallet tare)")

        PALLETS = {
            "EPAL 1 (Standard)": {"l": 1200, "w": 800, "tare": 23.0},
            "EPAL 2 (Industrial)": {"l": 1200, "w": 1000, "tare": 23.0}
        }

        def calculate_pallet_stacking(pallet_l, pallet_w, ext_l, ext_w, ext_h, box_wt, pcs_box, pallet_tare=23.0, max_h=1000.0, max_wt=1000.0):
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

        # Comparison Section
        ranked_df_copy = ranked_df.copy()
        ranked_df_copy['Footprint Area'] = ranked_df_copy['Ext. Length [mm]'] * ranked_df_copy['Ext. Width [mm]']
        sorted_by_footprint = ranked_df_copy.sort_values(by='Footprint Area')

        small_row = sorted_by_footprint.iloc[0]
        top1_row = ranked_df_copy.iloc[0]
        top2_row = ranked_df_copy.iloc[1] if len(ranked_df_copy) >= 2 else None
        top3_row = ranked_df_copy.iloc[2] if len(ranked_df_copy) >= 3 else None

        # Safe extraction of the Box ID / Specification column (Fixes KeyError)
        small_name = small_row.get("Box ID / Specification", small_row.get("BoxSize", "Smallest Box"))
        top1_name = top1_row.get("Box ID / Specification", top1_row.get("BoxSize", "Top 1 Best Box"))
        top2_name = top2_row.get("Box ID / Specification", top2_row.get("BoxSize", "Top 2 Best Box")) if top2_row is not None else "N/A"
        top3_name = top3_row.get("Box ID / Specification", top3_row.get("BoxSize", "Top 3 Best Box")) if top3_row is not None else "N/A"

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

        st.markdown("""
            <div class='saas-card'>
                <div class='saas-card-title'>⚖️ EPAL 1 Pallet Benchmark Comparison</div>
        """, unsafe_allow_html=True)

        comp_df = pd.DataFrame([
            {"Metric": "Box Specification", "Smallest Box (Top 10)": small_name, "Top 1 Best Box": top1_name, "Top 2 Best Box": top2_name, "Top 3 Best Box": top3_name},
            {"Metric": "Parts / Box", "Smallest Box (Top 10)": f"{int(small_row['Number of Parts per Box'])} pcs", "Top 1 Best Box": f"{int(top1_row['Number of Parts per Box'])} pcs", "Top 2 Best Box": f"{int(top2_row['Number of Parts per Box'])} pcs" if top2_row is not None else "N/A", "Top 3 Best Box": f"{int(top3_row['Number of Parts per Box'])} pcs" if top3_row is not None else "N/A"},
            {"Metric": "Boxes / EPAL 1", "Smallest Box (Top 10)": f"{bt_s} boxes", "Top 1 Best Box": f"{bt_1} boxes", "Top 2 Best Box": f"{bt_2} boxes" if top2_row is not None else "N/A", "Top 3 Best Box": f"{bt_3} boxes" if top3_row is not None else "N/A"},
            {"Metric": "Total Yield / Pallet", "Smallest Box (Top 10)": f"{pcs_s} pcs", "Top 1 Best Box": f"{pcs_1} pcs", "Top 2 Best Box": f"{pcs_2} pcs" if top2_row is not None else "N/A", "Top 3 Best Box": f"{pcs_3} pcs" if top3_row is not None else "N/A"},
            {"Metric": "Pallet Gross Weight", "Smallest Box (Top 10)": f"{wt_s} kg", "Top 1 Best Box": f"{wt_1} kg", "Top 2 Best Box": f"{wt_2} kg" if top2_row is not None else "N/A", "Top 3 Best Box": f"{wt_3} kg" if top3_row is not None else "N/A"},
            {"Metric": "Pallet Packaging Cost", "Smallest Box (Top 10)": f"€ {(bt_s * small_row['Box Price (€)']) + 8:.2f}", "Top 1 Best Box": f"€ {(bt_1 * top1_row['Box Price (€)']) + 8:.2f}", "Top 2 Best Box": f"€ {(bt_2 * top2_row['Box Price (€)']) + 8:.2f}" if top2_row is not None else "N/A", "Top 3 Best Box": f"€ {(bt_3 * top3_row['Box Price (€)']) + 8:.2f}" if top3_row is not None else "N/A"}
        ])
        st.table(comp_df.set_index("Metric"))
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 3: MCKEE COMPRESSION SAFETY CHECK
    # --------------------------------------------------------------------------
    with tab_compression:
        st.markdown("#### 🗜️ Corrugated McKee Box Compression Test (BCT)")
        st.caption("Verifies whether bottom boxes can withstand vertical static loading under environmental degradation factors.")

        col_stk_opt, col_box_chk = st.columns(2)
        with col_stk_opt:
            stack_style = st.selectbox(
                "Pallet Configuration:",
                ["Single Pallet Load", "Double-Stacked Pallets (Pallet-on-Pallet)"]
            )
        with col_box_chk:
            selected_box_t3 = st.selectbox("Inspect Box Specification:", options=available_boxes, key="box_t3_select")

        viz_box_t3 = ranked_df[ranked_df["Box ID / Specification"] == selected_box_t3].iloc[0]

        # Environmental sliders / selections
        c_env1, c_env2, c_env3 = st.columns(3)
        with c_env1:
            moisture_sel = st.selectbox("Moisture / Humidity:", ["Dry", "Normal", "Humid", "Wet"], index=1)
        with c_env2:
            spread_sel = st.selectbox("Load Spread:", ["Even", "Uneven", "Center", "Corner"], index=0)
        with c_env3:
            storage_sel = st.selectbox("Storage Duration:", ["Short (days)", "Medium (weeks)", "Long (months)"], index=1)

        f_moisture = {"Dry": 1.0, "Normal": 1.1, "Humid": 1.3, "Wet": 1.6}[moisture_sel]
        f_spread = {"Even": 1.0, "Uneven": 1.2, "Center": 1.35, "Corner": 1.5}[spread_sel]
        f_storage = {"Short (days)": 1.0, "Medium (weeks)": 1.25, "Long (months)": 1.5}[storage_sel]

        QUALITY_PROPERTIES = {
            "1.20B": {"ect": 3.0, "thickness": 3.0, "name": "Single Wall - B Flute"},
            "1.20C": {"ect": 3.8, "thickness": 4.0, "name": "Single Wall - C Flute"},
            "2.30EB": {"ect": 5.5, "thickness": 4.5, "name": "Double Wall - EB Flute"},
            "2.30BC": {"ect": 7.5, "thickness": 6.5, "name": "Double Wall - BC Flute"}
        }

        q_class = str(viz_box_t3["Quality Class"]).strip()
        props = QUALITY_PROPERTIES.get(q_class, {"ect": 4.0, "thickness": 3.5, "name": "Custom Grade"})

        box_perimeter = 2 * (viz_box_t3["Int. Length [mm]"] + viz_box_t3["Int. Width [mm]"])
        bct_n = 1.82 * props["ect"] * np.sqrt(props["thickness"] * box_perimeter)
        bct_kg = round(bct_n / 9.81, 1)
        sf = round(1.5 * f_moisture * f_spread * f_storage, 2)
        safe_capacity = round(bct_kg / sf, 1)

        _, z_layers_c, best_l_c, _, p_wt_c, _, _, _ = calculate_pallet_stacking(
            1200, 800, viz_box_t3["Ext. Length [mm]"], viz_box_t3["Ext. Width [mm]"], 
            viz_box_t3["Ext. Height [mm]"], viz_box_t3["Total Weight (kg)"], int(viz_box_t3["Number of Parts per Box"])
        )

        actual_load = round(max(0, z_layers_c - 1) * viz_box_t3["Total Weight (kg)"], 1)
        if stack_style == "Double-Stacked Pallets (Pallet-on-Pallet)":
            actual_load += round(p_wt_c / max(1, best_l_c), 1)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Theoretical BCT", f"{bct_kg} kg")
        m2.metric("Safety Factor", f"{sf}x")
        m3.metric("Safe Design Capacity", f"{safe_capacity} kg")
        m4.metric("Actual Bottom Load", f"{actual_load} kg")

        if actual_load <= safe_capacity:
            st.markdown(f"""
                <div style='background-color:rgba(34, 197, 94, 0.12); border-left:4px solid #16a34a; padding:16px; border-radius:10px; margin-top:14px;'>
                    <b style='color:#16a34a;'>🟢 Structural Verification Passed</b><br>
                    <span style='font-size:13px;'>The actual load of <b>{actual_load} kg</b> is within safe capacity (<b>{safe_capacity} kg</b>) for <b>{q_class}</b>.</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background-color:rgba(239, 68, 68, 0.12); border-left:4px solid #dc2626; padding:16px; border-radius:10px; margin-top:14px;'>
                    <b style='color:#dc2626;'>🚨 Structural Failure Hazard</b><br>
                    <span style='font-size:13px;'>Actual load of <b>{actual_load} kg</b> exceeds safe threshold of <b>{safe_capacity} kg</b>. Recommend upgrading to double-wall grade (2.30BC) or reducing tier layers.</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.latex(r"\text{BCT (N)} = 1.82 \times \text{ECT} \times \sqrt{t \times P}")
        st.latex(r"\text{Safe Limit} = \frac{\text{BCT (kg)}}{\text{Combined Safety Factor}}")

else:
    st.warning("⚠️ No suitable boxes found in database matching active specifications.")
