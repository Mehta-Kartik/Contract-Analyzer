# import os
# import re
# from typing import Optional, Dict, Any, List
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
# import streamlit as st
# import chromadb
# from langchain_groq import ChatGroq
# from langchain_core.messages import SystemMessage, HumanMessage

# from src.config import DataIngestionConfig
# from src.pipeline.data_ingestion import run_data_ingestion_pipeline


# # ── Constants ──────────────────────────────────────────────────────────────────

# RAW_DIR         = os.path.join("data", "raw")
# PARSED_DIR      = os.path.join("data", "parsed")
# # chroma_db_dir   = os.path.join("vectorstore", "chroma_db")
# # COLLECTION_NAME = "contract_clauses"
# GROQ_MODEL      = "llama-3.1-8b-instant"

# os.makedirs(RAW_DIR,       exist_ok=True)
# os.makedirs(PARSED_DIR,    exist_ok=True)
# # os.makedirs(chroma_db_dir, exist_ok=True)


# # ── Page Config ────────────────────────────────────────────────────────────────

# st.set_page_config(page_title="Contract Analyzer", layout="wide")



# def get_contract_config(stem: str):
#     """Derive unique ChromaDB dir and collection name from the file stem."""
#     safe_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", stem).lower()
#     chroma_db_dir   = os.path.join("vectorstore", safe_stem)
#     collection_name = f"{safe_stem}_clauses"
#     os.makedirs(chroma_db_dir, exist_ok=True)
#     return chroma_db_dir, collection_name

# # ── Sidebar — API Key ──────────────────────────────────────────────────────────

# with st.sidebar:
#     st.header("🔑 Configuration")
#     groq_api_key = st.text_input(
#         "Groq API Key",
#         type="password",
#         placeholder="gsk_...",
#         help="Enter your Groq API key to enable AI-powered Q&A."
#     )
#     st.markdown("---")
#     st.caption("Model: `llama-3.1-8b-instant`")
#     if groq_api_key:
#         st.success("API key loaded ✓", icon="✅")
#     else:
#         st.warning("API key required for Q&A", icon="⚠️")


# # ── Utility: LLM ──────────────────────────────────────────────────────────────

# def get_llm(api_key: str) -> ChatGroq:
#     return ChatGroq(api_key=api_key, model=GROQ_MODEL, temperature=0.2)


# # ── Utility: Query Helpers ─────────────────────────────────────────────────────

# def normalize_query(query: str) -> str:
#     return re.sub(r"\s+", " ", query.strip())


# def extract_clause_reference(query: str) -> Optional[Dict[str, Optional[str]]]:
#     q = normalize_query(query).lower()
#     subclause_match = re.search(r'clause\s+(\d+)\s*[\.\(]?\s*([a-zA-Z0-9]+)\)?', q)
#     clause_match    = re.search(r'clause\s+(\d+)', q)

#     if subclause_match:
#         clause_number = subclause_match.group(1)
#         subclause_id  = subclause_match.group(2)
#         if subclause_id != clause_number:
#             return {"clause_number": clause_number, "subclause_id": subclause_id.lower()}

#     if clause_match:
#         return {"clause_number": clause_match.group(1), "subclause_id": None}

#     return None


# def is_general_document_question(query: str) -> bool:
#     q = normalize_query(query).lower()
#     keywords = [
#         "what is the agreement about", "what is this agreement about",
#         "heading", "title", "summary", "about the agreement",
#         "agreement heading", "agreement title"
#     ]
#     return any(kw in q for kw in keywords)


# # ── Utility: Retrieval ─────────────────────────────────────────────────────────

# def normalize_results(results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
#     ids       = results.get("ids",       [[]])[0]
#     docs      = results.get("documents", [[]])[0]
#     metas     = results.get("metadatas", [[]])[0]
#     distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(ids)

#     matches = []
#     for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
#         meta = meta or {}
#         matches.append({
#             "id":                doc_id,
#             "document":          doc,
#             "distance":          dist,
#             "chunk_type":        meta.get("chunk_type", ""),
#             "agreement_heading": meta.get("agreement_heading", ""),
#             "clause_number":     str(meta.get("clause_number", "")),
#             "subclause_id":      str(meta.get("subclause_id", "")).lower(),
#             "source_file":       meta.get("source_file", "")
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
#     subclause_id  = subclause_id.lower().strip() if subclause_id else None
#     query_text    = normalize_query(query_text) or f"clause {clause_number}" + (f".{subclause_id}" if subclause_id else "")

#     if not clause_number:
#         return {"matches": []}

#     where_filter = (
#         {"$and": [{"clause_number": clause_number}, {"subclause_id": subclause_id}]}
#         if subclause_id
#         else {"clause_number": clause_number}
#     )

#     results = collection.query(
#         query_texts=[query_text],
#         n_results=n_results,
#         where=where_filter,
#         include=["documents", "metadatas", "distances"]
#     )
#     return normalize_results(results)


# def retrieve_document_summary(collection, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
#     return retrieve_by_query(collection, query, n_results=n_results)


# # ── Utility: Context Formatter ─────────────────────────────────────────────────

# def format_context(results: Dict[str, List[Dict[str, Any]]], max_chunks: int = 5) -> Dict[str, Any]:
#     matches = results.get("matches", [])[:max_chunks]

#     if not matches:
#         return {"context_text": "", "sources": [], "matches": []}

#     context_blocks, sources, seen_docs = [], [], set()

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
#             "source_id":         index,
#             "id":                match.get("id", ""),
#             "clause_number":     match.get("clause_number", ""),
#             "subclause_id":      match.get("subclause_id", ""),
#             "agreement_heading": match.get("agreement_heading", ""),
#             "source_file":       match.get("source_file", ""),
#             "distance":          match.get("distance", None)
#         })

#     return {
#         "context_text": "\n\n".join(context_blocks),
#         "sources":      sources,
#         "matches":      matches
#     }


# # ── Utility: LLM Answer ────────────────────────────────────────────────────────

# SYSTEM_PROMPT = """You are a highly accurate legal contract analysis assistant.
# You are given excerpts from a contract document as context. Your job is to answer the user's question strictly based on the provided context.

# Rules:
# - Answer only from the provided context. Do NOT use outside knowledge.
# - If the context does not contain enough information, say: "The provided contract clauses do not contain sufficient information to answer this question."
# - Be concise, precise, and professional.
# - If referencing specific clauses, mention them explicitly (e.g., "As per Clause 3.2...").
# - Do NOT hallucinate clause numbers or obligations not present in the context.
# """

# # def generate_answer(query: str, context_text: str, llm: ChatGroq) -> str:
# #     if not context_text.strip():
# #         return "No relevant contract clauses were retrieved to answer your question."

# #     human_message = f"""Context from Contract:
# # \"\"\"
# # {context_text}
# # \"\"\"

# # Question: {query}

# # Answer:"""

# #     messages = [
# #         SystemMessage(content=SYSTEM_PROMPT),
# #         HumanMessage(content=human_message)
# #     ]
# #     response = llm.invoke(messages)
# #     return response.content.strip()
# def generate_answer(query: str, context_text: str, llm: ChatGroq, chat_history: list) -> str:
#     if not context_text.strip():
#         return "No relevant contract clauses were retrieved to answer your question."

#     # Build history messages (last 6 turns = 3 exchanges, to stay within token limits)
#     history_messages = []
#     for msg in chat_history[-6:]:
#         if msg["role"] == "user":
#             history_messages.append(HumanMessage(content=msg["content"]))
#         elif msg["role"] == "assistant":
#             history_messages.append(AIMessage(content=msg["content"]))

#     human_message = f"""Context from Contract:
# \"\"\"
# {context_text}
# \"\"\"

# Question: {query}

# Answer:"""

#     messages = [
#         SystemMessage(content=SYSTEM_PROMPT),
#         *history_messages,           # ← inject prior conversation
#         HumanMessage(content=human_message)
#     ]

#     response = llm.invoke(messages)
#     return response.content.strip()



# # ── Tabs Layout ────────────────────────────────────────────────────────────────

# st.title("📄 Contract Analyzer")

# tab1, tab2 = st.tabs(["📥 Data Ingestion", "💬 Query Contract"])


# # ══════════════════════════════════════════════════════════════════════════════
# # TAB 1 — Data Ingestion
# # ══════════════════════════════════════════════════════════════════════════════

# with tab1:
#     st.subheader("Data Ingestion Pipeline")
#     st.write("Upload a contract file in `.docx` format. The system will parse clauses and store them in the vector database.")

#     uploaded_file = st.file_uploader("Upload Contract (.docx)", type=["docx"])

#     if uploaded_file is not None:
#         filename         = uploaded_file.name
#         stem             = os.path.splitext(filename)[0]
#         file_path        = os.path.join(RAW_DIR,    filename)
#         output_path      = os.path.join(PARSED_DIR, f"{stem}_clauses.json")
#         output_path_text = os.path.join(PARSED_DIR, f"{stem}.txt")

#         chroma_db_dir, collection_name = get_contract_config(stem)

#         st.markdown("**Resolved Paths**")
#         st.code(
#             f"Input file     : {file_path}\n"
#             f"Clause JSON    : {output_path}\n"
#             f"Debug TXT      : {output_path_text}\n"
#             f"ChromaDB dir   : {chroma_db_dir}\n"
#             f"Collection     : {collection_name}"
#         )

#         if st.button("Run Ingestion Pipeline"):
#             with open(file_path, "wb") as f:
#                 f.write(uploaded_file.getbuffer())
#             st.info(f"File saved to: `{file_path}`")


#             config = DataIngestionConfig(
#                 file_path        = file_path,
#                 output_path      = output_path,
#                 output_path_text = output_path_text,
#                 chroma_db_dir    = chroma_db_dir,
#                 collection_name  = collection_name
#             )

#             with st.spinner("Running ingestion pipeline..."):
#                 try:
#                     artifact = run_data_ingestion_pipeline(config)
#                     st.success("✅ Ingestion completed successfully.")
#                     st.markdown(f"- Clause JSON saved to `{output_path}`")
#                     st.markdown(f"- Records inserted into ChromaDB collection `{collection_name}`")
#                     # Persist artifact in session so Q&A tab can detect it
#                     st.session_state["active_chroma_db_dir"]   = chroma_db_dir
#                     st.session_state["active_collection_name"] = collection_name
#                     st.session_state["active_contract_name"]   = filename
#                     st.session_state["ingestion_done"]         = True
#                     st.session_state["ingestion_done"] = True
#                     if "chroma_collection" in st.session_state:
#                         del st.session_state["chroma_collection"]
#                 except Exception as e:
#                     st.error(f"Pipeline failed: {e}")


# with tab2:
#     st.subheader("Ask Questions About Your Contract")

#     # Guard: API key
#     if not groq_api_key:
#         st.warning("⚠️ Please enter your Groq API key in the left sidebar to use Q&A.")
#         st.stop()

#     # Read active contract info from session state
#     active_chroma_db_dir   = st.session_state.get("active_chroma_db_dir")
#     active_collection_name = st.session_state.get("active_collection_name")
#     active_contract_name   = st.session_state.get("active_contract_name", "Unknown")

#     # Guard: ChromaDB must exist
#     chroma_ready = (
#         active_chroma_db_dir is not None
#         and os.path.exists(active_chroma_db_dir)
#         and bool(os.listdir(active_chroma_db_dir))
#     )
#     if not chroma_ready:
#         st.info("ℹ️ No vector store found yet. Please run the ingestion pipeline first (Tab 1).")
#         st.stop()

#     # Show which contract is currently active
#     st.caption(f"📄 Active contract: **{active_contract_name}** · Collection: `{active_collection_name}`")

#     # Load ChromaDB collection into session state (reloads when new contract is ingested)
#     if "chroma_collection" not in st.session_state:
#         try:
#             client = chromadb.PersistentClient(path=active_chroma_db_dir)
#             st.session_state["chroma_collection"] = client.get_collection(name=active_collection_name)
#         except Exception as e:
#             st.error(f"Failed to load ChromaDB collection: {e}")
#             st.stop()

#     collection = st.session_state["chroma_collection"]

#     # Initialize chat history
#     if "chat_history" not in st.session_state:
#         st.session_state["chat_history"] = []

#     # Render existing chat messages
#     for message in st.session_state["chat_history"]:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     # Chat input
#     user_query = st.chat_input("Ask something about the contract...")

#     if user_query:
#         # Display user message
#         with st.chat_message("user"):
#             st.markdown(user_query)
#         st.session_state["chat_history"].append({"role": "user", "content": user_query})

#         answer = ""  # ← ensures answer is always defined before appending to history

#         with st.chat_message("assistant"):
#             with st.spinner("Retrieving clauses and generating answer..."):
#                 try:
#                     llm        = get_llm(groq_api_key)
#                     clause_ref = extract_clause_reference(user_query)

#                     # ── Retrieval ──────────────────────────────────────────────
#                     if clause_ref:
#                         clause_number = clause_ref["clause_number"]
#                         subclause_id  = clause_ref["subclause_id"]
#                         results = retrieve_by_clause(
#                             collection    = collection,
#                             clause_number = clause_number,
#                             subclause_id  = subclause_id,
#                             query_text    = user_query,
#                             n_results     = 5
#                         )
#                         if not results["matches"]:
#                             results = retrieve_by_query(collection, user_query, n_results=5)

#                     elif is_general_document_question(user_query):
#                         results = retrieve_document_summary(collection, user_query, n_results=5)

#                     else:
#                         results = retrieve_by_query(collection, user_query, n_results=5)

#                     # ── Format & Generate ──────────────────────────────────────
#                     formatted    = format_context(results, max_chunks=5)
#                     context_text = formatted["context_text"]
#                     # answer       = generate_answer(user_query, context_text, llm)
#                     answer = generate_answer(
#                         user_query,
#                         context_text,
#                         llm,
#                         st.session_state["chat_history"]   # ← pass history
#                     )

#                     st.markdown(answer)

#                     # ── Sources Expander ───────────────────────────────────────
#                     if formatted["sources"]:
#                         with st.expander("📎 Retrieved Clause Sources", expanded=False):
#                             for src in formatted["sources"]:
#                                 st.markdown(
#                                     f"**Source {src['source_id']}** | "
#                                     f"Clause `{src['clause_number']}` "
#                                     f"{'· Sub `' + src['subclause_id'] + '`' if src['subclause_id'] else ''} | "
#                                     f"Agreement: *{src['agreement_heading']}* | "
#                                     f"File: `{src['source_file']}` | "
#                                     f"Distance: `{round(src['distance'], 4) if src['distance'] is not None else 'N/A'}`"
#                                 )

#                 except Exception as e:
#                     answer = f"❌ Error: {e}"
#                     st.error(answer)

#         st.session_state["chat_history"].append({"role": "assistant", "content": answer})

#     # Clear chat button
#     if st.session_state.get("chat_history"):
#         if st.button("🗑️ Clear Chat History"):
#             st.session_state["chat_history"] = []
#             st.rerun()




import os
import re
from typing import Optional, Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import streamlit as st
import chromadb
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from src.config import DataIngestionConfig
from src.pipeline.data_ingestion import run_data_ingestion_pipeline

# ── Constants ──────────────────────────────────────────────────────────────────

RAW_DIR         = os.path.join("data", "raw")
PARSED_DIR      = os.path.join("data", "parsed")
GROQ_MODEL      = "llama-3.1-8b-instant"

os.makedirs(RAW_DIR,       exist_ok=True)
os.makedirs(PARSED_DIR,    exist_ok=True)

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Contract Analyzer", layout="wide")

def get_contract_config(stem: str):
    """Derive unique ChromaDB dir and collection name from the file stem."""
    safe_stem = re.sub(r"[^a-zA-Z0-9_\\-]", "_", stem).lower()
    chroma_db_dir   = os.path.join("vectorstore", safe_stem)
    collection_name = f"{safe_stem}_clauses"
    os.makedirs(chroma_db_dir, exist_ok=True)
    return chroma_db_dir, collection_name

# ── Sidebar — API Key ──────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔑 Configuration")
    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Enter your Groq API key to enable AI-powered Q&A."
    )
    st.markdown("---")
    st.caption("Model: `llama-3.1-8b-instant`")
    if groq_api_key:
        st.success("API key loaded ✓", icon="✅")
    else:
        st.warning("API key required for Q&A", icon="⚠️")

# ── Utility: LLM ──────────────────────────────────────────────────────────────

def get_llm(api_key: str) -> ChatGroq:
    return ChatGroq(api_key=api_key, model=GROQ_MODEL, temperature=0.2)

# ── Utility: Query Helpers ─────────────────────────────────────────────────────

def normalize_query(query: str) -> str:
    return re.sub(r"\\s+", " ", query.strip())

def extract_clause_reference(query: str) -> Optional[Dict[str, Optional[str]]]:
    """Enhanced regex to catch all clause reference patterns."""
    q = normalize_query(query).lower()
    
    # More comprehensive clause patterns
    subclause_patterns = [
        r'clause\s+(\d+)\s*[\.\(]?\s*([a-zA-Z0-9]+)',
        r'clause\s+(\d+)[a-z]?\s*\.?\s*([a-zA-Z0-9]+)',
        r'cl\s+(\d+)\.?\s*([a-zA-Z0-9]+)',
        r'clause\s+(\d+)[a-z]?',
        r'cl\s+(\d+)'
    ]
    
    for pattern in subclause_patterns:
        subclause_match = re.search(pattern, q)
        if subclause_match:
            clause_number = subclause_match.group(1)
            if len(subclause_match.groups()) > 1 and subclause_match.group(2):
                subclause_id = subclause_match.group(2).lower()
                if subclause_id != clause_number:  # Ensure it's actually a subclause
                    return {"clause_number": clause_number, "subclause_id": subclause_id}
            else:
                return {"clause_number": clause_number, "subclause_id": None}
    
    return None

def is_general_document_question(query: str) -> bool:
    q = normalize_query(query).lower()
    keywords = [
        "what is the agreement about", "what is this agreement about",
        "heading", "title", "summary", "about the agreement",
        "agreement heading", "agreement title"
    ]
    return any(kw in q for kw in keywords)

# ── Utility: EXACT Clause Retrieval (NEW) ──────────────────────────────────────

def retrieve_exact_clause(collection, clause_number: str, subclause_id: Optional[str] = None, n_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """Retrieve EXACT clause matches using metadata filter ONLY (no embeddings)."""
    clause_number = str(clause_number).strip()
    
    if not clause_number:
        return {"matches": []}
    
    where_filter = (
        {"$and": [{"clause_number": clause_number}, {"subclause_id": {"$eq": subclause_id}}]}
        if subclause_id
        else {"clause_number": clause_number}
    )
    
    # Use empty query to avoid embedding similarity - pure metadata match
    results = collection.query(
        query_texts=[""],  # Empty query = no embedding similarity
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )
    
    return normalize_results(results)

def retrieve_exact_clause_plus_similar(collection, clause_number: str, subclause_id: Optional[str] = None, 
                                     query_text: str = "", n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """Get exact clause + semantically similar clauses for context."""
    # 1. Get EXACT clause first (priority)
    exact_results = retrieve_exact_clause(collection, clause_number, subclause_id, n_results=2)
    
    # 2. Get similar clauses around the same clause number for context
    query = normalize_query(query_text or f"clause {clause_number}")
    similar_results = retrieve_by_clause(
        collection, clause_number, subclause_id, query, n_results=3
    )
    
    # 3. Combine: exact first, then similar (deduplicate)
    all_matches = exact_results["matches"] + [m for m in similar_results["matches"] 
                                             if m["id"] not in {x["id"] for x in exact_results["matches"]}]
    
    return {"matches": all_matches[:n_results]}

# ── Utility: Retrieval ─────────────────────────────────────────────────────────

def normalize_results(results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    ids       = results.get("ids",       [[]])[0]
    docs      = results.get("documents", [[]])[0]
    metas     = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(ids)

    matches = []
    for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
        meta = meta or {}
        matches.append({
            "id":                doc_id,
            "document":          doc,
            "distance":          dist,
            "chunk_type":        meta.get("chunk_type", ""),
            "agreement_heading": meta.get("agreement_heading", ""),
            "clause_number":     str(meta.get("clause_number", "")),
            "subclause_id":      str(meta.get("subclause_id", "")).lower(),
            "source_file":       meta.get("source_file", "")
        })
    return {"matches": matches}

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
    subclause_id  = subclause_id.lower().strip() if subclause_id else None
    query_text    = normalize_query(query_text) or f"clause {clause_number}" + (f".{subclause_id}" if subclause_id else "")

    if not clause_number:
        return {"matches": []}

    where_filter = (
        {"$and": [{"clause_number": clause_number}, {"subclause_id": subclause_id}]}
        if subclause_id
        else {"clause_number": clause_number}
    )

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )
    return normalize_results(results)

def retrieve_document_summary(collection, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    return retrieve_by_query(collection, query, n_results=n_results)

# ── Utility: Context Formatter ─────────────────────────────────────────────────

def format_context(results: Dict[str, List[Dict[str, Any]]], max_chunks: int = 5) -> Dict[str, Any]:
    matches = results.get("matches", [])[:max_chunks]

    if not matches:
        return {"context_text": "", "sources": [], "matches": []}

    context_blocks, sources, seen_docs = [], [], set()

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
            "source_id":          index,
            "id":                 match.get("id", ""),
            "clause_number":      match.get("clause_number", ""),
            "subclause_id":       match.get("subclause_id", ""),
            "agreement_heading":  match.get("agreement_heading", ""),
            "source_file":        match.get("source_file", ""),
            "distance":           match.get("distance", None)
        })

    return {
        "context_text": "\n\n".join(context_blocks),
        "sources":       sources,
        "matches":       matches
    }

# ── Utility: LLM Answer ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a highly accurate legal contract analysis assistant.
You are given excerpts from a contract document as context. Your job is to answer the user's question strictly based on the provided context.

Rules:
- Answer only from the provided context. Do NOT use outside knowledge.
- If the context does not contain enough information, say: "The provided contract clauses do not contain sufficient information to answer this question."
- Be concise, precise, and professional.
- If referencing specific clauses, mention them explicitly (e.g., "As per Clause 3.2...").
- Do NOT hallucinate clause numbers or obligations not present in the context.
"""

def generate_answer(query: str, context_text: str, llm: ChatGroq, chat_history: list) -> str:
    if not context_text.strip():
        return "No relevant contract clauses were retrieved to answer your question."

    # Build history messages (last 6 turns = 3 exchanges, to stay within token limits)
    history_messages = []
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_messages.append(AIMessage(content=msg["content"]))

    human_message = f"""Context from Contract: {context_text} Question: {query} Answer:"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *history_messages,           # ← inject prior conversation
        HumanMessage(content=human_message)
    ]

    response = llm.invoke(messages)
    return response.content.strip()

# ── Tabs Layout ────────────────────────────────────────────────────────────────

st.title("📄 Contract Analyzer")

tab1, tab2 = st.tabs(["📥 Data Ingestion", "💬 Query Contract"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Data Ingestion
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Data Ingestion Pipeline")
    st.write("Upload a contract file in `.docx` format. The system will parse clauses and store them in the vector database.")

    uploaded_file = st.file_uploader("Upload Contract (.docx)", type=["docx"])

    if uploaded_file is not None:
        filename         = uploaded_file.name
        stem             = os.path.splitext(filename)[0]
        file_path        = os.path.join(RAW_DIR,    filename)
        output_path      = os.path.join(PARSED_DIR, f"{stem}_clauses.json")
        output_path_text = os.path.join(PARSED_DIR, f"{stem}.txt")

        chroma_db_dir, collection_name = get_contract_config(stem)

        st.markdown("**Resolved Paths**")
        st.code(
            f"Input file     : {file_path}\n"
            f"Clause JSON    : {output_path}\n"
            f"Debug TXT      : {output_path_text}\n"
            f"ChromaDB dir   : {chroma_db_dir}\n"
            f"Collection     : {collection_name}"
        )

        if st.button("Run Ingestion Pipeline"):
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.info(f"File saved to: `{file_path}`")

            config = DataIngestionConfig(
                file_path        = file_path,
                output_path      = output_path,
                output_path_text = output_path_text,
                chroma_db_dir    = chroma_db_dir,
                collection_name  = collection_name
            )

            with st.spinner("Running ingestion pipeline..."):
                try:
                    artifact = run_data_ingestion_pipeline(config)
                    st.success("✅ Ingestion completed successfully.")
                    st.markdown(f"- Clause JSON saved to `{output_path}`")
                    st.markdown(f"- Records inserted into ChromaDB collection `{collection_name}`")
                    # Persist artifact in session so Q&A tab can detect it
                    st.session_state["active_chroma_db_dir"]   = chroma_db_dir
                    st.session_state["active_collection_name"] = collection_name
                    st.session_state["active_contract_name"]   = filename
                    st.session_state["ingestion_done"]         = True
                    if "chroma_collection" in st.session_state:
                        del st.session_state["chroma_collection"]
                except Exception as e:
                    st.error(f"Pipeline failed: {e}")

with tab2:
    st.subheader("Ask Questions About Your Contract")

    # Guard: API key
    if not groq_api_key:
        st.warning("⚠️ Please enter your Groq API key in the left sidebar to use Q&A.")
        st.stop()

    # Read active contract info from session state
    active_chroma_db_dir   = st.session_state.get("active_chroma_db_dir")
    active_collection_name = st.session_state.get("active_collection_name")
    active_contract_name   = st.session_state.get("active_contract_name", "Unknown")

    # Guard: ChromaDB must exist
    chroma_ready = (
        active_chroma_db_dir is not None
        and os.path.exists(active_chroma_db_dir)
        and bool(os.listdir(active_chroma_db_dir))
    )
    if not chroma_ready:
        st.info("ℹ️ No vector store found yet. Please run the ingestion pipeline first (Tab 1).")
        st.stop()

    # Show which contract is currently active
    st.caption(f"📄 Active contract: **{active_contract_name}** · Collection: `{active_collection_name}`")

    # Load ChromaDB collection into session state (reloads when new contract is ingested)
    if "chroma_collection" not in st.session_state:
        try:
            client = chromadb.PersistentClient(path=active_chroma_db_dir)
            st.session_state["chroma_collection"] = client.get_collection(name=active_collection_name)
        except Exception as e:
            st.error(f"Failed to load ChromaDB collection: {e}")
            st.stop()

    collection = st.session_state["chroma_collection"]

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Render existing chat messages
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_query = st.chat_input("Ask something about the contract...")

    if user_query:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state["chat_history"].append({"role": "user", "content": user_query})

        answer = ""  # ← ensures answer is always defined before appending to history

        with st.chat_message("assistant"):
            with st.spinner("Retrieving clauses and generating answer..."):
                try:
                    llm          = get_llm(groq_api_key)
                    clause_ref   = extract_clause_reference(user_query)

                    # ── ENHANCED RETRIEVAL LOGIC ─────────────────────────────────────────
                    if clause_ref:
                        # **PRIORITY 1**: Exact clause retrieval when explicitly mentioned
                        st.info(f"🎯 Detected clause reference: Clause {clause_ref['clause_number']}{'.' + clause_ref['subclause_id'] if clause_ref['subclause_id'] else ''}")
                        results = retrieve_exact_clause_plus_similar(
                            collection=collection,
                            clause_number=clause_ref["clause_number"],
                            subclause_id=clause_ref["subclause_id"],
                            query_text=user_query,
                            n_results=5
                        )
                        
                        # Fallback to semantic search only if exact clause not found
                        if not results["matches"]:
                            st.warning("⚠️ Exact clause not found, falling back to semantic search...")
                            results = retrieve_by_query(collection, user_query, n_results=5)
                            
                    elif is_general_document_question(user_query):
                        results = retrieve_document_summary(collection, user_query, n_results=5)
                        
                    else:
                        results = retrieve_by_query(collection, user_query, n_results=5)

                    # ── Format & Generate ──────────────────────────────────────
                    formatted     = format_context(results, max_chunks=5)
                    context_text  = formatted["context_text"]
                    answer = generate_answer(
                        user_query,
                        context_text,
                        llm,
                        st.session_state["chat_history"]
                    )

                    st.markdown(answer)

                    # ── Sources Expander ───────────────────────────────────────
                    if formatted["sources"]:
                        with st.expander("📎 Retrieved Clause Sources", expanded=False):
                            for src in formatted["sources"]:
                                subclause_text = f"· Sub `{src['subclause_id']}`" if src['subclause_id'] else ""
                                st.markdown(
                                    f"**Source {src['source_id']}** | "
                                    f"Clause `{src['clause_number']}`{subclause_text} | "
                                    f"Agreement: *{src['agreement_heading']}* | "
                                    f"File: `{src['source_file']}` | "
                                    f"Distance: `{round(src['distance'], 4) if src['distance'] is not None else 'N/A'}`"
                                )

                except Exception as e:
                    answer = f"❌ Error: {e}"
                    st.error(answer)

        st.session_state["chat_history"].append({"role": "assistant", "content": answer})

    # Clear chat button
    if st.session_state.get("chat_history"):
        if st.button("🗑️ Clear Chat History"):
            st.session_state["chat_history"] = []
            st.rerun()