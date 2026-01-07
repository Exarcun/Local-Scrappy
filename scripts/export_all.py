"""
Export all records to Excel

Usage: python scripts/export_all.py <database.db>

Exports all records from the database to Excel.
"""

import sys
import os
import sqlite3
import pandas as pd

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from config import OUTPUT_DIR, ensure_output_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_all.py <database.db>")
        sys.exit(1)

    db_path = sys.argv[1]
    if not os.path.exists(db_path):
        print(f"[!] Database not found: {db_path}")
        sys.exit(1)

    # Derive output filename from database name
    db_name = os.path.splitext(os.path.basename(db_path))[0]
    ensure_output_dir()
    output_file = os.path.join(OUTPUT_DIR, f"{db_name}_all.xlsx")

    print(f"[*] Reading from {db_path}...")

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT name, type, address, phone, email, website, source_url
        FROM businesses
        ORDER BY name
    """, conn)
    conn.close()

    print(f"[*] Loaded {len(df)} records")

    # Export
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='All Records')

        worksheet = writer.sheets['All Records']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            max_length = min(max_length, 50)
            worksheet.column_dimensions[chr(65 + idx)].width = max_length

    print(f"\n[SUCCESS] Exported to {output_file}")
    print(f"  Records: {len(df)}")
    print(f"  Size: {os.path.getsize(output_file) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
