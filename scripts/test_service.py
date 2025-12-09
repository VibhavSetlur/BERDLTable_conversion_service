#!/usr/bin/env python3
"""End-to-end test script for BERDLTable_conversion_service V1.0.

This script directly imports the service implementation and calls the
`get_table_data` method with a sample table ("Genes"). It prints the
resulting JSON structure and the granular performance metrics:
- `db_query_ms`
- `conversion_ms`
- `response_time_ms`

The output can be inspected to verify that the service meets Chris
Henry's requirements for fast, whole‑table delivery.
"""

import json
import time
from pathlib import Path

# Adjust import path to the lib directory
import sys
from pathlib import Path

# Add the lib directory to sys.path (contains the package)
lib_path = Path(__file__).resolve().parents[1] / "lib"
sys.path.append(str(lib_path))

from BERDLTable_conversion_service.BERDLTable_conversion_serviceImpl import BERDLTable_conversion_serviceImpl

def main():
    # Initialise the service implementation (loads the bundled SQLite DB)
    service = BERDLTable_conversion_serviceImpl()

    # Choose a table that exists in the bundled DB
    table_name = "Genes"
    print(f"Requesting table '{table_name}' from the service...")

    start = time.time()
    result = service.get_table_data({"berdl_table_id": "mock", "table_name": table_name})
    elapsed = (time.time() - start) * 1000

    # Pretty‑print the result (trimmed for readability)
    print("\n--- Service Response (trimmed) ---")
    trimmed = {
        "row_count": result.get("row_count"),
        "headers": result.get("headers"),
        "db_query_ms": result.get("db_query_ms"),
        "conversion_ms": result.get("conversion_ms"),
        "response_time_ms": result.get("response_time_ms"),
    }
    print(json.dumps(trimmed, indent=2))
    print(f"\nTotal client‑side elapsed time: {elapsed:.1f} ms")

if __name__ == "__main__":
    main()
