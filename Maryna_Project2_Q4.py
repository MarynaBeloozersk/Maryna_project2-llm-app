"""
Project 2 – Q4
Web App with Closed-Source LLM (Google Gemini 2.0 Flash)
Author: Maryna Basalay

How to run:

1) Install required Python packages:
   pip install streamlit pymupdf docx2txt beautifulsoup4 google-genai

2) Get a free Gemini API key in Google AI Studio.

3) Run the Streamlit app:
   streamlit run Project2_Q4.py

This file implements:
• Question 4 – same functionality as Question 1 (upload txt/pdf/docx/html
  files, extract text, submit a question), but now uses a closed-source
  online LLM (Google Gemini 2.0 Flash) instead of a local open-source model.
"""

import streamlit as st
import tempfile
import fitz               
import docx2txt
from bs4 import BeautifulSoup

from google import genai 


def load_text_from_file(file):
    """
    Load text from an uploaded file (txt, pdf, docx, html)
    and return extracted plain text.
    """
    filename = file.name.lower()

    # Save uploaded file to a temporary path
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        temp_path = tmp.name

    # TXT
    if filename.endswith(".txt"):
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return text

    # PDF
    if filename.endswith(".pdf"):
        text = ""
        pdf_document = fitz.open(temp_path)
        for page in pdf_document:
            text += page.get_text() + "\n"
        return text

    # DOCX
    if filename.endswith(".docx"):
        text = docx2txt.process(temp_path)
        return text

    # HTML / HTM
    if filename.endswith(".html") or filename.endswith(".htm"):
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n")
        return text

    # Unsupported extension → empty context
    return ""


st.title("Input to AI (Closed-Source LLM – Google Gemini 2.0 Flash)")

# User enters their own API key at runtime (not stored in code)
gemini_api_key = st.text_input(
    "Enter your Gemini API key:",
    type="password",
)
st.caption("You can obtain a free API key at Google AI Studio: https://ai.google.dev/gemini-api")

question = st.text_input("Enter your question:")

uploaded_file = st.file_uploader(
    "Upload attachment (optional):",
    type=["txt", "pdf", "docx", "html"]
)

if st.button("Ask"):
    if not gemini_api_key:
        st.error("Please enter your Gemini API key above.")
    elif not question.strip():
        st.error("Please enter your question.")
    else:
        # Extract context from uploaded file (if any)
        if uploaded_file is not None:
            context_text = load_text_from_file(uploaded_file)
        else:
            context_text = ""

        # Configure Gemini client with the user-provided API key
        client = genai.Client(api_key=gemini_api_key)

        # Build prompt for the model
        prompt = f"""
Context from document (may be empty):
{context_text}

Question:
{question}

Answer clearly and use the document context when it is relevant.
"""

        try:
            # Call the closed-source online LLM (Gemini 2.0 Flash)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            st.subheader("AI Response:")
            st.write(response.text)

        except Exception as e:
            st.error(f"Error while calling Gemini API: {e}")
