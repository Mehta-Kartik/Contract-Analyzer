from dataclasses import dataclass


@dataclass
class DataIngestionArtifact:
    chroma_db_dir:str
    collection_name:str
    