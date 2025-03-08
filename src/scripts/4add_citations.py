import re
import json
import os

def parse_citation_mapping(mapping_str):
    """
    Parse a citation mapping string into a dictionary.
    Each line should have the form:
       [number]: URL
    """
    citation_dict = {}
    if mapping_str:
        for line in mapping_str.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r'\[(\d+)\]:\s*(.+)', line)
            if match:
                citation_num = match.group(1)
                url = match.group(2).strip()
                citation_dict[citation_num] = url
    return citation_dict

def update_text_with_citations(text, mapping_str):
    """
    Replace inline citation markers in text (e.g. [1])
    with Markdown links using the provided mapping string.
    For example, [1] becomes [1](URL).
    """
    citations = parse_citation_mapping(mapping_str)
    
    def replacer(match):
        ref = match.group(1)
        if ref in citations:
            return f'[{ref}]({citations[ref]})'
        return match.group(0)
    
    updated_text = re.sub(r'\[(\d+)\]', replacer, text)
    return updated_text

def process_record(record):
    """
    For each key pair, update the text field so that inline citation markers are replaced
    with their Markdown link using the associated citation mapping.
    
    The key pairs are:
      1. engagements_combined (update using engagements_combined_citation_mapping)
      2. background (update using background_citation_mapping)
      3. roles_and_responsibilities (update using roles_and_responsibilities_citation_mapping)
    """
    if "engagements_combined" in record and "engagements_combined_citation_mapping" in record:
        record["engagements_combined"] = update_text_with_citations(
            record["engagements_combined"],
            record["engagements_combined_citation_mapping"]
        )
    if "background" in record and "background_citation_mapping" in record:
        record["background"] = update_text_with_citations(
            record["background"],
            record["background_citation_mapping"]
        )
    if "roles_and_responsibilities" in record and "roles_and_responsibilities_citation_mapping" in record:
        record["roles_and_responsibilities"] = update_text_with_citations(
            record["roles_and_responsibilities"],
            record["roles_and_responsibilities_citation_mapping"]
        )
    return record

def main():
    script_dir = os.path.dirname(__file__)
    input_json = os.path.join(script_dir, "../../output/2final_combined_research_results.json")
    output_json = os.path.join(script_dir, "../../output/3final_combined_research_cited.json")
    
    if not os.path.exists(input_json):
        print(f"Error: Input file {input_json} not found.")
        return

    with open(input_json, "r", encoding="utf-8") as f:
        all_records = json.load(f)

    updated_records = []
    for record in all_records:
        # Process the record to update inline citations for the three key pairs
        record = process_record(record)
        # Build a new record that retains only the desired keys including the new ones
        new_record = {
            "Email": record.get("Email", ""),
            "Person Linkedin Url": record.get("Person Linkedin Url", ""),
            "First Name": record.get("First Name", ""),
            "Last Name": record.get("Last Name", ""),
            "Title": record.get("Title", ""),
            "Company": record.get("Company", ""),
            "Website": record.get("Website", ""),
            "Company Linkedin Url": record.get("Company Linkedin Url", ""),
            "Facebook Url": record.get("Facebook Url", ""),
            "company_background": record.get("company_background", ""),
            "engagements_combined": record.get("engagements_combined", ""),
            "roles_and_responsibilities": record.get("roles_and_responsibilities", ""),
            "background": record.get("background", ""),
            "most_relevant_topic": record.get("most_relevant_topic", ""),
            "researching_topic": record.get("researching_topic", ""),
            "relevant_painpoint": record.get("relevant_painpoint", ""),
            "email_body": record.get("email_body", ""),
            "email_output_final": record.get("email_output_final", ""),
            "email_subject": record.get("email_subject", ""),
            "email_subject_extract": record.get("email_subject_extract", "")
        }
        updated_records.append(new_record)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(updated_records, f, indent=2)

    print(f"Updated records written to {output_json}")

if __name__ == "__main__":
    main()