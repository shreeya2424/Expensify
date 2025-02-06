import streamlit as st
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px

# Initialize database
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create the table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_name TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    note TEXT
)
''')
conn.commit()

# File to store balance
BALANCE_FILE = "balance.txt"

def initialize_balance():
    if not os.path.exists(BALANCE_FILE):
        st.warning("No balance found. Please add an initial balance:")
        initial_balance = st.number_input("Initial Balance", min_value=0, step=1)
        if st.button("Set Balance"):
            with open(BALANCE_FILE, "w") as f:
                f.write(str(initial_balance))
            st.success(f"Balance set to {initial_balance:.2f}")

def get_balance():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            return float(f.read())
    return None

def update_balance(amount, operation):
    current_balance = get_balance()

    if current_balance is not None:
        if operation == "Debit":
            current_balance -= amount
        elif operation == "Credit":
            current_balance += amount
        with open(BALANCE_FILE, "w") as f:
            f.write(str(current_balance))

        return current_balance
    
def add_expense(expense_name, amount,type, category, date, note):
    c.execute('''
    INSERT INTO expenses (expense_name, amount,type, category, date,  note)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (expense_name, amount,type, category, date, note))
    conn.commit()

def get_latest_expenses(limit=5):
    c.execute('''SELECT * FROM expenses ORDER BY id DESC LIMIT ?''', (limit,))
    return c.fetchall()

# main_____________________________________________

st.set_page_config(
    page_title="Expensify!",
    # layout="wide"
)

st.title("Expensify!")
st.subheader("Track and visualize your expenses")
# Initialize balance if not already set
if not os.path.exists(BALANCE_FILE):
    initialize_balance()
    st.session_state.show_form = False

if 'show_form' not in st.session_state:
    st.session_state.show_form = False

if st.button("Add a new Transaction"):
    st.session_state.show_form = True

if st.session_state.show_form:
    st.subheader("Add New Expense")
    # Input form
    with st.form("add_expense_form", clear_on_submit=True):
        expense_name = st.text_input("Expense Name", max_chars=50)
        amount = st.number_input("Amount", min_value=0, step=1)
        operation_type = st.selectbox("Type", ["Debit", "Credit"])  # Add type field
        category = st.selectbox("Category", ["Work", "Food", "Bill", "Shop", "Other"])
        date = st.date_input("Date")
        note = st.text_input("Note (Optional)")
        submitted = st.form_submit_button("Add Expense")

        # print('submit btn baja')
    print(submitted)
    if submitted:
        print('submit to hua')
        if expense_name and amount > 0:
            print('here')
            add_expense(expense_name, amount,operation_type,category, date.strftime('%Y-%m-%d'), note)
            updated_balance = update_balance(amount, operation_type)
            st.success(f"Expense added successfully!")
            # st.success(f"Expense added successfully! Updated Balance: ₹{updated_balance:.2f}")
            balance = get_balance()
            if balance is not None:
                    st.subheader(f"Current Balance: ₹{updated_balance:.2f}")


        else:
            st.error("Please fill in all required fields correctly.")

# Display the latest 5 entries
st.subheader("Latest Expenses")
latest_expenses = get_latest_expenses()

if latest_expenses:
    st.table(
        [{
            "Expense Name": row[1],
            "Amount": row[2],
            "Type": row[3],
            "Category": row[4],
            "Date": row[5],
            # "Sent To": row[5],
            "Note": row[6]
        } for row in latest_expenses]
    )
else:
    st.info("No expenses recorded yet.")




# Initialize session state for report form
if "show_report_form" not in st.session_state:
    st.session_state.show_report_form = False

# Button to open report form
if st.button("Visualize"):
    st.session_state.show_report_form = True  # Keep form open after refresh

# Show the form only if the button was clicked
if st.session_state.show_report_form:
    st.subheader('Enter the dates for which you would like the reports.')
    
    with st.form("report_dates", clear_on_submit=True):
        from_date = st.date_input("From")
        to_date = st.date_input("To")
        report_dates_submitted = st.form_submit_button("Generate")
    
    if report_dates_submitted:
        query = "SELECT * FROM expenses WHERE date BETWEEN ? AND ?"
        all_data = pd.read_sql_query(query, conn, params=(from_date, to_date))
        report_data=all_data[['amount','type','category','date']]
        # st.write(report_data)
        report_data['date'] = report_data['date'].astype(str)
        st.subheader("Here is your report!")
        st.dataframe(all_data, use_container_width=True)





        # if "show_all" not in st.session_state:
        #     st.session_state.show_all = False  # Default to showing 5 rows
        # st.dataframe(all_data if st.session_state.show_all else all_data.head(5), use_container_width=True)

        # # Display table based on state
        # if st.session_state.show_all:
        #     st.dataframe(all_data, use_container_width=True)  # Show all rows
        # else:
        #     st.dataframe(all_data.head(5), use_container_width=True)  # Show top 5 rows

        # Buttons for actions
        col1, col2,col3 = st.columns([1, 1,1])

        with col1:
            pass
            # if st.button("Show all"):
            #     st.session_state.show_all = True  # Update state
            #     st.experimental_rerun() # Refresh UI

        with col3:
            csv = all_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download .csv", csv, "expenses.csv", "text/csv", key="download-csv")



# Create the line plot
        # report_data['date'] = pd.to_datetime(report_data['date'])
        grouped_data = report_data.groupby(['date', 'type']).sum().reset_index()

        fig10 = px.line(grouped_data, x='date', y='amount', color='type', color_discrete_map={'Debit': 'red', 'Credit': 'blue'},title="Total Amount Over Time by Type",category_orders={"date": sorted(grouped_data['date'].unique())})
        st.plotly_chart(fig10)

# pichart
        fig2= px.pie(report_data, values='amount', names='category', title='Expense Distribution by Category')
        st.plotly_chart(fig2)

# bargraph
        # fig3 = px.bar(report_data, x='date', y='amount', color='category', title='Amount vs Date (Stacked by Category)', barmode='stack')  
        # st.plotly_chart(fig3)
        fig3 = px.bar(report_data, x='date', y='amount', color='category', title='Amount vs Date (Stacked by Category)', barmode='stack')

# Update layout to restrict x-axis range
        fig3.update_layout(xaxis=dict(range=[0, None]))

        st.plotly_chart(fig3)


        

