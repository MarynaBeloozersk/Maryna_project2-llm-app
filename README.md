# Web-Based LLM App – Project 2

This repository contains the web-based LLM application developed for **Project 2: Build Your Own Web-Based LLM App** (MSIS 5193: Programming for Data Science and Analytics I).

The app is built using **Streamlit** and a **local open-source LLM via Ollama**.  
It supports document upload (TXT, PDF, DOCX, HTML), document-based question answering, and automatic extraction of abbreviations.

---

## Features

### ✔ Document Upload
- Supported formats: `.txt`, `.pdf`, `.docx`, `.html`
- Extracted text is used as context for the LLM

### ✔ Document-Based Q&A (Question 1)
- User enters a question
- The app passes both the question and the document text to an open-source LLM
- Returns a concise answer using document context

### ✔ Abbreviation Index Generation (Question 2)
- Detects scientific abbreviations using patterns like:
  - `Full Term (ABBR)`
  - `ABBR (Full Term)`
- Produces a clean abbreviation → full-term index

### ✔ Deployment (Question 3)
- This app is fully compatible with Streamlit Community Cloud
- Abbreviation extraction works in the cloud
- LLM-based Q&A may require a cloud LLM (Ollama cannot run in Streamlit Cloud)

---

## Main File

- `Project2_Q2.py` (used for deployment)
  - Implements Q1: document-based question answering  
  - Implements Q2: abbreviation extraction

---

## Technology Stack

- **Python 3.13+**
- **Streamlit**
- **Ollama** (local LLM runtime)
- **LangChain-Ollama**
- **PyMuPDF (pymupdf)**
- **docx2txt**
- **BeautifulSoup4**

---

## Installation

Install Python dependencies:

```bash
pip install streamlit langchain-ollama pymupdf docx2txt beautifulsoup4
