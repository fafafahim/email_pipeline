import json
import os

# Define relative paths
script_dir = os.path.dirname(__file__)
input_json = os.path.join(script_dir, "../../output/3final_combined_research_cited.json")
output_json = os.path.join(script_dir, "../../output/3final_combined_research_cited.json")

# Use if fields need to be added after content has been converted to HTML
# input_json = os.path.join(script_dir, "../../output/5html_converted_content.json")
# output_json = os.path.join(script_dir, "../../output/5html_converted_content.json")



with open(input_json, "r", encoding="utf-8") as f:
    all_records = json.load(f)

filtered_records = []
for record in all_records:
    # Add the 'exclude' key to each record
    record["exclude"] = False
    record["email_feedback"] = ""
    record["flag"] = False
    record["viewed"] = False
    record["exported"] = False
    filtered_records.append(record)

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(filtered_records, f, indent=2)

print(f"Filtered records written to {output_json}")