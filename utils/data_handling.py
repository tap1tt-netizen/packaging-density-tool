import streamlit as st
import pandas as pd
import os
import urllib.request
import json

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

def log_feedback_locally(feedback_entry, feedback_file="feedback_log.csv"):
    new_row = pd.DataFrame([feedback_entry])
    if os.path.exists(feedback_file):
        new_row.to_csv(feedback_file, mode='a', header=False, index=False)
    else:
        new_row.to_csv(feedback_file, mode='w', header=True, index=False)

def post_teams_webhook(feedback_entry):
    try:
        if "teams" in st.secrets and st.secrets["teams"]["webhook_url"] != "":
            webhook_url = st.secrets["teams"]["webhook_url"]
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.2",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "text": "📦 New App Feedback Received!",
                                    "weight": "Bolder",
                                    "size": "Medium",
                                    "color": "Accent"
                                },
                                {
                                    "type": "FactSet",
                                    "facts": [
                                        {"title": "📅 Timestamp:", "value": feedback_entry["Timestamp"]},
                                        {"title": "👤 Submitted By:", "value": feedback_entry["User"]},
                                        {"title": "⭐ Rating:", "value": feedback_entry["Rating"]}
                                    ]
                                },
                                {
                                    "type": "TextBlock",
                                    "text": f"💬 Comments:\n\"{feedback_entry['Comments']}\"",
                                    "wrap": True,
                                    "italic": True
                                }
                            ]
                        }
                    }
                ]
            }
            req = urllib.request.Request(url=webhook_url, method="POST")
            req.add_header("Content-Type", "application/json")
            jsondata = json.dumps(payload).encode("utf-8")
            
            with urllib.request.urlopen(req, data=jsondata) as response:
                return response.status in [200, 201, 202]
    except Exception as e:
        print(f"Teams webhook failed: {e}")
    return False
