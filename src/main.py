# main.py
import streamlit as st
from litellm import completion
from dotenv import load_dotenv
import os
from app.prompts import SystemPrompt  # Assuming prompts.py is in 'app' folder
from app.utils import PDFProcessor  # Import PDFProcessor from utils.py
import tempfile

# Load environment variables from .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize PDF Processor
pdf_processor = PDFProcessor()

# Streamlit page configuration
st.set_page_config(page_title="Chat with Document", page_icon="📄")

# App description
st.markdown(
    """
    *Ask questions about the content of your uploaded PDF document, or just chat!
    Powered by Gemini and LiteLLM.*
    """
)

# Function to display chat messages with role-based styling
def display_message(role: str, content: str):
    """Displays chat messages in Streamlit chat interface with role-based styling."""
    with st.chat_message(role):
        st.markdown(content)

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

# Document upload section
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_file_path = tmp_file.name # Get the temporary file path

    # Extract text from PDF using PDFProcessor
    document_text = pdf_processor.pdf_to_text(pdf_file_path)

    if document_text:
        st.session_state.document_text = document_text # Store extracted text in session state
        st.success("Document uploaded and processed successfully!")
        st.markdown("Preview of document content:")
        st.markdown(f"> {document_text[:200]}...") # Display a snippet of the document
    else:
        st.error("Failed to extract text from the document. Document might contain images or be corrupted.")

    os.remove(pdf_file_path) # Clean up temporary file after processing

# Chat input section
prompt = st.chat_input("Ask something...")

if prompt:
    # Prepare user message and display it
    user_message_content = prompt
    st.session_state.messages.append({"role": "user", "content": user_message_content})
    display_message("user", user_message_content)

    # Initialize placeholder for streaming response
    message_placeholder = st.empty()
    full_response = ""

    try:
        llm_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        # Prepare context-aware prompt for the LLM only if document_text is available
        if st.session_state.document_text:
            context_document = st.session_state.document_text
            user_prompt_with_context = f"Context Document:\n{context_document}\n\nUser Query: {prompt}"
            llm_messages.append({"role": "user", "content": user_prompt_with_context})
        else:
            llm_messages.append({"role": "user", "content": prompt}) # Just use user prompt if no document

        # Call LiteLLM completion API for response generation with streaming
        response = completion(
            model="gemini/gemini-1.5-flash-001",
            messages=llm_messages,
            stream=True,
        )

        # Stream and display assistant response
        for part in response:
            chunk = part.choices[0].delta.content or "" # Extract content chunk from response part
            full_response += chunk # Accumulate full response
            message_placeholder.markdown(full_response) # Update placeholder with current response

        # Store assistant response in session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"An error occurred: {e}") # Display error message if exception occurs