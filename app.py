import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image

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

# Visual Input Method Selector
upload_method = st.sidebar.radio("Select Visual Reference Method:", ["Multi-Angle 2D Photos", "3D CAD Model (.STL/.STEP)"])

uploaded_top = None
uploaded_front = None
uploaded_side = None
uploaded_stl = None

# Auto-extraction variables
auto_l, auto_w, auto_h = 170.0, 110.0, 40.0

if upload_method == "Multi-Angle 2D Photos":
    uploaded_top = st.sidebar.file_uploader("Upload TOP View (Length x Width)", type=["png", "jpg", "jpeg"])
    uploaded_front = st.sidebar.file_uploader("Upload FRONT View (Length x Height)", type=["png", "jpg", "jpeg"])
    uploaded_side = st.sidebar.file_uploader("Upload SIDE View (Width x Height)", type=["png", "jpg", "jpeg"])
else:
    uploaded_stl = st.sidebar.file_uploader("Upload 3D CAD File (.STL, .STEP, .STP)", type=["stl", "step", "stp"])
    if uploaded_stl is not None:
        filename = uploaded_stl.name.lower()
        try:
            import trimesh
            uploaded_stl.seek(0)
            if filename.endswith('.step') or filename.endswith('.stp'):
                mesh_cad = trimesh.load(uploaded_stl, file_type='step')
            else:
                mesh_cad = trimesh.load(uploaded_stl, file_type='stl')
            
            # Automatically extract bounding box boundaries
            bounds = mesh_cad.bounding_box.extents
            # Sort to align with Length (longest), Width (medium), Height (shortest)
            dims = sorted(bounds)
            auto_h = round(dims[0], 1)
            auto_w = round(dims[1], 1)
            auto_l = round(dims[2], 1)
            st.sidebar.success(f"📐 Auto-Extracted Dimensions: {auto_l} x {auto_w} x {auto_h} mm")
        except Exception as e_cad:
            st.sidebar.warning(f"Could not auto-extract CAD dimensions: {e_cad}")

# Product Physical Dimensions Inputs (Pre-filled with CAD data if available)
st.sidebar.markdown("#### Part Dimensions (mm)")
prod_l = st.sidebar.number_input("Part Length (mm)", min_value=1.0, value=float(auto_l), step=1.0)
prod_w = st.sidebar.number_input("Part Width (mm)", min_value=1.0, value=float(auto_w), step=1.0)
prod_h = st.sidebar.number_input("Part Height (mm)", min_value=1.0, value=float(auto_h), step=1.0)

# Product Weight
st.sidebar.markdown("#### Part Weight (kg)")
prod_wt = st.sidebar.number_input("Weight per Part (kg)", min_value=0.01, value=0.25, step=0.05)

st.sidebar.markdown("---")
st.sidebar.header("📏 Divider & Clearance Spacing")

# Margins and Clearances
clear_side = st.sidebar.slider("Sides Clearance buffer (mm)", min_value=0, max_value=20, value=2)
clear_height = st.sidebar.slider("Height Clearance buffer (mm)", min_value=0, max_value=20, value=4)

sep_xy = st.sidebar.slider("Separator X/Y Thickness (mm)", min_value=0, max_value=10, value=2)
sep_z = st.sidebar.slider("Separator Z Thickness (mm)", min_value=0, max_value=10, value=4)

strict_flat = st.sidebar.checkbox("Strict Flat Packing (Highly Recommended)", value=True)

sort_criteria = st.sidebar.selectbox("Rank Box Options By:", ["Volumetric Efficiency (%)", "Number of Parts per Box", "Box Price (€)"])


# --- RECONMENDATION SYSTEM MATHEMATICS ---
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
        prod_l, prod_w, prod_h
    )
    
    if parts_count == 0:
        continue
        
    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row['Quality'])
    total_payload_wt = parts_count * prod_wt
    total_package_weight = total_payload_wt + box_weight
    
    is_large_box = (ext_l >= 600.0) and (ext_w >= 400.0)
    if not is_large_box and total_package_weight > 15.0:
        continue
        
    if total_payload_wt > row['Max. Load [kg]']:
        continue
        
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
    
    # KPI Metric Cards
    st.subheader("💡 Best Matched Packing Insights")
    best_box = ranked_df.iloc[0]
    clean_box_size = best_box['Box ID / Specification'].split(':')[-1].strip()
    
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
    display_df = ranked_df.drop(columns=["_nx", "_ny", "_nz", "_ox", "_oy", "_oz", "Int. Length [mm]", "Int. Width [mm]", "Int. Height [mm]", "Ext. Length [mm]", "Ext. Width [mm]", "Ext. Height [mm]"])
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
    with st.expander("📋 Click to view Step-by-Step Visual Blueprint Loading Map", expanded=True):
        col_text, col_flat, col_stack = st.columns([2.5, 3, 2.5])
        
        # Pull raw packing metrics
        nx = int(best_box["_nx"])
        ny = int(best_box["_ny"])
        nz = int(best_box["_nz"])
        ox = int(best_box["_ox"])
        oy = int(best_box["_oy"])
        oz = int(best_box["_oz"])
        
        # Calculate dynamic placement style
        placement_style = determine_placement_style(prod_l, prod_w, prod_h, oz)
        
        with col_text:
            st.markdown("<div class='guide-box'><h4><b>🛠️ 3-Step Packing Instruction</b></h4><hr>", unsafe_allow_html=True)
            
            # Step 1: Orientation
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
            
            # Step 2: Grid Layout
            st.markdown(f"""
            <b>Step 2: Arrange the Floor Grid</b><br>
            Lay down a grid of <b>{nx} columns</b> and <b>{ny} rows</b> of parts on the floor of the box. 
            <ul>
                <li>This packs exactly <b>{nx * ny} parts</b> on this layer.</li>
                <li>Place the 2mm partition grids between each part.</li>
            </ul>
            """, unsafe_allow_html=True)
            
            # Step 3: Dynamic stacking guide
            if nz > 1:
                st.markdown(f"""
                <b>Step 3: Stacking Vertical Layers</b><br>
                <ul>
                    <li>Lay down a flat 4mm cardboard divider sheet on top of your completed layer.</li>
                    <li>Repeat the same grid layout of {nx*ny} parts on top.</li>
                    <li>Do this until you have built a total of <b>{nz} vertical layers</b> (reaching <b>{int(best_box['Number of Parts per Box'])} pieces</b> in total).</li>
                </ul>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <b>Step 3: Finish Packing</b><br>
                Since all <b>{int(best_box['Number of Parts per Box'])} parts</b> fit in <b>1 single floor layer</b>, you do not need any flat shelf dividers or vertical stacking. 
                <br>Just seal the box and ship!
                """, unsafe_allow_html=True)
                
            st.markdown(f"<p style='color:#1864ab; margin-top:10px;'><b>⚖️ Operational Weight:</b> Safe at {best_box['Total Weight (kg)']} kg.</p></div>", unsafe_allow_html=True)
            
            # Display uploaded part photo dynamically inside the packing guide panel
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
            # Generate Matplotlib Blueprint of the floor layout
            fig, ax = plt.subplots(figsize=(6, 4))
            box_l = best_box["Int. Length [mm]"]
            box_w = best_box["Int. Width [mm]"]
            ext_l = best_box["Ext. Length [mm]"]
            ext_w = best_box["Ext. Width [mm]"]
            
            # Draw box border
            ax.add_patch(patches.Rectangle((0, 0), box_l, box_w, fill=False, edgecolor='#212529', linewidth=2.5, label='Box Wall'))
            
            # Draw clearance hatch regions
            ax.add_patch(patches.Rectangle((0, 0), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((0, box_w - clear_side), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((0, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((box_l - clear_side, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            
            # --- DYNAMIC GRID CENTERING LOGIC ---
            total_grid_w = nx * ox + (nx - 1) * sep_xy
            total_grid_h = ny * oy + (ny - 1) * sep_xy
            leftover_x = (box_l - 2 * clear_side) - total_grid_w
            leftover_y = (box_w - 2 * clear_side) - total_grid_h
            
            start_x_offset = clear_side + (leftover_x / 2)
            start_y_offset = clear_side + (leftover_y / 2)
            
            # Draw perfectly centered parts
            for r in range(ny):
                y_pos = start_y_offset + r * (oy + sep_xy)
                for c in range(nx):
                    x_pos = start_x_offset + c * (ox + sep_xy)
                    ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#a5d8ff', edgecolor='#1971c2', linewidth=1.2))
                    ax.text(x_pos + ox/2, y_pos + oy/2, f"{c+1}, {r+1}", ha='center', va='center', fontsize=8, color='#0f4c81', fontweight='bold')
            
            # Custom Red Dimension Indicator Arrows
            ax.annotate('', xy=(0, -25), xytext=(box_l, -25),
                        arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
            ax.text(box_l/2, -45, f"{int(ext_l)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center')
            
            ax.annotate('', xy=(box_l + 25, 0), xytext=(box_l + 25, box_w),
                        arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
            ax.text(box_l + 45, box_w/2, f"{int(ext_w)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center', va='center', rotation=-90)
            
            # Dynamic layer header directly on top of the layout diagram
            ax.text(box_l/2, box_w + 15, f"Layers: {nz} Vertical", color='#dc3545', fontsize=14, fontweight='bold', ha='center')
            
            ax.set_xlim(-40, box_l + 80)
            ax.set_ylim(-60, box_w + 35)
            ax.set_aspect('equal')
            ax.axis('off')
            st.pyplot(fig)
            plt.close(fig)
            
        with col_stack:
            # --- PURE PYTHON 3D DYNAMIC STACKING VISUALIZER (WebGL sandbox block proof!) ---
            fig3d = plt.figure(figsize=(4, 4))
            ax3d = fig3d.add_subplot(111, projection='3d')
            
            # Render realistic 3D wireframe boxes aligned in 3D representing your actual parts inside
            l_box = best_box["Int. Length [mm]"]
            w_box = best_box["Int. Width [mm]"]
            h_box = best_box["Int. Height [mm]"]
            
            # Scale coordinates down for Matplotlib aspect ratio rendering stability
            scale_factor = 100.0 / l_box
            l_scaled = l_box * scale_factor
            w_scaled = w_box * scale_factor
            h_scaled = h_box * scale_factor
            
            part_l_scaled = ox * scale_factor
            part_w_scaled = oy * scale_factor
            part_h_scaled = oz * scale_factor
            
            # Draw the outer box wireframe
            v_box = np.array([
                [0, 0, 0], [l_scaled, 0, 0], [l_scaled, w_scaled, 0], [0, w_scaled, 0],
                [0, 0, h_scaled], [l_scaled, 0, h_scaled], [l_scaled, w_scaled, h_scaled], [0, w_scaled, h_scaled]
            ])
            box_faces = [
                [v_box[0], v_box[1], v_box[5], v_box[4]], [v_box[1], v_box[2], v_box[6], v_box[5]],
                [v_box[2], v_box[3], v_box[7], v_box[6]], [v_box[3], v_box[0], v_box[4], v_box[7]]
            ]
            box_poly = Poly3DCollection(box_faces, facecolors='none', edgecolors='#212529', linewidths=1.5, alpha=0.5)
            ax3d.add_collection3d(box_poly)
            
            # Draw stacked part compartments dynamically layer-by-layer!
            for layer in range(nz):
                z_floor = layer * (part_h_scaled + 2)  # slight gap for dividers
                
                # Draw grid compartments
                for r in range(ny):
                    y_start = (start_y_offset + r * (oy + sep_xy)) * scale_factor
                    for c in range(nx):
                        x_start = (start_x_offset + c * (ox + sep_xy)) * scale_factor
                        
                        # Draw individual 3D solid parts inside the wireframe box!
                        vp = np.array([
                            [x_start, y_start, z_floor], 
                            [x_start + part_l_scaled, y_start, z_floor], 
                            [x_start + part_l_scaled, y_start + part_w_scaled, z_floor], 
                            [x_start, y_start + part_w_scaled, z_floor],
                            [x_start, y_start, z_floor + part_h_scaled], 
                            [x_start + part_l_scaled, y_start, z_floor + part_h_scaled], 
                            [x_start + part_l_scaled, y_start + part_w_scaled, z_floor + part_h_scaled], 
                            [x_start, y_start + part_w_scaled, z_floor + part_h_scaled]
                        ])
                        part_faces = [
                            [vp[0], vp[1], vp[5], vp[4]], [vp[1], vp[2], vp[6], vp[5]],
                            [vp[2], vp[3], vp[7], vp[6]], [vp[3], vp[0], vp[4], vp[7]],
                            [vp[4], vp[5], vp[6], vp[7]]
                        ]
                        part_poly = Poly3DCollection(part_faces, facecolors='#a5d8ff', edgecolors='#1971c2', linewidths=0.5, alpha=0.7)
                        ax3d.add_collection3d(part_poly)
                
                # Big Red Layer annotation on the front panel
                ax3d.text(-15, -15, z_floor + part_h_scaled/2, f"{layer + 1}", color='#dc3545', fontweight='bold', fontsize=20, ha='center', va='center')
                
            ax3d.set_xlim(-20, l_scaled + 20)
            ax3d.set_ylim(-20, w_scaled + 20)
            ax3d.set_zlim(-10, h_scaled + 10)
            ax3d.view_init(elev=22, azim=-65)
            ax3d.axis('off')
            
            plt.title("3D Part Stacking View", fontsize=11, fontweight='bold', color='#212529', pad=10)
            st.pyplot(fig3d)
            plt.close(fig3d)
else:
    st.warning("⚠️ No suitable boxes in your database can fit this product under the active weight or dimension parameters.")
