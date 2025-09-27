import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scipy import stats
import streamlit as st
import openai
openai.api_key = ''

personal_expenses = pd.read_excel("pft.xlsx")


print(personal_expenses.shape)
print(personal_expenses.describe())
print(personal_expenses.isna().sum())

personal_expenses = personal_expenses.drop(columns=[
    'Conversion rate from source/accounting currency to ils',
    'comments',
    'Labeling',
    'Discount_club',
    'Discount_key'
])
print(personal_expenses["Debit_currency"].unique())
print(personal_expenses["Original_transaction_currency"].unique())
print(personal_expenses.transaction_type.unique())
personal_expenses.drop(columns='Original_transaction_currency', inplace=True)
mismatched_amounts = personal_expenses[personal_expenses["debit_amount"] != personal_expenses["Original_transaction_amount"]]
if not mismatched_amounts.empty:
    print("Mismatched debit_amount and Original_transaction_amount:")
    print(mismatched_amounts)
    personal_expenses.loc[mismatched_amounts.index, 'debit_amount'] = personal_expenses.loc[mismatched_amounts.index, 'Original_transaction_amount']
personal_expenses.drop(columns='Original_transaction_amount', inplace=True)
print(personal_expenses.dtypes) #Chec Data Types and Convert if Necessary
personal_expenses['transaction_date'] = pd.to_datetime(personal_expenses['transaction_date'], format='mixed', errors='coerce')
personal_expenses = personal_expenses.sort_values(by="transaction_date")
personal_expenses.reset_index(drop=True, inplace=True)
print(personal_expenses['Name_of_the_business'].unique())
personal_expenses['Name_of_the_business'].replace("Transfer in BIT BIP", "Transfer in BIT", inplace=True)
# 10. Check for Outliers and Handle Them
personal_expenses['z_score'] = stats.zscore(personal_expenses['debit_amount'])
outlier_threshold = 3
outliers = personal_expenses[personal_expenses['z_score'].abs() > outlier_threshold]

if not outliers.empty:
    print("Outliers detected:")
    print(outliers[['transaction_date', 'Name_of_the_business', 'debit_amount', 'z_score']])
    personal_expenses = personal_expenses[personal_expenses['z_score'].abs() <= outlier_threshold]
    personal_expenses.drop(columns='z_score', inplace=True)

def get_total_spending():
    return personal_expenses['debit_amount'].sum()

def get_avg_spending(period='month'):
    if period == 'month':
        return personal_expenses.groupby(personal_expenses['Billing_date'].dt.to_period('M'))['debit_amount'].sum().mean()
    elif period == 'week':
        return personal_expenses.groupby(personal_expenses['Billing_date'].dt.to_period('W'))['debit_amount'].sum().mean()

def get_high_spending_areas(threshold=0.2):
    category_spending = personal_expenses.groupby('category')['debit_amount'].sum()
    total_spending = get_total_spending()
    return category_spending[category_spending > threshold * total_spending]

def calculate_monthly_savings_needed(loan_amount, account_balance, interest_rate, repayment_period_months):
    monthly_interest_rate = interest_rate / 12 / 100
    monthly_payment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -repayment_period_months)
    savings_needed = monthly_payment - (account_balance * monthly_interest_rate)
    return savings_needed



st.set_page_config(page_title="Financial Advice Dashboard", layout="wide")
st.title("Financial Advice Dashboard")

col1, col2 = st.columns([1.5, 1])

with col1:
# Interactive Visualizations
    st.subheader("Money Spent per Category")
    debit_amount_by_category = personal_expenses.debit_amount.groupby(personal_expenses.category).sum().sort_values()
    fig = px.bar(debit_amount_by_category, x=debit_amount_by_category.index, y=debit_amount_by_category.values,
                labels={'x':'Category', 'y':'Money Spent'})
    fig.update_traces(hovertemplate='Category: %{x}<br>Money Spent: INR%{y:.2f}')
    st.plotly_chart(fig)

    st.subheader("Money spent over time")
    month_range = st.slider('Select Month Range',
                            min_value=int(personal_expenses['Billing_date'].dt.month.min()),
                            max_value=int(personal_expenses['Billing_date'].dt.month.max()),
                            value=(int(personal_expenses['Billing_date'].dt.month.min()),
                                int(personal_expenses['Billing_date'].dt.month.max())))

    filtered_data = personal_expenses[
        (personal_expenses['Billing_date'].dt.month >= month_range[0]) &
        (personal_expenses['Billing_date'].dt.month <= month_range[1])
    ]
    debit_amount_by_month = filtered_data.debit_amount.groupby(filtered_data.Billing_date.dt.month).sum()

    fig = px.line(x=debit_amount_by_month.index, y=debit_amount_by_month.values,
                labels={'x':'Month', 'y':'Total money spent'})
    fig.update_xaxes(tickvals=personal_expenses.Billing_date.dt.month.unique(),
                    ticktext=personal_expenses.Billing_date.dt.month_name().unique())
    st.plotly_chart(fig)

    st.subheader('Distribution of Payment Choices')
    payment_choice_distribution = personal_expenses['The_way_the_transaction_is_carried_out'].value_counts()
    fig = px.pie(payment_choice_distribution, values=payment_choice_distribution.values, names=payment_choice_distribution.index)
    st.plotly_chart(fig)

    st.subheader("Spending Insights")
    st.write(f"Total Spending: INR{get_total_spending():.2f}")
    st.write(f"Average Monthly Spending: INR{get_avg_spending('month'):.2f}")
    st.write(f"Average Weekly Spending: INR{get_avg_spending('week'):.2f}")

    high_spending_areas = get_high_spending_areas()
    if not high_spending_areas.empty:
        st.write("\nHigh Spending Areas:")
        st.write(high_spending_areas)
    else:
        st.write("\nNo High Spending Areas Detected")

    st.subheader("Loan Repayment Calculator")

    loan_amount = st.number_input("Enter your loan amount:", value=0.0)
    account_balance = st.number_input("Enter your current account balance:", value=0.0)
    interest_rate = st.number_input("Enter your loan interest rate (%):", value=0.0)
    repayment_period_months = st.number_input("Enter your desired repayment period in months:", value=0)

    if st.button("Calculate"):
        if loan_amount > 0 and repayment_period_months > 0:
            savings_needed = calculate_monthly_savings_needed(loan_amount, account_balance, interest_rate, repayment_period_months)
            st.write(f"You need to save approximately INR{savings_needed:.2f} per month to repay your loan.")
        else:
            st.warning("Please enter valid loan amount and repayment period.")
    file_path = "pft.xlsx"
    personal_expenses = pd.read_excel(file_path)

    def summarize_data(expenses):
        category_summary = expenses.groupby('category')['debit_amount'].sum().to_dict()

        business_summary = expenses.groupby('Name_of_the_business')['debit_amount'].sum().to_dict()

        transaction_type_summary = expenses.groupby('transaction_type')['debit_amount'].sum().to_dict()

        summary = (
            f"Category Summary: {category_summary}\n"
            f"Business Summary: {business_summary}\n"
            f"Transaction Type Summary: {transaction_type_summary}\n"
        )
        
        return summary

with col2:
    def prepare_context():
        total_spending = get_total_spending()
        avg_monthly_spending = get_avg_spending('month')
        avg_weekly_spending = get_avg_spending('week')
        high_spending_areas = get_high_spending_areas().to_dict()

        excel_summary = personal_expenses.describe().to_string()


        context = (
            f"Total Spending: INR{total_spending:.2f}\n"
            f"Average Monthly Spending: INR{avg_monthly_spending:.2f}\n"
            f"Average Weekly Spending: INR{avg_weekly_spending:.2f}\n"
            f"High Spending Areas: {high_spending_areas}\n"
        )
        
        return context

    context_info = prepare_context() +  summarize_data(personal_expenses)

    st.title("Chat with Financial Assistant")

    st.header("Ask Financial Insights")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        role = "User" if message["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {message['content']}")
    prompt = st.text_input("Ask about your financial data or insights")

    if prompt:
        # Store the user message in session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        context_info = prepare_context() + summarize_data(personal_expenses)

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides insights based on financial data. Output without mentioning exactly how much I spent on each category."},
                {"role": "system", "content": context_info}
            ] + st.session_state.messages,
            max_tokens=400,
            temperature=0.7,
        )

        assistant_message = response.choices[0].message.content.strip()

        st.session_state.messages.append({"role": "assistant", "content": assistant_message})

    if st.session_state.messages:
        latest_message = next((msg for msg in reversed(st.session_state.messages) if msg["role"] == "assistant"), None)
        if latest_message:
            st.subheader("Assistant's Response")
            st.markdown(f"**Assistant:** {latest_message['content']}")  