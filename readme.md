# Creating a New Virtual Environment
To create a new virtual environment in Python, follow these steps:

1. Open a terminal in Visual Studio Code.

2. Navigate to the directory where you want to create the virtual environment.

3. Run the following command to create a new virtual environment:

`python3 -m venv emailQA_venv`

# Activate the virtual environment:

On macOS and Linux:
`source emailQA_venv/bin/activate`

On Windows:
`emailQA_venv\Scripts\activate`

5. Verify that the virtual environment is active by checking the command prompt, which should now include the name of your virtual environment.

6. To ensure that no existing dependencies are used, you can check the installed packages list, which should be empty or contain only pip and setuptools:

`pip list`

# Evironment Variables

1. Create accounts with Azure and Perplexity.
2. Obtain the API keys for both services.
3. Create a `.env` file in the root directory of the project using the same format at `env.txt`.

Values in `env.txt` are illustrative only. Replace them with your own API keys.

Create the `Perplexity` account and get the API key.

Register for an Azure free account and create the following resources:
`Azure AI services | Speech service` resource in azure portal and get the key and endpoint.
`Azure OpenAI` resource in azure portal and get the key and endpoint.



# Install Dependencies

To install the required dependencies, run the following command:

```pip install -r requirements.txt```

## Install Frontend Dependencies

```npm install microsoft-cognitiveservices-speech-sdk```

Navigate to frontend folder

```cd frontend```

Install the frontend dependencies

```npm install```

# Testing the Application

To test the application is working, `Run All` in the jupyter notebook called `test_run.ipynb`

# Input

Create a csv file and upload it to the `src/input` folder. The csv file should contain the following columns at minimum:
- `First Name`
- `Last Name`
- `Email`
- `Company`
- `Title`

# Output

The intermediary output will be generated in the `src/output` folder. `5html_converted_content.json` and `6email_feedback.json` are used to generate the frontend.

# Export

The final output will be generated in the `src/export` folder.

# Using the Application

1. Change variables and prompts in `src/variables` and `src/prompts` as needed.
2. Run the jupyter notebook called `2. first_review.ipynb`.
3. Run `python3 frontend/main.py` to start the frontend.
4. Open the frontend in your browser at `http://localhost:5100`.
5. Review emails and feedback in the frontend.
6. Run the jupyter notebook called `3. second_review.ipynb`.
7. Remove comments from export scripts in jupyter notebooks to generate the final output.

## src/variables

You can add your own txt files in `src/variables`. These variables can be referred in the prompts.
For example, you can add a file called `company.txt` in `src/variables` and refer it in the prompts as `{company}`.

## src/prompts

Adjust the prompts in `src/prompts` to fit your use case.

### why_them.txt
**Purpose:** Generates specific reasons why the recipient is the right person to talk to, based on their profile. Avoids generic content or references to your startup.

**Variables:**
- `{relevant_painpoint}`
- `{most_relevant_topic}`
- `{First Name}`
- `{Last Name}`
- `{engagements_combined}`
- `{background}`
- `{roles_and_responsibilities}`

---

### researching_topic.txt
**Purpose:** Generates a concise research statement based on the most relevant topic. The output should be a single statement about one topic, avoiding questions and mentions of your current work.

**Variables:**
- `{most_relevant_topic}`
- `{offering}`

---

### relevant_painpoint.txt
**Purpose:** Identifies a pain point the recipient should have knowledge of, based on their profile. The output should connect the researching topic and current focus without including identifying information or references to your capability.

**Variables:**
- `{researching_topic}`
- `{current_focus}`
- `{First Name}`
- `{Last Name}`
- `{engagements_combined}`
- `{background}`
- `{roles_and_responsibilities}`

---

### most_relevant_topic.txt
**Purpose:** Selects the most relevant item from the recipient's profile to secure an informational meeting. Excludes references to your capability.

**Variables:**
- `{offering}`
- `{First Name}`
- `{Last Name}`
- `{engagements_combined}`
- `{background}`
- `{roles_and_responsibilities}`

---

### email_subject.txt
**Purpose:** Crafts a subject line for an email, focusing on the specific problem or challenge presented in the email. The subject line should emphasize the purpose of seeking feedback, remaining concise and direct.

**Variables:**
- `{email_output_final}`

---

### email_subject_extract.txt
**Purpose:** Extracts the subject line from the email subject prompt, outputting only the subject line.

**Variables:**
- `{email_subject}`

---

### email_subject_extract_after_feedback.txt
**Purpose:** Extracts the subject line from the email subject after feedback prompt, outputting only the subject line.

**Variables:**
- `{email_subject_after_feedback}`

---

### email_subject_after_feedback.txt
**Purpose:** Crafts a subject line for an email after incorporating feedback. The subject line should focus on the specific problem or challenge and emphasize the purpose of seeking feedback.

**Variables:**
- `{email_after_feedback}`

---

### email_output_final.txt
**Purpose:** Rewrites an email body to have a natural flow and conversational tone. Introduces the sender, mentions the researching topic, current focus, and relevant pain point, and ends with a request for a brief call.

**Variables:**
- `{First Name}`
- `{researching_topic}`
- `{current_focus}`
- `{relevant_painpoint}`
- `{why_them}`
- `{email_body}`

---

### email_body.txt
**Purpose:** Writes an email body that introduces the sender, mentions the researching topic, current focus, and relevant pain point, and ends with a request for a brief call. The email should have a semi-formal human tone, avoiding hype or filler.

**Variables:**
- `{First Name}`
- `{researching_topic}`
- `{current_focus}`
- `{relevant_painpoint}`
- `{why_them}`

---

### email_after_feedback.txt
**Purpose:** Rewrites an email body by incorporating feedback and new content. The email should have a natural flow and conversational tone, avoiding suggested solutions or claims of solving problems.

**Variables:**
- `{email_feedback}`
- `{email_output_final}`
- `{content_after_feedback}`

---

### content_after_feedback.txt
**Purpose:** Rewrites an email body by incorporating feedback. The email should be inquisitive rather than assertive, focusing on what the sender wants to learn from the recipient. Avoids suggested solutions or claims of solving problems.

**Variables:**
- `{email_feedback}`
- `{email_output_final}`
- `{First Name}`
- `{Last Name}`
- `{prospect_info}`
- `{engagements_combined}`
- `{background}`
- `{roles_and_responsibilities}`
- `{example_emails}`

---

### company_background.txt
**Purpose:** Writes a detailed report on a company. If no company exists, the output should be "NA" and nothing else.

**Variables:**
- `{Company}`

