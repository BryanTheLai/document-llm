import streamlit as st
from litellm import completion
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

st.title("Simple Gemini Chatbot with History")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Chat message display function
def display_message(role: str, content: str):
    with st.chat_message(role):
        st.markdown(content)


# Display chat history
for message in st.session_state.messages:
    display_message(message["role"], message["content"])

# Handle user input
if prompt := st.chat_input("What is up?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    display_message("user", prompt)

    # Get and display Gemini response
    try:
        response = completion(model="gemini/gemini-2.0-flash", messages=[{"content": prompt, "role": "user"}])
        gemini_response = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": gemini_response})
        display_message("assistant", gemini_response)
    except Exception as e:
        st.error(f"An error occurred: {e}")