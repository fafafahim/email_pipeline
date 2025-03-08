#!/usr/bin/env python3
import os
import argparse
import pandas as pd
import csv
from glob import glob
from dotenv import load_dotenv
from openai import AzureOpenAI
import time
import json

# Load .env variables
load_dotenv()

def append_record_to_json(record: dict, output_json: str):
    # If the file already exists, load its JSON content;
    # otherwise initialize an empty list.
    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
    else:
        records = []
    records.append(record)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

########################################
# Prompt Config 
########################################
script_dir = os.path.dirname(__file__)
records_limit_value = None
input_name = os.path.join(script_dir, "../../output/5html_converted_content.json")
output_name = os.path.join(script_dir, "../../output/6email_feedback")    # don't include the .csv extension

########################################
# Prompt Config 
########################################
PROMPT_CONFIGS = [
    {
        "name": "content_after_feedback",
        "prompt_path": os.path.join(script_dir, "../../src/prompts/content_after_feedback.txt"),
        "model_name": "o1",
        "output_key": "content_after_feedback",        
        "max_completion_tokens": 10000       
    },
    {
        "name": "email_after_feedback",
        "prompt_path": os.path.join(script_dir, "../../src/prompts/email_after_feedback.txt"),
        "model_name": "o1",
        "output_key": "email_after_feedback",        
        "max_completion_tokens": 10000       
    },
    {
        "name": "email_subject_after_feedback",
        "prompt_path": os.path.join(script_dir, "../../src/prompts/email_subject_after_feedback.txt"),
        "model_name": "o3-mini",
        "output_key": "email_subject_after_feedback",        
        "max_completion_tokens": 4000 
    },
    {
        "name": "email_subject_extract_after_feedback",
        "prompt_path": os.path.join(script_dir, "../../src/prompts/email_subject_extract_after_feedback.txt"),
        "model_name": "gpt-4o",
        "output_key": "email_subject_extract_after_feedback",        
        # "max_completion_tokens": 1000 
    }
]

########################################
# Pricing details (per 1,000,000 tokens)
########################################
PRICING = {
    "o1": {
        "input": 5.00,
        "output": 20.00,
    },
    "o3-mini": {
        "input": 1.10,
        "output": 4.40,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    }
}

# Rate limit delays (in seconds) computed from requests per minute limits.
RATE_LIMIT_DELAYS = {
    "o3-mini": 180 / 500,  # 0.36 seconds per request
    "o1": 180 / 500,       # 0.36 seconds per request
    "gpt-4o": 180 / 2700,   # ~0.066 seconds per request (you may choose a slightly higher value to be conservative)
}

########################################
# Helper: Prompt Replacement
########################################
def get_prompt(template: str, variables: dict) -> str:
    prompt = str(template)
    for key, val in variables.items():
        placeholder = "{" + key + "}"
        if placeholder in prompt:
            prompt = prompt.replace(placeholder, val)
    if "{" in prompt:
        idx = prompt.index("{")
        raise Exception(f"Unprocessed variable found at position {idx}: {prompt[idx:idx+30]}")
    return prompt

########################################
# Helper: Call Azure OpenAI with token usage tracking
########################################
API_KEY     = os.getenv("OPENAI_API_KEY")
API_BASE    = os.getenv("AZURE_ENDPOINT")
API_VERSION = "2024-12-01-preview"


def call_azure(model_name: str, prompt_text: str, max_tokens: int,
               reasoning_effort_o1: str = "high", reasoning_effort_o3mini: str = "medium",
               request_timeout_o1: int = 600, request_timeout_o3mini: int = 6000, request_timeout_gpt4o: int = 600) -> (str, dict):
    client = AzureOpenAI(
        azure_endpoint=API_BASE,
        api_key=API_KEY,
        api_version=API_VERSION
    )

    extra_params = {}  # default extra parameters
    req_timeout = None

    if model_name.startswith("o1"):
        req_timeout = request_timeout_o1
    elif model_name.startswith("o3-mini"):
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
    
    try:
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
                timeout=req_timeout,
                **extra_params
            )
    except TypeError as e:
        if "reasoning_effort" in str(e):
            extra_params.pop("reasoning_effort", None)
            if model_name.startswith("gpt-4o"):
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    timeout=req_timeout,
                    max_tokens=max_tokens
                )
            else:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                    timeout=req_timeout,
                    **extra_params
                )
        else:
            raise e

    content = response.choices[0].message.content.strip()
    usage = response.usage if hasattr(response, "usage") else {}
    if hasattr(usage, "dict"):
        usage = usage.dict()
    return content, usage


########################################
# Helper: Calculate Cost for a record
########################################
def calculate_cost(record):
    total_cost = 0.0
    for cfg in PROMPT_CONFIGS:
        model = cfg["model_name"]
        pricing = PRICING.get(model)
        if not pricing:
            continue
        key = cfg["output_key"]
        prompt_tokens = float(record.get(f"{key}_prompt_tokens", 0))
        completion_tokens = float(record.get(f"{key}_completion_tokens", 0))
        input_cost = pricing["input"] * (prompt_tokens / 1_000_000)
        output_cost = pricing["output"] * (completion_tokens / 1_000_000)
        total_cost += input_cost + output_cost
    return total_cost

########################################
# CLI Argument Parsing
########################################
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=str, default=input_name)
    # parser.add_argument("--output-csv", type=str, default=f"{output_name}.csv")
    parser.add_argument("--output-json", type=str, default=f"{output_name}.json")
    return parser.parse_args()

########################################
# Append a record to CSV (filtered to desired columns)
########################################
# def append_record(record: dict, output_csv: str, fieldnames: list):
#     file_exists = os.path.exists(output_csv)
#     filtered_record = { key: record.get(key, "") for key in fieldnames }
#     with open(output_csv, "a", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         if not file_exists:
#             writer.writeheader()
#         writer.writerow(filtered_record)

########################################
# Helper: Get desired output columns ordering
########################################
def get_desired_columns(df):
    desired_cols = [
        "First Name", "Last Name", "Title", "Company", "Company Name for Emails", 
        "Website", "Company Linkedin Url", "Facebook Url", "Email", "Person Linkedin Url",
        "most_relevant_topic", "researching_topic", "relevant_painpoint", 
        "email_body", "email_subject_extract", "email_subject",
        "background", "background_citation_mapping", "engagements_combined", "engagements_combined_citation_mapping", 
        "roles_and_responsibilities","roles_and_responsibilities_citation_mapping",
        # "email_subject_prompt_tokens", "email_subject_completion_tokens", "email_subject_total_tokens",
        # "most_relevant_topic_prompt_tokens", "most_relevant_topic_completion_tokens", "most_relevant_topic_total_tokens",
        # "researching_topic_prompt_tokens", "researching_topic_completion_tokens", "researching_topic_total_tokens",
        # "relevant_painpoint_prompt_tokens", "relevant_painpoint_completion_tokens", "relevant_painpoint_total_tokens",
        # "email_body_prompt_tokens", "email_body_completion_tokens", "email_body_total_tokens",
        "total_cost"
    ]
    return desired_cols

########################################
# Main
########################################
def main():
    args = parse_args()
    limit = records_limit_value

    # Check file extension and read accordingly
    ext = os.path.splitext(args.input_csv)[1].lower()
    if ext == ".json":
        df = pd.read_json(args.input_csv)
    else:
        df = pd.read_csv(args.input_csv)
    
    all_records = df.to_dict("records")

    processed_emails = set()
    # if os.path.exists(args.output_csv):
    #     processed_df = pd.read_csv(args.output_csv)
    #     processed_emails = set(processed_df["Email"])
    records = [r for r in all_records if r.get("Email") not in processed_emails]
    
    if limit is not None:
        records = records[:limit]

    vars_paths = glob(os.path.join(script_dir, "../../src/variables/*"))
    global_vars = {}
    for v in vars_paths:
        with open(v, "r", encoding="utf-8") as f:
            key = os.path.basename(v).split(".")[0].strip()
            global_vars[key] = f.read().strip()

    prompt_templates = {}
    for cfg in PROMPT_CONFIGS:
        with open(cfg["prompt_path"], "r", encoding="utf-8") as f:
            prompt_templates[cfg["name"]] = f.read()

    for record in records:
        email_feedback = record.get("email_feedback", "").strip()
        if not email_feedback:
            continue  # Skip records with empty or whitespace-only "email_feedback"

        prompt_vars = dict(record)
        prompt_vars.update(global_vars)
        for cfg in PROMPT_CONFIGS:
            template = prompt_templates[cfg["name"]]
            prompt_text = get_prompt(template, prompt_vars)
            model_name = cfg["model_name"]
            max_tokens = cfg.get("max_completion_tokens", 4000)
            
            print(f"Running prompt {cfg['name']} for record {record.get('Email')}")
            result, usage = call_azure(model_name, prompt_text, max_tokens)
            print(f"Done running prompt {cfg['name']} for record {record.get('Email')}")
            
            key = cfg["output_key"]
            record[key] = result
            record[f"{key}_prompt_tokens"] = usage.get("prompt_tokens", 0)
            record[f"{key}_completion_tokens"] = usage.get("completion_tokens", 0)
            record[f"{key}_total_tokens"] = usage.get("total_tokens", 0)
            prompt_vars[key] = result
            
            delay = RATE_LIMIT_DELAYS.get(model_name, 0)
            time.sleep(delay)

        record["total_cost"] = calculate_cost(record)
        
        # Append the processed record to CSV and JSON
        # append_record(record, args.output_csv, get_desired_columns(df))
        append_record_to_json(record, args.output_json)
        
        print(f"Processed record for Email: {record.get('Email')}, Total Cost: ${record['total_cost']:.6f}")

if __name__ == "__main__":
    delays = [30, 120, 240, 480, 600]  # delays in seconds: 30s, 2min, 4min, 8min, 10min
    delay_index = 0
    while True:
        try:
            main()  # process all records
            break  # If main() completes successfully, exit the loop
        except Exception as e:
            print(f"An error occurred: {e}")
            wait_time = delays[delay_index]
            print(f"Waiting {wait_time} seconds before restarting...")
            time.sleep(wait_time)
            # Increase the delay up to the maximum (10 minutes), then keep using it repeatedly.
            if delay_index < len(delays) - 1:
                delay_index += 1