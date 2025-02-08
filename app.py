import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px

# Function to create a user-specific database
def create_user_db(user_id):
    # Create a folder for user data if it doesn't exist
    user_folder = f"user_data/{user_id}"
    os.makedirs(user_folder, exist_ok=True)
    
    # Create the database connection
    conn = sqlite3.connect(f'{user_folder}/{user_id}_data.db')
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

    return conn

# Function to initialize user balance file
def create_balance_file(user_id,initial_balance):
    user_folder = f"user_data/{user_id}"
    balance_file = f"{user_folder}/{user_id}_balance.txt"
    # If the balance file doesn't exist, create it with an initial balance
    if not os.path.exists(balance_file):
        print('file create?')
        with open(balance_file, 'w') as f:
            f.write(str(initial_balance))  # Initial balance set to 0.00
    return balance_file

# Function to get user balance
def get_balance(user_id):
    balance_file = f"user_data/{user_id}/{user_id}_balance.txt"  # user-specific balance file
    if os.path.exists(balance_file):
        with open(balance_file, "r") as f:
            return float(f.read())
    
    return None

# Function to update user balance
def update_balance(amount, operation, user_id):
    current_balance = get_balance(user_id)
    st.write(current_balance)
    if current_balance is not None:
        if operation == "Debit":
            current_balance -= amount
        elif operation == "Credit":
            current_balance += amount
        balance_file = f"user_data/{user_id}/{user_id}_balance.txt"  # user-specific balance file
        with open(balance_file, "w") as f:
            f.write(str(current_balance))

        return current_balance

# Function to add an expense
def add_expense(expense_name, amount, type, category, date, note, user_id):
    conn = create_user_db(user_id)

    c = conn.cursor()
    c.execute('''
    INSERT INTO expenses (expense_name, amount, type, category, date, note)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (expense_name, amount, type, category, date, note))
    conn.commit()

# Function to get latest expenses
def get_latest_expenses(user_id, limit=5):
    conn = create_user_db(user_id)
    c = conn.cursor()
    c.execute('''SELECT * FROM expenses ORDER BY id DESC LIMIT ?''', (limit,))
    return c.fetchall()

# main________________________________________________________________________________________

st.set_page_config(
    page_title="Expensify!",
)

st.title("Expensify!")
st.subheader("Track and visualize your expenses")

if "user_id" not in st.session_state:
    user_input = st.text_input("Enter your username:", max_chars=20)

    # Only set session_state when user_input is non-empty
    if user_input:
        st.session_state.user_id = user_input
        st.rerun()  # Forces the script to re-run so the session_state gets updated

# Now user_id should be properly stored in session_state
if "user_id" in st.session_state:
    user_id = st.session_state.user_id
    st.write(f"Welcome, {user_id}!")
    
    # Initialize balance if not already set
    if get_balance(user_id) is None:
        st.warning("No balance found. Please add an initial balance:")
        initial_balance = st.number_input("Initial Balance", min_value=0, step=1)
        if st.button("Set Balance"):
            create_balance_file(user_id,initial_balance)
            # update_balance(initial_balance, "Credit", user_id)
            st.success(f"Balance set to ₹{initial_balance:.2f}")

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

        if submitted:
            if expense_name and amount > 0:
                add_expense(expense_name, amount, operation_type, category, date.strftime('%Y-%m-%d'), note, user_id)
                updated_balance = update_balance(amount, operation_type, user_id)
                st.success(f"Expense added successfully!")
                balance = get_balance(user_id)
                if balance is not None:
                    st.subheader(f"Current Balance: ₹{updated_balance:.2f}")
            else:
                st.error("Please fill in all required fields correctly.")

    # Display the latest 5 entries
    st.subheader("Latest Expenses")
    latest_expenses = get_latest_expenses(user_id)

    if latest_expenses:
        st.table(
            [{
                "Expense Name": row[1],
                "Amount": row[2],
                "Type": row[3],
                "Category": row[4],
                "Date": row[5],
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
            conn = create_user_db(user_id)
            query = "SELECT * FROM expenses WHERE date BETWEEN ? AND ?"
            all_data = pd.read_sql_query(query, conn, params=(from_date, to_date))
            report_data = all_data[['amount', 'type', 'category', 'date']]
            report_data['date'] = report_data['date'].astype(str)
            st.subheader("Here is your report!")
            st.dataframe(all_data, use_container_width=True)

                        # Buttons for actions
            col1, col2,col3 = st.columns([1, 1,1])

            with col3:
                csv = all_data.to_csv(index=False).encode('utf-8')
                st.download_button("Download .csv file", csv, "expenses.csv", "text/csv", key="download-csv")
            

            # viz___________________________________________________________________
            grouped_data = report_data.groupby(['date', 'type']).sum().reset_index()
# line chart
            fig10 = px.line(grouped_data, x='date', y='amount', color='type', color_discrete_map={'Debit': 'red', 'Credit': 'blue'},title="Total Amount Over Time by Type",category_orders={"date": sorted(grouped_data['date'].unique())})
            st.plotly_chart(fig10)

    # pichart
            fig2= px.pie(report_data, values='amount', names='category', title='Expense Distribution by Category')
            st.plotly_chart(fig2)

    # bargraph
            fig3 = px.bar(report_data, x='date', y='amount', color='category', title='Amount vs Date (Stacked by Category)', barmode='stack')  
            st.plotly_chart(fig3)

                # alag hi code kya pata
            # # Pie chart
            # fig2 = px.pie(report_data, values='amount', names='category', title='Expense Distribution by Category')
            # st.plotly_chart(fig2)

            # # Bar chart
            # fig3 = px.bar(report_data, x='date', y='amount', color='category', title='Amount vs Date (Stacked by Category)', barmode='stack')  
            # st.plotly_chart(fig3)

            # # Line chart
            # grouped_data = report_data.groupby(['date', 'type']).sum().reset_index()
            # fig10 = px.line(grouped_data, x='date', y='amount', color='type', color_discrete_map={'Debit': 'red', 'Credit': 'blue'}, title="Total Amount Over Time by Type", category_orders={"date": sorted(grouped_data['date'].unique())})
            # st.plotly_chart(fig10)
else:
    st.write("Please enter your username.")
