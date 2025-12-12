
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def call_service(method, params):
    payload = {
        "version": "1.1",
        "method": "BERDLTable_conversion_service." + method,
        "params": [params],
        "id": str(time.time())
    }
    try:
        start = time.time()
        response = requests.post(BASE_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        duration = (time.time() - start) * 1000
        
        if 'error' in data:
            print(f"❌ {method} Failed: {data['error']}")
            return None
            
        result = data['result'][0]
        print(f"✅ {method} Success ({duration:.1f}ms client-side)")
        return result
    except Exception as e:
        print(f"❌ {method} Exception: {e}")
        return None

def verify_flow():
    print("--- Starting Dynamic Service Flow Verification ---")
    
    # 1. List Pangenomes
    print("\n1. Fetching Pangenomes...")
    pangenomes = call_service("list_pangenomes", {"berdl_table_id": "demo"})
    if not pangenomes: return
    
    pg_list = pangenomes.get('pangenomes', [])
    print(f"   Found {len(pg_list)} pangenomes.")
    target_pg = next((p['pangenome_id'] for p in pg_list if p['pangenome_id'] == 'pg_lims'), None)
    
    if not target_pg:
        print("❌ 'pg_lims' not found!")
        return
    print(f"   Targeting: {target_pg}")

    # 2. List Tables
    print(f"\n2. Fetching Tables for {target_pg}...")
    tables_res = call_service("list_tables", {"berdl_table_id": "demo", "pangenome_id": target_pg})
    if not tables_res: return
    
    tables = tables_res.get('tables', [])
    print(f"   Found {len(tables)} tables: {tables}")
    if "Genes" not in tables:
        print("❌ 'Genes' table not found!")
        return

    # 3. Load Genes Table (First Page)
    print("\n3. Loading 'Genes' Table (Page 1)...")
    page1 = call_service("get_table_data", {
        "user_id": "test_script",
        "berdl_table_id": "demo",
        "pangenome_id": target_pg,
        "table_name": "Genes",
        "limit": 5,
        "offset": 0
    })
    
    if page1:
        print(f"   Source: {page1.get('source')}")
        print(f"   Response Time (Backend): {page1.get('response_time_ms')}ms")
        print(f"   Rows Returned: {len(page1.get('data', []))}")
        print(f"   Total Count: {page1.get('total_count')}")

    # 4. Filter Query (Simulating User Input 'dgoA')
    print("\n4. Filtering for 'dgoA'...")
    filter_res = call_service("get_table_data", {
        "user_id": "test_script",
        "berdl_table_id": "demo",
        "pangenome_id": target_pg,
        "table_name": "Genes",
        "limit": 5,
        "query_filters": {"Gene Name": "dgoA"}
    })
    
    if filter_res:
        print(f"   Source: {filter_res.get('source')}")
        print(f"   Filtered Count: {filter_res.get('filtered_count')}")
        data = filter_res.get('data', [])
        print(f"   Rows Matching: {len(data)}")
        for row in data:
            print(f"   Match: {row[3]} - {row[4]}") # Index 3 is Gene Name often, checking headers would be better but this is quick verify

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_flow()
