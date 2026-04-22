import json
import os
import chromadb
from src.logger import logging
from src.config import DataIngestionConfig


def load_json(json_path: str) -> dict:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_records(data: dict) -> list:
    """
    Converts structured clause JSON into a flat list of ChromaDB-ready records.
    Each main clause and each subclause becomes a separate document record.
    """
    records = []
    agreement_heading = data.get("agreement_heading", "")
    source_file = data.get("source_file", "")
    clauses = data.get("clauses", [])

    for clause in clauses:
        clause_number = clause.get("clause_number", "")
        clause_title = clause.get("clause_title", "")
        clause_text = clause.get("clause_text", "").strip()
        subclauses = clause.get("subclauses", [])

        # Build main clause document
        main_text_parts = []
        if clause_title:
            main_text_parts.append(f"Clause {clause_number}: {clause_title}")
        if clause_text:
            main_text_parts.append(clause_text)

        main_document = "\n".join(main_text_parts).strip()

        if main_document:
            records.append({
                "id": f"{source_file}::clause::{clause_number}",
                "document": main_document,
                "metadata": {
                    "agreement_heading": agreement_heading,
                    "source_file": source_file,
                    "clause_number": clause_number,
                    "subclause_id": "",
                    "parent_clause_number": clause_number,
                    "chunk_type": "clause"
                }
            })

        # Build subclause documents
        for sub in subclauses:
            subclause_id = sub.get("subclause_id", "")
            sub_text = sub.get("text", "").strip()

            if not sub_text:
                continue

            sub_document = f"Clause {clause_number}.{subclause_id}: {sub_text}"

            records.append({
                "id": f"{source_file}::subclause::{clause_number}::{subclause_id}",
                "document": sub_document,
                "metadata": {
                    "agreement_heading": agreement_heading,
                    "source_file": source_file,
                    "clause_number": clause_number,
                    "subclause_id": subclause_id,
                    "parent_clause_number": clause_number,
                    "chunk_type": "subclause"
                }
            })

    return records


def ingest_to_chroma(json_path: str, chroma_db_dir: str, collection_name: str) -> None:
    """
    Loads clause JSON and inserts all records into a ChromaDB collection.

    Args:
        json_path: Path to the parsed clause JSON file.
        chroma_db_dir: Directory where ChromaDB stores its data.
        collection_name: Name of the ChromaDB collection to insert into.
    """
    logging.info("Starting ChromaDB ingestion.")
    logging.info(f"JSON source: {json_path}")
    logging.info(f"ChromaDB directory: {chroma_db_dir}")
    logging.info(f"Collection name: {collection_name}")

    data = load_json(json_path)
    records = build_records(data)

    if not records:
        logging.warning("No records found in JSON. Ingestion skipped.")
        return

    os.makedirs(chroma_db_dir, exist_ok=True)

    client = chromadb.PersistentClient(path=chroma_db_dir)
    collection = client.get_or_create_collection(name=collection_name)

    ids = [r["id"] for r in records]
    documents = [r["document"] for r in records]
    metadatas = [r["metadata"] for r in records]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    logging.info(f"Inserted {len(records)} records into collection '{collection_name}'.")
    logging.info(f"ChromaDB stored at: {chroma_db_dir}")