import streamlit as st
import openai
import json
import math
from googleapiclient.discovery import build  # YouTube API client
import re
import speech_recognition as sr
from gtts import gTTS, lang
import os
import tempfile
import base64
from deep_translator import GoogleTranslator
import pycountry

# Initialize OpenAI GPT-4 API key
openai.api_key = ''  # Replace with your actual OpenAI API key
YOUTUBE_API_KEY = ''  # Replace with your actual YouTube API key

# Function to translate text
def translate_text(text, target_language):
    try:
        translation = GoogleTranslator(source='auto', target=target_language).translate(text)
        return translation
    except Exception as e:
        return f"Translation Error: {e}"

# Function to recognize speech using the microphone
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            st.success("Recognized text: " + text)
            return text
        except sr.UnknownValueError:
            st.error("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
    return ""

# Function to speak text using gTTS and return the audio file path
def speak_text(text, language):
    if language not in lang.tts_langs():
        st.error(f"Language not supported: {language}")
        return None
    tts = gTTS(text=text, lang=language)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# Function to convert language name to ISO 639-1 code
def get_language_code(language_name):
    try:
        language = pycountry.languages.lookup(language_name)
        return language.alpha_2
    except LookupError:
        st.error(f"Language not recognized: {language_name}")
        return None

# Function to autoplay audio in Streamlit
def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

# Function to truncate content to fit within token limit
def truncate_text(text, max_tokens):
    truncated_text = text[:max_tokens]
    return truncated_text

# Function to estimate token count (approximation)
def estimate_token_count(text):
    return len(text.split())  # Rough estimate: 1 word = 1 token

# Function to load the user's profile from the uploaded file
def load_user_profile(profile_file):
    user_profile = profile_file.read().decode('utf-8')  # Decode bytes to string
    return user_profile

# Function to load the loans information from the uploaded file
def load_loans_info(loans_file):
    loans_info = loans_file.read().decode('utf-8')  # Decode bytes to string
    return loans_info

# Function to call OpenAI GPT-4 API to get loan details based on user's choice
def get_loan_info(user_profile, loans_info, loan_choice, language):
    prompt = f"""
    User Profile: {user_profile}
    Loans Information: {loans_info}
    
    The user is interested in the {loan_choice} loan from TVS Credit.
    Provide detailed information about this loan type, including benefits and limitations, and suggest any other relevant loans. Draw parallels to the user profile, at each step telling if this is a good fit for them. This needs to be Hyperpersonalized!!.
    In addition to the above, give me 3 personalized loan recommendations based on the user's profile and available loan information.
    Please provide the response in {language}.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a loan expert providing tailored advice and also recommendations."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

# YouTube search function
def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # Perform YouTube search
    search_response = youtube.search().list(
        q=query,
        part='snippet',
        maxResults=1,  # Get only the top result
        type='video'
    ).execute()

    if search_response['items']:
        video_id = search_response['items'][0]['id']['videoId']
        video_title = search_response['items'][0]['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_title, video_url
    else:
        return None, None

# Function to check if user query contains a request for YouTube video
def is_asking_for_video(user_input):
    # Check for common patterns like "video", "tutorial", "see", etc.
    video_request_keywords = ["video", "watch", "tutorial", "see"]
    return any(re.search(rf"\b{keyword}\b", user_input, re.IGNORECASE) for keyword in video_request_keywords)

# Function to suggest optimal loan parameters using AI
def get_optimal_loan_suggestion(user_profile, language):
    prompt = f"""
    User Profile: {user_profile}
    
    Based on the user's financial profile, suggest the optimal loan amount, tenure, and down payment. The suggestions should take into account the user's financial goals, income, and ability to repay comfortably.
    Don't make it too verbose, suggest a value first and a one line justification. Make it tabular.
    Please provide the response in {language}.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial expert providing personalized loan suggestions."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

# Function to calculate EMI
def calculate_emi(principal, annual_rate, tenure_years):
    monthly_rate = annual_rate / (12 * 100)
    tenure_months = tenure_years * 12
    emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
    return round(emi, 2)

# Streamlit UI
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
    # Read user profile and loans information from the same directory
    with open("user_profile.txt", "r", encoding="utf-8") as profile_file:
        user_profile = profile_file.read()

    with open("loans_info.txt", "r", encoding="utf-8") as loans_file:
        loans_info = loans_file.read()

except FileNotFoundError:
    st.error("One or both of the required files are missing. Please ensure 'user_profile.txt' and 'loans_info.txt' are in the same directory as this script.")
    user_profile = None
    loans_info = None

if user_profile and loans_info:
    # Create columns for layout
    col1, col2 = st.columns(2)

with col1:
    # Language selection for translation

    st.sidebar.header("Language Settings")
    language = st.sidebar.selectbox("Select Language", ["English", "Hindi", "Telugu", "Tamil", "Kannada", "Marathi"])
    language_codes = {
        "English": "en",
        "Hindi": "hi",
        "Telugu": "te",
        "Tamil": "ta",
        "Kannada": "kn",
        "Marathi": "mr"
    }
    target_language_code = language_codes[language]

    # Translate the radio button label and options
    input_method_label = translate_text("Select input method:", target_language_code)
    text_option = translate_text("Text", target_language_code)
    voice_option = translate_text("Voice", target_language_code)

    # Input method selection
    input_method = st.radio(input_method_label, (text_option, voice_option))

    # Translate the text input label
    loan_input_label = translate_text("Enter the loan type you're interested in:", target_language_code)

    # Input text and languages
    if input_method == text_option:
        loan_choice = st.text_input(loan_input_label)
    else:
        if st.button(translate_text("Record", target_language_code)):
            loan_choice = recognize_speech()
            st.session_state['recognized_text'] = loan_choice
        loan_choice = st.session_state.get('recognized_text', '')


    # Translate static text on the page
    st.subheader(translate_text("Loan Choice Input", target_language_code))
    st.write(translate_text("Please enter or record the type of loan you are interested in.", target_language_code))

    # Translate button
    if st.button(translate_text("Translate Loan Choice", target_language_code)):
        if loan_choice:
            translated_loan_choice = translate_text(loan_choice, target_language_code)
            st.subheader(translate_text("Translated Loan Choice:", target_language_code))
            st.write(translated_loan_choice)
            
            # Speak the translated text
            st.subheader(translate_text("Speaking the Translated Loan Choice:", target_language_code))
            audio_file_path = speak_text(translated_loan_choice, target_language_code)
            if audio_file_path:
                autoplay_audio(audio_file_path)
        else:
            st.error(translate_text("Please enter a loan choice.", target_language_code))

    # Call API only once when user clicks the button and save to session_state
    if st.button(translate_text("Get Loan Information", target_language_code)):
        st.session_state['loan_details'] = get_loan_info(user_profile, loans_info, loan_choice, language)
        st.session_state['loan_suggestion'] = get_optimal_loan_suggestion(user_profile, language)

    # Display the results from session_state (preserved between reruns)
    if st.session_state.get('loan_details'):
        st.subheader(translate_text("Loan Details:", target_language_code))
        translated_loan_details = translate_text(st.session_state['loan_details'], target_language_code)
        st.write(translated_loan_details)

        # TTS for loan details
        st.subheader(translate_text("Listen to Loan Details:", target_language_code))
        audio_file_path = speak_text(translated_loan_details, target_language_code)
        if audio_file_path:
            autoplay_audio(audio_file_path)

        st.subheader(translate_text("Your Suggested EMI", target_language_code))
        translated_loan_suggestion = translate_text(st.session_state['loan_suggestion'], target_language_code)
        st.write(translated_loan_suggestion)

        # TTS for loan suggestion
        st.subheader(translate_text("Listen to Loan Suggestion:", target_language_code))
        audio_file_path = speak_text(translated_loan_suggestion, target_language_code)
        if audio_file_path:
            autoplay_audio(audio_file_path)

    # EMI Calculator UI
    st.subheader(translate_text("EMI Calculator", target_language_code))

    # Use session_state to save EMI input values to persist them
    principal = st.number_input(translate_text("Loan Amount (in ₹):", target_language_code), min_value=1000, step=500, value=st.session_state.get('principal', 500000))
    annual_rate = st.slider(translate_text("Annual Interest Rate (in %):", target_language_code), min_value=1.0, max_value=20.0, step=0.1, value=st.session_state.get('annual_rate', 7.5))
    tenure_years = st.slider(translate_text("Loan Tenure (in years):", target_language_code), min_value=1, max_value=30, step=1, value=st.session_state.get('tenure_years', 15))

    # Store slider values in session_state to persist them
    st.session_state['principal'] = principal
    st.session_state['annual_rate'] = annual_rate
    st.session_state['tenure_years'] = tenure_years

    if st.button(translate_text("Calculate EMI", target_language_code)):
        emi = calculate_emi(principal, annual_rate, tenure_years)
        st.markdown(f"<h3 style='color:green;'>{translate_text('Your Monthly EMI:', target_language_code)} ₹{emi}</h3>", unsafe_allow_html=True)

with col2:
    # Chatbot section on the right side of the UI
    st.subheader(translate_text("Personalized Loan-Based Chatbot", target_language_code))

    # Display the video if available at the top of the chatbot section
    if st.session_state.get('video_url'):
        st.video(st.session_state['video_url'])  # Embed the video within the chatbot column

    user_message = st.text_input(translate_text("You:", target_language_code), key="user_message")

    if user_message:
        # Append user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        # If user asks for a video or tutorial, perform a YouTube search
        if is_asking_for_video(user_message):
            video_title, video_url = search_youtube(f"TVS Credit {loan_choice} loan tutorial")
            if video_title and video_url:
                bot_reply = f"I found a relevant video for you: {video_title}."
                st.session_state['video_url'] = video_url 
                st.video(st.session_state['video_url'])  # Embed the video within the chatbot column
            else:
                bot_reply = "Sorry, I couldn't find any relevant videos."
                st.session_state['video_url'] = None  # Clear the video URL if no video found
        else:
            # Generate response from OpenAI API using chat history for context maintenance
            response_chatbot = openai.chat.completions.create(
                model="gpt-4o",
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

        # Translate bot reply
        translated_bot_reply = translate_text(bot_reply, target_language_code)

        # Append bot reply to chat history for context maintenance
        st.session_state.chat_history.append({"role": "assistant", "content": translated_bot_reply})

        # TTS for bot reply
        st.subheader(translate_text("Listen to Assistant's Reply:", target_language_code))
        audio_file_path = speak_text(translated_bot_reply, target_language_code)
        if audio_file_path:
            autoplay_audio(audio_file_path)

    # Display chat history
    for message in reversed(st.session_state.chat_history):
        if message["role"] == "user":
            st.write(f"**{translate_text('You', target_language_code)}**: {message['content']}")
        else:
            st.write(f"**{translate_text('Assistant', target_language_code)}**: {message['content']}")

