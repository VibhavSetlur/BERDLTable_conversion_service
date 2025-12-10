/*
A KBase module: BERDLTable_conversion_service
Serves tabular data from BERDLTables objects to web applications.

VERSION HISTORY:
    V1.0 - Hardcoded data from bundled lims_mirror.db for performance testing
    V1.5 - (Future) Download and cache BERDLTables from workspace
    V2.0 - (Future) Add filtering and pagination support
*/

module BERDLTable_conversion_service {

    /* ========================================================================
       TYPE DEFINITIONS
       ======================================================================== */

    /* Input parameters for get_table_data method */
    typedef structure {
        string berdl_table_id;  /* BERDLTables object reference */
        string table_name;      /* Name of table to retrieve */
        int offset;             /* Skip N rows */
        int limit;              /* Return max N rows */
        string sort_column;     /* Column to sort by */
        string sort_order;      /* "asc" or "desc" */
        string search_value;    /* Global search term */
        mapping<string, string> query_filters; /* Column-specific filters (AND logic) */
    } GetTableDataParams;

    /* Output containing table data with performance metrics */
    typedef structure {
        list<string> headers;           /* Column names */
        list<list<string>> data;        /* Row data as 2D string array */
        int row_count;                  /* Number of rows returned in this page */
        int total_count;                /* Total rows in table (before filtering) */
        int filtered_count;             /* Total rows matching search (before pagination) */
        string table_name;              /* Name of table */
        float response_time_ms;         /* Total server-side time */
        float db_query_ms;              /* SQLite SELECT time */
        float conversion_ms;            /* Python → JSON conversion time */
    } TableDataResult;

    /* Input parameters for list_tables method */
    typedef structure {
        string berdl_table_id;  /* BERDLTables object reference */
    } ListTablesParams;

    /* Output containing available table names */
    typedef structure {
        list<string> tables;    /* List of table names in the BERDLTables object */
    } ListTablesResult;

    /* Legacy report output structure - kept for compatibility */
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;


    /* ========================================================================
       METHOD DEFINITIONS
       ======================================================================== */

    /*
        Retrieves table data from a BERDLTables object as a 2D string array.
        
        V1.0: Returns data from bundled lims_mirror.db (ignores berdl_table_id).
        V1.5: Will download and cache BERDLTables from workspace.
        V2.0: Will add filtering and pagination parameters.
        
        @param params - GetTableDataParams with berdl_table_id and table_name
        @return TableDataResult with headers, data, row_count, and timing info
    */
    funcdef get_table_data(GetTableDataParams params) returns (TableDataResult result);

    /*
        Lists available tables in a BERDLTables object.
        
        V1.0: Returns tables from bundled lims_mirror.db (ignores berdl_table_id).
        
        @param params - ListTablesParams with berdl_table_id
        @return ListTablesResult with list of table names
    */
    funcdef list_tables(ListTablesParams params) returns (ListTablesResult result);

    /*
        Legacy method for running as a standard KBase app with report output.
        Kept for backwards compatibility.
        
        @param params - Mapping of parameter names to values
        @return ReportResults with report name and reference
    */
    funcdef run_BERDLTable_conversion_service(mapping<string,UnspecifiedObject> params) 
        returns (ReportResults output) authentication required;

};
