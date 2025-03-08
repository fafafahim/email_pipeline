#!/usr/bin/env python3
import os
import argparse
import json
import time
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env
load_dotenv()

########################################
# Azure OpenAI configuration
########################################
API_KEY     = os.getenv("OPENAI_API_KEY")
API_BASE    = os.getenv("AZURE_ENDPOINT")
API_VERSION = "2024-12-01-preview"

########################################
# Helper: Call Azure OpenAI with token usage tracking
########################################
def call_azure(model_name: str, prompt_text: str, max_tokens: int,
               reasoning_effort_o1: str = "high", reasoning_effort_o3mini: str = "low",
               request_timeout_o1: int = 600, request_timeout_o3mini: int = 6000, request_timeout_gpt4o: int = 600) -> (str, dict):
    client = AzureOpenAI(
        azure_endpoint=API_BASE,
        api_key=API_KEY,
        api_version=API_VERSION
    )
    extra_params = {}
    req_timeout = None

    if model_name.startswith("o1"):
        extra_params["reasoning_effort"] = reasoning_effort_o1
        req_timeout = request_timeout_o1
    elif model_name.startswith("o3-mini"):
        extra_params["reasoning_effort"] = reasoning_effort_o3mini
        req_timeout = request_timeout_o3mini
    elif model_name.startswith("gpt-4o"):
        req_timeout = request_timeout_gpt4o
    else:
        req_timeout = 60

    messages = [
        {
            "role": "system",
            "content": "You are an early stage entrepreneur reaching out to people to conduct needs assessment."
        },
        {"role": "user", "content": prompt_text},
    ]

    if model_name.startswith("gpt-4o"):
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            timeout=req_timeout,
            max_tokens=max_tokens,
            **extra_params
        )
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens,
            timeout=req_timeout
        )

    content = response.choices[0].message.content.strip()
    usage = response.usage if hasattr(response, "usage") else {}
    if hasattr(usage, "dict"):
        usage = usage.dict()
    return content, usage

########################################
# Helper: Deduplicate and combine prospect information
#
# Combines the following keys from the record:
#   - engagements_combined / engagements_combined_citation_mapping
#   - roles_and_responsibilities / roles_and_responsibilities_citation_mapping
#   - background / background_citation_mapping
#
# The model is instructed to deduplicate redundant content while replacing
# inline citation markers with clickable HTML links.
#
# Expects a JSON response with one key "prospect_info" whose value is the deduplicated HTML.
########################################
def deduplicate_prospect_info(rec: dict) -> str:
    engagements   = rec.get("engagements_combined", "").strip()
    roles         = rec.get("roles_and_responsibilities", "").strip()
    background    = rec.get("background", "").strip()


    prompt = f"""
You are provided with three content blocks and their corresponding citation mappings.
The content blocks are labeled as follows:

Content 1 (from "engagements_combined"):
```{engagements}```

Content 2 (from "roles_and_responsibilities"):
```{roles}```

Content 3 (from "background"):
```{background}```

Your tasks:
1. Combine these three content blocks into a single deduplicated prospect information text.
2. Remove duplicate content that appear across the blocks while preserving the overall meaning. However, if content add additional context or details, it should be retained.
3. Retain every citation marker present in the content (e.g., [1]), replace it with an inline clickable HTML anchor tag using the provided citation mapping. For example, if the citation mapping for "1" gives a URL, then the marker should become: [1](http://www.website-name.com).
4. **Output ONLY one valid markdown object with one key "prospect_info". Do not include any additional text or explanation.**
"""
    print("Deduplicating prospect info for a record...")
    response_text, usage = call_azure(MODEL_NAME, prompt, max_tokens=10000)
    
    # Directly assign the raw markdown response to prospect_info
    prospect_info = response_text

    return prospect_info

########################################
# Main function: Process JSON data and store output in a JSON file
########################################
def main():
    script_dir = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(
        description=(
            "Deduplicate and combine prospect content using Azure OpenAI GPT‑4o, "
            "and store the deduplicated output with a new key 'prospect_info' into a JSON file."
        )
    )
    parser.add_argument("--input-json", type=str, default=os.path.join(script_dir, "../../output/3final_combined_research_cited.json"),
                        help="Input JSON file containing the records (default: 3final_combined_research_cited.json)")
    parser.add_argument("--output-json", type=str, default=os.path.join(script_dir, "../../output/4cited_deduplicated_content.json"),
                        help="Output JSON file to store records with 'prospect_info'")
    args = parser.parse_args()

    # Load JSON records (expected to be an array of objects)
    with open(args.input_json, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {args.input_json}")

    # Process each record: generate deduplicated prospect_info
    for idx, rec in enumerate(records):
        prospect_info = deduplicate_prospect_info(rec)
        rec["prospect_info"] = prospect_info
        # Exclude specified keys from the output
        exclusion_keys = [
            "email_subject_prompt_tokens", "email_subject_completion_tokens", "email_subject_total_tokens",
            "most_relevant_topic_prompt_tokens", "most_relevant_topic_completion_tokens", "most_relevant_topic_total_tokens",
            "researching_topic_prompt_tokens", "researching_topic_completion_tokens", "researching_topic_total_tokens",
            "relevant_painpoint_prompt_tokens", "relevant_painpoint_completion_tokens", "relevant_painpoint_total_tokens",
            "email_body_prompt_tokens", "email_body_completion_tokens", "email_body_total_tokens",
            "total_cost"
        ]
        for key in exclusion_keys:
            rec.pop(key, None)
        print(f"Processed record {idx + 1}/{len(records)}.")

    # Write the updated records to the output JSON file
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Deduplicated JSON output saved to {args.output_json}")

if __name__ == "__main__":
    # Define your deployment name 
    MODEL_NAME = "o3-mini"
    main()