# Import libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# File where data will be stored
DATA_FILE = "sleep_data.csv"

# Load sleep data from the file
def load_data():
    try:
        return pd.read_csv(DATA_FILE, parse_dates=['date'])
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "hours", "type", "person"])

# Save a new entry to the file
def save_entry(date, hours, sleep_type, person):
    new_row = pd.DataFrame([[date, hours, sleep_type, person]],
                           columns=["date", "hours", "type", "person"])
    try:
        pd.read_csv(DATA_FILE)
        new_row.to_csv(DATA_FILE, mode='a', index=False, header=False)
    except FileNotFoundError:
        new_row.to_csv(DATA_FILE, index=False)

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
