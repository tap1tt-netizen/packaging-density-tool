import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import base64
import plotly.graph_objects as go

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
        background-color: #f1f3f5;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ced4da;
    }
    .warning-box {
        background-color: #fff9db;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #f59f00;
        margin-bottom: 15px;
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

# Visual Input Method Selector
upload_method = st.sidebar.radio("Select Visual Reference Method:", ["Multi-Angle 2D Photos", "3D CAD Model (.STL/.STEP)"])
uploaded_top = None
uploaded_front = None
uploaded_side = None
uploaded_stl = None
mesh_cad = None  # Global reference to loaded 3D mesh

# Default part dimensions and weight
auto_l, auto_w, auto_h = 170.0, 110.0, 40.0
calculated_weight_kg = 0.25

# Standard Engineering Material Densities (g/cm^3)
MATERIAL_DENSITIES = {
    "ABS Plastic": 1.04,
    "PLA Plastic": 1.24,
    "Polypropylene (PP)": 0.90,
    "Polycarbonate (PC)": 1.20,
    "Aluminum": 2.70,
    "Mild Steel": 7.85,
    "Stainless Steel": 8.00
}

if upload_method == "Multi-Angle 2D Photos":
    uploaded_top = st.sidebar.file_uploader("Upload TOP View (Length x Width)", type=["png", "jpg", "jpeg"])
    uploaded_front = st.sidebar.file_uploader("Upload FRONT View (Length x Height)", type=["png", "jpg", "jpeg"])
    uploaded_side = st.sidebar.file_uploader("Upload SIDE View (Width x Height)", type=["png", "jpg", "jpeg"])
else:
    # ALLOW INTAKE OF STL OR STEP SPECIFICATIONS
    uploaded_stl = st.sidebar.file_uploader("Upload 3D CAD File (.STL, .STEP, .STP)", type=["stl", "step", "stp"])
    if uploaded_stl is not None:
        filename = uploaded_stl.name.lower()
        try:
            import trimesh
            uploaded_stl.seek(0)
            
            # PARSE DYNAMICALLY BASED ON ACTUAL COMPATIBLE CAD EXTENSIONS
            if filename.endswith('.step') or filename.endswith('.stp'):
                import cascadio
                mesh_cad = trimesh.load(uploaded_stl, file_type='step')
            else:
                mesh_cad = trimesh.load(uploaded_stl, file_type='stl')
            
            # Calculate and load exact coordinates
            bounds = mesh_cad.bounding_box.extents
            dims = sorted(bounds)
            auto_h = round(dims[0], 1)
            auto_w = round(dims[1], 1)
            auto_l = round(dims[2], 1)
            
            # Extract raw CAD solid volume
            cad_volume = mesh_cad.volume
            
            # Auto unit scaling detector (cm to mm)
            is_cm_scale = auto_l < 50.0
            if is_cm_scale:
                auto_l *= 10.0
                auto_w *= 10.0
                auto_h *= 10.0
                cad_volume *= 1000.0  # Scale volume from cm^3 to mm^3
                
            st.sidebar.success(f"📐 Auto-Extracted Dimensions: {auto_l} x {auto_w} x {auto_h} mm")
            
            # Dynamic Material Density Selector
            st.sidebar.markdown("#### 🪵 Material Weight Extractor")
            selected_material = st.sidebar.selectbox("Select Part Material:", list(MATERIAL_DENSITIES.keys()), index=6) # Default to Stainless Steel
            density = MATERIAL_DENSITIES[selected_material]
            
            # Calculate weight: Vol (mm^3) * Density (g/cm^3) * 1e-6 (kg/g_mm3)
            calculated_weight_kg = round(cad_volume * density * 1e-6, 3)
            st.sidebar.info(f"⚖️ Calculated Solid Weight ({selected_material}): **{calculated_weight_kg} kg**")
            
        except Exception as e_cad:
            st.sidebar.warning(f"Could not auto-extract CAD dimensions: {e_cad}")

# Product Physical Dimensions Inputs (Pre-filled with CAD data if available)
st.sidebar.markdown("#### Part Dimensions (mm)")
prod_l = st.sidebar.number_input("Part Length (mm)", min_value=1.0, value=float(auto_l), step=1.0)
prod_w = st.sidebar.number_input("Part Width (mm)", min_value=1.0, value=float(auto_w), step=1.0)
prod_h = st.sidebar.number_input("Part Height (mm)", min_value=1.0, value=float(auto_h), step=1.0)

# Product Weight (Pre-filled with calculated weight if CAD file is uploaded)
st.sidebar.markdown("#### Part Weight (kg)")
prod_wt = st.sidebar.number_input("Weight per Part (kg)", min_value=0.01, value=float(calculated_weight_kg), step=0.05)

st.sidebar.markdown("---")
st.sidebar.header("📏 Divider & Clearance Spacing")

# Margins and Clearances
clear_side = st.sidebar.slider("Sides Clearance buffer (mm)", min_value=0, max_value=20, value=2, help="Clearance at the wall edges")
clear_height = st.sidebar.slider("Height Clearance buffer (mm)", min_value=0, max_value=20, value=4, help="Clearance at the top height edge")
sep_xy = st.sidebar.slider("Separator X/Y Thickness (mm)", min_value=0, max_value=10, value=2, help="Thickness of the horizontal dividers")
sep_z = st.sidebar.slider("Separator Z Thickness (mm)", min_value=0, max_value=10, value=4, help="Thickness of the vertical shelf dividers")

# Dropdown for Packing Orientation Rules
orientation_rule = st.sidebar.selectbox(
    "Select Orientation Rule:",
    ["Automatic (Highest Quantity)", "Force Flat Packing Only", "Force Standing on Edge", "Force Standing Vertical"],
    help="Control whether the system forces a specific loading style or automatically finds the absolute maximum layout."
)

sort_criteria = st.sidebar.selectbox("Rank Box Options By:", ["Volumetric Efficiency (%)", "Number of Parts per Box", "Box Price (€)"])

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

# Helper to identify the physical placement style
def determine_placement_style(p_l, p_w, p_h, oz):
    dims = sorted([p_l, p_w, p_h])
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
    
    # Weight Rule Check (Boxes >= 600x400 bypass 15kg limit)
    is_large_box = (ext_l >= 595.0) and (ext_w >= 395.0)
    if not is_large_box and total_package_weight > 15.0:
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
    
    # KPI Metric Cards
    st.subheader("💡 Best Matched Packing Insights")
    best_box = ranked_df.iloc[0]
    
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
    
    # Main Recommendations Table
    st.subheader("🏆 Top 10 Recommended Cardboard Boxes")
    display_df = ranked_df.drop(columns=["_nx", "_ny", "_nz", "_ox", "_oy", "_oz", "Int. Length [mm]", "Int. Width [mm]", "Int. Height [mm]", "Ext. Length [mm]", "Ext. Width [mm]"])
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
    
    # --- DYNAMIC PACKING GUIDE & MATPLOTLIB BLUEPRINT EXPANDER ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Step-by-Step Visual Blueprint Loading Map")
    
    # --- DYNAMIC SELECTBOX MEMORY (SESSION STATE) ---
    available_boxes = list(ranked_df["Box ID / Specification"].values)
    
    if "selected_box" not in st.session_state:
        st.session_state["selected_box"] = available_boxes[0]
        
    if st.session_state["selected_box"] in available_boxes:
        default_index = available_boxes.index(st.session_state["selected_box"])
    else:
        default_index = 0
        st.session_state["selected_box"] = available_boxes[0]

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

    # Render blueprints container
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
                
            st.markdown(f"<p style='color:#1864ab; margin-top:10px;'><b>⚖️ Operational Weight:</b> Safe at {viz_box['Total Weight (kg)']} kg.</p></div>", unsafe_allow_html=True)
            
            if upload_method == "Multi-Angle 2D Photos" and uploaded_top is not None:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 📸 Active Orientation Photo View:")
                
                dims = sorted([prod_l, prod_w, prod_h])
                if int(oz) == int(dims[0]) and uploaded_top is not None:
                    st.image(Image.open(uploaded_top), caption="Laying Flat (Top View)", use_column_width=True)
                elif int(oz) == int(dims[1]) and uploaded_front is not None:
                    st.image(Image.open(uploaded_front), caption="Standing on Edge (Front View)", use_column_width=True)
                elif int(oz) == int(dims[2]) and uploaded_side is not None:
                    st.image(Image.open(uploaded_side), caption="Standing Vertical (Side View)", use_column_width=True)
                else:
                    st.image(Image.open(uploaded_top), caption="Uploaded Top View Reference", use_column_width=True)
            
        with col_flat:
            fig, ax = plt.subplots(figsize=(6, 4))
            box_l = viz_box["Int. Length [mm]"]
            box_w = viz_box["Int. Width [mm]"]
            ext_l = viz_box["Ext. Length [mm]"]
            ext_w = viz_box["Ext. Width [mm]"]
            
            ax.add_patch(patches.Rectangle((0, 0), box_l, box_w, fill=False, edgecolor='#212529', linewidth=2.5, label='Box Wall'))
            
            ax.add_patch(patches.Rectangle((0, 0), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((0, box_w - clear_side), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((0, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((box_l - clear_side, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            
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
            fig3d = plt.figure(figsize=(4, 3.5))
            ax3d = fig3d.add_subplot(111, projection='3d')
            w_scale = 100
            l_scale = w_scale * (box_l / box_w)
            h_scale = 30
            
            # --- PERFECT AXIS VERTICAL ASPECT RETENTION ---
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
            
            plt.title("Vertical Stacking Blueprint", fontsize=11, fontweight='bold', color='#212529', pad=10)
            st.pyplot(fig3d)
            plt.close(fig3d)

    # --- DYNAMIC INTERACTIVE 3D DIGITAL TWIN VIEWPORT ---
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔄 Interactive 3D Digital Twin Viewport (Rotatable)")
    
    col_cad, col_packing_3d = st.columns(2)
    
    with col_cad:
        st.markdown("##### 🔍 Rotatable 3D CAD Part Model")
        if mesh_cad is not None:
            try:
                # Extract faces and vertices from loaded CAD file
                v_coords = mesh_cad.vertices
                f_indices = mesh_cad.faces
                
                x_v, y_v, z_v = v_coords[:, 0], v_coords[:, 1], v_coords[:, 2]
                i_f, j_f, k_f = f_indices[:, 0], f_indices[:, 1], f_indices[:, 2]
                
                # Draw the fully interactive 3D model using Plotly Mesh3d
                fig_cad = go.Figure(data=[
                    go.Mesh3d(
                        x=x_v, y=y_v, z=z_v,
                        i=i_f, j=j_f, k=k_f,
                        color='#d1d5db',
                        opacity=1.0,
                        flatshading=False,
                        lighting=dict(
                            ambient=0.5,
                            diffuse=0.9,
                            roughness=0.15,
                            specular=1.6,
                            fresnel=0.6
                        ),
                        lightposition=dict(
                            x=1000,
                            y=1000,
                            z=1500
                        ),
                        name="3D CAD Part"
                    )
                ])
                fig_cad.update_layout(
                    scene=dict(
                        aspectmode='data',
                        xaxis=dict(visible=False),
                        yaxis=dict(visible=False),
                        zaxis=dict(visible=False)
                    ),
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
            # Construct a fully interactive 3D wireframe box with real packed parts inside!
            fig_pack = go.Figure()
            
            # Helper to add a 3D wireframe outline for a compartment slot
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

            # Helper to add actual CAD model mesh into a specific compartment (aligned and scaled!)
            def add_plotly_mesh_part(fig_scene, x_pos, y_pos, z_pos, dx, dy, dz, raw_v, raw_f, text_str):
                # Calculate extent of raw mesh
                min_v = np.min(raw_v, axis=0)
                max_v = np.max(raw_v, axis=0)
                raw_extent = max_v - min_v
                
                # Align and scale mesh to fit exactly inside the target (dx, dy, dz)
                v_scaled = (raw_v - min_v) * np.array([dx / raw_extent[0], dy / raw_extent[1], dz / raw_extent[2]])
                
                # Move to compartment position (perfectly centered within its compartment slot)
                v_final = v_scaled + np.array([x_pos, y_pos, z_pos])
                
                # Render using Gouraud-shaded mesh
                fig_scene.add_trace(go.Mesh3d(
                    x=v_final[:, 0], y=v_final[:, 1], z=v_final[:, 2],
                    i=raw_f[:, 0], j=raw_f[:, 1], k=raw_f[:, 2],
                    color='#74c0fc', opacity=1.0,
                    flatshading=False,
                    lighting=dict(ambient=0.5, diffuse=0.9, specular=1.0, roughness=0.2),
                    name=text_str,
                    hoverinfo="text",
                    text=text_str,
                    showlegend=False
                ))

            # Centering mathematics matching the 2D Matplotlib Blueprint
            total_grid_w = nx * ox + (nx - 1) * sep_xy
            total_grid_h = ny * oy + (ny - 1) * sep_xy
            leftover_x = (box_l - 2 * clear_side) - total_grid_w
            leftover_y = (box_w - 2 * clear_side) - total_grid_h
            
            start_x_offset = clear_side + (leftover_x / 2)
            start_y_offset = clear_side + (leftover_y / 2)
            
            # Determine target cells to display the detailed CAD part
            total_parts = nx * ny * nz
            selected_cells = []
            if total_parts <= 4:
                # Draw in all slots if quantity is small
                for l in range(nz):
                    for r in range(ny):
                        for c in range(nx):
                            selected_cells.append((c, r, l))
            else:
                # Draw in exactly 3 distinct spots on the top layer so they are visible and non-overlapping
                selected_cells.append((0, 0, nz - 1))
                if nx > 2 and ny > 2:
                    selected_cells.append((nx // 2, ny // 2, nz - 1))
                selected_cells.append((nx - 1, ny - 1, nz - 1))

            # Draw compartments & selectively insert parts
            for layer in range(nz):
                z_pos = layer * (oz + sep_z)
                for r in range(ny):
                    y_pos = start_y_offset + r * (oy + sep_xy)
                    for c in range(nx):
                        x_pos = start_x_offset + c * (ox + sep_xy)
                        
                        # Always draw the empty compartment slot outline
                        add_wireframe_compartment(fig_pack, x_pos, y_pos, z_pos, ox, oy, oz)
                        
                        # Only insert the detailed CAD part mesh in selected cells
                        if (c, r, layer) in selected_cells and mesh_cad is not None:
                            add_plotly_mesh_part(
                                fig_pack, x_pos, y_pos, z_pos, ox, oy, oz, 
                                mesh_cad.vertices, mesh_cad.faces, 
                                f"Part @ Col {c+1}, Row {r+1}, Layer {layer+1}"
                            )
            
            # Draw Transparent Outer Box boundaries (FEFCO Box Walls)
            box_v = np.array([
                [0, 0, 0], [box_l, 0, 0], [box_l, box_w, 0], [0, box_w, 0],
                [0, 0, viz_box["Int. Height [mm]"]], [box_l, 0, viz_box["Int. Height [mm]"]],
                [box_l, box_w, viz_box["Int. Height [mm]"]], [0, box_w, viz_box["Int. Height [mm]"]]
            ])
            
            # Box Edges structure
            edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
                (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
                (0, 4), (1, 5), (2, 6), (3, 7)   # Verticals
            ]
            
            # Add wireframe box outline
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
                scene=dict(
                    xaxis_title="Length (mm)",
                    yaxis_title="Width (mm)",
                    zaxis_title="Height (mm)",
                    aspectmode='data'
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                height=380
            )
            st.plotly_chart(fig_pack, use_container_width=True)
        except Exception as e_pack_plotly:
            st.warning(f"Error rendering interactive 3D box packing model: {e_pack_plotly}")
else:
    st.warning("⚠️ No suitable boxes in your database can fit this product under the active weight or dimension parameters.")
