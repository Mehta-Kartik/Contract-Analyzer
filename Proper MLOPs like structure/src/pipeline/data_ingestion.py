# from src.component.clause_parser import parse_clauses
# from src.component.vectorstore_ingestor import ingest_to_chroma
# from src.config import DataIngestionConfig
# from src.logger import logging
# from src.artifacts.artifact import DataIngestionArtifact
# # from chro//sma
# import chromadb

# def run_data_ingestion_pipeline(dataingestionconfig:DataIngestionConfig):
#     """
#     Orchestrates the full data ingestion pipeline:
#       Step 1: Parse .docx contract into structured clause JSON.
#       Step 2: Ingest clause JSON into ChromaDB.
#     """
#     config = dataingestionconfig

#     logging.info("Data ingestion pipeline started.")

#     # Step 1: Parse DOCX to JSON
#     logging.info("Step 1: Clause parsing started.")
#     json_path = parse_clauses(
#         file_path_docx=config.file_path,
#         output_path=config.output_path
#     )
#     logging.info("Step 1: Clause parsing completed.")

#     # Step 2: Ingest JSON to ChromaDB
#     logging.info("Step 2: ChromaDB ingestion started.")
#     ingest_to_chroma(
#         json_path=json_path,
#         chroma_db_dir=config.chroma_db_dir,
#         collection_name=config.collection_name
#     )
#     logging.info("Step 2: ChromaDB ingestion completed.")

#     logging.info("Data ingestion pipeline completed successfully.")

#     client = chromadb.PersistentClient(path=config.chroma_db_dir)
#     # embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
#     collection = client.get_collection(
#         name=config.collection_name,
#         # embedding_function=embedding_fn  # ← Required if you're passing query strings
#     )
#     # print(collection)
#     dataingestionartifact=DataIngestionArtifact(chroma_db_dir=config.chroma_db_dir,collection_name=config.collection_name)
#     return dataingestionartifact
#     # return config.chroma_db_dir,config.collection_name




# if __name__ == "__main__":
#     run_data_ingestion_pipeline()






from src.component.clause_parser import parse_clauses
from src.component.vectorstore_ingestor import ingest_to_chroma
from src.config import DataIngestionConfig
from src.logger import logging
from src.artifacts.artifact import DataIngestionArtifact

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from chromadb import Documents, EmbeddingFunction, Embeddings


from typing import Dict, Any

from sentence_transformers import SentenceTransformer
class LegalBGEEmbedding(EmbeddingFunction[Documents]):
    def __init__(self):
        self.model = SentenceTransformer("ArchitRastogi/BGE-Small-LegalEmbeddings-USCode")
    def __call__(self, input: Documents) -> Embeddings:
        texts = [str(doc) for doc in input]
        return self.model.encode(texts, normalize_embeddings=True).tolist()
    
def run_data_ingestion_pipeline(dataingestionconfig: DataIngestionConfig):
    """
    Orchestrates the full data ingestion pipeline:
      Step 1: Parse .docx contract into structured clause JSON.
      Step 2: Ingest clause JSON into ChromaDB using zembed-1.
    """
    config = dataingestionconfig

    logging.info("Data ingestion pipeline started.")

    embedding_fn = LegalBGEEmbedding()

    # Step 1: Parse DOCX to JSON
    logging.info("Step 1: Clause parsing started.")
    json_path = parse_clauses(
        file_path_docx=config.file_path,
        output_path=config.output_path
    )
    logging.info("Step 1: Clause parsing completed.")

    # Step 2: Ingest JSON to ChromaDB
    logging.info("Step 2: ChromaDB ingestion started.")
    ingest_to_chroma(
        json_path=json_path,
        chroma_db_dir=config.chroma_db_dir,
        collection_name=config.collection_name,
        embedding_function=embedding_fn
    )
    logging.info("Step 2: ChromaDB ingestion completed.")

    logging.info("Data ingestion pipeline completed successfully.")

    client = chromadb.PersistentClient(path=config.chroma_db_dir)
    
    collection = client.get_collection(
        name=config.collection_name,
        embedding_function=embedding_fn
    )

    dataingestionartifact = DataIngestionArtifact(
        chroma_db_dir=config.chroma_db_dir,
        collection_name=config.collection_name
    )
    return dataingestionartifact


if __name__ == "__main__":
    run_data_ingestion_pipeline()