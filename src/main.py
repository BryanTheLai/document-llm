import streamlit as st
from litellm import completion
from dotenv import load_dotenv
import os
from app.prompts import SystemPrompt

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Function to display chat messages with role-based styling
def display_message(role: str, content: str):
    with st.chat_message(role):
        st.markdown(content)

# Initialize session state for chat messages
if "messages" not in st.session_state:
    system_prompt_content = SystemPrompt("").system_prompt()
    
    # Initialize messages list with system prompt
    st.session_state.messages = [{"role": "system", "content": system_prompt_content}]

# Display existing chat history from session state
for message in st.session_state.messages:
    if message["role"] != "system":  # Skip displaying system prompt
        display_message(message["role"], message["content"])

# Get user input
prompt = st.chat_input("Ask something...")

# Process user input if provided
if prompt:
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    display_message("user", prompt)

    # Generate and display  assistant's response
    try:
        # Create a placeholder for  streaming response
        message_placeholder = st.empty()
        # Initialize an empty string to store  full response
        full_response = ""
        # Call  completion API with streaming enabled
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[
                {"role": m["role"], "content": m["content"], }
                for m in st.session_state.messages
            ],
            stream=True,
            #temperature=0.9,
            
        )
        # Iterate streaming response
        for part in response:
            # Append content from streaming response to full response
            full_response += part.choices[0].delta.content or ""
            # Update message placeholder with current full response
            message_placeholder.markdown(full_response)
  

        # Add to session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    except Exception as e:
        # Display error if something goes wrong
        st.error(f"An error occurred: {e}")