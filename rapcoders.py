import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="Smart Mess Tracker",
    page_icon="🍽️",
    layout="wide"
)

DB_NAME = "smart_mess.db"


# =====================================
# STEP 5: SQLITE DATABASE
# =====================================

def create_database():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS food_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            food_prepared REAL NOT NULL,
            food_consumed REAL NOT NULL,
            food_wasted REAL NOT NULL,
            wastage_percentage REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_record(record_date, prepared, consumed, wasted, percentage):
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        INSERT INTO food_records
        (date, food_prepared, food_consumed,
         food_wasted, wastage_percentage)
        VALUES (?, ?, ?, ?, ?)
    """, (
        str(record_date),
        prepared,
        consumed,
        wasted,
        percentage
    ))

    conn.commit()
    conn.close()


def get_records():
    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
        SELECT
            id AS ID,
            date AS Date,
            food_prepared AS 'Food Prepared (kg)',
            food_consumed AS 'Food Consumed (kg)',
            food_wasted AS 'Food Wasted (kg)',
            wastage_percentage AS 'Wastage Percentage'
        FROM food_records
        ORDER BY date DESC, id DESC
    """, conn)

    conn.close()
    return df


def delete_record(record_id):
    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        "DELETE FROM food_records WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()


# Create database automatically
create_database()


# =====================================
# MAIN TITLE
# =====================================

st.title("🍽️ Food Management Dashboard")

st.divider()


# =====================================
# STEP 1: ENTER DAILY FOOD DETAILS
# =====================================

st.header("📝 Enter Daily Food Details")

col1, col2 = st.columns(2)

with col1:

    selected_date = st.date_input(
        "Select Date",
        value=date.today()
    )

    food_prepared = st.number_input(
        "Food Prepared (kg)",
        min_value=0.0,
        value=50.0,
        step=1.0
    )

with col2:

    food_wasted = st.number_input(
        "Food Wasted (kg)",
        min_value=0.0,
        value=5.0,
        step=1.0
    )


# =====================================
# CALCULATIONS
# =====================================

food_consumed = food_prepared - food_wasted

if food_prepared > 0:

    wastage_percentage = (
        food_wasted / food_prepared
    ) * 100

else:
    wastage_percentage = 0


st.info(
    f"Food Consumed: {food_consumed:.2f} kg"
)

st.info(
    f"Wastage Percentage: {wastage_percentage:.2f}%"
)


# =====================================
# STEP 2: SAVE RECORD IN SQLITE
# =====================================

if st.button("💾 Save Daily Record", type="primary"):

    if food_prepared <= 0:

        st.error("Please enter food prepared greater than zero.")

    elif food_wasted > food_prepared:

        st.error("Food wasted cannot exceed food prepared.")

    else:

        save_record(
            selected_date,
            food_prepared,
            food_consumed,
            food_wasted,
            wastage_percentage
        )

        st.success(
            "Record permanently saved in database! 🎉"
        )

        st.rerun()


st.divider()


# =====================================
# LOAD DATABASE RECORDS
# =====================================

df = get_records()


# =====================================
# STEP 3: DASHBOARD AND GRAPHS
# =====================================

if not df.empty:

    df["Date"] = pd.to_datetime(df["Date"])

    st.header("📊 Food Management Dashboard")

    total_prepared = df["Food Prepared (kg)"].sum()

    total_consumed = df["Food Consumed (kg)"].sum()

    total_wasted = df["Food Wasted (kg)"].sum()

    total_records = len(df)

    overall_percentage = (
        total_wasted / total_prepared * 100
        if total_prepared > 0 else 0
    )

    # Dashboard cards

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        total_records
    )

    col2.metric(
        "Food Prepared",
        f"{total_prepared:.2f} kg"
    )

    col3.metric(
        "Food Consumed",
        f"{total_consumed:.2f} kg"
    )

    col4.metric(
        "Food Wasted",
        f"{total_wasted:.2f} kg"
    )

    st.metric(
        "Overall Wastage Percentage",
        f"{overall_percentage:.2f}%"
    )

    # Daily statistics

    st.subheader("Daily Food Statistics")

    daily_data = df.groupby("Date")[
        [
            "Food Prepared (kg)",
            "Food Consumed (kg)",
            "Food Wasted (kg)"
        ]
    ].sum()

    st.bar_chart(daily_data)

    # Wastage trend

    st.subheader("Food Wastage Trend")

    wastage_data = df.groupby("Date")[
        "Food Wasted (kg)"
    ].sum()

    st.line_chart(wastage_data)


    # =====================================
    # STEP 4: MONTHLY REPORT
    # =====================================

    st.divider()

    st.header("📅 Monthly Food Report")

    df["Month"] = df["Date"].dt.strftime("%B %Y")

    available_months = sorted(
        df["Month"].unique(),
        key=lambda x: pd.to_datetime(x, format="%B %Y"),
        reverse=True
    )

    selected_month = st.selectbox(
        "Select Month",
        available_months
    )

    monthly_df = df[
        df["Month"] == selected_month
    ]

    monthly_prepared = monthly_df[
        "Food Prepared (kg)"
    ].sum()

    monthly_consumed = monthly_df[
        "Food Consumed (kg)"
    ].sum()

    monthly_wasted = monthly_df[
        "Food Wasted (kg)"
    ].sum()

    monthly_percentage = (
        monthly_wasted / monthly_prepared * 100
        if monthly_prepared > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Monthly Prepared",
        f"{monthly_prepared:.2f} kg"
    )

    col2.metric(
        "Monthly Consumed",
        f"{monthly_consumed:.2f} kg"
    )

    col3.metric(
        "Monthly Wasted",
        f"{monthly_wasted:.2f} kg"
    )

    st.metric(
        "Monthly Wastage Percentage",
        f"{monthly_percentage:.2f}%"
    )

    st.subheader("Monthly Records")

    st.dataframe(
        monthly_df.drop(columns=["Month"]),
        use_container_width=True,
        hide_index=True
    )


    # =====================================
    # ALL SAVED RECORDS
    # =====================================

    st.divider()

    st.header("📋 All Saved Food Records")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================
    # DELETE INCORRECT RECORD
    # =====================================

    st.divider()

    st.header("🗑️ Delete Incorrect Record")

    record_options = {
        f"ID {row['ID']} | {row['Date']} | "
        f"Wasted: {row['Food Wasted (kg)']} kg": int(row["ID"])
        for _, row in df.iterrows()
    }

    selected_record = st.selectbox(
        "Select record to delete",
        list(record_options.keys())
    )

    if st.button("Delete Selected Record"):

        delete_record(
            record_options[selected_record]
        )

        st.success("Record deleted successfully.")

        st.rerun()


    # =====================================
    # DOWNLOAD CSV REPORT
    # =====================================

    st.divider()

    csv_data = df.drop(
        columns=["Month"]
    ).to_csv(index=False)

    st.download_button(
        label="📥 Download Food Report (CSV)",
        data=csv_data,
        file_name="smart_mess_food_report.csv",
        mime="text/csv"
    )

else:

    st.info(
        "No food records available. "
        "Enter daily details and save your first record."
    )


# =====================================
# FOOTER
# =====================================

st.divider()

st.caption(
    "🍽️ Smart Mess Tracker | "
    "Food Waste Reduction System"
)