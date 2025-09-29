#  Bank Statement AI Parser Agent

An **AI-powered agent (`agent.py`)** that automatically generates custom Python parsers for bank statements in PDF format.
The agent uses **Google Gemini API** to generate, validate, and self-correct parser scripts until they produce structured data matching a given CSV schema.

---

##  Table of Contents

* [Overview](#-overview)
* [How It Works](#-how-it-works)
* [Setup Instructions](#-setup-instructions)
* [Requirements](#-requirements)
* [Usage](#-usage)
* [Workflow Diagram](#-workflow-diagram)
---

##  Overview

Parsing bank statements is often a manual, error-prone task due to varied formats across banks.
This project solves that by **auto-generating a reusable parser per bank** using the **Gemini AI API**.
Once generated, each parser is stored under `custom_parsers/` and can be reused for future statements.

---

##  How It Works

For a given bank, the agent takes:

* **Bank statement PDF** → e.g., `data/icici_statements.pdf`
* **Expected CSV schema** → e.g., `data/icici_expected.csv`

The process:

1. **Read PDF text** → extract raw text using `PyPDF2`.
2. **Generate parser** → Gemini creates a function:

   ```python
   def parse(pdf_path) -> pandas.DataFrame
   ```
3. **Save parser** → stored at `custom_parsers/{bank}_parser.py`.
4. **Run parser dynamically** → import + execute on the PDF.
5. **Validate schema** → check DataFrame against expected CSV schema.
6. **Retry if needed** → on failure, retry up to **3 times** with self-corrections.
7. **Store final parser** → reusable for future statements.

---

##  Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/anvith-1001/karbon-ai-anvi.git
cd karbon_bank_ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_api_key_here
```

### 5. Prepare input files

Place input files in the `data/` folder:

```
data/{bankname}_statements.pdf
data/{bankname}_expected.csv
```

 Example:

```
data/icici_statements.pdf
data/icici_expected.csv
```

---

##  Requirements

Your `requirements.txt` should include:

```
pandas
PyPDF2
python-dotenv
google-generativeai
```

Optional (for debugging / development):

```
argparse
```

Install all with:

```bash
pip install -r requirements.txt
```

---

##  Usage

Run the agent for a specific bank:

```bash
python agent.py --bank <bank_name>
```

 Example:

```bash
python agent.py --bank icici
```

This will:

* Generate (or reuse) `custom_parsers/icici_parser.py`
* Parse the given `icici_statements.pdf`
* Validate against `icici_expected.csv`

---

## Workflow Diagram

```
         ┌─────────────┐
         │ Bank PDF     │
         └──────┬───────┘
                │
                ▼
         ┌─────────────┐
         │ Extract text │
         └──────┬───────┘
                │
                ▼
         ┌──────────────────┐
         │ Gemini: generate │
         │ parser function  │
         └──────┬───────────┘
                │
        Save as custom_parsers/{bank}_parser.py
                │
                ▼
         ┌─────────────┐
         │ Run parser   │
         │ dynamically  │
         └──────┬───────┘
                │
                ▼
         ┌────────────────┐
         │ Validate output │
         │ against schema  │
         └──────┬─────────┘
                │
        Success? ──────────────► Store parser (Reusable)
                │
               No
                ▼
        ┌─────────────────────┐
        │ Retry with feedback │
        │ (up to 3 attempts)  │
        └─────────────────────┘
```

