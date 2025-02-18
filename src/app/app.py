import time
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from llm.prompts import SystemPrompt
from utils.PDFProcessor import PDFProcessor
import tempfile

st.set_page_config(page_title="Chat with Document", page_icon="📄")


# Gemini model configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Gemini Model Options - Constants for model names improve readability and maintainability
model_options = {
    "Gemini 1.5 Flash 8b": "gemini-1.5-flash-8b", # Constant Model Name
    "Gemini 1.5 Flash": "gemini-1.5-flash-001", # Constant Model Name
    "Gemini 1.5 Pro": "gemini-1.5-pro",       # Constant Model Name
    "*Gemini 2.0 Flash Lite": "gemini/gemini-2.0-flash-lite-preview-02-05", # Constant Model Name
    "Gemini 2.0 Flash": "gemini/gemini-2.0-flash-001", # Constant Model Name
    "*Gemini 2.0 Pro": "gemini/gemini-2.0-pro-exp-02-05", # Constant Model Name
}


def initialize_gemini_model(selected_model_name: str) -> genai.GenerativeModel:
    """Initializes and returns a Gemini GenerativeModel."""
    return genai.GenerativeModel(
        model_name=selected_model_name,
        generation_config=generation_config,
    )


def configure_google_api(google_api_key: str) -> None:
    """Configures the Google Generative AI API with the provided API key."""
    genai.configure(api_key=google_api_key)


def setup_sidebar() -> tuple[str, str]:
    """Sets up the sidebar with model selection and API key input.

    Returns:
        tuple[str, str]: Selected model name and the entered Google API key.
    """
    model_display_name = st.selectbox("Choose a Model:", list(model_options.keys())) # More descriptive name
    selected_model_name = model_options[model_display_name] # Get the actual model name

    google_api_key = st.text_input(
        "Enter your Google API Key:",
        type="password",
        help="Create your API key at (https://aistudio.google.com/apikey). Use personal account, not school account.",
    )
    if not google_api_key: # Simple check for API key
        st.warning("⚠️ Google API key is required for Gemini models.")

    return selected_model_name, google_api_key


def display_chat_message(role: str, content: str) -> None:
    """Displays chat messages in the Streamlit chat interface with role-based styling."""
    with st.chat_message(role):
        st.markdown(content)


def initialize_session_state() -> None:
    """Initializes necessary session state variables for chat messages, document text, and chat session."""
    if "messages" not in st.session_state:
        system_prompt_content = SystemPrompt("").system_prompt()
        st.session_state.messages = [{"role": "system", "content": system_prompt_content}]

    if "document_text" not in st.session_state:
        st.session_state.document_text = ""

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = None


def display_chat_history() -> None:
    """Displays chat history from session state, excluding the system prompt."""
    for message in st.session_state.messages:
        if message["role"] != "system":
            display_chat_message(message["role"], message["content"])


def initialize_chat_session(api_key: str, selected_model_name: str) -> genai.ChatSession:
    """Initializes and returns a new chat session with the Gemini model."""
    configure_google_api(api_key)
    model = initialize_gemini_model(selected_model_name)
    return model.start_chat(history=[])


def process_pdf_upload() -> None:
    """Handles PDF document uploads, extracts text, and updates session state."""
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_file_path = tmp_file.name

        pdf_processor = PDFProcessor()
        document_text = pdf_processor.pdf_to_text(pdf_file_path)

        if document_text:
            st.session_state.document_text = document_text
            st.success("Document uploaded and processed successfully!")
            st.markdown("Preview of document content:")
            st.markdown(f"> {document_text[:200]}...")
        else:
            st.error(
                "Failed to extract text. Document might contain images or be corrupted."
            )
        os.remove(pdf_file_path)


def handle_user_prompt(prompt: str) -> None:
    """Handles user chat input, generates model response, and updates chat history.

    Args:
        prompt (str): User's chat input prompt.
    """
    user_message_content = prompt
    st.session_state.messages.append({"role": "user", "content": user_message_content})

    if st.session_state.chat_session is None:
        st.error("Please enter your Google API key in the sidebar to start chatting.")
        st.stop()

    display_chat_message("user", user_message_content)

    chat_session: genai.ChatSession = st.session_state.chat_session # type: ignore # Ensuring chat_session is not None
    input_token_count_request = chat_session.model.count_tokens(user_message_content)
    input_token_count = input_token_count_request.total_tokens

    message_placeholder = st.empty()
    full_response = ""

    try:
        if st.session_state.document_text: # Check if document text exists to provide context
            context_document = st.session_state.document_text
            user_prompt_with_context = (
                f"Context Document:\n{context_document}\n\nUser Query: {prompt}"
            )
            user_message_content = user_prompt_with_context
            input_token_count_request = chat_session.model.count_tokens(user_message_content)
            input_token_count = input_token_count_request.total_tokens

        gemini_response = chat_session.send_message(
            user_message_content, stream=True
        )

        for chunk in gemini_response:
            chunk_text = chunk.text
            full_response += chunk_text
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

        output_token_count: int = gemini_response.usage_metadata.candidates_token_count if gemini_response.usage_metadata else 0 # Token usage
        total_token_count: int = gemini_response.usage_metadata.total_token_count if gemini_response.usage_metadata else 0 # Total token count

        st.info(f"Input Tokens: {input_token_count} | Output Tokens: {output_token_count} | Total Tokens: {total_token_count}")

    except Exception as e:
        st.error(f"An error occurred: {e}")


def main() -> None:
    """Main function to set up and run the Streamlit chat application."""
    """Main function to run the Streamlit application."""

    st.markdown(
        """
        *Ask questions about your uploaded PDF document, or just chat!
        Powered by Google Gemini.*
        """
    )

    real_model_name, api_key = setup_sidebar()
    initialize_session_state()
    display_chat_history()

    if st.session_state.chat_session is None and api_key and real_model_name:
        st.session_state.chat_session = initialize_chat_session(api_key, real_model_name)

    process_pdf_upload()

    prompt = st.chat_input("Ask something...")
    if prompt:
        handle_user_prompt(prompt)


if __name__ == "__main__":
    main()