# -*- coding: utf-8 -*-
"""
BERDLTable_conversion_service_server_test.py - Test Suite

Comprehensive tests for the BERDLTable Conversion Service with performance metrics.
Includes both integrated tests (with KBase auth) and standalone tests (local only).

USAGE:
    Integrated tests (in Docker): kb-sdk test
    Standalone tests (local):     python -m pytest test/ -v
"""

import os
import sys
import time
import unittest
from configparser import ConfigParser

# Add lib to path for local testing
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from BERDLTable_conversion_service.BERDLTable_conversion_serviceImpl import BERDLTable_conversion_service
from BERDLTable_conversion_service import db_utils


class BERDLTableConversionServiceTest(unittest.TestCase):
    """
    Test suite for BERDLTable Conversion Service.
    
    Tests both service methods and underlying database utilities.
    Includes performance benchmarks for reporting to PI.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up test fixtures.
        
        Supports two modes:
        1. Integrated mode: Full KBase environment with auth (inside Docker)
        2. Standalone mode: Local testing without KBase infrastructure
        """
        cls.performance_results = []
        
        # Check if running in KBase environment
        cls.is_kbase_env = 'KB_AUTH_TOKEN' in os.environ
        
        if cls.is_kbase_env:
            # Integrated mode - full KBase setup
            cls._setup_kbase_environment()
        else:
            # Standalone mode - minimal setup for local testing
            cls._setup_standalone()
    
    @classmethod
    def _setup_kbase_environment(cls):
        """Configure for KBase integrated testing."""
        from BERDLTable_conversion_service.BERDLTable_conversion_serviceServer import MethodContext
        from BERDLTable_conversion_service.authclient import KBaseAuth as _KBaseAuth
        from installed_clients.WorkspaceClient import Workspace
        
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('BERDLTable_conversion_service'):
            cls.cfg[nameval[0]] = nameval[1]
        
        # Get username from Auth
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        
        # Create context
        cls.ctx = MethodContext(None)
        cls.ctx.update({
            'token': token,
            'user_id': user_id,
            'provenance': [{
                'service': 'BERDLTable_conversion_service',
                'method': 'test_method',
                'method_params': []
            }],
            'authenticated': 1
        })
        
        # Initialize service
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = BERDLTable_conversion_service(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        
        # Create test workspace
        suffix = int(time.time() * 1000)
        cls.wsName = "test_BERDLTable_" + str(suffix)
        cls.wsClient.create_workspace({'workspace': cls.wsName})
    
    @classmethod
    def _setup_standalone(cls):
        """Configure for standalone local testing."""
        print("\n" + "=" * 60)
        print("RUNNING IN STANDALONE MODE (no KBase auth)")
        print("=" * 60 + "\n")
        
        # Minimal config for local testing
        cls.cfg = {
            'scratch': '/tmp/berdl_test'
        }
        
        # Create scratch directory if needed
        os.makedirs(cls.cfg['scratch'], exist_ok=True)
        
        # Initialize service
        cls.serviceImpl = BERDLTable_conversion_service(cls.cfg)
        cls.ctx = {}  # Empty context for standalone mode
        cls.wsName = None

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures and print performance report."""
        # Print performance summary
        if cls.performance_results:
            print("\n" + "=" * 60)
            print("PERFORMANCE REPORT")
            print("=" * 60)
            for result in cls.performance_results:
                print(f"  {result['test']}: {result['time_ms']:.2f}ms "
                      f"({result['rows']} rows, {result['throughput']:.0f} rows/sec)")
            print("=" * 60 + "\n")
        
        # Clean up KBase workspace if in integrated mode
        if hasattr(cls, 'wsName') and cls.wsName and cls.is_kbase_env:
            try:
                cls.wsClient.delete_workspace({'workspace': cls.wsName})
                print('Test workspace was deleted')
            except Exception as e:
                print(f'Failed to delete workspace: {e}')

    # =========================================================================
    # Database Utility Tests
    # =========================================================================

    def test_db_utils_list_tables(self):
        """Test listing tables from database."""
        db_path = self.serviceImpl.db_path
        tables = db_utils.list_tables(db_path)
        
        self.assertIsInstance(tables, list)
        self.assertGreater(len(tables), 0, "Should find at least one table")
        self.assertIn("Genes", tables, "Genes table should exist")
        
        print(f"\n  Found {len(tables)} tables: {tables}")

    def test_db_utils_get_table_data(self):
        """Test extracting table data with timing breakdown."""
        db_path = self.serviceImpl.db_path
        table_name = "Genes"
        
        start = time.time()
        headers, data, total_count, filtered_count, db_query_ms, conversion_ms = db_utils.get_table_data(db_path, table_name)
        elapsed_ms = (time.time() - start) * 1000
        
        self.assertIsInstance(headers, list)
        self.assertIsInstance(data, list)
        self.assertGreater(len(headers), 0)
        self.assertGreater(len(data), 1000, "Genes table should have >1000 rows")
        
        # Verify data is all strings
        for row in data[:5]:  # Check first 5 rows
            for cell in row:
                self.assertIsInstance(cell, str)
        
        # Record performance
        rows = len(data)
        throughput = rows / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
        self.performance_results.append({
            'test': 'db_utils.get_table_data',
            'time_ms': elapsed_ms,
            'rows': rows,
            'throughput': throughput
        })
        
        print(f"\n  Extracted {rows} rows in {elapsed_ms:.2f}ms ({throughput:.0f} rows/sec)")

    # =========================================================================
    # Service Method Tests
    # =========================================================================

    def test_list_tables_method(self):
        """Test list_tables service method."""
        params = {"berdl_table_id": "test/1/1"}  # Ignored in V1.0
        
        result = self.serviceImpl.list_tables(self.ctx, params)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        tables_result = result[0]
        self.assertIn("tables", tables_result)
        self.assertIsInstance(tables_result["tables"], list)
        self.assertGreater(len(tables_result["tables"]), 0)
        
        print(f"\n  list_tables returned: {tables_result['tables']}")

    def test_get_table_data_genes(self):
        """Test get_table_data for Genes table with full performance metrics."""
        params = {
            "berdl_table_id": "test/1/1",  # Ignored in V1.0
            "table_name": "Genes"
        }
        
        start = time.time()
        result = self.serviceImpl.get_table_data(self.ctx, params)
        total_time_ms = (time.time() - start) * 1000
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        table_result = result[0]
        
        # Verify structure
        self.assertIn("headers", table_result)
        self.assertIn("data", table_result)
        self.assertIn("row_count", table_result)
        self.assertIn("table_name", table_result)
        self.assertIn("response_time_ms", table_result)
        self.assertIn("total_count", table_result)
        self.assertIn("filtered_count", table_result)
        
        # Verify content
        self.assertEqual(table_result["table_name"], "Genes")
        self.assertGreater(table_result["row_count"], 1000)
        self.assertEqual(len(table_result["data"]), table_result["row_count"])
        
        # Record performance
        rows = table_result["row_count"]
        server_time = table_result["response_time_ms"]
        throughput = rows / (total_time_ms / 1000) if total_time_ms > 0 else 0
        
        self.performance_results.append({
            'test': 'get_table_data (Genes)',
            'time_ms': total_time_ms,
            'rows': rows,
            'throughput': throughput
        })
        
        print(f"\n  get_table_data returned {rows} rows")
        print(f"  Server processing time: {server_time:.2f}ms")
        print(f"  Total time: {total_time_ms:.2f}ms")
        print(f"  Throughput: {throughput:.0f} rows/sec")
        print(f"  Headers: {table_result['headers'][:5]}...")

    def test_get_table_data_invalid_table(self):
        """Test error handling for invalid table name."""
        params = {
            "berdl_table_id": "",
            "table_name": "NonexistentTable"
        }
        
        with self.assertRaises(ValueError) as context:
            self.serviceImpl.get_table_data(self.ctx, params)
        
        self.assertIn("not found", str(context.exception))
        print(f"\n  Correctly raised error: {context.exception}")

    def test_get_table_data_missing_table_name(self):
        """Test error handling for missing table name."""
        params = {
            "berdl_table_id": "test/1/1",
            "table_name": ""
        }
        
        with self.assertRaises(ValueError) as context:
            self.serviceImpl.get_table_data(self.ctx, params)
        
        self.assertIn("required", str(context.exception))
        print(f"\n  Correctly raised error: {context.exception}")

    # =========================================================================
    # V2.0 Feature Tests (Query & Pagination)
    # =========================================================================

    def test_get_table_data_pagination(self):
        """Test limit and offset parameters."""
        # 1. Get first 10 rows
        params1 = {
            "table_name": "Genes",
            "limit": 10,
            "offset": 0
        }
        result1 = self.serviceImpl.get_table_data(self.ctx, params1)[0]
        self.assertEqual(len(result1["data"]), 10)
        self.assertEqual(result1["row_count"], 10)
        self.assertEqual(result1["total_count"], 3356)
        
        # 2. Get next 10 rows
        params2 = {
            "table_name": "Genes",
            "limit": 10,
            "offset": 10
        }
        result2 = self.serviceImpl.get_table_data(self.ctx, params2)[0]
        self.assertEqual(len(result2["data"]), 10)
        
        # Verify rows are different (using ID column, usually second column index 1)
        id1 = result1["data"][0][1]
        id2 = result2["data"][0][1]
        self.assertNotEqual(id1, id2)
        print(f"\n  Pagination Verified: Row 1 ID={id1}, Row 11 ID={id2}")

    def test_get_table_data_sorting(self):
        """Test sorting by column."""
        # Sort by "ID" column in Genes table
        params = {
            "table_name": "Genes",
            "limit": 5,
            "sort_column": "ID",
            "sort_order": "asc"
        }
        result = self.serviceImpl.get_table_data(self.ctx, params)[0]
        data = result["data"]
        
        # Verify sorted order
        col_idx = result["headers"].index("ID")
        values = [row[col_idx] for row in data]
        sorted_values = sorted(values)
        self.assertEqual(values, sorted_values)
        
        # Reverse sort
        params["sort_order"] = "desc"
        result_desc = self.serviceImpl.get_table_data(self.ctx, params)[0]
        values_desc = [row[col_idx] for row in result_desc["data"]]
        
        # Verify desc results are sorted in descending order
        self.assertEqual(values_desc, sorted(values_desc, reverse=True))
        
        # Verify we got different data (top vs bottom of table)
        self.assertNotEqual(values, values_desc)
        
        print(f"\n  Sorting Verified: ASC={values[:3]}..., DESC={values_desc[:3]}...")

    def test_get_table_data_search(self):
        """Test global search filtering."""
        # Search for specific gene name or ID
        search_term = "ACIAD0001"
        params = {
            "table_name": "Genes",
            "search_value": search_term,
            "limit": 100
        }
        result = self.serviceImpl.get_table_data(self.ctx, params)[0]
        
        self.assertGreater(result["row_count"], 0)
        self.assertLess(result["row_count"], result["total_count"])
        self.assertEqual(result["filtered_count"], result["row_count"])
        
        # Verify search term matches at least one column in each row
        match_found = False
        for row in result["data"]:
            row_match = False
            for cell in row:
                if search_term in str(cell):
                    row_match = True
                    break
            if not row_match:
                self.fail(f"Row returned that does not contain '{search_term}': {row}")
        
        print(f"\n  Search Verified: Found {result['filtered_count']} rows matching '{search_term}'")

    def test_get_table_data_column_filter(self):
        """Test column-specific filtering."""
        # Search for Genes where primary_function contains "DNA" AND ID contains "00"
        query_filters = {
            "Primary_function": "DNA",
            "ID": "00"
        }
        params = {
            "table_name": "Genes",
            "query_filters": query_filters,
            "limit": 100
        }
        result = self.serviceImpl.get_table_data(self.ctx, params)[0]
        
        # Verify filtered count
        self.assertGreater(result["row_count"], 0)
        self.assertLess(result["row_count"], result["total_count"])
        
        # Verify each row matches both conditions
        pf_idx = result["headers"].index("Primary_function")
        id_idx = result["headers"].index("ID")
        
        for row in result["data"]:
            self.assertIn("dna", row[pf_idx].lower(), f"Primary_function should contain 'DNA' (case-insensitive): {row[pf_idx]}")
            self.assertIn("00", row[id_idx], f"ID should contain '00': {row[id_idx]}")
            
        print(f"\n  Column Filter Verified: Found {len(result['data'])} rows matching {query_filters}")

    # =========================================================================
    # Performance Stress Tests
    # =========================================================================

    def test_performance_multiple_tables(self):
        """Test fetching multiple tables to measure throughput."""
        tables_to_test = self.serviceImpl.available_tables[:5]  # First 5 tables
        
        print(f"\n  Testing {len(tables_to_test)} tables...")
        
        for table_name in tables_to_test:
            params = {"berdl_table_id": "", "table_name": table_name}
            
            start = time.time()
            result = self.serviceImpl.get_table_data(self.ctx, params)
            elapsed_ms = (time.time() - start) * 1000
            
            table_result = result[0]
            rows = table_result["row_count"]
            throughput = rows / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
            
            self.performance_results.append({
                'test': f'get_table_data ({table_name})',
                'time_ms': elapsed_ms,
                'rows': rows,
                'throughput': throughput
            })
            
            print(f"    {table_name}: {rows} rows in {elapsed_ms:.2f}ms")


# =========================================================================
# Standalone Performance Test Script
# =========================================================================

def run_performance_benchmark():
    """
    Run performance benchmarks without unittest framework.
    
    Use this for quick benchmarking:
        python test/BERDLTable_conversion_service_server_test.py --benchmark
    """
    print("\n" + "=" * 60)
    print("BERDL TABLE SERVICE - PERFORMANCE BENCHMARK")
    print("=" * 60 + "\n")
    
    # Initialize service
    cfg = {'scratch': '/tmp/berdl_test'}
    os.makedirs(cfg['scratch'], exist_ok=True)
    service = BERDLTable_conversion_service(cfg)
    
    print(f"Database: {service.db_path}")
    print(f"Available tables: {service.available_tables}\n")
    
    # Benchmark each table
    results = []
    for table_name in service.available_tables:
        params = {"berdl_table_id": "", "table_name": table_name}
        
        # Warm-up run
        service.get_table_data({}, params)
        
        # Timed run
        start = time.time()
        result = service.get_table_data({}, params)
        elapsed_ms = (time.time() - start) * 1000
        
        table_result = result[0]
        rows = table_result["row_count"]
        throughput = rows / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
        
        results.append({
            'table': table_name,
            'rows': rows,
            'time_ms': elapsed_ms,
            'throughput': throughput
        })
        
        print(f"  {table_name:20s} | {rows:6d} rows | {elapsed_ms:8.2f}ms | {throughput:8.0f} rows/sec")
    
    # Summary
    total_rows = sum(r['rows'] for r in results)
    total_time = sum(r['time_ms'] for r in results)
    avg_throughput = sum(r['throughput'] for r in results) / len(results)
    
    print("\n" + "-" * 60)
    print(f"  TOTAL: {total_rows} rows in {total_time:.2f}ms")
    print(f"  AVG THROUGHPUT: {avg_throughput:.0f} rows/sec")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    if '--benchmark' in sys.argv:
        run_performance_benchmark()
    else:
        unittest.main()
