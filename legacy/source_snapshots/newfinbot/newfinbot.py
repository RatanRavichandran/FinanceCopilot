import autogen
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuration for LLM
# Setting configurations for autogen
config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST.json",
    file_location=r"C:\Users\Ratan\Desktop\newfinbot",
    filter_dict={
        "model": {
            "gpt-4o-mini",
        }
    }
)

config_list
llm_config = {
    "config_list": config_list,
    "cache_seed": 42
}

# Define the agents
user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="A human admin.",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "groupchat",
        "use_docker": False,
    },
    human_input_mode="NEVER",
)

coder = autogen.AssistantAgent(
    name="Coder",
    llm_config=llm_config,
)

critic = autogen.AssistantAgent(
    name="Critic",
    system_message="""Critic. You are a knowledgeable assistant with expertise in assessing the quality of visualization code. Your task is to provide a score from 1 (poor) to 10 (excellent) for each evaluation, along with a clear rationale. You must adhere to visualization best practices in your assessments. Specifically, evaluate the code across the following dimensions:

- Bugs (bugs): Are there any bugs, logic errors, syntax errors, or typos? Could the code fail to execute? How should these issues be resolved? If any bug exists, the bug score must be less than 5.
- Data Transformation (transformation): Is the data appropriately transformed for the visualization type? For example, is the dataset correctly filtered, aggregated, or grouped as needed? If a date field is used, is it converted to a date object?
- Goal Compliance (compliance): How well does the code meet the specified visualization goals?
- Visualization Type (type): Considering best practices, is the chosen visualization type suitable for the data and intent? Is there a more effective visualization type for conveying insights? If a different type is more appropriate, the score must be less than 5.
- Data Encoding (encoding): Is the data encoded correctly for the visualization type?
- Aesthetics (aesthetics): Are the aesthetics appropriate for the visualization type and the data?

You must provide a score for each of the above dimensions.
{bugs: 0, transformation: 0, compliance: 0, type: 0, encoding: 0, aesthetics: 0}
Do not suggest code.
Finally, based on your critique, suggest a concrete list of actions that the coder should take to improve the code.
""",
)

# Create a group chat with the agents
groupchat = autogen.GroupChat(agents=[user_proxy, coder, critic], messages=[], max_round=20)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Load the data
file_path = "pft.xlsx"
personal_expenses = pd.read_excel(file_path)

# Define a function to initiate the chat
def initiate_chat():
    user_proxy.initiate_chat(
        manager,
        message="""Hello, I would like to analyze my financial data and receive suggestions for appropriate visualizations. To assist you better, here are some details about the dataset:

Type of Financial Data: The dataset includes information on personal expenses, such as debit amounts, transaction types, and categories of spending.
Data Structure: The data is stored in an Excel file format, with columns for transaction date, debit amount, category, and business name.
Focus Areas: I am particularly interested in identifying spending trends over time, comparing spending across different categories, and detecting any unusual spending patterns.
Please analyze the dataset with these details in mind and suggest visualizations that can effectively communicate the insights.

find the dataset at "pft.xlsx" """,
    )

# Streamlit interface
st.title("Financial Data Analysis with Multi-Agent System")

if st.button("Start Analysis"):
    initiate_chat()

# Display the chat messages
for message in manager.groupchat.messages:
    st.write(f"{message['role'].capitalize()}: {message['content']}")

