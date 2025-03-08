#!/usr/bin/env python
import argparse
import csv
import json
import os
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

# API endpoint and key configuration.
API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar-reasoning-pro"
API_KEY = os.getenv("PERPLEXITY_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Pricing details (in dollars):
#   - Input tokens: cost per 1,000,000 tokens
#   - Output tokens: cost per 1,000,000 tokens
#   - Searches: cost per 1,000 searches
PRICING = {
    "sonar-reasoning-pro": {"input": 2, "output": 8, "search": 5},
    "sonar-reasoning":     {"input": 1, "output": 5, "search": 5},
    "sonar-pro":           {"input": 3, "output": 15, "search": 5},
    "sonar":               {"input": 1, "output": 1, "search": 5},
}

def extract_final_answer(text):
    """
    Remove any chain-of-thought section enclosed in <think>...</think> tags.
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def map_citations(final_text, citations):
    """
    Map inline citation markers (e.g., [1], [2], …) to their corresponding citation text.
    If no inline markers are found, simply number the citations sequentially.
    """
    mapping_lines = []
    for i, citation in enumerate(citations):
        marker = f"[{i+1}]"
        if marker in final_text:
            mapping_lines.append(f"{marker}: {citation}")
    if not mapping_lines:
        mapping_lines = [f"[{i+1}]: {citation}" for i, citation in enumerate(citations)]
    return "\n".join(mapping_lines)

def perform_query(template, first_name, last_name, title, company, max_tokens, model=DEFAULT_MODEL):
    """
    Build the prompt from the provided template and contact details,
    call the API, and return a tuple:
       (query_text, final_response, citations, citation_mapping, cost)
    
    Cost is estimated using a word-count approximation for tokens and a default
    number of searches (3 for Pro models; 1 for others).
    """
    query_text = template.format(
        first_name=first_name, last_name=last_name, title=title, company=company
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query_text}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
    }
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [])
        raw_text = choices[0].get("message", {}).get("content", "") if choices else ""
        final_text = extract_final_answer(raw_text)
        citations = data.get("citations", [])
        usage = data.get("usage", {})

        # Estimate tokens via word count (rough approximation)
        prompt_tokens = len(query_text.split())
        completion_tokens = len(final_text.split())

        # Default number of searches:
        # For Pro models (sonar-reasoning-pro, sonar-pro) default to 3; otherwise, default to 1.
        if model in {"sonar-reasoning-pro", "sonar-pro"}:
            searches = usage.get("searches", 3)
        else:
            searches = usage.get("searches", 1)

        pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
        cost_input = (prompt_tokens / 1_000_000) * pricing["input"]
        cost_output = (completion_tokens / 1_000_000) * pricing["output"]
        cost_search = (searches / 1000) * pricing["search"]
        total_cost = cost_input + cost_output + cost_search

        citation_mapping = map_citations(final_text, citations)
        return query_text, final_text, citations, citation_mapping, total_cost

    except requests.RequestException as e:
        print(f"Error querying API for {first_name} {last_name}: {e}")
        return query_text, "", [], "", 0.0

# -------------------------------------------------------------------
# Query configurations:
#
# "engagements_combined" includes details on:
#   1. Casual Publications
#   2. Conference Engagements
#   3. Events Engagements
#   4. Podcast Engagements
#   5. Peer-Reviewed Publications
#   6. Webinar Engagements
#
# "roles_and_responsibilities" supports a custom model.
#
# "background" (formerly "prospect") supports a custom model.
# -------------------------------------------------------------------
QUERY_CONFIGS = {
    "engagements_combined": {
        "template": (
            "You are an expert SDR researcher and your job is to perform research.\n"
            "###Target person###\n"
            "{first_name} {last_name}, {title}, {company}\n"
            "###Instructions###\n"
            "Please provide the following details:\n\n"
            "1. **Casual Publications**: Find all white papers, blogs, commentaries, news articles, book chapters, trade journals, and theses (excluding peer-reviewed publications). "
            "Include work that pre-dates the current company and role. Generate a detailed abstract for each if available and concatenate the findings.\n\n"
            "2. **Conference Engagements**: Identify the conferences the person attended or where they were a speaker recently (exclude events before 2023). "
            "Summarize each conference in detail. If no information is found, output \"No information available\".\n\n"
            "3. **Events Engagements**: Identify the events the person attended or where they were a speaker recently (exclude events before 2023). "
            "Summarize each event in detail. If no information is found, output \"No information available\".\n\n"
            "4. **Podcast Engagements**: Identify the podcasts the person participated in recently (exclude results before 2023). "
            "Summarize each podcast in detail. If no information is found, output \"No information available\".\n\n"
            "5. **Peer-Reviewed Publications**: Find all peer-reviewed publications (including work that pre-dates the current company and role). "
            "Generate a detailed abstract for each if available and concatenate the findings.\n\n"
            "6. **Webinar Engagements**: Identify the webinars the person attended or where they were a speaker recently (exclude events before 2023). "
            "Summarize each webinar in detail. If no information is found, output \"No information available\".\n\n"
            "Present your answer in a structured format, clearly separating each section."
        ),
        "max_tokens": 4000,
        "model": "sonar-reasoning-pro" 
    },
    "roles_and_responsibilities": {
        "template": (
            "You are an expert SDR researcher and your job is perform research.\n"
            "###Target person###\n"
            "{first_name} {last_name} is the {title} at {company}.\n"
            "###\n"
            "Generate a description of their roles and responsibilities. Provide a thorough description.\n"
            "###Output requirements###\n"
            "If no specific information is found, research the typical roles and responsibilities of a {title} at {company}.\n"
            "If information is available, concatenate each finding."
        ),
        "max_tokens": 2000,
        "model": "sonar"  
    },
    "background": {
        "template": (
            "You are an expert SDR researcher and your job is to perform research.\n"
            "###Target person###\n"
            "{first_name} {last_name}, {title}, {company}\n"
            "###\n"
            'Write a thorough summary of "{first_name} {last_name}" background. This should include information about who they are, '
            "what their professional contributions are, who they've worked with, and any notable extracurricular achievements.###\n\n"
            "Research {company} focusing on what their products/services are, their target market, and any recent news or events related to the company."
        ),
        "max_tokens": 10000,
        "model": "sonar-pro" 
    },
}

def search_query(query_type, first_name, last_name, title, company):
    """
    Dispatch the query request based on the query type and return:
       (query_text, response_text, citations, citation_mapping, cost)
    """
    config = QUERY_CONFIGS.get(query_type)
    if not config:
        raise ValueError(f"Query type '{query_type}' is not defined.")
    template = config["template"]
    max_tokens = config["max_tokens"]
    model = config.get("model", DEFAULT_MODEL)
    return perform_query(template, first_name, last_name, title, company, max_tokens, model)

def process_contacts(input_csv, output_csv, output_fields, query_types, skip, limit):
    """
    Read the input CSV of contacts, run each specified query for every contact,
    sum the cost for all queries per record, and write each record immediately
    to both a CSV file and a JSON Lines file.
    
    Only process records after skipping the first `skip` rows and up to `limit` records.
    """
    # Determine the JSON output filename (JSON Lines format).
    json_filename = output_csv[:-4] + ".jsonl" if output_csv.lower().endswith(".csv") else output_csv + ".jsonl"

    processed_count = 0

    with open(input_csv, newline="", encoding="utf-8") as infile, \
         open(output_csv, mode="a", newline="", encoding="utf-8") as csvfile, \
         open(json_filename, mode="a", encoding="utf-8") as jsonfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(csvfile, fieldnames=output_fields)

        # Write header only if file is empty.
        if csvfile.tell() == 0:
            writer.writeheader()
        
        for i, row in enumerate(reader):
            if i < skip:
                continue
            if limit is not None and processed_count >= limit:
                print("Reached processing limit.")
                break

            email = row.get("Email", "").strip()
            if not email:
                print("Skipping row with missing Email")
                continue

            first_name = row.get("First Name", "").strip()
            last_name = row.get("Last Name", "").strip()
            title = row.get("Title", "").strip()
            company = row.get("Company", "").strip()
            linkedin_url = row.get("Person Linkedin Url", "").strip()
            website = row.get("Website", "").strip()
            company_linkedin_url = row.get("Company Linkedin Url", "").strip()
            facebook_url = row.get("Facebook Url", "").strip()

            contact_info = {
                "Email": email,
                "Person Linkedin Url": linkedin_url,
                "First Name": first_name,
                "Last Name": last_name,
                "Title": title,
                "Company": company,
                "Website": website,
                "Company Linkedin Url": company_linkedin_url,
                "Facebook Url": facebook_url,
            }
            total_cost = 0.0
            for qt in query_types:
                print(f"Searching for '{qt}' for {first_name} {last_name} | {title} at {company}")
                # We no longer store the raw query text.
                _, response_text, citations, citation_mapping, cost = search_query(
                    qt, first_name, last_name, title, company
                )
                contact_info[qt] = response_text
                contact_info[f"{qt}_citations"] = "; ".join(citations) if citations else ""
                contact_info[f"{qt}_citation_mapping"] = citation_mapping
                contact_info[f"{qt}_cost"] = f"${cost:.5f}"
                total_cost += cost
                print(f"Processed '{qt}' for {email} at an estimated cost of ${cost:.5f}")
            contact_info["Total_Cost"] = f"${total_cost:.5f}"
            
            # Write record immediately to CSV and JSON Lines file.
            writer.writerow(contact_info)
            jsonfile.write(json.dumps(contact_info) + "\n")
            csvfile.flush()
            jsonfile.flush()
            processed_count += 1
            print(f"Record for {email} written to CSV and JSON.")
            
    print(f"Output written to {output_csv} and {json_filename}")

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Query contacts using the sonar-reasoning-pro API with custom research prompts, "
            "calculate the cost per processed record, and output the results as CSV and JSON Lines."
        )
    )
    parser.add_argument(
        "--input-csv",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "../../input/apollo-contacts-export.csv"),
        help="Path to the input CSV file containing contact data.",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "../../output/1perplexity_results.csv"),
        help="Path for the output CSV file.",
    )
    parser.add_argument(
        "--query-types",
        type=str,
        default=",".join(list(QUERY_CONFIGS.keys())),
        help="Comma-separated list of query types to run. Options: " +
             ", ".join(list(QUERY_CONFIGS.keys())),
    )
    parser.add_argument(
        "--output-fields",
        type=str,
        default="",
        help="Comma-separated list of output field names. If empty, default fields are used.",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of records to skip from the beginning (for resuming processing).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records to process in this run.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    allowed_query_types = list(QUERY_CONFIGS.keys())
    query_types = [qt.strip() for qt in args.query_types.split(",") if qt.strip() in allowed_query_types]
    if not query_types:
        print("No valid query types provided. Exiting.")
        return

    if args.output_fields:
        output_fields = [field.strip() for field in args.output_fields.split(",")]
    else:
        base_fields = ["Email", "Person Linkedin Url", "First Name", "Last Name", "Title", "Company", "Website", "Company Linkedin Url", "Facebook Url"]
        additional_fields = []
        for qt in query_types:
            additional_fields.extend([qt, f"{qt}_citations", f"{qt}_citation_mapping", f"{qt}_cost"])
        additional_fields.append("Total_Cost")
        output_fields = base_fields + additional_fields

    process_contacts(args.input_csv, args.output_csv, output_fields, query_types, args.skip, args.limit)

if __name__ == "__main__":
    main()