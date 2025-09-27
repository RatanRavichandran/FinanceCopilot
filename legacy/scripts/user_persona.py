import streamlit as st
import openai
import os

openai.api_key = ""  # Replace with your actual OpenAI API key

def generate_personalized_recommendation(responses):
    profile_summary = "\n".join([f"{key}: {value}" for key, value in responses.items()])
    prompt = f"""
    You are a loan advisor at TVS Credit. Based on the customer's profile below, provide a personalized loan recommendation.
    Address the customer respectfully and provide relevant loan options, highlighting the benefits and how they meet the customer's needs.

    Customer Profile:
    {profile_summary}

    Recommendation:
    """

    try:
        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": 'system', 'content': 'You are a helpful loan advisor at TVS Credit.'},
                {"role": 'user', 'content': prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        recommendation = response.choices[0].message.content.strip()
    except Exception as e:
        recommendation = f"An error occurred while generating the recommendation: {e}"

    return recommendation

def generate_detailed_profile(session_state):
    profile_summary = "\n".join([f"{key}: {value}" for key, value in session_state.items() if key != 'step'])
    prompt = f"""
You are a loan advisor at TVS Credit. Your task is to provide a detailed user profile based on the customer's information below. This profile will be used for all TVS loan services to give tailored answers to the user.
Please ensure the user profile includes the following details:

Personal Information
Financial Information
Employment Information
Loan Details
Use the provided information to create a comprehensive user profile that will enable tailored loan services for the customer.

    Customer Profile:
    {profile_summary}

    Detailed Profile:
    """

    try:
        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": 'system', 'content': 'You are a helpful loan advisor at TVS Credit.'},
                {"role": 'user', 'content': prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        detailed_profile = response.choices[0].message.content.strip()
    except Exception as e:
        detailed_profile = f"An error occurred while generating the detailed profile: {e}"

    return detailed_profile

def save_user_profile_to_file(session_state):
    script_path = os.path.abspath(os.path.dirname(__file__))
    profile_filename = os.path.join(script_path, "user_profile.txt")
    
    with open(profile_filename, "w", encoding='utf-8') as file:
        file.write("User Profile:\n")
        for key, value in session_state.items():
            if key != 'step':
                file.write(f"{key}: {value}\n")

    detailed_profile = generate_detailed_profile(session_state)
    with open(profile_filename, "a", encoding='utf-8') as file:
        file.write("\nDetailed Profile:\n")
        file.write(detailed_profile)

    print(f"User profile saved to {profile_filename}")

def get_user_profile():
    st.title("Welcome to TVS Credit Loan Application")
    st.write("""
    To provide you with the best loan options, we'd like to understand your needs better.
    Please complete this short questionnaire. It will take only a few minutes.
    """)

    total_steps = 7

    if 'step' not in st.session_state:
        st.session_state.step = 1

    def calculate_progress(step):
        return int((step - 1) / total_steps * 100)

    st.progress(calculate_progress(st.session_state.step))

    if st.session_state.step == 1:
        st.header("Step 1: Tell us about yourself")
        age = st.number_input("What is your age?", min_value=18, max_value=100, value=25)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        location = st.text_input("City and State")
        marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])
        employment_status = st.selectbox("Employment Status", ["Employed", "Self-Employed", "Business Owner", "Student", "Unemployed"])

        if st.button("Next"):
            st.session_state.age = age
            st.session_state.gender = gender
            st.session_state.location = location
            st.session_state.marital_status = marital_status
            st.session_state.employment_status = employment_status
            st.session_state.step = 2
            st.experimental_rerun()

    elif st.session_state.step == 2:
        st.header("Step 2: Your Financial Status")
        income_range = st.selectbox(
            "Current monthly income range:",
            ["Below ₹25,000", "₹25,000 – ₹50,000", "₹50,001 – ₹1,00,000", "Above ₹1,00,000"]
        )
        employment_type = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business Owner"])
        existing_loans = st.radio("Do you have any existing loans or debts?", ["Yes", "No"])
        credit_history = st.radio("Are you aware of your credit history?", ["Yes", "No"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 1
                st.experimental_rerun()
        with col2:
            if st.button("Next"):
                st.session_state.income_range = income_range
                st.session_state.employment_type = employment_type
                st.session_state.existing_loans = existing_loans
                st.session_state.credit_history = credit_history
                st.session_state.step = 3
                st.experimental_rerun()

    elif st.session_state.step == 3:
        st.header("Step 3: Loan Preferences")
        loan_type = st.selectbox(
            "Type of loan you're interested in:",
            ["Two-Wheeler Loan", "Used Car Loan", "Consumer Durable Loan", "Personal Loan", "Business Loan"]
        )
        loan_amount = st.number_input("Preferred Loan Amount (in ₹)", min_value=10000, max_value=10000000, step=10000, value=500000)
        repayment_tenure = st.selectbox(
            "Preferred Loan Tenure",
            ["Less than 1 year", "1 – 3 years", "3 – 5 years", "More than 5 years"]
        )
        interest_rate_sensitivity = st.select_slider(
            "Interest Rate Sensitivity",
            options=["Low", "Medium", "High"]
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 2
                st.experimental_rerun()
        with col2:
            if st.button("Next"):
                st.session_state.loan_type = loan_type
                st.session_state.loan_amount = loan_amount
                st.session_state.repayment_tenure = repayment_tenure
                st.session_state.interest_rate_sensitivity = interest_rate_sensitivity
                st.session_state.step = 4
                st.experimental_rerun()

    elif st.session_state.step == 4:
        st.header("Step 4: Specific Needs")
        loan_purpose = st.selectbox(
            "Primary purpose of your loan:",
            ["Purchasing a Vehicle", "Home Renovation", "Education Expenses", "Business Expansion", "Other"]
        )
        if loan_purpose == "Other":
            loan_purpose_details = st.text_input("Please specify the purpose of your loan")
        else:
            loan_purpose_details = loan_purpose

        urgency_level = st.selectbox(
            "How soon do you need the loan?",
            ["Immediately", "Within a month", "In 2-3 months", "No hurry"]
        )
        collateral_available = st.radio("Do you have any collateral to offer?", ["Yes", "No"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 3
                st.experimental_rerun()
        with col2:
            if st.button("Next"):
                st.session_state.loan_purpose_details = loan_purpose_details
                st.session_state.urgency_level = urgency_level
                st.session_state.collateral_available = collateral_available
                st.session_state.step = 5
                st.experimental_rerun()

    elif st.session_state.step == 5:
        st.header("Step 5: Risk Appetite and Preferences")
        variable_interest = st.radio("Comfortable with variable interest rates?", ["Yes", "No"])
        repayment_option = st.selectbox(
            "Preferred Repayment Option",
            ["Fixed Installments", "Flexible Payment Options"]
        )
        insurance_option = st.radio("Open to insurance or protection plans with the loan?", ["Yes", "No"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 4
                st.experimental_rerun()
        with col2:
            if st.button("Next"):
                st.session_state.variable_interest = variable_interest
                st.session_state.repayment_option = repayment_option
                st.session_state.insurance_option = insurance_option
                st.session_state.step = 6
                st.experimental_rerun()    
    elif st.session_state.step == 6:
        st.header("Review and Submit")

        st.write("Please review and update your responses if necessary:")

        # Create an editable form for the user to review and modify their responses
        with st.form("review_form"):
            st.session_state.age = st.number_input("What is your age?", min_value=18, max_value=100, value=st.session_state.age)
            st.session_state.gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(st.session_state.gender))
            st.session_state.location = st.text_input("City and State", value=st.session_state.location)
            st.session_state.marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"], index=["Single", "Married", "Divorced", "Widowed"].index(st.session_state.marital_status))
            st.session_state.employment_status = st.selectbox("Employment Status", ["Employed", "Self-Employed", "Business Owner", "Student", "Unemployed"], index=["Employed", "Self-Employed", "Business Owner", "Student", "Unemployed"].index(st.session_state.employment_status))

            st.session_state.income_range = st.selectbox(
                "Current monthly income range:",
                ["Below ₹25,000", "₹25,000 – ₹50,000", "₹50,001 – ₹1,00,000", "Above ₹1,00,000"],
                index=["Below ₹25,000", "₹25,000 – ₹50,000", "₹50,001 – ₹1,00,000", "Above ₹1,00,000"].index(st.session_state.income_range)
            )
            st.session_state.employment_type = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business Owner"], index=["Salaried", "Self-Employed", "Business Owner"].index(st.session_state.employment_type))
            st.session_state.existing_loans = st.radio("Do you have any existing loans or debts?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.existing_loans))
            st.session_state.credit_history = st.radio("Are you aware of your credit history?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.credit_history))

            st.session_state.loan_type = st.selectbox(
                "Type of loan you're interested in:",
                ["Two-Wheeler Loan", "Used Car Loan", "Consumer Durable Loan", "Personal Loan", "Business Loan"],
                index=["Two-Wheeler Loan", "Used Car Loan", "Consumer Durable Loan", "Personal Loan", "Business Loan"].index(st.session_state.loan_type)
            )
            st.session_state.loan_amount = st.number_input("Preferred Loan Amount (in ₹)", min_value=10000, max_value=10000000, step=10000, value=st.session_state.loan_amount)
            st.session_state.repayment_tenure = st.selectbox(
                "Preferred Loan Tenure",
                ["Less than 1 year", "1 – 3 years", "3 – 5 years", "More than 5 years"],
                index=["Less than 1 year", "1 – 3 years", "3 – 5 years", "More than 5 years"].index(st.session_state.repayment_tenure)
            )
            st.session_state.interest_rate_sensitivity = st.select_slider(
                "Interest Rate Sensitivity",
                options=["Low", "Medium", "High"],
                value=st.session_state.interest_rate_sensitivity
            )

            st.session_state.loan_purpose_details = st.text_input("Primary purpose of your loan", value=st.session_state.loan_purpose_details)
            st.session_state.urgency_level = st.selectbox(
                "How soon do you need the loan?",
                ["Immediately", "Within a month", "In 2-3 months", "No hurry"],
                index=["Immediately", "Within a month", "In 2-3 months", "No hurry"].index(st.session_state.urgency_level)
            )
            st.session_state.collateral_available = st.radio("Do you have any collateral to offer?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.collateral_available))

            st.session_state.variable_interest = st.radio("Comfortable with variable interest rates?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.variable_interest))
            st.session_state.repayment_option = st.selectbox(
                "Preferred Repayment Option",
                ["Fixed Installments", "Flexible Payment Options"],
                index=["Fixed Installments", "Flexible Payment Options"].index(st.session_state.repayment_option)
            )
            st.session_state.insurance_option = st.radio("Open to insurance or protection plans with the loan?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.insurance_option))

            # Submit button for the form
            submitted = st.form_submit_button("Confirm and Submit")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 5
                st.experimental_rerun()
        with col2:
            if submitted:
                # Save user profile to a text file
                save_user_profile_to_file(st.session_state)
                st.success("Thank you! Your information has been submitted.")
                st.session_state.step = 7
                st.experimental_rerun()

    elif st.session_state.step == 7:
        st.header("Final Loan Recommendations")
        responses = {
            "Age": st.session_state.age,
            "Gender": st.session_state.gender,
            "Location": st.session_state.location,
            "Marital Status": st.session_state.marital_status,
            "Employment Status": st.session_state.employment_status,
            "Monthly Income Range": st.session_state.income_range,
            "Employment Type": st.session_state.employment_type,
            "Existing Loans or Debts": st.session_state.existing_loans,
            "Credit History Awareness": st.session_state.credit_history,
            "Interested Loan Type": st.session_state.loan_type,
            "Preferred Loan Amount": f"₹{st.session_state.loan_amount}",
            "Preferred Loan Tenure": st.session_state.repayment_tenure,
            "Interest Rate Sensitivity": st.session_state.interest_rate_sensitivity,
            "Loan Purpose": st.session_state.loan_purpose_details,
            "Urgency Level": st.session_state.urgency_level,
            "Collateral Availability": st.session_state.collateral_available,
            "Comfort with Variable Interest Rates": st.session_state.variable_interest,
            "Preferred Repayment Option": st.session_state.repayment_option,
            "Open to Insurance Plans": st.session_state.insurance_option,
        }

        with st.spinner("Generating your personalized recommendation..."):
            recommendation = generate_personalized_recommendation(responses)
        st.write(recommendation)
        st.balloons()

        if st.button("Start Over"):
            st.session_state.clear()
            st.experimental_rerun()

def main():
    get_user_profile()

if __name__ == "__main__":
    main()
