import json
import csv
import re
import sys
from bs4 import BeautifulSoup
import os

# Get the list_name from the command line arguments
list_name = "PLACEHOLDER3"

# Load JSON data
script_dir = os.path.dirname(__file__)
input_json_path = os.path.join(script_dir, "../../output/6email_feedback.json")
with open(input_json_path, 'r') as file:
    data = json.load(file)

# Function to remove HTML tags and convert to plain text
def html_to_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator='\n')

# Filter records where "exclude" is false and "email_feedback" is not provided
filtered_data = [
    record for record in data 
    if 
        not record.get("exclude", True) 
        and record.get("email_feedback")
]

# Prepare CSV data
csv_data = []
for record in filtered_data:
    csv_data.append({
        "Email": record.get("Email", ""),
        "First Name": record.get("First Name", ""),
        "Last Name": record.get("Last Name", ""),
        "Person Linkedin Url": record.get("Person Linkedin Url", ""),
        "Title": record.get("Title", ""),
        # "email_subject_extract": record.get("email_subject_extract", ""),
        # "email_output_final": html_to_text(record.get("email_output_final", "")),
        "email_subject_extract_after_feedback": record.get("email_subject_extract_after_feedback", ""),
        "email_after_feedback": html_to_text(record.get("email_after_feedback", ""))
        
    })

# Write to CSV
output_dir = os.path.join(script_dir, "../../export")
os.makedirs(output_dir, exist_ok=True)
csv_file_path = os.path.join(output_dir, f'{list_name}.csv')
with open(csv_file_path, 'w', newline='') as csvfile:
    fieldnames = ["Email", "First Name", "Last Name", "Person Linkedin Url", "Title", 
                #   "email_subject_extract", "email_output_final", 
                  "email_subject_extract_after_feedback", "email_after_feedback" 
                  ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in csv_data:
        writer.writerow(row)

print(f"CSV file has been created at {csv_file_path}")