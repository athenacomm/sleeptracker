# Import libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# Connect to Google Sheet by ID
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key("1R9u3t0yb5SC5LRGJRJpTsLsWopAmgWjpYlZbrnqppyI").sheet1
    return sheet

# Load sleep data from Google Sheet
def load_data():
    sheet = get_sheet()
    df = get_as_dataframe(sheet).dropna(how='all')
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

# Save a new entry to Google Sheet
def save_entry(date, hours, sleep_type, person):
    sheet = get_sheet()
    df = load_data()
    new_row = pd.DataFrame([[date, hours, sleep_type, person]], columns=["date", "hours", "type", "person"])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    sheet.clear()
    set_with_dataframe(sheet, updated_df)

# Format ordinal suffix for dates (1st, 2nd, 3rd, etc.)
def add_suffix(d):
    if 11 <= d <= 13:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

# Draw the chart
def plot_sleep(data, person_filter, days):
    if person_filter != "Both":
        data = data[data["person"] == person_filter]

    recent_data = data[data["date"] >= pd.Timestamp.today() - pd.Timedelta(days=days)]

    if recent_data.empty:
        st.write("No data to display.")
        return

    # Add formatted date column
    recent_data["formatted_date"] = recent_data["date"].apply(
        lambda d: f"{d.strftime('%A')} {d.day}{add_suffix(d.day)} {d.strftime('%B %Y')}"
    )

    # Group by formatted date and person
    daily_totals = recent_data.groupby(["formatted_date", "person"])["hours"].sum().unstack().fillna(0)

    fig, ax = plt.subplots()
    daily_totals.plot(kind="bar", stacked=False, ax=ax)
    ax.set_ylabel("Hours slept")
    ax.set_title(f"Sleep in last {days} days")
    st.pyplot(fig)

# --- Streamlit App Interface ---

st.title("Sleep Tracker")

st.subheader("Log sleep")

with st.form("sleep_form"):
    date = st.date_input("Date", value=datetime.today())
    hours = st.number_input("Hours slept", min_value=0.0, max_value=24.0, step=0.25)
    sleep_type = st.selectbox("Type", ["Sleep", "Nap"])
    person = st.selectbox("Who slept?", ["Lloyd", "Georgia"])
    submitted = st.form_submit_button("Save")

    if submitted:
        save_entry(date, hours, sleep_type, person)
        st.success("Saved!")

st.subheader("Sleep Visualisation")

data = load_data()
person_filter = st.selectbox("View sleep for", ["Both", "Lloyd", "Georgia"])
days = st.slider("Show data for how many days?", 3, 60, 7)

plot_sleep(data, person_filter, days)
