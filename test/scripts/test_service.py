#!/usr/bin/env python3
"""
Interactive CLI for BERDLTable Conversion Service
Walks users through API usage, generating code snippets and executing requests live.
"""

import sys
import json
import time
import os
from pathlib import Path
import configparser

# Setup Python Path to import 'lib'
lib_path = Path(__file__).resolve().parents[2] / "lib"
sys.path.append(str(lib_path))

try:
    from BERDLTable_conversion_service.BERDLTable_conversion_serviceImpl import BERDLTable_conversion_service
except ImportError:
    print(f"ERROR: Could not find library at {lib_path}")
    sys.exit(1)

# Formatting Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_step(n, text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {n}] {text}{Colors.ENDC}")

def print_code(code_str):
    print("\n" + Colors.GREEN + code_str + Colors.ENDC + "\n")

def main():
    # 1. Initialize
    print_header("BERDLTable Service CLI Explorer")
    print("Initializing local service instance...")
    
    config = {'scratch': '/tmp/test_service_cli'}
    if not os.path.exists(config['scratch']):
        os.makedirs(config['scratch'])
        
    # Load Config from test_local/test.cfg
    cfg_path = Path(__file__).resolve().parents[2] / "test_local" / "test.cfg"
    test_config = configparser.ConfigParser()
    try:
        with open(cfg_path, 'r') as f:
            # Add dummy section for ConfigParser
            content = "[global]\n" + f.read()
        test_config.read_string(content)
        token = test_config['global']['test_token']
        print(f"Loaded token: {token[:5]}...")
    except Exception as e:
        print(f"{Colors.WARNING}Could not load token from {cfg_path}: {e}{Colors.ENDC}")
        token = None

    service = BERDLTable_conversion_service(config)
    ctx = {"user_id": "cly_user", "token": token}
    
    # 2. List Pangenomes
    print_step(1, "Discovering Pangenomes")
    
    # User Input for Object ID
    default_obj = "76990/ADP1Test"
    obj_ref = input(f"Enter BERDLTables Object Ref [default '{default_obj}']: ").strip()
    if not obj_ref: obj_ref = default_obj
    
    print(f"calling service.list_pangenomes(berdl_table_id='{obj_ref}')...")
    
    pg_result = service.list_pangenomes(ctx, {'berdl_table_id': obj_ref})[0]
    pangenomes = pg_result['pangenomes']
    
    print(f"\nFound {len(pangenomes)} pangenomes:")
    print(f"{'Index':<6} {'ID':<15} {'Taxonomy':<30}")
    print("-" * 60)
    for idx, pg in enumerate(pangenomes):
        print(f"{idx:<6} {pg['pangenome_id']:<15} {pg['pangenome_taxonomy']:<30}")
        
    # 3. Select Pangenome
    print_step(2, "Select Pangenome")
    try:
        idx = input(f"Enter index to use [0-{len(pangenomes)-1}] (default 0): ").strip()
        if not idx: idx = 0
        idx = int(idx)
        selected_pg = pangenomes[idx]['pangenome_id']
    except (ValueError, IndexError):
        print(f"{Colors.WARNING}Invalid selection. Using default 'pg_lims'.{Colors.ENDC}")
        selected_pg = "pg_lims"
        
    print(f"Selected: {Colors.BOLD}{selected_pg}{Colors.ENDC}")
    
    # 4. List Tables
    print_step(3, "List Tables")
    print(f"calling service.list_tables(pangenome_id='{selected_pg}', berdl_table_id='{obj_ref}')...")
    
    try:
        t_result = service.list_tables(ctx, {'pangenome_id': selected_pg, 'berdl_table_id': obj_ref})[0]
        tables = t_result['tables']
        print(f"\nAvailable Tables ({len(tables)}):")
        # Print in columns
        for i in range(0, len(tables), 3):
            print("  ".join(f"{t:<20}" for t in tables[i:i+3]))
    except Exception as e:
        print(f"{Colors.FAIL}Error listing tables: {e}{Colors.ENDC}")
        return

    # 5. Build Query
    print_step(4, "Build Query Parameters")
    
    default_table = "Genes" if "Genes" in tables else tables[0]
    table_name = input(f"Table to query [default '{default_table}']: ").strip()
    if not table_name: table_name = default_table
    
    limit = input("Limit rows [default 10]: ").strip()
    limit = int(limit) if limit else 10
    
    offset = input("Offset [default 0]: ").strip()
    offset = int(offset) if offset else 0
    
    # Filters
    filters = {}
    add_filter = input("Add column filter? (y/N): ").lower().strip()
    if add_filter == 'y':
        col = input("Column name (e.g., Primary_function): ").strip()
        val = input("Value (e.g., DNA): ").strip()
        if col and val:
            filters[col] = val

    params = {
        "pangenome_id": selected_pg,
        "table_name": table_name,
        "berdl_table_id": obj_ref,
        "limit": limit,
        "offset": offset,
        "query_filters": filters
    }
    
    # 6. Show Code
    print_step(5, "Generated Python Code")
    code = f"""# Connect to service
service = BERDLTable_conversion_service(config)

# Define parameters
params = {json.dumps(params, indent=4)}

# Execute Request
result = service.get_table_data(ctx, params)[0]"""
    print_code(code)
    
    input("Press Enter to execute this code...")
    
    # 7. Execute
    print_step(6, "Execution Results")
    try:
        start_t = time.time()
        result = service.get_table_data(ctx, params)[0]
        total_time = (time.time() - start_t) * 1000
        
        # Header Stats
        print(f"{Colors.BOLD}Status{Colors.ENDC}: Success")
        print(f"Total Rows in DB: {result.get('total_count', 'N/A')}")
        print(f"Filtered Rows:    {result.get('filtered_count', 'N/A')}")
        print(f"Returned Rows:    {result.get('row_count', 0)}")
        
        # Timing
        print(f"\n{Colors.BOLD}Performance Metrics{Colors.ENDC}:")
        print(f"  Backend Query:   {result.get('db_query_ms', 0):.2f} ms")
        print(f"  Conversion:      {result.get('conversion_ms', 0):.2f} ms")
        print(f"  Total Server:    {result.get('response_time_ms', 0):.2f} ms")
        print(f"  Client Total:    {total_time:.2f} ms")
        
        # Data Preview
        print(f"\n{Colors.BOLD}Data Preview ({min(5, len(result['data']))} rows){Colors.ENDC}:")
        headers = result['headers']
        print(" | ".join(f"{h[:15]:<15}" for h in headers))
        print("-" * (18 * len(headers)))
        
        for row in result['data'][:5]:
            # Truncate long cells
            print(" | ".join(f"{str(cell)[:15]:<15}" for cell in row))
            
    except Exception as e:
        print(f"{Colors.FAIL}Execution Failed:\n{e}{Colors.ENDC}")

if __name__ == "__main__":
    main()
