# ==============================================================================
# 4. RECOMMENDATION SYSTEM MATHEMATICS
# ==============================================================================
# calculations.py
import numpy as np
import pandas as pd
import streamlit as st

def calculate_packing(box_int_l, box_int_w, box_int_h, p_l, p_w, p_h, rule, clear_side=2, clear_height=4, sep_xy=2, sep_z=4, enforce_lot=False, lot_multiplier=24):
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

# Helper to retrieve either manual fine-tuned or max default quantity & package weight
# Helper to retrieve either manual fine-tuned or max default quantity & package weight
def get_live_box_metrics(row, weight_per_part, prod_l, prod_w, prod_h, clear_side, clear_height):
    box_spec = row["Box ID / Specification"]
    qty_key = f"manual_qty_{box_spec}"
    default_max_qty = int(row["No of Parts per Box"])
    # If the user has manually tuned the quantity, fetch it from session_state
    active_qty = int(st.session_state.get(qty_key, default_max_qty))
    
    # Recalculate dynamic package weight
    ext_l = row.get("Ext. Length [mm]") if "Ext. Length [mm]" in row else row.get("Ext. Length [mm]")
    
    # Robust Width Lookup: Check both spacing variations
    ext_w = row.get("Ext.Width [mm]") if "Ext.Width [mm]" in row else row.get("Ext. Width [mm]")
    
    ext_h = row.get("Ext. Height [mm]") if "Ext. Height [mm]" in row else row.get("Ext. Height [mm]")
    
    box_weight = estimate_box_weight(ext_l, ext_w, ext_h, row["Flute Type"] if "Flute Type" in row else row.get("Quality"))
    live_total_weight = round((active_qty * weight_per_part) + box_weight, 2)
    
    # Recalculate volumetric efficiency based on active loaded parts
    single_part_vol = prod_l * prod_w * prod_h
    
    # Robust Internal Dimension Lookups
    int_l = row.get("Int.Length [mm]") if "Int.Length [mm]" in row else row.get("Int. Length [mm]")
    int_w = row.get("Width [mm]") if "Width [mm]" in row else row.get("Int. Width [mm]")
    int_h = row.get("Height [mm]") if "Height [mm]" in row else row.get("Int. Height [mm]")
    
    box_internal_vol = int_l * int_w * int_h
    live_vol_efficiency = round(((active_qty * single_part_vol) / box_internal_vol) * 100, 2)
    
    return active_qty, live_total_weight, live_vol_efficiency

# 🌟 ADD THIS FUNCTION AT THE VERY BOTTOM OF calculations.py 🌟
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
