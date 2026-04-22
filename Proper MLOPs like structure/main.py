import os
import streamlit as st
from src.config import DataIngestionConfig
from src.pipeline.data_ingestion import run_data_ingestion_pipeline

# ── Constants ─────────────────────────────────────────────────────────────────

RAW_DIR       = os.path.join("data", "raw")
PARSED_DIR    = os.path.join("data", "parsed")
CHROMA_DB_DIR = os.path.join("vectorstore", "chroma_db")
COLLECTION_NAME = "contract_clauses"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Contract Analyzer - Ingestion",
    layout="centered"
)

st.title("Contract Analyzer")
st.subheader("Data Ingestion Pipeline")
st.write("Upload a contract file in `.docx` format. The system will parse clauses and store them in the vector database.")

# ── File Upload ───────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader("Upload Contract (.docx)", type=["docx"])

if uploaded_file is not None:
    filename     = uploaded_file.name
    stem         = os.path.splitext(filename)[0]

    # Paths derived from uploaded filename
    file_path        = os.path.join(RAW_DIR, filename)
    output_path      = os.path.join(PARSED_DIR, f"{stem}_clauses.json")
    output_path_text = os.path.join(PARSED_DIR, f"{stem}.txt")

    # Display resolved paths so user can verify
    st.markdown("**Resolved Paths**")
    st.code(
        f"Input file     : {file_path}\n"
        f"Clause JSON    : {output_path}\n"
        f"Debug TXT      : {output_path_text}\n"
        f"ChromaDB dir   : {CHROMA_DB_DIR}\n"
        f"Collection     : {COLLECTION_NAME}"
    )

    if st.button("Run Ingestion Pipeline"):
        # Step 1: Save uploaded file to disk with original filename
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.info(f"File saved to: {file_path}")

        # Step 2: Build config
        config = DataIngestionConfig(
            file_path        = file_path,
            output_path      = output_path,
            output_path_text = output_path_text,
            chroma_db_dir    = CHROMA_DB_DIR,
            collection_name  = COLLECTION_NAME
        )

        # Step 3: Run pipeline
        with st.spinner("Running ingestion pipeline..."):
            try:
                dataingestionartifact=run_data_ingestion_pipeline(config)
                st.success("Ingestion completed successfully.")
                st.markdown(f"- Clause JSON saved to `{output_path}`")
                st.markdown(f"- Records inserted into ChromaDB collection `{COLLECTION_NAME}`")
                print(dataingestionartifact)
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
    