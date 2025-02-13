# main.py
import time
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from app.prompts import SystemPrompt
from app.utils import PDFProcessor
import tempfile

# Load environment variables from .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Google Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()
  
# Initialize Gemini model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 65536,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-001",  # Or "gemini-pro" if you prefer
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

# Function to display chat messages with role-based styling
def display_message(role: str, parts: str):
    """Displays chat messages in Streamlit chat interface with role-based styling."""
    with st.chat_message(role):
        st.markdown(parts)


# Initialize session state variables
if "messages" not in st.session_state:
    # Initialize chat messages history with system prompt
    system_prompt_content = SystemPrompt("").system_prompt()
    st.session_state.messages = [{"role": "system", "parts": system_prompt_content}]

if "document_text" not in st.session_state:
    # Initialize document text storage
    st.session_state.document_text = ""

if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])


# Display chat history from session state
for message in st.session_state.messages:
    if message["role"] != "system":  # Do not display system prompt in chat history
        display_message(message["role"], message["parts"])

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
        st.markdown("Preview of document parts:")
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
    st.session_state.messages.append({"role": "user", "parts": user_message_content})

    # Calculate token count for user message
    input_token_count_request = model.count_tokens(user_message_content)
    input_token_count = input_token_count_request.total_tokens

    display_message("user", user_message_content)

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
            input_token_count_request = model.count_tokens(user_message_content)
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
        st.session_state.messages.append({"role": "model", "parts": full_response})

        # Display token counts after response is generated
        output_token_count: int = gemini_response.usage_metadata.candidates_token_count if gemini_response.usage_metadata else 0
        total_token_count: int = gemini_response.usage_metadata.total_token_count if gemini_response.usage_metadata else 0

        st.info(f"Input Tokens: {input_token_count} | Output Tokens: {output_token_count} | Total Tokens: {total_token_count}")


    except Exception as e:
        st.error(f"An error occurred: {e}")  # Display error message if exception occurs