import re
import pandas as pd
from PyPDF2 import PdfReader
from typing import List, Dict, Any

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses a bank statement PDF using PyPDF2, extracting transaction data
    into a structured pandas DataFrame.
    """

    # Regex for standard date DD-MM-YYYY format at the start of a line
    DATE_PATTERN = re.compile(r'^\d{2}-\d{2}-\d{4}')

    # Define required columns exactly
    COLUMNS = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']

    def safe_float(s: Any) -> float | None:
        """Robustly converts a string part into a float, handling common delimiters."""
        try:
            s_clean = str(s).replace(',', '').strip()
            if not s_clean or s_clean == '-':
                return None
            return float(s_clean)
        except ValueError:
            return None

    transactions: List[Dict[str, Any]] = []

    try:
        reader = PdfReader(pdf_path)
    except Exception:
        # Return empty DataFrame if the file cannot be read
        return pd.DataFrame(transactions, columns=COLUMNS)

    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue

        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            # Check if the line starts with a date pattern
            if not parts or not DATE_PATTERN.match(parts[0]):
                continue

            date = parts[0]

            # Identify numerical values working backward.
            # We expect Txn_Amount and Balance to be the last two numeric fields.
            numeric_parts = []
            desc_end_index = len(parts)

            # Find the final numeric sequence (Balance, then Txn_Amount)
            for i in range(len(parts) - 1, 0, -1):
                f_val = safe_float(parts[i])
                if f_val is not None:
                    # Store (value, original index)
                    numeric_parts.append((f_val, i))

                # Check if we have found the necessary two numbers (Amount, Balance)
                if len(numeric_parts) >= 2:
                    # If the current part (i) is not numeric, we have found the boundary
                    if f_val is None:
                        desc_end_index = i + 1
                        break
                    # If we hit the beginning of the line (i=1) and found 2 numbers,
                    # the description boundary is index 1.
                    elif i == 1:
                        desc_end_index = i
                        break

                # If we encounter non-numeric data before finding 2 numbers, stop parsing this line
                elif f_val is None and len(numeric_parts) < 2:
                    break

            if len(numeric_parts) < 2:
                # Must have at least Amount and Balance
                continue

            # Since we append backwards:
            # numeric_parts[0] is Balance (last element of line)
            # numeric_parts[1] is Transaction Amount (second to last element of line)

            Balance = numeric_parts[0][0]
            Txn_Amount = numeric_parts[1][0]

            # Determine description boundary if the loop completed without a non-numeric stop
            if desc_end_index == len(parts):
                # This happens if the last part processed was Txn_Amount (index numeric_parts[1][1])
                desc_end_index = numeric_parts[1][1]

            # Description is everything between the Date (index 0) and the start of Txn_Amount
            desc_start_index = 1
            Description = " ".join(parts[desc_start_index : desc_end_index])

            Debit_Amt = 0.0
            Credit_Amt = 0.0

            # Heuristic to classify the transaction amount
            desc_lower = Description.lower()

            # Classify as Credit based on common keywords
            if any(keyword in desc_lower for keyword in ["credit", "deposit", "salary", "interest"]):
                Credit_Amt = Txn_Amount
            # Default to Debit otherwise (e.g., payment, purchase, bill, transfer)
            else:
                Debit_Amt = Txn_Amount

            transactions.append({
                'Date': date,
                'Description': Description,
                'Debit Amt': Debit_Amt,
                'Credit Amt': Credit_Amt,
                'Balance': Balance
            })

    df = pd.DataFrame(transactions, columns=COLUMNS)

    # Ensure numerical columns are properly cast
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
