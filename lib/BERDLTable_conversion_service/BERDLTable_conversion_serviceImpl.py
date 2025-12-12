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
        
        # Perform cleanup of old databases
        self._cleanup_old_pangenome_dbs(max_age_days=1)
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
        pangenome_id = params.get("pangenome_id", "default")
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


        # 3. Locate/Download SQLite DB (Level 2)
        # In a real scenario, we use handle_ref from the pangenome metadata to download
        # For V1.0/Demo, we map everything to the local bundled DB via the helper
        db_path = self._get_pangenome_db_path(pangenome_id)
        
        if not os.path.exists(db_path):
            self.logger.error(f"Database not found at {db_path}")
            raise ValueError(f"Database file not found for pangenome_id '{pangenome_id}' at path: {db_path}")

        # Check if table exists
        if not db_utils.validate_table_exists(db_path, table_name):
            # Try listing tables from the actual path we are using
            tables = db_utils.list_tables(db_path)
            available = ", ".join(tables)
            raise ValueError(f"Table '{table_name}' not found in {db_path}. Available tables: {available}")
        
        # 4. Query SQLite (Level 3 + V3.0 Optimization)
        t0 = time.time()
        
        # Extract columns for V2.0 features
        limit = params.get('limit')
        offset = params.get('offset')
        sort_col = params.get('sort_column')
        sort_dir = params.get('sort_order')
        search_val = params.get('search_value') # Deprecated in V3.0 UI but supported
        
        # V2.1 Column Filters
        query_filters = params.get('query_filters', {})
        
        try:
            # Ensure indices exist (V3.0 Optimization)
            db_utils.ensure_indices(db_path, table_name)
            
            headers, data, total_count, filtered_count, _, _ = db_utils.get_table_data(
                db_path, 
                table_name,
                limit=limit,
                offset=offset,
                sort_column=sort_col,
                sort_order=sort_dir,
                search_value=search_val,
                query_filters=query_filters
            )
        except Exception as e:
             self.logger.error(f"Database error: {e}")
             raise ValueError(f"Error querying table {table_name}: {str(e)}")

        db_query_ms = (time.time() - t0) * 1000
        
        # 5. Format & Return
        response_time_ms = (time.time() - start_time) * 1000
        conversion_ms = (time.time() - t0) * 1000 # Approximation
        
        result = {
            "headers": headers,
            "data": data,
            "row_count": len(data),
            "total_count": total_count,
            "filtered_count": filtered_count,
            "table_name": table_name,
            "response_time_ms": response_time_ms,
            "db_query_ms": db_query_ms,
            "conversion_ms": conversion_ms,
            "source": "SQLite"
        }
        
        return [result]
        #END get_table_data

        # Type validation
        if not isinstance(result, dict):
            raise ValueError('Method get_table_data return value result is not type dict as required.')
        
        return [result]


    def list_pangenomes(self, ctx, params):
        """
        Lists available pangenomes in a BERDLTables object.
        Fetches metadata from Workspace.
        """
        berdl_table_id = params.get("berdl_table_id", "")
        self.logger.info(f"list_pangenomes for {berdl_table_id}")
        
        # Mock Data Structure based on user request (V3.1)
        mock_pangenomes = [
            {
                "pangenome_id": "pg_lims",
                "pangenome_taxonomy": "LIMS Default (Bundled)",
                "user_genomes": ["lims/bundled"],
                "berdl_genomes": ["lims_mirror"],
                "handle_ref": "bundled"
            },
            {
                "pangenome_id": "pg_ecoli_k12",
                "pangenome_taxonomy": "Escherichia coli K12 (Mock)",
                "user_genomes": ["my_ws/bin_1", "my_ws/bin_2"],
                "berdl_genomes": ["ecoli1", "ecoli2"],
                "handle_ref": "KBH_12345"
            },
            {
                "pangenome_id": "pg_b_subtilis",
                "pangenome_taxonomy": "Bacillus subtilis (Mock)",
                "user_genomes": ["my_ws/bin_3"],
                "berdl_genomes": ["bsub1"],
                "handle_ref": "KBH_67890"
            }
        ]
        
        result = {"pangenomes": mock_pangenomes}
        return [result]


    def _cleanup_old_pangenome_dbs(self, max_age_days=1):
        """
        Removes temporary pangenome directories older than max_age_days.
        """
        now = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        pangenome_base_dir = os.path.join(self.scratch, 'pangenome_dbs')
        
        self.logger.info(f"Running database cleanup for {pangenome_base_dir} (Retention: {max_age_days} days)...")
        
        if not os.path.exists(pangenome_base_dir):
             return
             
        count = 0
        
        try:
            for dirname in os.listdir(pangenome_base_dir):
                dir_path = os.path.join(pangenome_base_dir, dirname)
                
                if os.path.isdir(dir_path):
                    try:
                        # Check modification time of directory
                        mtime = os.path.getmtime(dir_path)
                        
                        if now - mtime > max_age_seconds:
                            shutil.rmtree(dir_path)
                            self.logger.info(f"Removed old pangenome cache: {dirname}")
                            count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to check/remove {dirname}: {e}")
                    
            if count > 0:
                self.logger.info(f"Cleanup complete. Removed {count} pangenome caches.")
            else:
                self.logger.info("Cleanup complete. No old caches found.")
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


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
        
        # In real impl, use pangenome_id to find correct DB file
        pangenome_id = params.get("pangenome_id", "default") # Added pangenome_id
        db_path = self._get_pangenome_db_path(pangenome_id) # Changed to use helper
        
        try:
            tables = db_utils.list_tables(db_path)
            result = {"tables": tables}
        except Exception as e:
            self.logger.error(f"Error listing tables: {e}")
            raise ValueError(f"Error listing tables from {db_path}: {str(e)}")
        
        self.logger.info(f"Returning {len(result['tables'])} tables")
        #END list_tables

        # Type validation
        if not isinstance(result, dict):
            raise ValueError('Method list_tables return value result is not type dict as required.')
        
        return [result]

    def _get_pangenome_db_path(self, pangenome_id):
        # Helper to resolve DB path
        # In real impl, this maps pangenome_id -> /scratch/user/pangenome_id/data.db
        
        # DEMO SIMULATION LOGIC:
        # 1. pg_lims: Maps to bundled DB. First access = Simulate Download (Delay).
        # 2. Others:  Simulate API Not Implemented error.
        
        if pangenome_id != "pg_lims" and pangenome_id != "default":
             # Simulate missing backend for mock pangenomes
             raise ValueError(f"Simulated Error: Backend API for pangenome '{pangenome_id}' is not yet connected.")
        
        # Create a unique directory for this pangenome_id in scratch
        safe_pangenome_id = str(pangenome_id).replace('/', '_').replace(':', '_')
        pangenome_cache_dir = os.path.join(self.scratch, 'pangenome_dbs', safe_pangenome_id)
        os.makedirs(pangenome_cache_dir, exist_ok=True)
        
        # Define the target path for the DB file
        target_db_path = os.path.join(pangenome_cache_dir, "lims_mirror.db")
        
        # If the target DB doesn't exist, copy the bundled one (Simulate Download)
        if not os.path.exists(target_db_path):
            if os.path.exists(self.db_path):
                # Calculate simulated delay based on file size
                file_size = os.path.getsize(self.db_path)
                size_mb = file_size / (1024 * 1024)
                simulated_speed = 2.5 # MB/s
                delay = size_mb / simulated_speed
                
                self.logger.info(f"Simulating download: {size_mb:.2f} MB @ {simulated_speed} MB/s = {delay:.2f}s")
                
                # Check if we should enforce a minimum delay for demo visibility
                if delay < 1.0: delay = 1.0
                
                time.sleep(delay)
                shutil.copy2(self.db_path, target_db_path)
            else:
                self.logger.error(f"Bundled database not found at {self.db_path}. Cannot simulate download.")
                return self.db_path 
        else:
             self.logger.info(f"Using cached DB for {pangenome_id}")
        
        return target_db_path


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
