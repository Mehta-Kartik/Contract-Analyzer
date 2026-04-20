# print("Jay Ganesh")

# import re
# from typing import Optional, Dict, Any, List

# import chromadb


# CHROMA_DB_DIR = r"D:\ProjectAarya\Contract Analyzer\vectorstore\chroma_db"
# COLLECTION_NAME = "contract_clauses"


# def normalize_query(query: str) -> str:
#     query = query.strip()
#     query = re.sub(r"\s+", " ", query)
#     return query


# def extract_clause_reference(query: str) -> Optional[Dict[str, Optional[str]]]:
#     query = normalize_query(query).lower()

#     clause_match = re.search(r'clause\s+(\d+)', query)
#     subclause_match = re.search(r'clause\s+(\d+)\s*[\.\(]?\s*([a-zA-Z0-9]+)\)?', query)

#     if subclause_match:
#         clause_number = subclause_match.group(1)
#         subclause_id = subclause_match.group(2)

#         if subclause_id != clause_number:
#             return {
#                 "clause_number": clause_number,
#                 "subclause_id": subclause_id.lower()
#             }

#     if clause_match:
#         return {
#             "clause_number": clause_match.group(1),
#             "subclause_id": None
#         }

#     return None


# def is_general_document_question(query: str) -> bool:
#     q = normalize_query(query).lower()
#     keywords = [
#         "what is the agreement about",
#         "what is this agreement about",
#         "heading",
#         "title",
#         "summary",
#         "about the agreement",
#         "agreement heading",
#         "agreement title"
#     ]
#     return any(keyword in q for keyword in keywords)


# def normalize_results(results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
#     ids = results.get("ids", [[]])[0]
#     docs = results.get("documents", [[]])[0]
#     metas = results.get("metadatas", [[]])[0]
#     distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(ids)

#     matches = []
#     for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
#         meta = meta or {}
#         matches.append({
#             "id": doc_id,
#             "document": doc,
#             "distance": dist,
#             "chunk_type": meta.get("chunk_type", ""),
#             "agreement_heading": meta.get("agreement_heading", ""),
#             "clause_number": str(meta.get("clause_number", "")),
#             "subclause_id": str(meta.get("subclause_id", "")).lower(),
#             "source_file": meta.get("source_file", "")
#         })

#     return {"matches": matches}


# def retrieve_by_query(collection, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
#     query = normalize_query(query)

#     if not query:
#         return {"matches": []}

#     results = collection.query(
#         query_texts=[query],
#         n_results=n_results,
#         include=["documents", "metadatas", "distances"]
#     )

#     return normalize_results(results)


# def retrieve_by_clause(
#     collection,
#     clause_number: str,
#     subclause_id: Optional[str] = None,
#     query_text: str = "",
#     n_results: int = 5
# ) -> Dict[str, List[Dict[str, Any]]]:
#     clause_number = str(clause_number).strip()
#     subclause_id = subclause_id.lower().strip() if subclause_id else None
#     query_text = normalize_query(query_text) or f"clause {clause_number}" + (f".{subclause_id}" if subclause_id else "")

#     if not clause_number:
#         return {"matches": []}

#     if subclause_id:
#         where_filter = {
#             "$and": [
#                 {"clause_number": clause_number},
#                 {"subclause_id": subclause_id}
#             ]
#         }
#     else:
#         where_filter = {"clause_number": clause_number}

#     results = collection.query(
#         query_texts=[query_text],
#         n_results=n_results,
#         where=where_filter,
#         include=["documents", "metadatas", "distances"]
#     )

#     return normalize_results(results)


# def retrieve_document_summary(collection, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
#     return retrieve_by_query(collection, query, n_results=n_results)


# def format_context(results: Dict[str, List[Dict[str, Any]]], max_chunks: int = 5) -> Dict[str, Any]:
#     matches = results.get("matches", [])[:max_chunks]

#     if not matches:
#         return {
#             "context_text": "",
#             "sources": [],
#             "matches": []
#         }

#     context_blocks = []
#     sources = []
#     seen_docs = set()

#     for index, match in enumerate(matches, start=1):
#         doc = (match.get("document") or "").strip()

#         if not doc or doc in seen_docs:
#             continue

#         seen_docs.add(doc)

#         source_line = (
#             f"Source {index} | "
#             f"Agreement: {match.get('agreement_heading', '')} | "
#             f"Clause: {match.get('clause_number', '')} | "
#             f"Subclause: {match.get('subclause_id', '')} | "
#             f"File: {match.get('source_file', '')}"
#         )

#         context_blocks.append(f"{source_line}\n{doc}")
#         sources.append({
#             "source_id": index,
#             "id": match.get("id", ""),
#             "clause_number": match.get("clause_number", ""),
#             "subclause_id": match.get("subclause_id", ""),
#             "agreement_heading": match.get("agreement_heading", ""),
#             "source_file": match.get("source_file", ""),
#             "distance": match.get("distance", None)
#         })

#     return {
#         "context_text": "\n\n".join(context_blocks),
#         "sources": sources,
#         "matches": matches
#     }


# def print_results(results: Dict[str, List[Dict[str, Any]]]) -> None:
#     matches = results.get("matches", [])

#     if not matches:
#         print("\nNo matching records found.")
#         return

#     print("\nTop Matches:\n")

#     for i, match in enumerate(matches, start=1):
#         print("=" * 100)
#         print(f"Result #{i}")
#         print(f"ID           : {match.get('id', '')}")
#         print(f"Distance     : {match.get('distance', '')}")
#         print(f"Chunk Type   : {match.get('chunk_type', '')}")
#         print(f"Agreement    : {match.get('agreement_heading', '')}")
#         print(f"Clause No    : {match.get('clause_number', '')}")
#         print(f"Subclause ID : {match.get('subclause_id', '')}")
#         print(f"Source File  : {match.get('source_file', '')}")
#         print("-" * 100)
#         print(match.get("document", ""))
#         print()


# def main():
#     client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
#     collection = client.get_collection(name=COLLECTION_NAME)

#     print(f"Connected to collection: {COLLECTION_NAME}")
#     print("Type your query below. Type 'exit' to quit.\n")

#     while True:
#         query = input("Enter query: ").strip()

#         if query.lower() in {"exit", "quit"}:
#             print("Exiting query console.")
#             break

#         if not query:
#             print("Please enter a valid query.\n")
#             continue

#         clause_ref = extract_clause_reference(query)

#         try:
#             if clause_ref:
#                 clause_number = clause_ref["clause_number"]
#                 subclause_id = clause_ref["subclause_id"]

#                 if subclause_id:
#                     print(f"\nDetected direct lookup for Clause {clause_number}.{subclause_id}\n")
#                 else:
#                     print(f"\nDetected direct lookup for Clause {clause_number}\n")

#                 results = retrieve_by_clause(
#                     collection=collection,
#                     clause_number=clause_number,
#                     subclause_id=subclause_id,
#                     query_text=query,
#                     n_results=5
#                 )

#                 if not results["matches"]:
#                     print("No exact clause match found. Falling back to semantic retrieval.\n")
#                     results = retrieve_by_query(collection, query, n_results=5)

#             elif is_general_document_question(query):
#                 results = retrieve_document_summary(collection, query, n_results=5)

#             else:
#                 results = retrieve_by_query(collection, query, n_results=5)

#             print_results(results)

#         except Exception as e:
#             print(f"\nError while querying collection: {e}\n")


# if __name__ == "__main__":
#     main()





print("Jay Ganesh")

import re
from typing import Optional, Dict, Any, List

import chromadb
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import os

# ─────────────────────────────────────────────
CHROMA_DB_DIR = r"D:\ProjectAarya\Contract Analyzer\vectorstore\chroma_db"
COLLECTION_NAME = "contract_clauses"

GROQ_API_KEY = input("Enter Groq API key")  # 🔑 Provide your Groq API key here
GROQ_MODEL = "llama-3.1-8b-instant"  # or "mixtral-8x7b-32768", "gemma2-9b-it"
# ─────────────────────────────────────────────


# ─── LLM Initialization ───────────────────────────────────────────────────────

def get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.2,
    )


# ─── Query Normalization ──────────────────────────────────────────────────────

def normalize_query(query: str) -> str:
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query


# ─── Clause Reference Extraction ─────────────────────────────────────────────

def extract_clause_reference(query: str) -> Optional[Dict[str, Optional[str]]]:
    query = normalize_query(query).lower()

    clause_match = re.search(r'clause\s+(\d+)', query)
    subclause_match = re.search(r'clause\s+(\d+)\s*[\.\(]?\s*([a-zA-Z0-9]+)\)?', query)

    if subclause_match:
        clause_number = subclause_match.group(1)
        subclause_id = subclause_match.group(2)

        if subclause_id != clause_number:
            return {
                "clause_number": clause_number,
                "subclause_id": subclause_id.lower()
            }

    if clause_match:
        return {
            "clause_number": clause_match.group(1),
            "subclause_id": None
        }

    return None


# ─── General Document Question Detection ─────────────────────────────────────

def is_general_document_question(query: str) -> bool:
    q = normalize_query(query).lower()
    keywords = [
        "what is the agreement about",
        "what is this agreement about",
        "heading",
        "title",
        "summary",
        "about the agreement",
        "agreement heading",
        "agreement title"
    ]
    return any(keyword in q for keyword in keywords)


# ─── Result Normalization ─────────────────────────────────────────────────────

def normalize_results(results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(ids)

    matches = []
    for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
        meta = meta or {}
        matches.append({
            "id": doc_id,
            "document": doc,
            "distance": dist,
            "chunk_type": meta.get("chunk_type", ""),
            "agreement_heading": meta.get("agreement_heading", ""),
            "clause_number": str(meta.get("clause_number", "")),
            "subclause_id": str(meta.get("subclause_id", "")).lower(),
            "source_file": meta.get("source_file", "")
        })

    return {"matches": matches}


# ─── Retrieval Functions ──────────────────────────────────────────────────────

def retrieve_by_query(collection, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    query = normalize_query(query)

    if not query:
        return {"matches": []}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    return normalize_results(results)


def retrieve_by_clause(
    collection,
    clause_number: str,
    subclause_id: Optional[str] = None,
    query_text: str = "",
    n_results: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    clause_number = str(clause_number).strip()
    subclause_id = subclause_id.lower().strip() if subclause_id else None
    query_text = normalize_query(query_text) or f"clause {clause_number}" + (f".{subclause_id}" if subclause_id else "")

    if not clause_number:
        return {"matches": []}

    if subclause_id:
        where_filter = {
            "$and": [
                {"clause_number": clause_number},
                {"subclause_id": subclause_id}
            ]
        }
    else:
        where_filter = {"clause_number": clause_number}

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    return normalize_results(results)


def retrieve_document_summary(collection, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    return retrieve_by_query(collection, query, n_results=n_results)


# ─── Context Formatter ────────────────────────────────────────────────────────

def format_context(results: Dict[str, List[Dict[str, Any]]], max_chunks: int = 5) -> Dict[str, Any]:
    matches = results.get("matches", [])[:max_chunks]

    if not matches:
        return {
            "context_text": "",
            "sources": [],
            "matches": []
        }

    context_blocks = []
    sources = []
    seen_docs = set()

    for index, match in enumerate(matches, start=1):
        doc = (match.get("document") or "").strip()

        if not doc or doc in seen_docs:
            continue

        seen_docs.add(doc)

        source_line = (
            f"Source {index} | "
            f"Agreement: {match.get('agreement_heading', '')} | "
            f"Clause: {match.get('clause_number', '')} | "
            f"Subclause: {match.get('subclause_id', '')} | "
            f"File: {match.get('source_file', '')}"
        )

        context_blocks.append(f"{source_line}\n{doc}")
        sources.append({
            "source_id": index,
            "id": match.get("id", ""),
            "clause_number": match.get("clause_number", ""),
            "subclause_id": match.get("subclause_id", ""),
            "agreement_heading": match.get("agreement_heading", ""),
            "source_file": match.get("source_file", ""),
            "distance": match.get("distance", None)
        })

    return {
        "context_text": "\n\n".join(context_blocks),
        "sources": sources,
        "matches": matches
    }


# ─── LLM Answer Generation ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a highly accurate legal contract analysis assistant.
You are given excerpts from a contract document as context. Your job is to answer the user's question strictly based on the provided context.

Rules:
- Answer only from the provided context. Do NOT use outside knowledge.
- If the context does not contain enough information, say: "The provided contract clauses do not contain sufficient information to answer this question."
- Be concise, precise, and professional.
- If referencing specific clauses, mention them explicitly (e.g., "As per Clause 3.2...").
- Do NOT hallucinate clause numbers or obligations not present in the context.
"""

def generate_answer(query: str, context_text: str, llm: ChatGroq) -> str:
    if not context_text.strip():
        return "No relevant contract clauses were retrieved to answer your question."

    human_message = f"""Context from Contract:
\"\"\"
{context_text}
\"\"\"

Question: {query}

Answer:"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_message)
    ]

    response = llm.invoke(messages)
    return response.content.strip()


# ─── Print Raw Retrieval Results ──────────────────────────────────────────────

def print_results(results: Dict[str, List[Dict[str, Any]]]) -> None:
    matches = results.get("matches", [])

    if not matches:
        print("\nNo matching records found.")
        return

    print("\nTop Matches:\n")

    for i, match in enumerate(matches, start=1):
        print("=" * 100)
        print(f"Result #{i}")
        print(f"ID           : {match.get('id', '')}")
        print(f"Distance     : {match.get('distance', '')}")
        print(f"Chunk Type   : {match.get('chunk_type', '')}")
        print(f"Agreement    : {match.get('agreement_heading', '')}")
        print(f"Clause No    : {match.get('clause_number', '')}")
        print(f"Subclause ID : {match.get('subclause_id', '')}")
        print(f"Source File  : {match.get('source_file', '')}")
        print("-" * 100)
        print(match.get("document", ""))
        print()


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)
    llm = get_llm()

    print(f"Connected to collection: {COLLECTION_NAME}")
    print(f"LLM: {GROQ_MODEL}")
    print("Type your query below. Type 'exit' to quit.\n")

    while True:
        query = input("Enter query: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Exiting query console.")
            break

        if not query:
            print("Please enter a valid query.\n")
            continue

        clause_ref = extract_clause_reference(query)

        try:
            # ── Step 1: Retrieve ──────────────────────────────────────────────
            if clause_ref:
                clause_number = clause_ref["clause_number"]
                subclause_id = clause_ref["subclause_id"]

                if subclause_id:
                    print(f"\nDetected direct lookup for Clause {clause_number}.{subclause_id}\n")
                else:
                    print(f"\nDetected direct lookup for Clause {clause_number}\n")

                results = retrieve_by_clause(
                    collection=collection,
                    clause_number=clause_number,
                    subclause_id=subclause_id,
                    query_text=query,
                    n_results=5
                )

                if not results["matches"]:
                    print("No exact clause match found. Falling back to semantic retrieval.\n")
                    results = retrieve_by_query(collection, query, n_results=5)

            elif is_general_document_question(query):
                results = retrieve_document_summary(collection, query, n_results=5)

            else:
                results = retrieve_by_query(collection, query, n_results=5)

            # ── Step 2: Print Raw Chunks ──────────────────────────────────────
            print_results(results)

            # ── Step 3: Format Context ────────────────────────────────────────
            formatted = format_context(results, max_chunks=5)
            context_text = formatted["context_text"]

            # ── Step 4: Generate LLM Answer ───────────────────────────────────
            print("\n" + "▓" * 100)
            print("🤖 LLM Answer (via Groq):\n")
            answer = generate_answer(query, context_text, llm)
            print(answer)
            print("▓" * 100 + "\n")

        except Exception as e:
            print(f"\nError while querying collection: {e}\n")


if __name__ == "__main__":
    main()