import streamlit as st
from litellm import completion
from dotenv import load_dotenv
import os
from app.prompts import SystemPrompt
from app.utils import PDFProcessor
import tempfile


# Configuration Section
MODEL_OPTIONS = {
    "Gemini 1.5 Flash 8b": "gemini/gemini-1.5-flash-8b",
    "Gemini 1.5 Flash": "gemini/gemini-1.5-flash-001",
    "Gemini 1.5 Pro": "gemini-1.5-pro",
    "*Gemini 2.0 Flash Lite": "gemini/gemini-2.0-flash-lite-preview-02-05",
    "Gemini 2.0 Flash": "gemini/gemini-2.0-flash-001",
    "*Gemini 2.0 Pro": "gemini/gemini-2.0-pro-exp-02-05",
    "Deepseek-R1 1.5B": "ollama/deepseek-r1:1.5b",
}


# Streamlit page configuration
st.set_page_config(page_title="Chat with Document", page_icon="📄")


# Function to display chat messages with role-based styling
def display_message(role: str, content: str):
    """Displays chat messages in Streamlit chat interface with role-based styling."""
    with st.chat_message(role):
        st.markdown(content)


def generate_llm_response(
    model: str, messages: list[dict[str, str]], api_key: str | None = None
) -> str:
    """
    Generates a response from a language model using LiteLLM completion API.

    Args:
        model: The name of the language model to use.
        messages: A list of message dictionaries for the conversation history.
        api_key: The API key for the language model provider (optional for Ollama).

    Returns:
        The full response from the language model as a string.
    """
    full_response = ""
    message_placeholder = st.empty()
    try:
        response = completion(
            model=model,
            api_key=api_key,
            messages=messages,
            stream=True,
        )
        for part in response:
            chunk = part.choices[0].delta.content or ""
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")  # Add a streaming cursor
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""  # Return empty string in case of error
    message_placeholder.markdown(full_response)  # Final response without cursor
    return full_response


def process_pdf_document(uploaded_file) -> str:
    """
    Processes an uploaded PDF document, extracts text, and handles temporary file management.

    Args:
        uploaded_file: The uploaded PDF file object from Streamlit.

    Returns:
        The extracted text content from the PDF, or an empty string if processing fails.
    """
    pdf_processor = PDFProcessor()  # Initialize processor here, function scope
    document_text = ""
    if uploaded_file is not None:
        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_file_path = tmp_file.name  # Get the temporary file path

        # Extract text from PDF using PDFProcessor
        document_text = pdf_processor.pdf_to_text(pdf_file_path)

        if document_text:
            st.success("Document uploaded and processed successfully!")
            st.markdown("Preview of document content:")
            st.markdown(f"> {document_text[:200]}...")  # Display a snippet of the document
        else:
            st.error(
                "Failed to extract text from the document. Document might contain images or be corrupted."
            )

        os.remove(pdf_file_path)  # Clean up temporary file after processing
    return document_text


# Initialize session state variables
if "messages" not in st.session_state:
    # Initialize chat messages history with system prompt
    system_prompt_content = SystemPrompt("").system_prompt()
    st.session_state.messages = [{"role": "system", "content": system_prompt_content}]

if "document_text" not in st.session_state:
    # Initialize document text storage
    st.session_state.document_text = ""

# Display chat history from session state
for message in st.session_state.messages:
    if message["role"] != "system":  # Do not display system prompt in chat history
        display_message(message["role"], message["content"])

# Sidebar for API Key Input
with st.sidebar:
    selected_model_name = st.selectbox("Choose a Model:", list(MODEL_OPTIONS.keys()))
    selected_model = MODEL_OPTIONS[selected_model_name]

    google_api_key = st.text_input(
        "Enter your Google API Key:",
        type="password",  # Mask the input for security
        help="Create your API key at (https://aistudio.google.com/apikey). Important: Use your personal account, not school account.",
        disabled=selected_model.startswith("ollama"),  # Disable for Ollama models
    )

    if not google_api_key and selected_model.startswith("gemini"):
        st.warning("⚠️ Google API key is required for Gemini models.")


# App description
st.markdown(
    """
    *Ask questions about the content of your uploaded PDF document, or just chat!
    Powered by Gemini and LiteLLM.*
    """
)

# Document upload section
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file is not None:
    document_text = process_pdf_document(uploaded_file)
    if document_text:
        st.session_state.document_text = document_text  # Store extracted text in session state


# Chat input section
prompt = st.chat_input("Ask something...")

if prompt:
    # Prepare user message and display it
    user_message_content = prompt
    st.session_state.messages.append({"role": "user", "content": user_message_content})
    display_message("user", user_message_content)

    full_response = generate_llm_response(
        selected_model,
        st.session_state.messages,
        google_api_key if selected_model.startswith("gemini") else None,
    )
    if full_response:  # Only append if response is not empty (error case)
        st.session_state.messages.append({"role": "assistant", "content": full_response})