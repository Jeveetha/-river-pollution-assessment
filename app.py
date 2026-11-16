
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="River Water Quality Assessment",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 AI-Driven River Pollution Assessment")
st.caption("Module 1: Historical River Water Quality Assessment")

# Load datasets
@st.cache_data
def load_data():
    records = pd.read_csv("assessment_records.csv")
    stations = pd.read_csv("station_assessment.csv")

    records["Sample_Date"] = pd.to_datetime(
        records["Sample_Date"], errors="coerce"
    )

    return records, stations

records, stations = load_data()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

station_options = ["All Stations"] + sorted(
    records["Station"].dropna().unique().tolist()
)

selected_station = st.sidebar.selectbox(
    "Select Monitoring Station",
    station_options
)

min_date = records["Sample_Date"].min().date()
max_date = records["Sample_Date"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range

    filtered = records[
        (records["Sample_Date"].dt.date >= start_date) &
        (records["Sample_Date"].dt.date <= end_date)
    ].copy()
else:
    filtered = records.copy()

if selected_station != "All Stations":
    filtered = filtered[
        filtered["Station"] == selected_station
    ]

# Overview
st.header("1. Dashboard Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Records", len(filtered))
col2.metric("Stations Covered", filtered["Station"].nunique())
col3.metric(
    "Date Range",
    f"{filtered['Sample_Date'].min().year if len(filtered) else '-'} – "
    f"{filtered['Sample_Date'].max().year if len(filtered) else '-'}"
)

if filtered.empty:
    st.warning("No records found for the selected filters.")
    st.stop()

# Parameter summaries
st.header("2. Parameter-wise Assessment")

summary_data = {
    "Parameter": ["pH", "Dissolved Oxygen", "Fecal Coliform", "BOD"],
    "Available Records": [
        filtered["pH_Status"].ne("Not Available").sum(),
        filtered["DO_Status"].ne("Not Available").sum(),
        filtered["FC_Status"].ne("Not Available").sum(),
        filtered["BOD_Status"].ne("Not Available").sum()
    ],
    "Flagged Records": [
        filtered["pH_Status"].eq("Outside Reference").sum(),
        filtered["DO_Status"].eq("Below 5 mg/L").sum(),
        filtered["FC_Status"].isin(
            ["Above 500 to 2500", "Above 2500"]
        ).sum(),
        filtered["BOD_Status"].eq(
            "Above 3 mg/L - Provisional"
        ).sum()
    ]
}

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True)

st.caption(
    "Reference screening: pH 6.5–8.5; DO ≥ 5 mg/L; "
    "FC ≤ 500 MPN/100mL. BOD ≤ 3 mg/L is provisional. "
    "These are parameter-wise screening references, not an official WQI."
)

# Historical graphs
st.header("3. Historical Water Quality Trends")

parameters = [
    ("Potential of Hydrogen (pH)", "pH", 6.5, 8.5),
    ("Dissolved oxygen (mg/L)", "Dissolved Oxygen", 5, None),
    ("Fecal Coliform (MPN/100mL)", "Fecal Coliform", 500, None),
    ("Biochemical Oxygen Demand (mg/L)", "BOD (Provisional)", 3, None)
]

for i in range(0, 4, 2):
    cols = st.columns(2)

    for col, parameter in zip(cols, parameters[i:i+2]):
        column, title, lower, upper = parameter

        with col:
            fig, ax = plt.subplots(figsize=(7, 4))

            plot_data = filtered.sort_values("Sample_Date")
            values = pd.to_numeric(
                plot_data[column], errors="coerce"
            )

            ax.plot(
                plot_data["Sample_Date"],
                values,
                marker="o",
                linewidth=1.5
            )

            ax.axhline(
                lower, linestyle="--",
                label=f"Reference: {lower}"
            )

            if upper is not None:
                ax.axhline(
                    upper, linestyle="--",
                    label=f"Reference: {upper}"
                )

            ax.set_title(title)
            ax.set_xlabel("Sample Date")
            ax.set_ylabel(column)
            ax.grid(alpha=0.3)
            ax.legend()

            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

# Records
st.header("4. Water Quality Records")

st.dataframe(
    filtered.sort_values("Sample_Date"),
    use_container_width=True
)

# Downloads
st.header("5. Download Reports")

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Filtered Assessment CSV",
    data=csv_data,
    file_name="river_water_quality_assessment.csv",
    mime="text/csv"
)

station_csv = stations.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Station Assessment CSV",
    data=station_csv,
    file_name="station_level_assessment.csv",
    mime="text/csv"
)

st.caption(
    "Data source: CPCB Tamil Nadu historical water quality records. "
    "Assessment is based on available historical observations. "
    "Missing values are not treated as normal readings."
)
