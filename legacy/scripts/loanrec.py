import streamlit as st
import openai
import json
import math
from googleapiclient.discovery import build  # YouTube API client
import re

openai.api_key = ''  # Replace with your actual OpenAI API key
YOUTUBE_API_KEY = ''  # Replace with your actual YouTube API key


def truncate_text(text, max_tokens):
    truncated_text = text[:max_tokens]
    return truncated_text

def estimate_token_count(text):
    return len(text.split())  # Rough estimate: 1 word = 1 token

def load_user_profile(profile_file):
    user_profile = profile_file.read().decode('utf-8')  
    return user_profile

def load_loans_info(loans_file):
    loans_info = loans_file.read().decode('utf-8')  
    return loans_info

def get_loan_info(user_profile, loans_info, loan_choice):
    prompt = f"""
    User Profile: {user_profile}
    Loans Information: {loans_info}
    
    The user is interested in the {loan_choice} loan from TVS Credit.
    Provide detailed information about this loan type, including benefits and limitations, and suggest any other relevant loans. Draw paralells to the user profile, at each step telling if this is a good fit for them. This needs to be Hyperpersonalized!!.
    In addition to the above, give me 3 personalized loan recommendations based on the user's profile and available loan information.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a loan expert providing tailored advice and also recommendations."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()


def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    search_response = youtube.search().list(
        q=query,
        part='snippet',
        maxResults=1, 
        type='video'
    ).execute()

    if search_response['items']:
        video_id = search_response['items'][0]['id']['videoId']
        video_title = search_response['items'][0]['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_title, video_url
    else:
        return None, None

def is_asking_for_video(user_input):
    video_request_keywords = ["video", "watch", "tutorial", "see"]
    return any(re.search(rf"\b{keyword}\b", user_input, re.IGNORECASE) for keyword in video_request_keywords)


def get_optimal_loan_suggestion(user_profile):
    prompt = f"""
    User Profile: {user_profile}
    
    Based on the user's financial profile, suggest the optimal loan amount, tenure, and down payment. The suggestions should take into account the user's financial goals, income, and ability to repay comfortably.
    Don't make it too verbose, suggest a value first and a one line justification. Make it tabular.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial expert providing personalized loan suggestions."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

def calculate_emi(principal, annual_rate, tenure_years):
    monthly_rate = annual_rate / (12 * 100)
    tenure_months = tenure_years * 12
    emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
    return round(emi, 2)

st.set_page_config(page_title="Hyperpersonalized Pre-Loan Support Bot", layout="wide")
st.title("Hyperpersonalized Loan Assistance")

# Use session state to avoid rerunning heavy computations unnecessarily
if 'loan_details' not in st.session_state:
    st.session_state['loan_details'] = ""
if 'loan_suggestion' not in st.session_state:
    st.session_state['loan_suggestion'] = ""
if 'chat_history' not in st.session_state:
     st.session_state['chat_history'] = []

try:
    with open("user_profile.txt", "r", encoding="utf-8") as profile_file:
        user_profile = profile_file.read()

    with open("loans_info.txt", "r", encoding="utf-8") as loans_file:
        loans_info = loans_file.read()

except FileNotFoundError:
    st.error("One or both of the required files are missing. Please ensure 'user_profile.txt' and 'loans_info.txt' are in the same directory as this script.")
    user_profile = None
    loans_info = None
if profile_file and loans_file:

    col1, col2 = st.columns(2)

    with col1:
        loan_choice = st.text_input("Enter the loan type you're interested in:")

        if st.button("Get Loan Information"):
            st.session_state['loan_details'] = get_loan_info(user_profile, loans_info, loan_choice)
            st.session_state['loan_suggestion'] = get_optimal_loan_suggestion(user_profile)

        if st.session_state.get('loan_details'):
            st.subheader("Loan Details:")
            st.write(st.session_state['loan_details'])

            st.subheader("Your Suggested EMI")
            st.write(st.session_state['loan_suggestion'])

        st.subheader("EMI Calculator")

        principal = st.number_input("Loan Amount (in ₹):", min_value=1000, step=500, value=st.session_state.get('principal', 500000))
        annual_rate = st.slider("Annual Interest Rate (in %):", min_value=1.0, max_value=20.0, step=0.1, value=st.session_state.get('annual_rate', 7.5))
        tenure_years = st.slider("Loan Tenure (in years):", min_value=1, max_value=30, step=1, value=st.session_state.get('tenure_years', 15))

        st.session_state['principal'] = principal
        st.session_state['annual_rate'] = annual_rate
        st.session_state['tenure_years'] = tenure_years

        if st.button("Calculate EMI"):
            emi = calculate_emi(principal, annual_rate, tenure_years)
            st.markdown(f"<h3 style='color:green;'>Your Monthly EMI: ₹{emi}</h3>", unsafe_allow_html=True)

    with col2:
        st.subheader("Personalized Loan-Based Chatbot")

        if st.session_state.get('video_url'):
            st.video(st.session_state['video_url'])  

        user_message = st.text_input("You:", key="user_message")

        if user_message:
            st.session_state.chat_history.append({"role": "user", "content": user_message})

            if is_asking_for_video(user_message):
                video_title, video_url = search_youtube(f"TVS Credit {loan_choice} loan tutorial")
                if video_title and video_url:
                    bot_reply = f"I found a relevant video for you: {video_title}."
                    st.session_state['video_url'] = video_url 
                    st.video(st.session_state['video_url'])  
                else:
                    bot_reply = "Sorry, I couldn't find any relevant videos."
                    st.session_state['video_url'] = None  # Clear the video URL if no video found
            else:
                response_chatbot = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": """You are a knowledgeable assistant specializing in providing personalized information about loans. 
                        Your responses should be detailed, accurate, and most importantly hyperpersonalized and tailored to the user's specific needs and questions. 
                        When providing information, please ensure that you explain any technical terms or concepts in a clear and understandable manner. Additionally, feel free to offer tips and advice to help users make informed decisions about their loan options."""},
                        {"role": "system", "content": f"Loans Information: {loans_info}, User Profile: {user_profile}"}
                    ] + st.session_state.chat_history,
                    max_tokens=600,
                    n=1,
                    stop=None,
                    temperature=0.7,
                )

                bot_reply = response_chatbot.choices[0].message.content.strip()
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
        for message in reversed(st.session_state.chat_history):
            if message["role"] == "user":
                st.write(f"**You**: {message['content']}")
            else:
                st.write(f"**Assistant**: {message['content']}")
