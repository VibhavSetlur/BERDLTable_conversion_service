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
        string pangenome_id;    /* Specific pangenome ID within the object (optional - uses first found if empty) */
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
        string source;                  /* Data source: "REDIS", "SQLite", "Cache" */
    } TableDataResult;

    /* Input parameters for list_pangenomes method */
    typedef structure {
        string berdl_table_id;  /* BERDLTables object reference */
    } ListPangenomesParams;

    /* Information about a single pangenome in the BERDLTables set */
    typedef structure {
        string pangenome_id;
        string pangenome_taxonomy;
        list<string> user_genomes;
        list<string> berdl_genomes;
        string handle_ref;     /* Reference to the SQLite file handle */
    } PangenomeMetadata;

    /* Output containing available pangenomes */
    typedef structure {
        list<PangenomeMetadata> pangenomes;
    } ListPangenomesResult;

    /* Input parameters for list_tables method */
    typedef structure {
        string berdl_table_id;  /* BERDLTables object reference */
        string pangenome_id;    /* Specific pangenome ID (optional) */
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
        Lists available pangenomes in a BERDLTables object.
        Retrieves metadata from the workspace object.
    */
    funcdef list_pangenomes(ListPangenomesParams params) returns (ListPangenomesResult result);

    /*
        Lists available tables in a specific pangenome (or the first found).
        
        @param params - ListTablesParams with berdl_table_id and optional pangenome_id
        @return ListTablesResult with list of table names
    */
    funcdef list_tables(ListTablesParams params) returns (ListTablesResult result);

    /*
        Retrieves table data from a BERDLTables object as a 2D string array.
        
        V1.0: Returns data from bundled lims_mirror.db (ignores berdl_table_id).
        V1.5: Downloads and caches BERDLTables from workspace using handle_ref.
        V2.0: Supports filtering and pagination parameters.
        V3.1: Supports pangenome_id selection.
        
        @param params - GetTableDataParams with IDs and filtering options
        @return TableDataResult with headers, data, row_count, timing info, and source
    */
    funcdef get_table_data(GetTableDataParams params) returns (TableDataResult result);

    /*
        Legacy method for running as a standard KBase app with report output.
        Kept for backwards compatibility.
        
        @param params - Mapping of parameter names to values
        @return ReportResults with report name and reference
    */
    funcdef run_BERDLTable_conversion_service(mapping<string,UnspecifiedObject> params) 
        returns (ReportResults output) authentication required;

};
