import streamlit as st
import sqlite3
import os

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
        if operation == "debit":
            current_balance -= amount
        elif operation == "credit":
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

# Initialize balance if not already set
if not os.path.exists(BALANCE_FILE):
    initialize_balance()

# Main Page
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
        add_expense(expense_name, amount,operation_type,category, date.strftime('%Y-%m-%d'), note)
        updated_balance = update_balance(amount, operation_type)
        st.success(f"Expense added successfully!")
        # st.success(f"Expense added successfully! Updated Balance: ₹{updated_balance:.2f}")
    else:
        st.error("Please fill in all required fields correctly.")

# Display Current Balance
balance = get_balance()
if balance is not None:
    st.subheader(f"Current Balance: ₹{balance:.2f}")

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