import re
import json

file_path = r"D:\ProjectAarya\Contract Analyzer\data\parsed\AGREEMENT FOR BUILDING WHERE OWNER SUPPLIES PLOT AND ALL MATERIALS.txt"
output_path = r"D:\ProjectAarya\Contract Analyzer\data\parsed\Atext1.json"

main_clause_pattern = re.compile(r'^\s*(\d+)[\.\)]?\s+(.*)')
numeric_subclause_pattern = re.compile(r'^\s*(\d+\.\d+)[\.\)]?\s+(.*)')
alpha_subclause_pattern = re.compile(r'^\s*\(([a-zA-Z0-9]+)\)\s+(.*)')

stop_markers = [
    "IN WITNESS WHEREOF",
    "DATE:",
    "PLACE:",
    "WITNESSESS",
    "WITNESSES",
    "PARTY OF FIRST PART",
    "PARTY OF SECOND PART"
]

def is_stop_line(line: str) -> bool:
    upper_line = line.upper().strip()
    return any(marker in upper_line for marker in stop_markers)

clauses = []
current_clause = None
agreement_heading = None

with open(file_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

# Extract agreement heading: first non-empty line before clauses start
for line in lines:
    if main_clause_pattern.match(line):
        break
    if not agreement_heading:
        agreement_heading = line
        break

for line in lines:
    if is_stop_line(line):
        break

    numeric_sub_match = numeric_subclause_pattern.match(line)
    alpha_sub_match = alpha_subclause_pattern.match(line)
    main_match = main_clause_pattern.match(line)

    if numeric_sub_match and current_clause is not None:
        subclause_id = numeric_sub_match.group(1).strip()
        subclause_text = numeric_sub_match.group(2).strip()

        current_clause["subclauses"].append({
            "subclause_id": subclause_id,
            "text": subclause_text
        })

        current_clause["clause_text"].append(line)

    elif alpha_sub_match and current_clause is not None:
        subclause_id = alpha_sub_match.group(1).strip()
        subclause_text = alpha_sub_match.group(2).strip()

        current_clause["subclauses"].append({
            "subclause_id": subclause_id,
            "text": subclause_text
        })

        current_clause["clause_text"].append(line)

    elif main_match:
        clause_number = main_match.group(1).strip()
        clause_title = main_match.group(2).strip()

        if current_clause is not None:
            clauses.append(current_clause)

        current_clause = {
            "agreement_heading": agreement_heading,
            "clause_number": clause_number,
            "clause_title": clause_title,
            "clause_text": [],
            "subclauses": []
        }

    elif current_clause is not None:
        current_clause["clause_text"].append(line)

if current_clause is not None:
    clauses.append(current_clause)

for clause in clauses:
    clause["clause_text"] = "\n".join(clause["clause_text"]).strip()

final_json = {
    "agreement_heading": agreement_heading,
    "clauses": clauses
}

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=4, ensure_ascii=False)

print(f"Saved {len(clauses)} clauses to {output_path}")
print(f"Agreement heading: {agreement_heading}")