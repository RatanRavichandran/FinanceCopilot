import streamlit as st
import pandas as pd

# Title of the app
st.title("Transaction History")

file_path = 'statement.xlsx'

try:
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    df['Date'] = pd.to_datetime(df['Date'])  
    sorted_df = df.sort_values(by='Date', ascending=True)
    
    top_3_recent_transactions = sorted_df.head(3)
    
    st.subheader("Top 3 Recent Transactions")
    st.table(top_3_recent_transactions)

except FileNotFoundError:
    st.error(f"The file {file_path} does not exist. Please check the path.")
