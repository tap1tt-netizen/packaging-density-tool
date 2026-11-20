# ==============================================================================
# 2. BULLETPROOF DATABASE READER
# ==============================================================================
# database.py
import streamlit as st
import pandas as pd
import os

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
    # Drop visual spacing rows/empty spacer rows
    df = df.dropna(subset=['BoxSize']).copy()
    
    # Filter out single-flute qualities from database dynamically
    df = df[~df['Quality'].astype(str).str.strip().isin(['1.20B', '1.20C'])].copy()
    
    numeric_cols = [
        'Ext. Length [mm]', 'Ext.Width [mm]', 'Ext. Height [mm]',
        'Int.Length [mm]', 'Width [mm]', 'Height [mm]', 'Max. Load [kg]'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Box Price (€)'] = pd.to_numeric(df['PL'], errors='coerce').fillna(0.0)
    return df, loaded_file

# 🌟 ADD THIS FUNCTION AT THE VERY BOTTOM OF database.py 🌟
def log_feedback(feedback_entry):
    feedback_file = "feedback_log.csv"
    new_row = pd.DataFrame([feedback_entry])
    try:
        if os.path.exists(feedback_file):
            new_row.to_csv(feedback_file, mode='a', header=False, index=False)
        else:
            new_row.to_csv(feedback_file, mode='w', header=True, index=False)
        return True
    except Exception as e:
        print(f"Failed logging locally: {e}")
        return False
