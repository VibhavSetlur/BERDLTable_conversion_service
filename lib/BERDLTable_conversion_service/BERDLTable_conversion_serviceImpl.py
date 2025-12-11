# -*- coding: utf-8 -*-
"""
BERDLTable_conversion_serviceImpl.py - Implementation of BERDLTable Conversion Service

A KBase Dynamic Service that serves tabular data from BERDLTables objects
to web applications for performance testing and data visualization.

VERSION HISTORY:
    V1.0 - Serves data from bundled lims_mirror.db (hardcoded for performance testing)
    V1.5 - (Future) Download and cache BERDLTables from workspace
    V2.0 - (Future) Add filtering and pagination support

AUTHOR: Vibhav Setlur
DATE: 2024
"""

#BEGIN_HEADER
import logging
import os
import time

from BERDLTable_conversion_service import db_utils
from BERDLTable_conversion_service import redis_cache
from installed_clients.KBaseReportClient import KBaseReport
import shutil
import hashlib
import json
#END_HEADER


class BERDLTable_conversion_service:
    """
    Module Name:
    BERDLTable_conversion_service

    Module Description:
    A KBase Dynamic Service that serves tabular data from BERDLTables objects
    to web applications. Designed for high-performance data access in HTML reports.
    """

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa

    VERSION = "1.0.0"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    # Class-level constants
    DEFAULT_DB_PATH = "/kb/module/data/lims_mirror.db"
    #END_CLASS_HEADER

    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.scratch = config.get("scratch", "/kb/module/work/tmp")
        
        # Configure logging with timestamp and level
        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set database path - use bundled data for V1.0
        # V1.5 will add workspace download and caching
        self.data_dir = "/kb/module/data/"
        self.db_path = self.DEFAULT_DB_PATH
        
        # Check if running in local test mode (outside Docker)
        if not os.path.exists(self.db_path):
            # Try relative path for local testing
            local_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", "lims_mirror.db"
            )
            if os.path.exists(local_path):
                self.db_path = local_path
                self.logger.info(f"Using local database: {self.db_path}")
        
        # Pre-load table list for faster responses
        if os.path.exists(self.db_path):
            self.available_tables = db_utils.list_tables(self.db_path)
            self.logger.info(f"Loaded {len(self.available_tables)} tables: {self.available_tables}")
        else:
            self.available_tables = []
            self.logger.warning(f"Database not found: {self.db_path}")
        
        # Store callback URL for report generation (if available)
        self.callback_url = os.environ.get('SDK_CALLBACK_URL', None)
        
        self.logger.info("BERDLTable_conversion_service initialized successfully")
        #END_CONSTRUCTOR
        pass


    def get_table_data(self, ctx, params):
        """
        Retrieves table data from a BERDLTables object as a 2D string array.
        
        V1.0: Returns data from bundled lims_mirror.db (ignores berdl_table_id).
        V1.5: Will download and cache BERDLTables from workspace.
        V2.0: Will add filtering and pagination parameters.
        
        :param params: instance of type "GetTableDataParams" -> structure:
            parameter "berdl_table_id" of String (BERDLTables object reference)
            parameter "table_name" of String (Name of table to retrieve)
        :returns: instance of type "TableDataResult" -> structure:
            parameter "headers" of list of String (Column names)
            parameter "data" of list of list of String (Row data as 2D array)
            parameter "row_count" of Long (Total number of rows)
            parameter "table_name" of String (Name of table returned)
            parameter "response_time_ms" of Double (Server-side processing time)
        """
        # ctx is the context object
        # return variables are: result
        #BEGIN get_table_data
        start_time = time.time()
        
        self.logger.info("Starting get_table_data")
        self.logger.info(f"Params: {params}")
        
        # Extract parameters
        berdl_table_id = params.get("berdl_table_id", "")
        table_name = params.get("table_name", "")
        
        # V2.0: Extract pagination, sorting, and filter parameters
        limit = params.get("limit")
        offset = params.get("offset")
        sort_column = params.get("sort_column")
        sort_order = params.get("sort_order")
        search_value = params.get("search_value")
        query_filters = params.get("query_filters")
        
        # Validate table name
        if not table_name:
            raise ValueError("table_name is required")
            
        # V2.6: Redis Caching Layer
        # Check cache first (Level 2 Cache)
        # Generate deterministic cache key
        user_id = ctx.get('user_id', 'unknown_user')
        
        # Create a dict of relevant query params for hashing
        query_params = {
            "berdl_table_id": berdl_table_id,
            "table_name": table_name,
            "limit": limit,
            "offset": offset,
            "sort_column": sort_column,
            "sort_order": sort_order,
            "search_value": search_value,
            "query_filters": query_filters
        }
        
        # Serialize and hash
        param_hash = hashlib.sha256(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
        cache_key = f"{user_id}:{berdl_table_id}:{table_name}:{param_hash}"
        
        cached_result = redis_cache.get_cached_value("query_results", cache_key)
        if cached_result:
             self.logger.info(f"Redis Cache HIT for {cache_key}")
             # Ensure response_time_ms reflects that this was a cache hit (fast)
             # But we might want to preserve the 'cached' metrics?
             # For now, just return what was cached, updating response_time_ms to now
             cached_result['response_time_ms'] = (time.time() - start_time) * 1000
             cached_result['source'] = 'REDIS' # Optional: Add metadata
             return [cached_result]
        
        self.logger.info(f"Redis Cache MISS for {cache_key}")

        # V1.0: Use bundled database, ignore berdl_table_id
        # TODO V1.5: Download BERDLTables object from workspace and cache locally
        #            - Call workspace API to get BERDLTables object
        #            - Extract data handle references  
        #            - Download SQLite file to /data/cache/{object_id}/
        #            - Use cached path for subsequent calls
        # V2.5: Multi-User Caching & Persistence
        user_id = ctx.get('user_id', 'unknown_user')
        
        # 1. Define cache directory for this user and object
        # Sanitize IDs to be safe for filenames
        safe_user = str(user_id).replace('/', '_')
        safe_obj = str(berdl_table_id).replace('/', '_') if berdl_table_id else "bundled"
        
        cache_dir = os.path.join(self.scratch, 'berdl_cache', safe_user, safe_obj)
        os.makedirs(cache_dir, exist_ok=True)
        
        # 2. Resolve DB path in cache
        # Logic: If BERDLTable ID is provided, we should use the cached DB for that object.
        # Since V1.0/V1.5 is simulate/mock, we copy the bundled/local DB to this cache location 
        # to simulate a download.
        
        cached_db_path = os.path.join(cache_dir, f"{table_name}.db")
        
        if os.path.exists(cached_db_path):
             self.logger.info(f"Using cached database: {cached_db_path}")
             actual_db_path = cached_db_path
        else:
             self.logger.info(f"Database not in cache. Simulating download to: {cached_db_path}")
             # Mock Download: Copy from bundled location
             # Ensure source exists
             if os.path.exists(self.db_path):
                  # We copy the WHOLE db file. Note: In real/future versions, the DB might contains ALL tables
                  # or we might have one DB file per table.
                  # For this mock, we assume self.db_path contains the table.
                  # To avoid concurrency issues on copy, we might want a lock, but for now simple copy.
                  shutil.copy2(self.db_path, cached_db_path)
                  actual_db_path = cached_db_path
             else:
                  self.logger.error(f"Source bundled database not found at {self.db_path}")
                  # Fallback to whatever self.db_path was (likely fail later)
                  actual_db_path = self.db_path

        # Check if table exists
        if not db_utils.validate_table_exists(actual_db_path, table_name):
            # Try listing tables from the actual path we are using
            tables = db_utils.list_tables(actual_db_path)
            available = ", ".join(tables)
            raise ValueError(f"Table '{table_name}' not found in {actual_db_path}. Available tables: {available}")
        
        # V3.0 Optimization: Ensure indices exist for this table
        # This is fast if indices already exist (SQLite IF NOT EXISTS)
        try:
             db_utils.ensure_indices(actual_db_path, table_name)
        except Exception as e:
             self.logger.warning(f"Failed to ensure indices: {e}")

        # Extract table data with timing breakdown
        headers, data, total_count, filtered_count, db_query_ms, conversion_ms = db_utils.get_table_data(
            actual_db_path, 
            table_name,
            limit=limit,
            offset=offset,
            sort_column=sort_column,
            sort_order=sort_order,
            search_value=search_value,
            query_filters=query_filters
        )
        
        # Calculate total response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Build result with performance metrics
        result = {
            "headers": headers,
            "data": data,
            "row_count": len(data),
            "total_count": total_count,
            "filtered_count": filtered_count,
            "table_name": table_name,
            "response_time_ms": response_time_ms,
            "db_query_ms": db_query_ms,
            "conversion_ms": conversion_ms
        }
        self.logger.info(
            f"Returned {len(data)} rows from '{table_name}' - "
            f"query: {db_query_ms:.2f}ms, convert: {conversion_ms:.2f}ms, total: {response_time_ms:.2f}ms"
        )
        
        # Cache the result in Redis
        # Use default TTL (1 hour)
        redis_cache.set_cached_value("query_results", cache_key, result)
        
        #END get_table_data

        # Type validation
        if not isinstance(result, dict):
            raise ValueError('Method get_table_data return value result is not type dict as required.')
        
        return [result]


    def list_tables(self, ctx, params):
        """
        Lists available tables in a BERDLTables object.
        
        V1.0: Returns tables from bundled lims_mirror.db (ignores berdl_table_id).
        
        :param params: instance of type "ListTablesParams" -> structure:
            parameter "berdl_table_id" of String (BERDLTables object reference)
        :returns: instance of type "ListTablesResult" -> structure:
            parameter "tables" of list of String (List of table names)
        """
        # ctx is the context object
        # return variables are: result
        #BEGIN list_tables
        self.logger.info("Starting list_tables")
        self.logger.info(f"Params: {params}")
        
        berdl_table_id = params.get("berdl_table_id", "")
        
        # V1.0: Ignore berdl_table_id, return bundled tables
        if berdl_table_id:
            self.logger.info(f"V1.0: Ignoring berdl_table_id '{berdl_table_id}', using bundled data")
        
        result = {
            "tables": self.available_tables
        }
        
        self.logger.info(f"Returning {len(self.available_tables)} tables")
        #END list_tables

        # Type validation
        if not isinstance(result, dict):
            raise ValueError('Method list_tables return value result is not type dict as required.')
        
        return [result]


    def run_BERDLTable_conversion_service(self, ctx, params):
        """
        Legacy method for running as a standard KBase app with report output.
        Kept for backwards compatibility.
        
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure:
            parameter "report_name" of String
            parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_BERDLTable_conversion_service
        self.logger.info("Starting run_BERDLTable_conversion_service")
        self.logger.info(f"Params: {params}")
        
        # Create a simple report
        report = KBaseReport(self.callback_url)
        
        # Generate table summary for report
        table_info = []
        for table in self.available_tables:
            row_count = db_utils.get_table_row_count(self.db_path, table)
            table_info.append(f"{table}: {row_count} rows")
        
        report_text = (
            "BERDLTable Conversion Service\n"
            "==============================\n\n"
            f"Available tables:\n" + "\n".join(f"  - {t}" for t in table_info)
        )
        
        report_info = report.create({
            'report': {
                'objects_created': [],
                'text_message': report_text
            },
            'workspace_name': params.get('workspace_name', '')
        })
        
        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
        }
        #END run_BERDLTable_conversion_service

        # Type validation
        if not isinstance(output, dict):
            raise ValueError('Method run_BERDLTable_conversion_service return value output is not type dict as required.')
        
        return [output]


    def status(self, ctx):
        """
        Returns the status of this dynamic service.
        """
        #BEGIN_STATUS
        returnVal = {
            'state': "OK",
            'message': "",
            'version': self.VERSION,
            'git_url': self.GIT_URL,
            'git_commit_hash': self.GIT_COMMIT_HASH
        }
        #END_STATUS
        return [returnVal]
