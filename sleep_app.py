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
        return pd.DataFrame(columns=["date", "hours", "type", "person"])

    rows = []
    for record in all_records:
        fields = record["fields"]
        rows.append([
            fields.get("date"),
            fields.get("hours"),
            fields.get("type"),
            fields.get("person")
        ])

    df = pd.DataFrame(rows, columns=["date", "hours", "type", "person"])
    df["date"] = pd.to_datetime(df["date"])
    return df

# Save entry to Airtable
def save_entry(date, hours, sleep_type, person):
    url = f"https://api.airtable.com/v0/{st.secrets['AIRTABLE_BASE_ID']}/{st.secrets['AIRTABLE_TABLE_ID']}"
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "fields": {
            "date": date.strftime("%Y-%m-%d"),
            "hours": hours,
            "type": sleep_type,
            "person": person
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in [200, 201]:
        st.error(f"Failed to save entry: {response.text}")

# Format ordinal suffix for dates
def add_suffix(d):
    if 11 <= d <= 13:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

# Plot rolling 5-day average sleep
def plot_average_sleep(data):
    today = pd.Timestamp.today().normalize()
    five_days_ago = today - pd.Timedelta(days=5)

    recent_data = data[(data["date"] >= five_days_ago) & (data["date"] <= today)]

    if recent_data.empty:
        st.write("No recent data to calculate averages.")
        return

    daily_totals = recent_data.groupby(["person", "date"])["hours"].sum().reset_index()
    averages = daily_totals.groupby("person")["hours"].mean().sort_values()

    fig, ax = plt.subplots()
    colours = ['#1f77b4', '#ff7f0e']  # Original matplotlib colours
    averages.plot(kind="barh", color=colours[:len(averages)], ax=ax)
    ax.set_xlabel("Average Hours Slept")
    ax.set_title("5-Day Rolling Average Sleep (up to today)")
    st.pyplot(fig)

# Plot sleep data by day
def plot_sleep(data, person_filter, days):
    if person_filter != "Both":
        data = data[data["person"] == person_filter]

    recent_data = data[data["date"] >= pd.Timestamp.today() - pd.Timedelta(days=days)]

    if recent_data.empty:
        st.write("No data to display.")
        return

    # Add formatted date label
    recent_data["formatted_date"] = recent_data["date"].apply(
        lambda d: f"{d.strftime('%A')} {d.day}{add_suffix(d.day)} {d.strftime('%B %Y')}"
    )

    # Preserve sort by actual date
    recent_data["sort_key"] = recent_data["date"]
    grouped = recent_data.groupby(["sort_key", "person"]).agg({
        "hours": "sum",
        "formatted_date": "first"
    }).reset_index()

    pivot = grouped.pivot(index="formatted_date", columns="person", values="hours").fillna(0)

    # Sort so latest dates appear on the left
    date_order = grouped.drop_duplicates("formatted_date").sort_values("sort_key", ascending=False)["formatted_date"]
    pivot = pivot.loc[date_order]

    fig, ax = plt.subplots()
    pivot.plot(kind="bar", stacked=False, ax=ax)
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

# Load data
data = load_data()

# Average sleep section
st.subheader("Average Sleep Times")
if data.empty:
    st.write("No data to calculate averages.")
else:
    plot_average_sleep(data)

# Sleep visualisation section
st.subheader("Sleep Visualisation")
person_filter = st.selectbox("View sleep for", ["Both", "Lloyd", "Georgia"])
days = st.slider("Show data for how many days?", 3, 60, 7)
plot_sleep(data, person_filter, days)
