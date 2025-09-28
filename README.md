# Bank Statement AI Parser Agent

This project provides an AI-powered agent (`agent.py`) that automatically generates custom parsers for different bank statements in PDF format. The agent uses the **Google Gemini API** to write, test, and self-correct parser scripts so that extracted data matches a given CSV schema.

---

## How It Works

The agent takes two inputs for a given bank:
- **Bank statement PDF** (e.g., `data/icici_statements.pdf`)
- **Expected CSV schema** (e.g., `data/icici_expected.csv`)

It then:
1. Reads the PDF text.
2. Prompts Gemini to generate a Python parser function `parse(pdf_path) -> pandas.DataFrame`.
3. Saves the generated parser under `custom_parsers/{bank}_parser.py`.
4. Dynamically imports and runs the parser.
5. Validates the DataFrame against the expected schema.
6. If validation fails, retries up to **3 times** with self-corrections.

Once successful, the generated parser can be reused for the same bank’s statements.

---

## Setup Instructions

1. **Clone and set up environment**
git clone https://github.com/anvith-1001/karbon-ai-anvi.git
cd karbon_bank_ai
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

2. **Install dependencies**
   pip install -r requirements.txt

3. **Configure API key**
   Create a .env file in the project root with your Gemini API key:
   GOOGLE_API_KEY=your_api_key_here

4. **Prepare input files**
   Place your bank statement and schema in the data/ folder:

   data/{bankname}_statements.pdf
   data/{bankname}_expected.csv

   For example:
   data/icici_statements.pdf
   data/icici_expected.csv

5. **Run the agent**
   python agent.py --bank <bank_name>

   For example:
   python agent.py --bank icici


## Agent Diagram
The agent acts as a controller: it loads inputs (PDF + schema), prompts Gemini to generate or fix parser code, saves that code in custom_parsers/, dynamically imports and executes the parser on the PDF, then validates the output DataFrame against the expected CSV schema. If validation fails, the agent feeds the error and previous code back into Gemini for another attempt (up to 3 retries). Once a valid parser is produced, it is stored for future use.
