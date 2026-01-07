"""
Export uncategorized records to Excel

Usage: python scripts/export_uncategorized.py <database.db>

Exports records NOT classified as businesses (personal/private entries).
"""

import sys
import os
import re
import sqlite3
import pandas as pd

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from config import BUSINESS_SUFFIXES, OUTPUT_DIR, ensure_output_dir


def has_business_suffix(name):
    """Check if name contains business suffix."""
    if not name:
        return False
    for pattern in BUSINESS_SUFFIXES:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False


def classify_business(row):
    """Classify record as business or not."""
    if row['type'] and str(row['type']).strip():
        return True
    if row['website'] and str(row['website']).strip():
        return True
    if has_business_suffix(row['name']):
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_uncategorized.py <database.db>")
        sys.exit(1)

    db_path = sys.argv[1]
    if not os.path.exists(db_path):
        print(f"[!] Database not found: {db_path}")
        sys.exit(1)

    # Derive output filename from database name
    db_name = os.path.splitext(os.path.basename(db_path))[0]
    ensure_output_dir()
    output_file = os.path.join(OUTPUT_DIR, f"{db_name}_uncategorized.xlsx")

    print(f"[*] Reading from {db_path}...")

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT name, type, address, phone, email, website, source_url
        FROM businesses
        ORDER BY name
    """, conn)
    conn.close()

    print(f"[*] Loaded {len(df)} records")

    # Classify and filter uncategorized
    df['is_business'] = df.apply(classify_business, axis=1)
    df_uncategorized = df[df['is_business'] == False].copy()
    df_uncategorized = df_uncategorized.drop(columns=['is_business'])

    print(f"[*] Found {len(df_uncategorized)} uncategorized records")

    # Export
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_uncategorized.to_excel(writer, index=False, sheet_name='Uncategorized')

        worksheet = writer.sheets['Uncategorized']
        for idx, col in enumerate(df_uncategorized.columns):
            max_length = max(
                df_uncategorized[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            max_length = min(max_length, 50)
            worksheet.column_dimensions[chr(65 + idx)].width = max_length

    print(f"\n[SUCCESS] Exported to {output_file}")
    print(f"  Records: {len(df_uncategorized)}")
    print(f"  Size: {os.path.getsize(output_file) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
