#  Advertisement Guardian: AI-Powered Compliance Audit Engine

An autonomous, multimodal compliance orchestration engine designed to audit video advertisements for regulatory violations (FTC Endorsement Guidelines) and platform-specific formatting requirements (YouTube Ad Specifications).

Built with **LangGraph**, **FastAPI**, and **Azure AI Services**, this system automatically extracts video metadata, transcribes speech, captures visual claims, and validates the content using a Retrieval-Augmented Generation (RAG) pipeline.

## Key Features

* **Multimodal Video Processing:** Automatically downloads video URLs to Azure Blob Storage and processes them through Azure Video Indexer to extract OCR, transcripts, and visual claims.
* **Agentic Orchestration:** Utilizes LangGraph to manage the complex, multi-step workflow of data extraction, context retrieval, and LLM evaluation.
* **RAG-Powered Compliance:** Integrates Azure AI Search as a vector database to retrieve strict compliance rules from PDF documents (e.g., FTC Disclosures 101, YouTube Ad Specs).
* **Enterprise Observability:** Full telemetry and logging implemented via Azure Application Insights and LangSmith for real-time tracking of API health, workflow execution, and LLM token usage.

## Architecture

1. **Input:** User submits a video URL via FastAPI endpoint.
2. **Storage:** Video is downloaded and securely stored in Azure Blob Storage.
3. **Extraction:** Azure Video Indexer analyzes the video -> outputs OCR text, speech transcripts, and visual claims.
4. **Retrieval (RAG):** Azure AI Search queries the vector database containing compliance PDFs to find relevant rules based on the video's content.
5. **Evaluation:** Azure OpenAI Service evaluates the video data against the retrieved rules.
6. **Output:** System returns a structured JSON report detailing compliance status, categorized issues, and severity.

## Tech Stack

* **Core:** Python, FastAPI, Pydantic
* **AI & Orchestration:** LangChain, LangGraph, Azure OpenAI Service
* **Cloud Infrastructure (Azure):** Azure Video Indexer, Azure AI Search (Vector DB), Azure Blob Storage
* **Observability:** Azure Application Insights, LangSmith

## Project Structure


├── backend/
│   ├── data/                  # Compliance rulebooks (PDFs)
│   ├── scripts/               # Utility scripts (e.g., index_documents.py for Vector DB)
│   ├── source/
│   │   ├── api/               # FastAPI server and Telemetry setup
│   │   ├── graph/             # LangGraph state, nodes, and workflow definitions
│   │   └── services/          # Azure Video Indexer integrations
├── main.py                    # Application entry point
├── pyproject.toml / uv.lock   # Dependency management
└── README.md                  # Project documentation