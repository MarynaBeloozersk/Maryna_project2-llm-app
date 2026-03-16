# **Project 2 – Streamlit Applications (Q3 and Q4)**

## Apps Included

### 1. Abbreviation Extraction App
Extracts abbreviation–definition pairs from uploaded documents (TXT, PDF, DOCX, HTML).

Run with:
streamlit run abbreviation_extractor_app.py

### 2. Document Q&A LLM App
Allows users to upload a document and ask questions using Google's Gemini 2.0 Flash model.

Run with:
streamlit run document_qa_llm_app.py

This repository contains two Python/Streamlit applications created for **Project 2**.
---
## **Question 3 – Abbreviation Extraction App**
This Streamlit application extracts abbreviations (ABBR → Full Term) from uploaded documents:
- TXT  
- PDF  
- DOCX  
- HTML  
It uses pure Python text processing (no LLM model).
### Run locally:
streamlit run Maryna_Project2_Q3_cloud.py

---

## **Question 4 – Document Q&A with Gemini 2.0 Flash**
This Streamlit application allows the user to:
- upload a TXT, PDF, DOCX, or HTML document  
- extract the text from the file  
- enter a question  
- send the question + document context to **Google Gemini 2.0 Flash**  
- receive an AI-generated answer  
A Google API key is required.  
You can obtain one here: https://ai.google.dev/gemini-api
### Run locally:
streamlit run Maryna_Project2_Q4.py
