import re
import json
import os

# Define relative paths
script_dir = os.path.dirname(__file__)
input_file = os.path.join(script_dir, "../../output/1perplexity_results.jsonl")
output_file = os.path.join(script_dir, "../../output/1perplexity_results.json")

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Remove any line that starts with // (ignoring whitespace)
fixed_lines = [line for line in lines if not re.match(r'^\s*//', line)]

fixed_json_str = "".join(fixed_lines)

# Optionally, if your file should contain multiple JSON objects, wrap them in an array.
# For example, if the file contains multiple JSON objects on separate lines,
# you can split by line and wrap with [ and ].
try:
    data = json.loads(fixed_json_str)
except json.JSONDecodeError:
    # If there are multiple JSON objects, split and wrap in an array:
    objects = []
    for line in fixed_lines:
        line = line.strip()
        if line:  # non-empty
            try:
                objects.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # Skip or handle any errors accordingly
    data = objects

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Fixed JSON written to {output_file}")