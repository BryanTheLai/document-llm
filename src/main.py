import streamlit as st
from litellm import completion
from dotenv import load_dotenv
import os
from app.prompts import SystemPrompt

# Load environment variables from .env file
load_dotenv()

# Retrieve Google API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize session state for chat messages
if "messages" not in st.session_state:
    # Create a system prompt using the SystemPrompt class
    system_prompt_content = SystemPrompt("").system_prompt()
    # Initialize messages list with the system prompt
    st.session_state.messages = [{"role": "system", "content": system_prompt_content}]


# Function to display chat messages with role-based styling
def display_message(role: str, content: str):
    with st.chat_message(role):
        st.markdown(content)


# Display existing chat history from session state
for message in st.session_state.messages:
    if message["role"] != "system":  # Skip displaying the system prompt
        display_message(message["role"], message["content"])

# Get user input
prompt = st.chat_input("Whats on your mind today?")

# Process user input if provided
if prompt:
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    display_message("user", prompt)

    # Generate and display the assistant's response
    try:
        # Create a placeholder for the streaming response
        message_placeholder = st.empty()
        # Initialize an empty string to store the full response
        full_response = ""
        # Call the completion API with streaming enabled
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        # Iterate over the streaming response
        for part in response:
            # Append the content from the streaming response to the full response
            full_response += part.choices[0].delta.content or ""
            # Update the message placeholder with the current full response
            message_placeholder.markdown(full_response + "...")
        # Display the final response
        message_placeholder.markdown(full_response)

        # Store the full response for use later
        gemini_response = full_response

        # Add assistant message to session state
        st.session_state.messages.append({"role": "assistant", "content": gemini_response})
        # Display assistant message
        display_message("assistant", gemini_response)
    except Exception as e:
        # Display an error message if something goes wrong
        st.error(f"An error occurred: {e}")