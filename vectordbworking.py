import json
import os
import chromadb
from chromadb.config import Settings

JSON_FILE_PATH = r"D:\ProjectAarya\Contract Analyzer\data\parsed\AGREEMENT BETWEEN FILM PRODUCERS AND DISTRIBUTORS_clauses.json"
CHROMA_DB_DIR = r"D:\ProjectAarya\Contract Analyzer\vectorstore\chroma_db"
COLLECTION_NAME = "contract_clauses"

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_records(data, source_file):
    records = []

    agreement_heading = data.get("agreement_heading", "")
    clauses = data.get("clauses", [])

    for clause in clauses:
        clause_number = clause.get("clause_number", "")
        clause_title = clause.get("clause_title", "")
        clause_text = clause.get("clause_text", "").strip()
        subclauses = clause.get("subclauses", [])

        main_text_parts = []
        if clause_title:
            main_text_parts.append(f"Clause {clause_number}: {clause_title}")
        if clause_text:
            main_text_parts.append(clause_text)

        main_document = "\n".join(main_text_parts).strip()

        if main_document:
            records.append({
                "id": f"{os.path.basename(source_file)}::clause::{clause_number}",
                "document": main_document,
                "metadata": {
                    "agreement_heading": agreement_heading,
                    "source_file": os.path.basename(source_file),
                    "clause_number": clause_number,
                    "subclause_id": "",
                    "parent_clause_number": clause_number,
                    "chunk_type": "clause"
                }
            })

        for sub in subclauses:
            subclause_id = sub.get("subclause_id", "")
            sub_text = sub.get("text", "").strip()

            if not sub_text:
                continue

            sub_document = f"Clause {clause_number}.{subclause_id}: {sub_text}"

            records.append({
                "id": f"{os.path.basename(source_file)}::subclause::{clause_number}::{subclause_id}",
                "document": sub_document,
                "metadata": {
                    "agreement_heading": agreement_heading,
                    "source_file": os.path.basename(source_file),
                    "clause_number": clause_number,
                    "subclause_id": subclause_id,
                    "parent_clause_number": clause_number,
                    "chunk_type": "subclause"
                }
            })

    return records

def main():
    data = load_json(JSON_FILE_PATH)

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    records = build_records(data, JSON_FILE_PATH)

    if not records:
        print("No records found to insert.")
        return

    ids = [r["id"] for r in records]
    documents = [r["document"] for r in records]
    metadatas = [r["metadata"] for r in records]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Inserted {len(records)} records into Chroma collection '{COLLECTION_NAME}'")
    print(f"Database stored at: {CHROMA_DB_DIR}")

if __name__ == "__main__":
    main()