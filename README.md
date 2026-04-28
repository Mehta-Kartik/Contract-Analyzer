# Contract Analyzer

Contract Analyzer is a legal document analysis application that ingests `.docx` contracts, extracts clauses and subclauses, stores them in a ChromaDB vector database using Voyage AI embeddings, and provides a Streamlit-based question-answering interface powered by Groq LLMs.[1]

The project is designed as a retrieval-augmented generation (RAG) pipeline for contract understanding, with support for clause-aware retrieval, semantic search, source-grounded answers, and MLflow-based experiment tracking for both ingestion and query evaluation.[1]

## Features

- Upload and process `.docx` contract files through a Streamlit interface.[1]
- Parse agreement headings, main clauses, and multiple subclause formats including numeric, alphabetic, and Roman identifiers.[1]
- Convert structured contract clauses into ChromaDB-ready records with metadata such as clause number, subclause ID, source file, and chunk type.[1]
- Store contract chunks in ChromaDB with `voyage-law-2` embeddings for legal-semantic retrieval.[1]
- Support multiple retrieval strategies, including exact clause lookup, exact clause plus similar context, document-summary retrieval, and pure semantic query search.[1]
- Generate grounded answers using Groq's `llama-3.1-8b-instant` model with retrieved contract context.[1]
- Display retrieved sources, clause references, retrieval latency, and evaluation metrics in the UI.[1]
- Track ingestion and retrieval runs in MLflow, including artifacts, parameters, and metrics such as Recall@5 and clause retrieval accuracy.[1]

## Tech Stack

| Layer | Tools / Libraries |
|---|---|
| Frontend / UI | Streamlit [1] |
| LLM | Groq via `langchain_groq`, model `llama-3.1-8b-instant` [1] |
| Embeddings | Voyage AI, `voyage-law-2` [1] |
| Vector Database | ChromaDB [1] |
| Document Parsing | `python-docx`, regex-based clause parsing [1] |
| Experiment Tracking | MLflow [1] |
| Orchestration | Python pipeline modules [1] |

## How It Works

The application follows a two-stage workflow: ingestion and question answering.[1]

1. A user uploads a `.docx` contract in the Streamlit app.[1]
2. The ingestion pipeline parses the document, extracts clause structures, and saves structured JSON output.[1]
3. Parsed clauses and subclauses are flattened into records and inserted into a ChromaDB collection using Voyage embeddings.[1]
4. During Q&A, the app identifies whether the user is asking about a specific clause, a general summary, or a semantic concept, then applies the appropriate retrieval strategy.[1]
5. Retrieved context is passed to the Groq model, which generates a source-grounded response constrained to the contract text.[1]
6. Query runs, retrieval metrics, timings, and artifacts are logged to MLflow.[1]

## Project Structure

```text
.
├── artifacts.py
├── clause_parser.py
├── config.py
├── data_ingestion.py
├── evaluation.py
├── Exception.py
├── logger.py
├── main.py
├── mlflowutils.py
├── utils.py
├── vectorstore_ingestor.py
└── voyage_embeddings.py
```

### Core Files

- `main.py` contains the Streamlit application, ingestion UI, contract Q&A workflow, retrieval strategies, answer generation, and source display logic.[1]
- `data_ingestion.py` orchestrates contract parsing, embedding-based ingestion into ChromaDB, and MLflow logging for ingestion runs.[1]
- `clause_parser.py` extracts the agreement heading, main clauses, and subclauses from `.docx` files using regex-driven parsing logic.[1]
- `vectorstore_ingestor.py` transforms parsed clause JSON into ChromaDB records and inserts them into a persistent Chroma collection.[1]
- `voyage_embeddings.py` defines a custom embedding function wrapper for Voyage AI to support both document and query embeddings.[1]
- `evaluation.py` provides retrieval evaluation helpers such as `recall_at_k` and clause retrieval accuracy.[1]
- `mlflowutils.py` handles MLflow setup, run creation, metric logging, and JSON artifact logging.[1]
- `config.py` stores the ingestion configuration using a frozen dataclass.[1]
- `logger.py` configures timestamped file-based logging under a project-level `logs/` directory.[1]

## Retrieval Modes

The project supports multiple retrieval paths depending on the query type.[1]

- **Exact clause + similar context**: used when a clause reference is detected, such as `Clause 4` or `Clause 7.1`.[1]
- **Document summary retrieval**: used for broad questions such as the agreement title or what the document is about.[1]
- **Semantic query retrieval**: used for natural-language questions like payment terms, confidentiality, or termination.[1]
- **Semantic fallback**: used when an exact clause lookup does not return results.[1]

## Setup

### Prerequisites

Make sure the following are available before running the project:[1]

- Python 3.10+ recommended.[1]
- A Groq API key for answer generation in the Streamlit app.[1]
- A Voyage AI API key for embedding generation.[1]
- An MLflow tracking server, or a local/remote URI configured through environment variables.[1]

### Environment Variables

Create a `.env` file or export the required variables in your shell:[1]

```env
VOYAGE_API_KEY=your_voyage_api_key
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=Contract-Analyzer-RAG
```

Groq API access is collected from the Streamlit sidebar at runtime in the current implementation.[1]

### Install Dependencies

The dependency file is not included in the shared code, but the imports indicate that the project requires at least the following packages.[1]

```bash
pip install streamlit chromadb python-docx langchain-core langchain-groq voyageai mlflow python-dotenv dill numpy pandas
```

## Run the Application

Start the Streamlit app with:[1]

```bash
streamlit run main.py
```

After launch:[1]

- Enter your Groq API key in the sidebar.[1]
- Open the **Data Ingestion** tab and upload a `.docx` contract.[1]
- Run the ingestion pipeline to parse the contract and build the ChromaDB collection.[1]
- Switch to the **Query Contract** tab and ask questions about the uploaded contract.[1]

## Example Questions

You can ask questions such as:[1]

- `What is the termination clause?` [1]
- `What are the payment terms?` [1]
- `Is there a confidentiality obligation?` [1]
- `Explain Clause 3.` [1]
- `What is this agreement about?` [1]

## Data Flow

```text
DOCX Contract
   ↓
Clause Parser
   ↓
Structured JSON
   ↓
Record Builder
   ↓
Voyage Embeddings
   ↓
ChromaDB Collection
   ↓
Retriever
   ↓
Groq LLM
   ↓
Answer + Sources + Metrics
```

## Evaluation and Tracking

The system includes lightweight retrieval evaluation and MLflow tracking to improve observability.[1]

- Ingestion runs log parsing time, Chroma ingestion time, total ingestion time, and parsed contract artifacts.[1]
- Query runs log retrieval mode, latency, exact-match detection, number of sources, and generated answers as artifacts.[1]
- Benchmark mappings in `main.py` allow optional quick evaluation for selected known queries using Recall@5 and clause retrieval accuracy.[1]

## Output Artifacts

During execution, the project creates and uses these directories conceptually in the app flow:[1]

- `data/raw/` for uploaded contract files.[1]
- `data/parsed/` for parsed contract JSON and optional debug text outputs.[1]
- `vectorstore/<contract_name>/` for ChromaDB persistence.[1]
- `logs/` for application log files.[1]
- MLflow artifact storage for parsed contracts and retrieval outputs.[1]

## Notes

- The parser is designed for contracts that use recognizable numbering patterns for clauses and subclauses.[1]
- Clause extraction stops when stop markers such as `IN WITNESS WHEREOF`, `DATE:`, `PLACE:`, `SCHEDULE`, or `ANNEXURE` are encountered.[1]
- Answers are intentionally constrained by the system prompt to avoid hallucinating legal obligations beyond the retrieved contract text.[1]
- The current code shared includes module naming inconsistencies such as `mlflow_utils` versus `mlflowutils.py`, which should be aligned in the project before production use.[1]

## Future Improvements

- Add a `requirements.txt` or `pyproject.toml` for reproducible setup.[1]
- Support PDF and scanned-contract ingestion with OCR.[1]
- Add contract comparison across multiple uploaded agreements.[1]
- Expand benchmark datasets for more reliable retrieval evaluation.[1]
- Add authentication, document history, and exportable answer reports.[1]

## License

Add your preferred license here, such as MIT, Apache-2.0, or a custom academic/project license.[1]
