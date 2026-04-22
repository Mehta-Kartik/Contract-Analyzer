import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DataIngestionConfig:
    # Input: raw .docx contract file
    file_path: str 

    # Output: intermediate JSON after clause parsing
    output_path: str 

    # Output: intermediate .txt file (optional, for debugging)
    output_path_text: str 

    # ChromaDB storage directory
    chroma_db_dir: str 

    # ChromaDB collection name
    collection_name: str 