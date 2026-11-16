import streamlit as st
import numpy as np
import pandas as pd

@st.cache_data
def calculate_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h, rule, clear_side, clear_height, sep_xy, sep_z, enforce_lot=False, lot_multiplier=24):
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

def estimate_box_weight(ext_l, ext_w, ext_h, quality):
    if pd.isna(ext_l) or pd.isna(ext_w) or pd.isna(ext_h):
        return 0.15
    sheet_l_m = (2 * (ext_l + ext_w) + 40) / 1000.0
    sheet_w_m = (ext_h + ext_w) / 1000.0
    flat_area = sheet_l_m * sheet_w_m
    grammage_map = {'1.20B': 0.40, '1.20C': 0.45, '2.30EB': 0.70, '2.30BC': 0.85}
    g = grammage_map.get(str(quality).strip(), 0.50)
    return flat_area * g

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
