########################################
# To write each record as it processes it, you can modify the main function to append each processed record to the output JSON file immediately after conversion.
########################################

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
            "content": "You are a converter that converts markdown to clean HTML while preserving inline citation links."
        },
        {"role": "user", "content": prompt_text},
    ]

    # For gpt-4o, pass max_tokens normally; otherwise, use max_completion_tokens.
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
# Helper: Convert Markdown to HTML
########################################
def convert_markdown_to_html(markdown_content: str, model_name: str = "o3-mini") -> str:
    # The prompt instructs the model to convert markdown to HTML,
    # preserving clickable inline citation links.
    prompt = f"""
Convert the following markdown content into valid HTML.
Ensure that inline citations (e.g. [1](https://www.example.com)) are retained as clickable hyperlinks (e.g. <a href=\"https://www.example.com" target=\"_blank\">[1]</a>).
Do not include any extra explanation; output only valid HTML code.
    
{markdown_content}
"""
    html_content, _ = call_azure(model_name, prompt, max_tokens=10000)
    return html_content

########################################
# Main function: Process JSON data and store output
########################################
def main():
    script_dir = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(
        description="Convert markdown fields in the cited deduplicated content JSON to HTML."
    )
    parser.add_argument("--input-json", type=str, default=os.path.join(script_dir, "../../output/4cited_deduplicated_content.json"),
                        help="Input JSON file containing the cited_deduplicated_content")
    parser.add_argument("--output-json", type=str, default=os.path.join(script_dir, "../../output/5html_converted_content.json"),
                        help="Output JSON file with HTML-converted content")
    parser.add_argument("--model-name", type=str, default="o3-mini", help="Model to use for conversion")
    args = parser.parse_args()

    # Load JSON records (expected to be an array of objects following the schema)
    with open(args.input_json, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {args.input_json}")

    # Define the fields that need markdown-to-HTML conversion.
    # Other fields (e.g., Email, Person Linkedin Url, etc.) will remain unchanged.
    fields_to_convert = [
        "company_background",
        "engagements_combined",
        "roles_and_responsibilities",
        "background",
        "prospect_info"
    ]

    # Open the output JSON file in append mode
    with open(args.output_json, "w", encoding="utf-8") as f:
        f.write("[\n")  # Start the JSON array

        # Process each record: convert specified fields from markdown to HTML.
        for idx, rec in enumerate(records):
            for field in fields_to_convert:
                if field in rec and rec[field]:
                    markdown_text = rec[field]
                    html_text = convert_markdown_to_html(markdown_text, model_name=args.model_name)
                    rec[field] = html_text
            print(f"Converted record {idx + 1}/{len(records)}.")

            # Write the updated record to the output JSON file.
            json.dump(rec, f, indent=2, ensure_ascii=False)
            if idx < len(records) - 1:
                f.write(",\n")  # Add a comma between records

        f.write("\n]")  # End the JSON array
    print(f"HTML-converted JSON output saved to {args.output_json}")

if __name__ == "__main__":
    main()