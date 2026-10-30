import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
prod_l = st.sidebar.number_input("Part Length (mm)", min_value=1, value=170, step=1)
prod_w = st.sidebar.number_input("Part Width (mm)", min_value=1, value=110, step=1)
prod_h = st.sidebar.number_input("Part Height (mm)", min_value=1, value=40, step=1)

# Product Weight
st.sidebar.markdown("#### Part Weight (kg)")
prod_wt = st.sidebar.number_input("Weight per Part (kg)", min_value=0.01, value=0.25, step=0.05)

st.sidebar.markdown("---")
st.sidebar.header("📏 Divider & Clearance Spacing")

# Margins and Clearances (Directly from manager discussion)
clear_side = st.sidebar.slider("Sides Clearance buffer (mm)", min_value=0, max_value=20, value=2, help="Clearance at the wall edges (lengthwise and widthwise)")
clear_height = st.sidebar.slider("Height Clearance buffer (mm)", min_value=0, max_value=20, value=4, help="Clearance at the top height edge")

sep_xy = st.sidebar.slider("Separator X/Y Thickness (mm)", min_value=0, max_value=10, value=2, help="Thickness of the horizontal dividers")
sep_z = st.sidebar.slider("Separator Z Thickness (mm)", min_value=0, max_value=10, value=4, help="Thickness of the vertical shelf dividers")

sort_criteria = st.sidebar.selectbox("Rank Box Options By:", ["Volumetric Efficiency (%)", "Number of Parts per Box", "Box Price (€)"])


# --- RECONMENDATION SYSTEM MATHEMATICS ---
def calculate_3d_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h):
    orientations = [
        (p_l, p_w, p_h), (p_l, p_h, p_w),
        (p_w, p_l, p_h), (p_w, p_h, p_l),
        (p_h, p_l, p_w), (p_h, p_w, p_l)
    ]
    
    best_qty = 0
    best_config = None
    best_grid_layout = (0, 0, 0)
    
    for px, py, pz in orientations:
        # Number of slots along Length (X)
        nx = max(0, int((box_int_l - (2 * clear_side) + sep_xy) // (px + sep_xy)))
        # Number of slots along Width (Y)
        ny = max(0, int((box_int_w - (2 * clear_side) + sep_xy) // (py + sep_xy)))
        # Number of slots along Height (Z)
        nz = max(0, int((box_int_h - clear_height + sep_z) // (pz + sep_z)))
        
        total_parts = nx * ny * nz
        if total_parts > best_qty:
            best_qty = total_parts
            best_config = (px, py, pz)
            best_grid_layout = (nx, ny, nz)
            
    return best_qty, best_config, best_grid_layout


# Dynamic empty weight estimation of the FEFCO0201 flat sheets
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
    
    if pd.isna(box_int_l) or pd.isna(box_int_w) or pd.isna(box_int_h):
        continue
        
    # Get optimal 3D layout count
    parts_count, pack_orient, grid_layout = calculate_3d_packing(
        box_int_l, box_int_w, box_int_h, 
        prod_l, prod_w, prod_h
    )
    
    if parts_count == 0:
        continue
        
    box_weight = estimate_box_weight(ext_l, ext_w, row['Ext. Height [mm]'], row['Quality'])
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
    
    # Extract clean name so it doesn't wrap/truncate
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
    display_df = ranked_df.drop(columns=["_nx", "_ny", "_nz", "_ox", "_oy", "_oz", "Int. Length [mm]", "Int. Width [mm]"])
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
        col_text, col_plot = st.columns([2, 3])
        
        # Pull raw packing metrics
        nx = int(best_box["_nx"])
        ny = int(best_box["_ny"])
        nz = int(best_box["_nz"])
        ox = int(best_box["_ox"])
        oy = int(best_box["_oy"])
        oz = int(best_box["_oz"])
        
        with col_text:
            st.markdown("<div class='guide-box'><h4><b>🛠️ 3-Step Simple Packing Guide</b></h4><hr>", unsafe_allow_html=True)
            
            # Step 1: Orientation
            st.markdown(f"""
            <b>Step 1: Orient the Part</b><br>
            Place each individual part into the box so that:
            <ul>
                <li>📐 <b>Lengthwise side:</b> {ox} mm</li>
                <li>📐 <b>Widthwise side:</b> {oy} mm</li>
                <li>📐 <b>Height side (pointing UP):</b> {oz} mm</li>
            </ul>
            """, unsafe_allow_html=True)
            
            # Step 2: Grid Layout
            st.markdown(f"""
            <b>Step 2: Arrange the Floor Grid</b><br>
            Lay down a grid of <b>{nx} columns</b> and <b>{ny} rows</b> of parts on the floor of the box. 
            <ul>
                <li>This packs exactly <b>{nx * ny} parts</b> on the layer.</li>
                <li>Place the 2mm partition grids between each part.</li>
            </ul>
            """, unsafe_allow_html=True)
            
            # Step 3: Dynamic stacking guide (Checks if layers > 1)
            if nz > 1:
                st.markdown(f"""
                <b>Step 3: Stacking Vertical Layers</b><br>
                <ul>
                    <li>Lay down a flat 4mm cardboard divider sheet on top of your completed layer.</li>
                    <li>Repeat the same grid layout on top of the divider sheet.</li>
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
            
        with col_plot:
            # Generate Matplotlib Blueprint of the floor layout
            fig, ax = plt.subplots(figsize=(6, 4))
            box_l = best_box["Int. Length [mm]"]
            box_w = best_box["Int. Width [mm]"]
            
            # Draw box border
            ax.add_patch(patches.Rectangle((0, 0), box_l, box_w, fill=False, edgecolor='#212529', linewidth=2.5, label='Box Wall'))
            
            # Draw clearance hatch regions
            ax.add_patch(patches.Rectangle((0, 0), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((0, box_w - clear_side), box_l, clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((0, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            ax.add_patch(patches.Rectangle((box_l - clear_side, clear_side), clear_side, box_w - 2*clear_side, fill=True, color='#e9ecef', hatch='//', alpha=0.6))
            
            # Draw parts
            for r in range(ny):
                y_pos = clear_side + r * (oy + sep_xy)
                for c in range(nx):
                    x_pos = clear_side + c * (ox + sep_xy)
                    ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#a5d8ff', edgecolor='#1971c2', linewidth=1.2))
                    ax.text(x_pos + ox/2, y_pos + oy/2, f"{c+1}, {r+1}", ha='center', va='center', fontsize=8, color='#0f4c81', fontweight='bold')
            
            ax.set_xlim(-15, box_l + 15)
            ax.set_ylim(-15, box_w + 15)
            ax.set_aspect('equal')
            ax.axis('off')
            st.pyplot(fig)
            plt.close(fig)
else:
    st.warning("⚠️ No suitable boxes in your database can fit this product under the active weight or dimension parameters.")
