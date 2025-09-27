import streamlit as st
import openai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import PyPDF2
import re
import pdfplumber
from PIL import Image

# Set up OpenAI API
openai.api_key = ''
# Set up Presidio analyzer and anonymizer
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def post_process_text(text):
    """Post-processes text to clean fragmented sentences."""
    processed_text = re.sub(r'(?<!\.)\n', ' ', text)  # Replace newlines that aren't after periods with space
    processed_text = re.sub(r'\s+', ' ', processed_text)  # Normalize excessive spaces
    return processed_text.strip()

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text() or ''
    
    return post_process_text(text)

def display_pdf(uploaded_file, col):
    with pdfplumber.open(uploaded_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            pdf_image = page.to_image()
            img = pdf_image.original
            col.image(img, caption=f"Page {page_num + 1}", use_column_width=True)


def anonymize_text(text):
    analyzer_results = analyzer.analyze(text=text, language="en")
    anonymized_text = anonymizer.anonymize(
        text=text,
        analyzer_results=analyzer_results
    ).text
    return anonymized_text


def summarize_contract(contract):
    prompt = f""""Please summarize the following AONYMIZED contract, focusing on the essential details. I need to understand the core obligations and rights of each party involved.

Specifically, I'm interested in:

Parties: Who are the parties involved in the contract?
Effective Date: When does the contract come into effect?
Scope of Services/Goods: What exactly is being provided or exchanged?
Payment Terms: How much is to be paid, and according to what schedule?
Term and Termination: How long does the contract last, and under what conditions can it be terminated?
Confidentiality: Are there any confidentiality obligations?
Liability: What are the limitations of liability?
Governing Law: Which jurisdiction's law governs the contract?
MAKE SURE TO IGNORE THE ANONYMITY.
Please present the summary in a clear and concise manner, using bullet points or a table where appropriate. If there are any crucial clauses or unusual terms, please highlight those as well.\n\n{contract}"""


    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes legal contracts in simple terms."},
            {"role": "user", "content": prompt}
        ]
    )
    summary = response.choices[0].message.content.strip()
    return summary

def chat_with_contract(contract):
    """Chat interface for querying the contract using GPT-4."""
    prompt = f"You are a legal assistant that helps users understand the following contract:\n\n{contract}\n\nPlease answer the user's questions about the contract."
    
    st.session_state.messages = [{"role": "system", "content": prompt}]
    
    user_input = st.text_input("Ask a question about the contract:")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        assistant_response = response.choices[0].message.content.strip()
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        st.write(assistant_response)

def main():
    st.set_page_config(page_title="Loan Agreement Summarizer & Assistant", layout="wide")
    
    st.title("📄Loan Agreement Summarizer & Assistant")
    
    uploaded_file = st.file_uploader("Upload a contract (PDF or TXT)")
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1.5])  # Adjusted column width

        with col1:
            if uploaded_file.type == "application/pdf":
                st.subheader("Contract PDF")
                display_pdf(uploaded_file, col1)
                raw_text = extract_text_from_pdf(uploaded_file)  # Extract the text for processing
            elif uploaded_file.type == "text/plain":
                raw_text = uploaded_file.read().decode("utf-8")
            else:
                st.warning("Please upload a PDF or TXT file.")
                return

        anonymized_text = anonymize_text(raw_text)
        summary = summarize_contract(anonymized_text)

        with col2:
            st.subheader("Contract Summary")
            st.write(summary)
            st.markdown("***")
            st.subheader("Contract Assistant")
            chat_with_contract(anonymized_text)

if __name__ == "__main__":
    main()