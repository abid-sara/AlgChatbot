# AlgChatbot

AlgChatbot is a chatbot system designed to efficiently answer questions using uploaded DOCX documents (such as service descriptions, FAQs, and offers) for organizations like Algeria Telecom.

---

## Features

- Upload and process DOCX files into structured search chunks
- Hybrid search pipeline: TF-IDF, BM25, and multilingual embeddings
- Query answering in Arabic, French, and English
- Configurable search weights and methods
- LLM-powered customer support with context-aware answers

---

## Architecture Overview

```
AlgChatbot/
│
├── backend/      # Server-side code: chunking, vectorization, search, API, LLM
├── frontend/     # Client-side web application
└── .gitignore
```

- **Backend:** Handles document processing, search, and QA logic.
- **Frontend:** Provides a user-friendly chat interface.

---

## How to Run

### Backend
```bash
cd backend
```

It is recommended to use a virtual environment to manage dependencies.

### Create and activate a virtual environment

For **Windows**:
```sh
python -m venv venv
venv\Scripts\activate
```

For **macOS/Linux**:
```sh
python3 -m venv venv
source venv/bin/activate
```

Then, install the required dependencies:
```sh
pip install -r requirements.txt
```

```bash
# Start the backend server
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm start
# or
npm run dev
```

Frontend will be available at localhost. Ensure the backend is running and accessible.

---

## Chunking, Vectorization, and Search Pipeline

### 1. Chunking

- **Input:** DOCX files (FAQs, offers, service descriptions)
- **Process:**

  - Parsed using `DocxProcessor`
  - Paragraphs grouped into "chunks" with embedded service/context titles

- To get the chunks do:

```bash
cd backend
cd dev
python chunk_document.py
```

You will notice a creation of the file: **rag_chunks.json** inside the **data** folder

### 2. Vectorization

- **TF-IDF:** Keyword-based vectorization
- **BM25:** Probabilistic ranking based on term frequency & doc length
- **Embeddings:** Multilingual semantic vectors (`intfloat/multilingual-e5-base`)
- **Hybrid:** Weighted combination (e.g., `{"tfidf": 0.3, "bm25": 0.3, "embeddings": 0.4}`)
- **Preprocessing:**
  - Arabic: normalization (diacritics, variants)
  - Non-Arabic: lowercasing, punctuation stripping
  - Language detection for accurate processing

### 3. Search

- Methods: `tfidf`, `bm25`, `embeddings`, `hybrid`
- Hybrid optionally re-ranked with embeddings for best precision
- **Example Query:**  
  _"Is the E-facture service free?"_  
  **Result:** Direct answer chunk: `"Oui ce service est gratuit."`

---

## API Endpoints

- `POST /search` — Retrieve relevant chunks for a query
- `POST /qa` — Generate LLM answer with context

---

## LLM Integration

- Uses a configurable LLM (e.g., Gemini via `create_llm()`) ie: Factory class and provider
- Before calling the LLM:
  - Preprocess query (determine context, language, reformulation)
  - Gather up to 3 previous conversation turns for context
  - Construct prompt with:
    - Assistant role (official Algeria Telecom support)
    - Recent conversation history
    - Retrieved document chunks
    - Rules: answer in user’s language, use only provided context, fallback if answer missing, polite/professional tone

---

## Note:

When running the server the vector database will be created (if it is not created yet)

## License

Developer: ABID Sara

---
