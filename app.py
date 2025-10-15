import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, append_row, compute_vacation_total, infer_seniority
from datetime import date

st.set_page_config(page_title="HR Tool", layout="wide", page_icon="🧑‍💼")

@st.cache_data
def get_data():
    return load_data()

def main():
    st.title("HR Tool — Dashboard & Employee Manager")
    st.markdown("Multi-tab internal HR dashboard (Visualizations / Add Employee / Future: Chatbot)")

    df = get_data()
    tabs = st.tabs(["Visualizations", "Add Employee", "Future (Chatbot)"])

    # -------------------------
    # Tab 1: Visualizations
    # -------------------------
    with tabs[0]:
        st.header("Visualizations")

        # Filters
        with st.sidebar:
            st.header("Filters")
            depts = ["All"] + sorted(df["Department"].dropna().unique().tolist())
            selected_dept = st.selectbox("Department", depts, index=0)
            cantons = ["All"] + sorted(df["Residence (Canton)"].dropna().unique().tolist())
            selected_canton = st.selectbox("Canton", cantons, index=0)
            min_age, max_age = int(df["Age"].min()), int(df["Age"].max())
            age_range = st.slider("Age range", min_age, max_age, (min_age, max_age))

        # Apply filters
        vis_df = df.copy()
        if selected_dept != "All":
            vis_df = vis_df[vis_df["Department"] == selected_dept]
        if selected_canton != "All":
            vis_df = vis_df[vis_df["Residence (Canton)"] == selected_canton]
        vis_df = vis_df[(vis_df["Age"] >= age_range[0]) & (vis_df["Age"] <= age_range[1])]

        # Show counts
        cols = st.columns(3)
        cols[0].metric("Employees (filtered)", len(vis_df))
        if len(vis_df) > 0:
            avg_age = round(vis_df["Age"].mean(), 1)
        else:
            avg_age = "-"
        cols[1].metric("Average Age", avg_age)
        cols[2].metric("Departments represented", vis_df["Department"].nunique())

        # 1) Age distribution by department
        st.subheader("1) Age distribution by Department")
        if vis_df.empty:
            st.info("No data for selected filters.")
        else:
            fig1 = px.box(vis_df, x="Department", y="Age", points="all",
                          title="Age distribution per Department",
                          labels={"Age": "Age (years)"})
            st.plotly_chart(fig1, use_container_width=True)

        # 2) Workload by age (scatter)
        st.subheader("2) Workload by Age")
        if vis_df.empty:
            st.info("No data for selected filters.")
        else:
            # normalize workload to numeric fraction if stored as '80%'
            def workload_to_float(x):
                if isinstance(x, str) and x.endswith("%"):
                    return float(x.strip("%"))/100.0
                try:
                    return float(x)
                except:
                    return None
            vis_df["workload_frac"] = vis_df["Workload"].apply(workload_to_float)
            # jitter age a little for visualization
            import numpy as np
            jitter = np.random.normal(0, 0.2, size=len(vis_df))
            fig2 = px.scatter(vis_df, x="Age", y="workload_frac", color="Department",
                              hover_data=["First Name", "Last Name", "Department", "Workload"],
                              title="Workload (fraction) by Age",
                              labels={"workload_frac": "Workload (fraction)", "Age":"Age"})
            st.plotly_chart(fig2, use_container_width=True)

        # 3) General age distribution
        st.subheader("3) General Age Distribution")
        if vis_df.empty:
            st.info("No data for selected filters.")
        else:
            fig3 = px.histogram(vis_df, x="Age", nbins=15, title="Age histogram", marginal="box")
            st.plotly_chart(fig3, use_container_width=True)

        # Show filtered table option
        with st.expander("Show filtered data table"):
            st.dataframe(vis_df.reset_index(drop=True))

    # -------------------------
    # Tab 2: Add Employee
    # -------------------------
    with tabs[1]:
        st.header("Add a new employee")
        st.markdown("Use the form below to add a new employee. New rows are appended to the CSV in `data/`.")

        with st.form("add_employee_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            first_name = c1.text_input("First name", "")
            last_name = c2.text_input("Last name", "")
            canton = st.selectbox("Residence (Canton)", sorted(df["Residence (Canton)"].unique()))
            department = st.selectbox("Department", sorted(df["Department"].unique()))
            age = st.number_input("Age", min_value=16, max_value=100, value=30)
            workload_options = ["60%", "70%", "80%", "90%", "100%"]
            workload = st.selectbox("Workload", workload_options, index=4)
            seniority = st.selectbox("Seniority Level", ["Auto-suggest"] + ["Junior", "Mid", "Senior", "Manager", "Director"])
            hire_date = st.date_input("Hire date", value=date.today())
            # compute vacation total
            vacation_total = compute_vacation_total(workload)
            vacation_taken = st.number_input("Vacation days taken", min_value=0, max_value=vacation_total, value=0)

            submitted = st.form_submit_button("Add employee")

        if submitted:
            if not first_name or not last_name:
                st.error("First and last name are required.")
            else:
                # if auto-suggest selected, infer
                if seniority == "Auto-suggest":
                    seniority = infer_seniority(age, hire_date)
                new_row = {
                    "First Name": first_name,
                    "Last Name": last_name,
                    "Residence (Canton)": canton,
                    "Age": int(age),
                    "Department": department,
                    "Seniority Level": seniority,
                    "Workload": workload,
                    "Vacation Days Total": int(vacation_total),
                    "Vacation Days Taken": int(vacation_taken),
                    "Hire Date": pd.to_datetime(hire_date).date()
                }
                try:
                    append_row(new_row)
                    st.success(f"Added {first_name} {last_name} to dataset.")
                    st.json(new_row)
                    # Refresh cached data
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to append row: {e}")

    # -------------------------
    # Tab 3: Future (Chatbot)
    # -------------------------
    with tabs[2]:
        st.header("Future: Chatbot")
        st.info("This tab is reserved for a chat-bot / assistant to query the HR data (planned).")

if __name__ == "__main__":
    main()