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
        
        # Validate table name
        if not table_name:
            raise ValueError("table_name is required")
        
        # V1.0: Use bundled database, ignore berdl_table_id
        # TODO V1.5: Download BERDLTables object from workspace and cache locally
        #            - Call workspace API to get BERDLTables object
        #            - Extract data handle references  
        #            - Download SQLite file to /data/cache/{object_id}/
        #            - Use cached path for subsequent calls
        if berdl_table_id:
            self.logger.info(f"V1.0: Ignoring berdl_table_id '{berdl_table_id}', using bundled data")
        
        # Check if table exists
        if not db_utils.validate_table_exists(self.db_path, table_name):
            available = ", ".join(self.available_tables)
            raise ValueError(f"Table '{table_name}' not found. Available tables: {available}")
        
        # Extract table data with timing breakdown
        headers, data, db_query_ms, conversion_ms = db_utils.get_table_data(
            self.db_path, table_name
        )
        
        # Calculate total response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Build result with performance metrics
        result = {
            "headers": headers,
            "data": data,
            "row_count": len(data),
            "table_name": table_name,
            "response_time_ms": response_time_ms,
            "db_query_ms": db_query_ms,
            "conversion_ms": conversion_ms
        }
        
        self.logger.info(
            f"Returned {len(data)} rows from '{table_name}' - "
            f"query: {db_query_ms:.2f}ms, convert: {conversion_ms:.2f}ms, total: {response_time_ms:.2f}ms"
        )
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
