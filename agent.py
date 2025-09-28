import os
import argparse
import importlib.util
import re
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2

# load env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# extract text from pdf
def extract_text(pdf_path):
    reader = PyPDF2.PdfReader(open(pdf_path, "rb"))
    text = []
    for page in reader.pages: 
        text.append(page.extract_text() or "")
    return "\n".join(text)

# sanitize code to remove unwanted characters and lines
def sanitize_code(code: str) -> str:
    allowed = set('\t\n\r')
    filtered = ''.join(ch for ch in (code or "") if ch in allowed or 32 <= ord(ch) <= 126)
    cleaned_lines = []
    for line in filtered.splitlines():
        stripped = line.strip()
        if stripped.startswith('<') and stripped.endswith('>') and not stripped.startswith('<<'):
            continue
        cleaned_lines.append(line.rstrip())
    return '\n'.join(cleaned_lines).strip() + '\n'

def extract_code_block(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text or "", flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else (text or "").strip()

# system prompt for the LLM
def generate_parser(bank, pdf_text, schema_cols, old_code=None, error=None):
    model = genai.GenerativeModel(model_name="models/gemini-flash-latest")
    prompt = f"""
You are to generate Python code for a parser.
Requirements:
- Define parse(pdf_path) -> pandas.DataFrame.
- Ensure DataFrame columns exactly match {schema_cols}.
- Use PyPDF2.PdfReader to read every page and every line of pdf_path; do not rely on other PDF libraries or mock data.
- Do not include multiline string samples, placeholders, or dummy data.
- Return only valid Python source (no markdown fences or surrounding quotes) with minimal necessary comments.
- Parse text similar to:
{pdf_text[:1000]}

If fixing, here is old code:
{old_code or ""}
Error to fix:
{error or ""}
"""
    response = model.generate_content(prompt)
    return extract_code_block(response.text)

# save and run generated code file below ( with bank name)

def save_parser(bank, code):
    path = f"custom_parsers/{bank}_parser.py"
    os.makedirs("custom_parsers", exist_ok=True)
    with open(path, "w") as f:
        f.write(code)
    return path

def run_parser(bank, pdf_path):
    spec = importlib.util.spec_from_file_location(
        f"{bank}_parser", f"custom_parsers/{bank}_parser.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse(pdf_path)

def validate(df, schema_cols):
    return list(df.columns) == schema_cols

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", required=True, help="Bank name")
    args = parser.parse_args()
    bank = args.bank
    pdf_path = f"data/{bank}_statements.pdf"
    schema_path = f"data/{bank}_expected.csv"
    schema_cols = list(pd.read_csv(schema_path, nrows=1).columns)
    pdf_text = extract_text(pdf_path)

    attempts = 0
    old_code, error = None, None
    while attempts < 3:
        code = generate_parser(bank, pdf_text, schema_cols, old_code, error)
        if any(token in code for token in ("SAMPLE_", "dummy", "raw_text", "pdfplumber")):
            error = "Generated code must read directly from PDF without placeholders or unsupported libraries."
            old_code = code
            attempts += 1
            continue
        save_parser(bank, sanitize_code(code))
        try:
            df = run_parser(bank, pdf_path)
            if validate(df, schema_cols) and not df.empty:
                print("Parser generated successfully.")
                print(df.to_csv(index=False).strip())
                return
            else:
                error = f"Invalid output. Expected columns {schema_cols} and non-empty data, got {list(df.columns)} with {len(df)} rows."
        except Exception as e:
            error = str(e)
        old_code = code
        attempts += 1

    print("Failed to generate parser after 3 attempts.")

if __name__ == "__main__":
    main()