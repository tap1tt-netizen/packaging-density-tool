import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import plotly.graph_objects as go
import itertools

def draw_2d_blueprint(box_l, box_w, ext_l, ext_w, nx, ny, ox, oy, clear_side, sep_xy, active_quantity, active_layers):
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
    
    layer1_filled = min(active_quantity, nx * ny)
    slot_counter = 0
    font_sz = 5 if nx * ny > 100 else (6 if nx * ny > 36 else 8)
        
    for r in range(ny):
        y_pos = start_y_offset + r * (oy + sep_xy)
        for c in range(nx):
            x_pos = start_x_offset + c * (ox + sep_xy)
            slot_counter += 1
            if slot_counter <= layer1_filled:
                ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#a5d8ff', edgecolor='#1971c2', linewidth=1.2))
                ax.text(x_pos + ox/2, y_pos + oy/2, f"{c+1}, {r+1}", ha='center', va='center', fontsize=font_sz, color='#0f4c81', fontweight='bold')
            else:
                ax.add_patch(patches.Rectangle((x_pos, y_pos), ox, oy, fill=True, facecolor='#e2e8f0', edgecolor='#94a3b8', linewidth=1.0, linestyle='--', alpha=0.35))
                ax.text(x_pos + ox/2, y_pos + oy/2, "Empty", ha='center', va='center', fontsize=font_sz - 1, color='#64748b', fontstyle='italic')
    
    ax.annotate('', xy=(0, -35), xytext=(box_l, -35), arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
    ax.text(box_l/2, -60, f"{int(ext_l)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center')
    
    ax.annotate('', xy=(box_l + 35, 0), xytext=(box_l + 35, box_w), arrowprops=dict(arrowstyle='<->', color='#dc3545', linewidth=1.5))
    ax.text(box_l + 60, box_w/2, f"{int(ext_w)} mm", color='#dc3545', fontsize=10, fontweight='bold', ha='center', va='center', rotation=-90)
    
    ax.text(box_l/2, box_w + 15, f"Floor Grid: {nx}x{ny} | Active Layers: {active_layers}", color='#dc3545', fontsize=12, fontweight='bold', ha='center')
    
    ax.set_xlim(-60, box_l + 100)
    ax.set_ylim(-80, box_w + 40)
    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig)
    plt.close(fig)
