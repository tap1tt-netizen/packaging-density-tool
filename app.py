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

# Set up page layout and appearance
st.set_page_config(
    page_title="Packaging Density & Box Recommender Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme-Proof Styling: Uses Streamlit CSS variables to support Light and Dark themes perfectly
st.markdown("""
    <style>
    .metric-box {
        background-color: var(--background-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid var(--text-color);
        border-left: 5px solid #0056b3;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-height: 110px;
        color: var(--text-color);
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    .guide-box {
        background-color: var(--background-color);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid var(--text-color);
        color: var(--text-color);
    }
    .warning-box {
        background-color: rgba(245, 159, 0, 0.15);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #f59f00;
        margin-bottom: 15px;
        color: var(--text-color);
    }
    .danger-box {
        background-color: rgba(255, 135, 135, 0.15);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff8787;
        margin-bottom: 15px;
        color: var(--text-color);
    }
    .success-box {
        background-color: rgba(148, 216, 45, 0.15);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #94d82d;
        margin-bottom: 15px;
        color: var(--text-color);
    }
    </style>
""", unsafe_allow_html=True)

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
except Exception as e:
    st.error("⚠️ Database connection failed!")
    st.info("Please place your cardboard database file named `1.xlsx` in this folder:")
    st.code(os.getcwd())
    st.stop()

# --- SIDEBAR: OPERATOR INPUTS ---
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
    st.title("📦 Packaging Density & Interactive Box Recommender")
    st.markdown("### Grid-Based Product Accommodation & Operator Safety Tool")
    st.write("This tool calculates the maximum number of parts that can fit inside standard boxes with partition separators.")
    st.warning("⚠️ **Please select a part material** in the sidebar to recommend boxes.")
    st.stop()

# --- RECOMMENDATION SYSTEM MATHEMATICS ---
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
        continue
        
    parts_count, pack_orient, grid_layout = calculate_packing(
        box_int_l, box_int_w, box_int_h, 
        prod_l, prod_w, prod_h,
        rule=orientation_rule
    )
    
    if parts_count == 0:
        continue
        
    # Calculate Weights
    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row['Quality'])
    total_payload_wt = parts_count * prod_wt
    total_package_weight = total_payload_wt + box_weight
    
    # --- REQ 1: WEIGHT THRESHOLD SHIFT (UNDER 15KG ONLY FOR footprint <= 400x300) ---
    dims_footprint = sorted([ext_l, ext_w])
    is_manual_box = (dims_footprint[0] <= 300.0) and (dims_footprint[1] <= 400.0)
    
    if is_manual_box and total_package_weight > 15.0:
        continue
        
    # Structural Box Load check
    if total_payload_wt > row['Max. Load [kg]']:
        continue
        
    # Volumes & Air Spaces
    box_internal_vol = box_int_l * box_int_w * box_int_h
    occupied_volume = parts_count * single_part_vol
    vol_efficiency = (occupied_volume / box_internal_vol) * 100
    air_space_percent = 100.0 - vol_efficiency
    
    results.append({
        "Box ID / Specification": row['BoxSize'],
        "Box Footprint (Ext)": f"{int(ext_l)}x{int(ext_w)} mm",
        "Quality Class": row['Quality'],
        "Internal Dimensions": f"{int(box_int_l)}x{int(box_int_w)}x{int(box_int_h)} mm",
        "Int. Length [mm]": box_int_l,
        "Int. Width [mm]": box_int_w,
        "Int. Height [mm]": box_int_h,
        "Ext. Length [mm]": ext_l,
        "Ext. Width [mm]": ext_w,
        "Ext. Height [mm]": ext_h,
        "Number of Parts per Box": parts_count,
        "Optimal Grid Layout": f"{grid_layout[0]}x{grid_layout[1]}x{grid_layout[2]} (X x Y x Z)",
        "Optimal Orientation": f"{int(pack_orient[0])}x{int(pack_orient[1])}x{int(pack_orient[2])} mm",
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

# Render Results
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
    
    # --- TOP HEADER SAFETY BADGE LAYOUT ---
    col_title, col_safety_header = st.columns([7, 3])
    
    with col_title:
        st.title("📦 BSH Packaging Density & Box Recommender")
        st.markdown("### Grid-Based Product Accommodation & Stacking Optimizer")
    
    with col_safety_header:
        total_package_weight = best_box["Total Weight (kg)"]
        ext_l = best_box["Ext. Length [mm]"]
        ext_w = best_box["Ext. Width [mm]"]
        dims_footprint = sorted([ext_l, ext_w])
        is_manual_box = (dims_footprint[0] <= 300.0) and (dims_footprint[1] <= 400.0)
        
        if total_package_weight > 15.0:
            if not is_manual_box:
                st.markdown(f"""
                    <div style='background-color:rgba(224, 49, 49, 0.15); border-left:5px solid #e03131; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#e03131; font-size:16px;'>🚨 Forklift Transport Required</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>{total_package_weight} kg (Bypasses manual limit)</span><br>
                        <span style='font-size:11px;'>Box footprint <b>{int(ext_l)}x{int(ext_w)} mm</b> is larger than the <b>400x300 mm</b> manual threshold. Therefore, exceeding 15 kg is <b>permitted</b>.</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color:rgba(224, 49, 49, 0.15); border-left:5px solid #e03131; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                        <b style='color:#e03131; font-size:16px;'>🚨 Overweight Manual Box</b><br>
                        <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>{total_package_weight} kg (Exceeds 15kg limit)</span><br>
                        <span style='font-size:11px;'>Box footprint <b>{int(ext_l)}x{int(ext_w)} mm</b> is within the <b>400x300 mm</b> manual threshold, but exceeds 15 kg limit. This is prohibited for manual operator packing!</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background-color:rgba(43, 138, 62, 0.15); border-left:5px solid #2b8a3e; padding:15px; border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:10px;'>
                    <b style='color:#2b8a3e; font-size:16px;'>🟢 Safe Operational Weight</b><br>
                    <span style='font-size:14px; font-weight:bold; color: var(--text-color);'>Safe at {total_package_weight} kg</span><br>
                    <span style='font-size:11px;'>Box footprint <b>{int(ext_l)}x{int(ext_w)} mm</b> is within the <b>400x300 mm</b> manual threshold. Approved for Safe Manual Operator Packing.</span>
                </div>
            """, unsafe_allow_html=True)
            
    st.success(f"Connected to Cardboard Database: `{filename_loaded}`")
    
    st.subheader("💡 Best Matched Packing Insights")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                <b>👑 Best Recommendation</b><br>
                <span style='font-size:11px; font-weight:bold; color:#0056b3;'>
                    {best_box['Box ID / Specification']}<br>
                    <span style='color:#dc3545;'>[Quality: {best_box['Quality Class']}]</span>
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
    
    # ==========================================
    # TAB 1: BOX RECOMMENDER & INDIVIDUAL LOADING
    # ==========================================
    with tab_recommender:
        display_df = ranked_df.drop(columns=["_nx", "_ny", "_nz", "_ox", "_oy", "_oz", "Int. Length [mm]", "Int. Width [mm]", "Int. Height [mm]", "Ext. Length [mm]", "Ext. Width [mm]"])
        
        col_header, col_export_hub = st.columns([7, 3])
        with col_header:
            st.subheader("🏆 Top 10 Recommended Cardboard Boxes")
            
        with col_export_hub:
            export_format = st.selectbox(
                "📥 Select Export Format...",
                ["-- Choose Format --", "Export to Excel (.xlsx)", "Export to CSV (.csv)"],
                index=0,
                key="export_selector_hub",
                help="Download the live Top 10 recommendations directly to your machine."
            )
            
            if export_format == "Export to Excel (.xlsx)":
                buffer_xls = io.BytesIO()
                with pd.ExcelWriter(buffer_xls, engine='openpyxl') as writer:
                    display_df.to_excel(writer, sheet_name='Top_10_Recommendations', index=True)
                xls_data = buffer_xls.getvalue()
                st.download_button(
                    label="🟢 Click to Download Excel Sheet",
                    data=xls_data,
                    file_name="Top_10_Recommended_Boxes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            elif export_format == "Export to CSV (.csv)":
                csv_data = display_df.to_csv(index=True).encode('utf-8')
                st.download_button(
                    label="🔵 Click to Download CSV File",
                    data=csv_data,
                    file_name="Top_10_Recommended_Boxes.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
        st.dataframe(
            display_df,
            column_config={
                "Volumetric Efficiency (%)": st.column_config.ProgressColumn(
                    "Volumetric Efficiency (%)",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100,
                    color="blue"
                ),
                "Box Price (€)": st.column_config.NumberColumn(
                    "Box Price (€)",
                    format="€ %.2f"
                )
            },
            use_container_width=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Step-by-Step Visual Blueprint Loading Map")
        
        available_boxes = list(ranked_df["Box ID / Specification"].values)
        
        if "last_available_boxes" not in st.session_state or st.session_state["last_available_boxes"] != available_boxes:
            st.session_state["selected_box"] = available_boxes[0]
            st.session_state["last_available_boxes"] = available_boxes
        if "selected_box" not in st.session_state or st.session_state["selected_box"] not in available_boxes:
            st.session_state["selected_box"] = available_boxes[0]
            
        default_index = available_boxes.index(st.session_state["selected_box"])
        def on_box_change():
            st.session_state["selected_box"] = st.session_state["temp_box_selector"]
            
        selected_box_spec = st.selectbox(
            "Select a Cardboard Box from the Top 10 to generate its loading blueprints:",
            options=available_boxes,
            index=default_index,
            key="temp_box_selector",
            on_change=on_box_change
        )
        
        st.session_state["selected_box"] = selected_box_spec
        viz_box = ranked_df[ranked_df["Box ID / Specification"] == st.session_state["selected_box"]].iloc[0]
        
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
                st.markdown("<div class='guide-box'><h4><b>🛠️ 3-Step Packing Instruction</b></h4><hr>", unsafe_allow_html=True)
                
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
                
                st.markdown(f"""
                <b>Step 2: Arrange the Floor Grid</b><br>
                Lay down a grid of <b>{nx} columns</b> and <b>{ny} rows</b> of parts on the floor of the box. 
                <ul>
                    <li>This packs exactly <b>{nx * ny} parts</b> on this layer.</li>
                    <li>Place the {sep_xy}mm partition grids between each part.</li>
                </ul>
                """, unsafe_allow_html=True)
                
                if nz > 1:
                    st.markdown(f"""
                    <b>Step 3: Stacking Vertical Layers</b><br>
                    <ul>
                        <li>Lay down a flat {sep_z}mm cardboard divider sheet on top of your completed layer.</li>
                        <li>Repeat the same grid layout of {nx*ny} parts on top.</li>
                        <li>Do this until you have built a total of <b>{nz} vertical layers</b> (reaching <b>{int(viz_box['Number of Parts per Box'])} pieces</b> in total).</li>
                    </ul>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <b>Step 3: Finish Packing</b><br>
                    Since all <b>{int(viz_box['Number of Parts per Box'])} parts</b> fit in <b>1 single floor layer</b>, you do not need any flat shelf dividers or vertical stacking. 
                    <br>Just seal the box and ship!
                    """, unsafe_allow_html=True)
                    
                sel_package_weight = viz_box["Total Weight (kg)"]
                ext_l_sel = viz_box["Ext. Length [mm]"]
                ext_w_sel = viz_box["Ext. Width [mm]"]
                dims_footprint_sel = sorted([ext_l_sel, ext_w_sel])
                is_manual_box_sel = (dims_footprint_sel[0] <= 300.0) and (dims_footprint_sel[1] <= 400.0)
                
                if sel_package_weight > 15.0:
                    if not is_manual_box_sel:
                        st.markdown(f"<p style='color:#2b8a3e; font-weight:bold; margin-top:10px;'>🟢 Operational Weight: {sel_package_weight} kg (Permitted: Box footprint {int(ext_l_sel)}x{int(ext_w_sel)} mm exceeds 400x300 mm manual threshold)</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:#e03131; font-weight:bold; margin-top:10px;'>🚨 Operational Weight: {sel_package_weight} kg (Overweight manual packing error!)</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#2b8a3e; font-weight:bold; margin-top:10px;'>🟢 Operational Weight: Safe at {sel_package_weight} kg</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_flat:
                # Dynamically determine Streamlit Theme colors to protect contrast in dark/light modes
                st_text_color = '#FFFFFF' if st.get_option('theme.base') == 'dark' else '#212529'
                st_face_color = '#1c7ed6'
                st_edge_color = '#102a43'
                
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
                
                for r in range(ny):
                    y_pos = start_y_offset + r * (oy + sep_xy)
                    for c in range(nx):
                        x_pos = start_x_offset + c * (ox + sep_xy)
                        ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#a5d8ff', edgecolor='#1971c2', linewidth=1.2))
                        ax.text(x_pos + ox/2, y_pos + oy/2, f"{c+1}, {r+1}", ha='center', va='center', fontsize=8, color='#0f4c81', fontweight='bold')
                
                ax.annotate('', xy=(0, -25), xytext=(box_l, -25),
                            arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
                ax.text(box_l/2, -45, f"{int(ext_l)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center')
                
                ax.annotate('', xy=(box_l + 25, 0), xytext=(box_l + 25, box_w),
                            arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
                ax.text(box_l + 45, box_w/2, f"{int(ext_w)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center', va='center', rotation=-90)
                
                ax.text(box_l/2, box_w + 15, f"Layers: {nz} Vertical", color='#dc3545', fontsize=14, fontweight='bold', ha='center')
                
                ax.set_xlim(-40, box_l + 80)
                ax.set_ylim(-60, box_w + 35)
                ax.set_aspect('equal')
                ax.axis('off')
                st.pyplot(fig)
                plt.close(fig)
                
            with col_stack:
                fig3d = plt.figure(figsize=(4, 3.5), facecolor='none')
                ax3d = fig3d.add_subplot(111, projection='3d', facecolor='none')
                w_scale = 100
                l_scale = w_scale * (box_l / box_w)
                h_scale = 30
                
                z_aspect = max(30, nz * 15)
                ax3d.set_box_aspect((l_scale, w_scale, z_aspect))
                
                lbl_font = 9 if nz > 6 else 12
                
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
                    color = '#a5d8ff' if layer < nz - 1 else '#74c0fc'
                    poly = Poly3DCollection(faces, facecolors=color, edgecolors='#1971c2', linewidths=1.5, alpha=0.8)
                    ax3d.add_collection3d(poly)
                    
                    ax3d.text(-35, 20, z_start + h_scale/2, f"L{layer + 1}", color='#dc3545', fontweight='bold', fontsize=lbl_font, ha='right', va='center', zorder=100)
                    ax3d.plot([-30, 0], [10, 0], [z_start + h_scale/2, z_start + h_scale/2], color='#dc3545', linestyle=':', linewidth=1)
                    
                ax3d.set_xlim(-50, l_scale + 10)
                ax3d.set_ylim(-20, w_scale + 10)
                ax3d.set_zlim(0, nz * (h_scale + 5) + 10)
                ax3d.view_init(elev=22, azim=-65)
                ax3d.axis('off')
                
                plt.title("Vertical Stacking Blueprint", fontsize=11, fontweight='bold', color=st_text_color, pad=10)
                st.pyplot(fig3d)
                plt.close(fig3d)
                
        # --- DYNAMIC INTERACTIVE 3D DIGITAL TWIN VIEWPORT ---
        st.markdown("<hr>", unsafe_allow_html=True)
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
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                
                # 🟢 FIXED: Plotly correctly renders actual face indices (raw_f) instead of hardcoded bounding box indices
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
                        i=raw_f[:, 0],
                        j=raw_f[:, 1],
                        k=raw_f[:, 2],
                        color='#74c0fc', opacity=1.0,
                        flatshading=False,
                        lighting=dict(ambient=0.5, diffuse=0.9, specular=1.2, roughness=0.15, fresnel=0.5),
                        name=text_str,
                        hoverinfo="text",
                        text=text_str,
                        showlegend=False
                    ))
                
                total_grid_w = nx * ox + (nx - 1) * sep_xy
                total_grid_h = ny * oy + (ny - 1) * sep_xy
                leftover_x = (box_l - 2 * clear_side) - total_grid_w
                leftover_y = (box_w - 2 * clear_side) - total_grid_h
                start_x_offset = clear_side + (leftover_x / 2)
                start_y_offset = clear_side + (leftover_y / 2)
                
                selected_cells = []
                for l in range(nz):
                    if nz > 1:
                        c_diag = int(round(l * (nx - 1) / (nz - 1)))
                        r_diag = int(round(l * (ny - 1) / (nz - 1)))
                    else:
                        c_diag, r_diag = 0, 0
                    selected_cells.append((c_diag, r_diag, l))
                
                for layer in range(nz):
                    z_pos = layer * (oz + sep_z)
                    for r in range(ny):
                        y_pos = start_y_offset + r * (oy + sep_xy)
                        for c in range(nx):
                            x_pos = start_x_offset + c * (ox + sep_xy)
                            add_wireframe_compartment(fig_pack, x_pos, y_pos, z_pos, ox, oy, oz)
                            if (c, r, layer) in selected_cells and mesh_cad is not None:
                                add_plotly_mesh_part(
                                    fig_pack, x_pos, y_pos, z_pos, ox, oy, oz, 
                                    mesh_cad.vertices, mesh_cad.faces, 
                                    f"Part @ Col {c+1}, Row {r+1}, Layer {layer+1}"
                                )
                
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

    # =======================================================
    # TAB 2: PALLET STACKING OPTIMIZER & COMPARATIVE ANALYSIS
    # =======================================================
    with tab_pallet:
        st.subheader("🚛 Multi-Pallet Optimization Engine")
        st.markdown("Maximize pallet transport layout efficiency under a **1000 mm height constraint** and a **1000 kg gross weight limit**.")
        
        # EPAL Pallets Dimensions (in mm)
        PALLETS = {
            "EPAL 1 (Standard)": {"l": 1200, "w": 800, "tare": 23.0},
            "EPAL 2 (Industrial)": {"l": 1200, "w": 1000, "tare": 23.0}
        }
        
        # Universal Palletization Stacking Solver
        def calculate_pallet_stacking(pallet_l, pallet_w, ext_l, ext_w, ext_h, box_wt, pcs_box, pallet_tare=23.0, max_h=1000.0, max_wt=1000.0):
            # Orientation A (Lengthwise L-parallel)
            nx_a = int(pallet_l // ext_l)
            ny_a = int(pallet_w // ext_w)
            layers_a = nx_a * ny_a
            
            # Orientation B (Widthwise W-parallel)
            nx_b = int(pallet_l // ext_w)
            ny_b = int(pallet_w // ext_l)
            layers_b = nx_b * ny_b
            
            best_layer_qty = max(layers_a, layers_b)
            best_orient = "Lengthwise (L-parallel)" if layers_a >= layers_b else "Widthwise (W-parallel)"
            nx_best = nx_a if layers_a >= layers_b else nx_b
            ny_best = ny_a if layers_a >= layers_b else ny_b
            
            # Max vertical layers (Pure Box stacking height up to 1000mm)
            nz = int(max_h // ext_h)
            if nz < 1:
                nz = 1
                
            total_boxes = best_layer_qty * nz
            total_weight = total_boxes * box_wt + pallet_tare
            
            # Reduce stack height layers if pallet weight exceeds the 1000 kg threshold
            while total_weight > max_wt and nz > 1:
                nz -= 1
                total_boxes = best_layer_qty * nz
                total_weight = total_boxes * box_wt + pallet_tare
                
            total_pcs = total_boxes * pcs_box
            return total_boxes, nz, best_layer_qty, total_pcs, round(total_weight, 2), best_orient, nx_best, ny_best

        # -----------------------------------------------------------------------------
        # 1. AUTOMATED COMPARATIVE MATRIX: SMALLEST vs. TOP 1 vs. TOP 2 vs. TOP 3
        # -----------------------------------------------------------------------------
        st.markdown("### ⚖️ Automated Stacking Comparison")
        st.markdown("This matrix automatically compares **four benchmark options selected strictly from your recommended Top 10 list** on a standard EPAL 1 Pallet:")
        
        ranked_df_copy = ranked_df.copy()
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
            
            # Compute EPAL 1 standard pallet capacity for each benchmark choice
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
            
            # Determine the ultimate yield winner
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
                It delivers <b style='color:#2b8a3e;'>{max_yield} total pieces</b> per standard EPAL 1 pallet, ensuring maximum spatial shipping density.
            </div>
            """, unsafe_allow_html=True)
            
            # 🟢 NEW STYLING: Comparative Matrix Table (With Optimal Packing Orientation included)
            comp_df = pd.DataFrame([
                {"Metric Profile": "Box Specification ID", "Smallest Box (Top 10)": small_name, "Top 1 Best Box": top1_name, "Top 2 Best Box": top2_name, "Top 3 Best Box": top3_name},
                {"Metric Profile": "External Footprint Dimensions", "Smallest Box (Top 10)": f"{int(small_row['Ext. Length [mm]'])}x{int(small_row['Ext. Width [mm]'])} mm", "Top 1 Best Box": f"{int(top1_row['Ext. Length [mm]'])}x{int(top1_row['Ext. Width [mm]'])} mm", "Top 2 Best Box": f"{int(top2_row['Ext. Length [mm]'])}x{int(top2_row['Ext. Width [mm]'])} mm" if top2_row is not None else "N/A", "Top 3 Best Box": f"{int(top3_row['Ext. Length [mm]'])}x{int(top3_row['Ext. Width [mm]'])} mm" if top3_row is not None else "N/A"},
                {"Metric Profile": "Optimal Packing Orientation", "Smallest Box (Top 10)": determine_placement_style(prod_l, prod_w, prod_h, small_row["_oz"]), "Top 1 Best Box": determine_placement_style(prod_l, prod_w, prod_h, top1_row["_oz"]), "Top 2 Best Box": determine_placement_style(prod_l, prod_w, prod_h, top2_row["_oz"]) if top2_row is not None else "N/A", "Top 3 Best Box": determine_placement_style(prod_l, prod_w, prod_h, top3_row["_oz"]) if top3_row is not None else "N/A"},
                {"Metric Profile": "Parts Loaded (Per Box)", "Smallest Box (Top 10)": f"{int(small_row['Number of Parts per Box'])} Pcs", "Top 1 Best Box": f"{int(top1_row['Number of Parts per Box'])} Pcs", "Top 2 Best Box": f"{int(top2_row['Number of Parts per Box'])} Pcs" if top2_row is not None else "N/A", "Top 3 Best Box": f"{int(top3_row['Number of Parts per Box'])} Pcs" if top3_row is not None else "N/A"},
                {"Metric Profile": "Boxes Loaded (Per Pallet)", "Smallest Box (Top 10)": f"{bt_s} boxes", "Top 1 Best Box": f"{bt_1} boxes", "Top 2 Best Box": f"{bt_2} boxes" if top2_row is not None else "N/A", "Top 3 Best Box": f"{bt_3} boxes" if top3_row is not None else "N/A"},
                {"Metric Profile": "Total Pieces (Per Pallet)", "Smallest Box (Top 10)": f"{pcs_s} Pcs", "Top 1 Best Box": f"{pcs_1} Pcs", "Top 2 Best Box": f"{pcs_2} Pcs" if top2_row is not None else "N/A", "Top 3 Best Box": f"{pcs_3} Pcs" if top3_row is not None else "N/A"},
                {"Metric Profile": "Pallet Weight (inc. 23kg Tare)", "Smallest Box (Top 10)": f"{wt_s} kg", "Top 1 Best Box": f"{wt_1} kg", "Top 2 Best Box": f"{wt_2} kg" if top2_row is not None else "N/A", "Top 3 Best Box": f"{wt_3} kg" if top3_row is not None else "N/A"}
            ])
            st.table(comp_df)
        else:
            st.info("💡 Multiple unique box sizes are required in the inventory database to generate a comparative analysis.")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # -------------------------------------------------------------
        # 2. INDIVIDUAL STACKING REPORT & INTERACTIVE 3D PALLETIZER
        # -------------------------------------------------------------
        st.markdown(f"### 📦 Palletization Report & Interactive 3D Stacking Model")
        
        available_boxes_t2 = list(ranked_df["Box ID / Specification"].values)
        if "selected_box" not in st.session_state or st.session_state["selected_box"] not in available_boxes_t2:
            st.session_state["selected_box"] = available_boxes_t2[0]
            
        selected_box_t2 = st.selectbox(
            "Select any Cardboard Box to inspect its detailed pallet loading report & rotatable 3D stack:",
            options=available_boxes_t2,
            index=available_boxes_t2.index(st.session_state["selected_box"]),
            key="pallet_box_selector"
        )
        st.session_state["selected_box"] = selected_box_t2
        
        viz_box_t2 = ranked_df[ranked_df["Box ID / Specification"] == selected_box_t2].iloc[0]
        
        bx_ext_l = viz_box_t2["Ext. Length [mm]"]
        bx_ext_w = viz_box_t2["Ext. Width [mm]"]
        bx_ext_h = viz_box_t2["Ext. Height [mm]"]
        bx_wt = viz_box_t2["Total Weight (kg)"]
        pcs_per_bx = int(viz_box_t2["Number of Parts per Box"])
        
        col_metrics, col_plotly_pallet = st.columns([4, 6])
        
        with col_metrics:
            st.markdown(f"#### 📋 Stacking Report for **{selected_box_t2}**")
            
            # Compute EPAL 1
            b_total_1, z_layers_1, layer_qty_1, p_pcs_1, p_wt_1, orient_1, nx_1, ny_1 = calculate_pallet_stacking(
                PALLETS["EPAL 1 (Standard)"]["l"], PALLETS["EPAL 1 (Standard)"]["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, bx_wt, pcs_per_bx, PALLETS["EPAL 1 (Standard)"]["tare"]
            )
            # Compute EPAL 2
            b_total_2, z_layers_2, layer_qty_2, p_pcs_2, p_wt_2, orient_2, nx_2, ny_2 = calculate_pallet_stacking(
                PALLETS["EPAL 2 (Industrial)"]["l"], PALLETS["EPAL 2 (Industrial)"]["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, bx_wt, pcs_per_bx, PALLETS["EPAL 2 (Industrial)"]["tare"]
            )
            
            st.markdown(f"""
            <div style='background-color: var(--background-color); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--text-color); border-left: 5px solid #228be6;'>
                <h5 style='margin-top: 0px;'>🥇 EPAL 1 standard (1200 x 800 mm)</h5>
                <b>Orientation:</b> {orient_1}<br>
                📐 <b>Layer Layout Grid:</b> {nx_1} x {ny_1} (X x Y)<br>
                🪜 <b>Stacking Height (Vertical Layers):</b> {z_layers_1} layers<br>
                📦 <b>Total Boxes:</b> {b_total_1} units<br>
                ✨ <b>Total Pieces:</b> <b style='color:#2b8a3e;'>{p_pcs_1} Pcs</b><br>
                ⚖️ <b>Pallet Weight:</b> <b>{p_wt_1} kg</b> (including 23kg Pallet)
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
                ⚖️ <b>Pallet Weight:</b> <b>{p_wt_2} kg</b> (including 23kg Pallet)
            </div>
            """, unsafe_allow_html=True)
            
        with col_plotly_pallet:
            st.markdown("##### 🔄 High-Definition Rotatable 3D Palletizer View")
            
            pallet_sel = st.radio("Choose Stacking Blueprint Pallet View:", options=["EPAL 1 (1200x800)", "EPAL 2 (1200x1000)"])
            active_p_spec = PALLETS["EPAL 1 (Standard)"] if "EPAL 1" in pallet_sel else PALLETS["EPAL 2 (Industrial)"]
            
            p_boxes, p_layers, p_l_qty, _, _, p_orient, nx_act, ny_act = calculate_pallet_stacking(
                active_p_spec["l"], active_p_spec["w"],
                bx_ext_l, bx_ext_w, bx_ext_h, bx_wt, pcs_per_bx, active_p_spec["tare"]
            )
            
            try:
                fig_pallet_3d = go.Figure()
                
                # Draw Wood EPAL Pallet Base
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

    # =======================================================
    # TAB 3: MCKEE GRAVITY COMPRESSION SAFETY CHECK
    # =======================================================
    with tab_compression:
        st.subheader("🗜️ Corrugated Cardboard McKee Compression Strength Checker")
        st.markdown("Validate if the bottom cardboard box can handle the heavy vertical static loads from the stack above on a 1-meter pallet layout.")
        
        # --- REQ 1: STACKING METHODOLOGY SELECTOR ---
        st.markdown("#### ⚙️ Stacking Setup")
        stack_style = st.selectbox(
            "Select Pallet Stacking Configuration:",
            ["Single Pallet Load", "Double-Stacked Pallets (Pallet-on-Pallet)"],
            help="Single Pallet checks local column load. Double Stacking adds the entire gross weight of the top pallet onto the bottom boxes."
        )
        
        # 🟢 NEW DROP-DOWNS: Aligned drop-down metrics from PackagingTools.io standards
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
            transport_sel = st.selectbox("Transport Handling / Vibration:", ["LTL/FT FTL Truck", "Parcel shipping", "Air/Sea Cargo"], index=1)

        # Standard Multiplier Weights corresponding to the PackagingTools.io standards
        f_moisture = {"Dry": 1.0, "Normal": 1.1, "Humid": 1.3, "Wet": 1.6}[moisture_sel]
        f_spread = {"Even": 1.0, "Uneven": 1.2, "Center": 1.35, "Corner": 1.5}[spread_sel]
        f_fragility = {"Low": 1.0, "Medium": 1.15, "High": 1.3}[fragility_sel]
        f_storage = {"Short (days)": 1.0, "Medium (weeks)": 1.25, "Long (months)": 1.5}[storage_sel]
        f_transport = {"LTL/FT FTL Truck": 1.0, "Parcel shipping": 1.3, "Air/Sea Cargo": 1.4}[transport_sel]

        QUALITY_PROPERTIES = {
            "1.20B": {"ect": 3.0, "thickness": 3.0, "name": "Single Wall - B Flute"},
            "1.20C": {"ect": 3.8, "thickness": 4.0, "name": "Single Wall - C Flute"},
            "2.30EB": {"ect": 5.5, "thickness": 4.5, "name": "Double Wall - EB Flute"},
            "2.30BC": {"ect": 7.5, "thickness": 6.5, "name": "Double Wall - BC Flute"}
        }
        
        q_class = str(viz_box["Quality Class"]).strip()
        props = QUALITY_PROPERTIES.get(q_class, {"ect": 4.0, "thickness": 3.5, "name": "Custom / Unknown Grade"})
        
        ect_val = props["ect"]
        thickness_val = props["thickness"]
        q_name = props["name"]
        
        box_perimeter = 2 * (viz_box["Int. Length [mm]"] + viz_box["Int. Width [mm]"])
        bct_n = 5.876 * ect_val * np.sqrt(thickness_val * box_perimeter)
        bct_kg = round(bct_n / 9.81, 1) 
        
        # Calculate dynamic Combined Safety Factor (Base multiplier is 1.5)
        sf = round(1.5 * f_moisture * f_spread * f_fragility * f_storage * f_transport, 2)
        bct_safe_load = round(bct_kg / sf, 1)
        
        # Calculate actual static weight on bottom box
        _, z_layers_calc, best_layer_qty, _, p_wt_calc, _, _, _ = calculate_pallet_stacking(1200, 800, bx_ext_l, bx_ext_w, bx_ext_h, bx_wt, pcs_per_bx)
        boxes_above = max(0, z_layers_calc - 1)
        
        # Base load from boxes directly above in the stack
        actual_bottom_load = round(boxes_above * bx_wt, 1)
        
        # If Double Stacked is toggled, add top pallet gross load spread evenly over bottom pallet surface columns
        if stack_style == "Double-Stacked Pallets (Pallet-on-Pallet)":
            top_pallet_weight_contribution = round(p_wt_calc / max(1, best_layer_qty), 1)
            actual_bottom_load = round(actual_bottom_load + top_pallet_weight_contribution, 1)
        
        col_comp_kpis = st.columns(4)
        with col_comp_kpis[0]:
            st.metric("💪 Theoretical Box BCT Strength", f"{bct_kg} kg", help="Ultimate crushing force of a single box.")
        with col_comp_kpis[1]:
            st.metric("🛡️ Combined Safety Factor (SF)", f"{sf}x", help="Dynamic stacking margin calculated based on climate, storage, and handling conditions.")
        with col_comp_kpis[2]:
            st.metric("🔒 Safe Design Capacity", f"{bct_safe_load} kg", help=f"Maximum allowed load applying a {sf}x safety threshold.")
        with col_comp_kpis[3]:
            st.metric("🏋️ Actual Load on Bottom Box", f"{actual_bottom_load} kg", help="Total static weight supported by the lowest box on the stack.")
            
        st.markdown("#### 🔍 Structural Safety Verdict:")
        if actual_bottom_load == 0:
            st.markdown(f"""
            <div class='success-box'>
                <b>🟢 Safe (Single Layer Stack):</b> There are no other layers stacked above this box on the pallet. Compression failure is mathematically impossible.
            </div>
            """, unsafe_allow_html=True)
        elif actual_bottom_load <= bct_safe_load:
            st.markdown(f"""
            <div class='success-box'>
                <b>🟢 Safe Stacking Approved:</b> The actual load of <b>{actual_bottom_load} kg</b> is within the safe limit of <b>{bct_safe_load} kg</b>. 
                Cardboard quality class <b>{q_class} ({q_name})</b> is structurally sufficient for the bottom layers of this stack under current environment variables!
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='danger-box'>
                <b>🚨 Warning - Structural Failure Risk:</b> The actual load of <b>{actual_bottom_load} kg</b> exceeds the safe stacked design capacity of <b>{bct_safe_load} kg</b> under these environmental conditions!<br>
                <b>Recommendation:</b><br>
                1\. Upgrade the cardboard to a stronger grade (e.g., <b>2.30BC Double-Wall</b>).<br>
                2\. Decrease the stacking height on the pallet (reduce the number of layers).<br>
                3\. Use corner-board protectors to reinforce structural load paths.
            </div>
            """, unsafe_allow_html=True)
            
        # 🟢 FIXED: Raw f-string with double curly braces for math LaTeX syntax avoids f-string compile errors
        st.markdown(fr"""
        <div class='guide-box'>
            <h5>🧮 How McKee's Formula works under the hood:</h5>
            The Box Compression Test value is calculated using:<br>
            $$\text{{BCT}} = 5.876 \times \text{{ECT}} \times \sqrt{{t \times P}}$$
            <ul>
                <li><b>ECT (Edge Crush Test):</b> Standardized strength. For Quality <b>{q_class}</b>, ECT is <b>{ect_val} N/mm</b>.</li>
                <li><b>t (Thickness):</b> Cardboard thickness. For Quality <b>{q_class}</b>, thickness is <b>{thickness_val} mm</b>.</li>
                <li><b>P (Perimeter):</b> Measured boundary. For this box, perimeter is <b>{int(box_perimeter)} mm</b>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("⚠️ No suitable boxes in your database can fit this product under the active weight or dimension parameters.")
