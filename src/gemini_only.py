# test.py
import time
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from app.prompts import SystemPrompt # Ensure app.prompts is correctly implemented as in main.py
from app.utils import PDFProcessor # Ensure app.utils is correctly implemented as in main.py
import tempfile

# # Load environment variables from .env file
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # Configure Google Gemini API - API Key is configured later based on user input, but we can configure globally too initially.
# genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Model Options - Keeping only Gemini models, like main.py but adapted for google.generativeai model names
model_options = {
    "Gemini 1.5 Flash 8b": "gemini-1.5-flash-8b", # Model names might need exact match, check google.generativeai docs
    "Gemini 1.5 Flash": "gemini-1.5-flash-001",
    "Gemini 1.5 Pro": "gemini-1.5-pro",
    "*Gemini 2.0 Flash Lite": "gemini/gemini-2.0-flash-lite-preview-02-05", # Model names might need exact match
    "Gemini 2.0 Flash": "gemini/gemini-2.0-flash-001", # Model names might need exact match
    "*Gemini 2.0 Pro": "gemini/gemini-2.0-pro-exp-02-05", # Model names might need exact match
}


def initialize_model(selected_model_name: str) -> genai.GenerativeModel:
    """Initializes the Gemini model based on the selected model name."""
    return genai.GenerativeModel(
        model_name=selected_model_name,
        generation_config=generation_config,
    )

# Initialize PDF Processor
pdf_processor = PDFProcessor()

# Streamlit page configuration
st.set_page_config(page_title="Chat with Document", page_icon="📄")

# App description
st.markdown(
    """
    *Ask questions about the parts of your uploaded PDF document, or just chat!
    Powered by Google Gemini.*
    """
)

# Sidebar for API Key and Model Selection - Consistent with main.py sidebar
with st.sidebar:
    selected_model_name = st.selectbox("Choose a Model:", list(model_options.keys()))
    selected_model_real_name = model_options[selected_model_name] # Get the actual model name for google.generativeai

    google_api_key = st.text_input(
        "Enter your Google API Key:",
        type="password",
        help="Create your API key at (https://aistudio.google.com/apikey). Important: Use your personal account, not school account.",
    )
    if not google_api_key:
        st.warning("⚠️ Google API key is required for Gemini models.")
    else:
        genai.configure(api_key=google_api_key)

# Function to display chat messages with role-based styling
def display_message(role: str, content: str): # Renamed 'parts' to 'content' for consistency
    """Displays chat messages in Streamlit chat interface with role-based styling."""
    with st.chat_message(role):
        st.markdown(content)
# Initialize session state variables
if "messages" not in st.session_state:
    # Initialize chat messages history with system prompt
    system_prompt_content = SystemPrompt("").system_prompt() # Ensure SystemPrompt is correctly implemented as in main.py
    st.session_state.messages = [{"role": "system", "content": system_prompt_content}] # Use 'content' here

if "document_text" not in st.session_state:
    # Initialize document text storage
    st.session_state.document_text = ""

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None # Initialize to None, will be created when model is selected and API key is available

# Display chat history from session state
for message in st.session_state.messages:
    if message["role"] != "system":  # Do not display system prompt in chat history
        display_message(message["role"], message["content"]) # Use 'content' here

if st.session_state.chat_session is None and google_api_key and selected_model_real_name:
    genai.configure(api_key=google_api_key) # Configure API key here, after user input in sidebar
    model = initialize_model(selected_model_real_name) # Initialize model after API key is configured and model name selected
    st.session_state.chat_session = model.start_chat(history=[]) # Start new chat session only when model is initialized


# Document upload section
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_file_path = tmp_file.name  # Get the temporary file path

    # Extract text from PDF using PDFProcessor
    document_text = pdf_processor.pdf_to_text(pdf_file_path)

    if document_text:
        st.session_state.document_text = document_text  # Store extracted text in session state
        st.success("Document uploaded and processed successfully!")
        st.markdown("Preview of document content:") # Changed 'parts' to 'content'
        st.markdown(f"> {document_text[:200]}...")  # Display a snippet of the document
    else:
        st.error(
            "Failed to extract text from the document. Document might contain images or be corrupted."
        )

    os.remove(pdf_file_path)  # Clean up temporary file after processing

# Chat input section
prompt = st.chat_input("Ask something...")

if prompt:
    # Prepare user message and display it
    user_message_content = prompt
    st.session_state.messages.append({"role": "user", "content": user_message_content}) # Use 'content' here

    if st.session_state.chat_session is None:
        st.error("Please enter your Google API key in the sidebar to start chatting.")
        st.stop()

    display_message("user", user_message_content)

     # Calculate token count for user message - moved here after API key check
    input_token_count_request = st.session_state.chat_session.model.count_tokens(user_message_content) # Use model from chat_session
    input_token_count = input_token_count_request.total_tokens


    # Initialize placeholder for streaming response
    message_placeholder = st.empty()
    full_response = ""

    try:
        # Prepare context-aware prompt for the LLM only if document_text is available
        if st.session_state.document_text:
            context_document = st.session_state.document_text
            user_prompt_with_context = (
                f"Context Document:\n{context_document}\n\nUser Query: {prompt}"
            )
            user_message_content = user_prompt_with_context  # Use context-aware prompt
             # Recalculate token count for context-aware prompt
            input_token_count_request = st.session_state.chat_session.model.count_tokens(user_message_content) # Use model from chat_session
            input_token_count = input_token_count_request.total_tokens


        gemini_response = st.session_state.chat_session.send_message(
            user_message_content, stream=True
        )

        # Stream and display model response
        for chunk in gemini_response:
            chunk_text = chunk.text
            full_response += chunk_text
            message_placeholder.markdown(full_response)

        # Store model response in session state
        st.session_state.messages.append({"role": "assistant", "content": full_response}) # Changed 'model' to 'assistant' and 'parts' to 'content'

        # Display token counts after response is generated
        output_token_count: int = gemini_response.usage_metadata.candidates_token_count if gemini_response.usage_metadata else 0
        total_token_count: int = gemini_response.usage_metadata.total_token_count if gemini_response.usage_metadata else 0

        st.info(f"Input Tokens: {input_token_count} | Output Tokens: {output_token_count} | Total Tokens: {total_token_count}")


    except Exception as e:
        st.error(f"An error occurred: {e}")  # Display error message if exception occurs