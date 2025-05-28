import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests

# Track timestamps in session state
if "timestamps" not in st.session_state:
    st.session_state.timestamps = []

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
        return pd.DataFrame(columns=["date", "ml", "feed_type"])

    rows = []
    for record in all_records:
        fields = record["fields"]
        rows.append([
            fields.get("date"),
            fields.get("ml"),
            fields.get("feed_type")
        ])

    df = pd.DataFrame(rows, columns=["date", "ml", "feed_type"])
    df["date"] = pd.to_datetime(df["date"])
    return df

# Save entry to Airtable
def save_entry(date, ml, feed_type):
    url = f"https://api.airtable.com/v0/{st.secrets['AIRTABLE_BASE_ID']}/{st.secrets['AIRTABLE_TABLE_ID']}"
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "fields": {
            "date": date.strftime("%Y-%m-%d"),
            "ml": ml,
            "feed_type": feed_type
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in [200, 201]:
        st.error(f"Failed to save entry: {response.text}")

# Draw feeding chart
def plot_feedings(data, days):
    recent_data = data[data["date"] >= pd.Timestamp.today() - pd.Timedelta(days=days)]
    if recent_data.empty:
        st.write("No data to display.")
        return

    daily_totals = recent_data.groupby([recent_data["date"].dt.date, "feed_type"])["ml"].sum().unstack().fillna(0)
    daily_totals = daily_totals.sort_index(ascending=False)

    fig, ax = plt.subplots()
    daily_totals.plot(kind="bar", stacked=True, ax=ax, color=["#1f77b4", "#ff7f0e"])
    ax.set_ylabel("ml")
    ax.set_title(f"Milk Intake Over Last {days} Days")
    st.pyplot(fig)

# --- Streamlit App Interface ---
st.title("Baby Feeding Tracker")

# Show time since last feed
if st.session_state.timestamps:
    last_time = st.session_state.timestamps[-1]
    time_since = datetime.now() - last_time
    hours, remainder = divmod(time_since.total_seconds(), 3600)
    minutes = remainder // 60
    st.info(f"🕒 Time since last feed: {int(hours)}h {int(minutes)}m")

# Log new feed
st.subheader("Log a Feed")

with st.form("feeding_form"):
    date = st.date_input("Date", value=datetime.today())
    ml = st.number_input("Amount of milk (ml)", min_value=0, max_value=1000, step=10)
    feed_type = st.selectbox("Milk Type", ["Bottle", "Formula"])
    submitted = st.form_submit_button("Save")

    if submitted:
        save_entry(date, ml, feed_type)
        st.session_state.timestamps.append(datetime.now())
        st.success("Entry saved!")

# Show chart
data = load_data()
st.subheader("Feeding Overview")
days = st.slider("Show data for how many days?", 1, 30, 7)
plot_feedings(data, days)

