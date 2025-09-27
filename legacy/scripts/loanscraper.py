import requests
from bs4 import BeautifulSoup
import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to extract text from a webpage
def extract_text_from_webpage(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

def call_openai_gpt_api(chunk):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": chunk}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# Main function to process a webpage and save the output
def process_webpage(url, output_file):
    # Step 1: Extract text
    text = extract_text_from_webpage(url)
    
    # Step 2: Call OpenAI API on the entire text
    response = call_openai_gpt_api(text)
    
    # Step 3: Save output to a document
    with open(output_file, 'w') as file:
        file.write(response)
    print(f'Output saved to {output_file}')

# Example usage
url = 'https://www.tvscredit.com/loans/two-wheeler-loans/'
output_file = 'output_document.txt'
process_webpage(url, output_file)





