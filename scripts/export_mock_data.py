#!/usr/bin/env python3
"""
export_mock_data.py - Export SQLite database to JSON for HTML viewer testing

This script exports all tables from lims_mirror.db (or any SQLite database) 
to JSON files that can be served statically for the test_viewer.html.

Usage:
    python3 scripts/export_mock_data.py

Output:
    ui/mock_data/*.json - One file per table + tables.json manifest
"""

import sqlite3
import json
import os
import sys
import time

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lims_mirror.db')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'mock_data')


def export_database(db_path: str, output_dir: str) -> None:
    """
    Export all tables from SQLite database to JSON files.
    
    Args:
        db_path: Path to SQLite database
        output_dir: Directory to write JSON files
    """
    print("=" * 60)
    print("BERDL Mock Data Export")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Output:   {output_dir}")
    print("-" * 60)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables\n")
    
    # Export each table
    total_rows = 0
    total_bytes = 0
    start_time = time.time()
    
    for table in tables:
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        headers = [row[1] for row in cursor.fetchall()]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        # Convert to strings for JSON
        data = [
            [str(v) if v is not None else "" for v in row]
            for row in rows
        ]
        
        # Build result structure (matches service output format)
        table_data = {
            "headers": headers,
            "data": data,
            "row_count": len(data),
            "table_name": table,
            "response_time_ms": 0  # Calculated client-side
        }
        
        # Write to file
        output_path = os.path.join(output_dir, f"{table}.json")
        with open(output_path, 'w') as f:
            json.dump(table_data, f)
        
        file_size = os.path.getsize(output_path)
        total_rows += len(data)
        total_bytes += file_size
        
        print(f"  {table:25s} | {len(data):6d} rows | {file_size / 1024:8.1f} KB")
    
    # Write table manifest
    manifest = {"tables": tables}
    manifest_path = os.path.join(output_dir, "tables.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    
    conn.close()
    
    elapsed = time.time() - start_time
    
    print("-" * 60)
    print(f"TOTAL: {total_rows:,} rows | {total_bytes / 1024:.1f} KB | {elapsed:.2f}s")
    print("=" * 60)
    print(f"\nExported to: {output_dir}/")
    print("Use with ui/test_viewer.html for local testing.")


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found: {DB_PATH}")
        sys.exit(1)
    
    export_database(DB_PATH, OUTPUT_DIR)


if __name__ == "__main__":
    main()
