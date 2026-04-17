# Test DOCX parsing
from docx import Document
import os

file_path = "D:\ProjectAarya\Contract Analyzer\Templates\\agreement-between-manufacturer-and-dealer.docx"
doc = Document(file_path)
full_text = "\n".join([para.text for para in doc.paragraphs])

print("First 500 chars:")
print(full_text[:1000])
print(f"\nTotal lines: {len(full_text.splitlines())}")