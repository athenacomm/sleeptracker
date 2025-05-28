# Import libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests

# Load data from Airtable
def load_data():
    url = f"https://api.airtable.com/v0/{st.secrets['AIRTABLE_BASE_ID']}/{st.secrets['AIRTABLE_TABLE_ID']}"
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_TOKEN']}"
    }
    all_records = []
    offset = None

    while True:
        params = {"offset": offset} if offset else {}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break

    if not all_records:
        return pd.DataFrame(columns=["date", "ml", "type"])

    rows = []
    for record in all_records:
        fields
