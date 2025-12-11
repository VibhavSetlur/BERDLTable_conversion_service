# BERDLTable Conversion Service - User Guide

## Overview

The BERDLTable Conversion Service is a KBase Dynamic Service that provides high-performance access to tabular data from BERDLTables objects. It features a 2-layer caching architecture for optimal speed and supports advanced querying capabilities.

## Quick Start

### Local Development
```bash
# Start the service
python3 scripts/start_server.py

# Open the demo viewer
# Navigate to: file:///path/to/ui/demo_viewer.html
```

### KBase Deployment
The service will be accessible via the KBase narrative interface once deployed.

## Core Features

### V1.0 - Dynamic Service
- Serves tabular data from SQLite databases
- Returns data as 2D string arrays (JSON-RPC compatible)
- Performance metrics included in every response

### V2.0 - Server-Side Processing
- **Pagination**: `limit`, `offset` parameters
- **Sorting**: `sort_column`, `sort_order` parameters
- **Global search**: `search_value` parameter (deprecated in UI)
- **Counts**: `total_count`, `filtered_count` in responses

### V2.1 - Column Filtering
- **Per-column filters**: `query_filters` mapping (column → value)
- **AND logic**: Multiple filters combined with AND
- **Efficient**: Uses column indices (V3.0) for fast lookups

### V2.5 - Filesystem Caching
- **Multi-user support**: Namespaced by `user_id`
- **Persistent storage**: `/scratch/berdl_cache/<user_id>/<table_id>/`
- **Auto-download simulation**: Copies bundled DB to cache on first access

### V2.6 - Redis Result Caching
- **In-memory caching**: Redis stores JSON query results
- **Cache keys**: `user_id:table_id:query_hash` (SHA256)
- **TTL**: 3600 seconds (1 hour) automatic expiration
- **Graceful fallback**: Works without Redis (logs warning)

### V3.0 - Query Optimization
- **Automatic indexing**: `CREATE INDEX IF NOT EXISTS` on all columns
- **Column-first design**: Deprioritized global search in UI
- **Performance**: 20-50ms indexed queries vs. 200+ ms full scans

## API Reference

### `get_table_data(params)`

**Input Parameters:**
```javascript
{
    "berdl_table_id": "string",    // BERDLTable workspace reference
    "table_name": "string",        // Table name (e.g., "Genes")
    "limit": int,                  // Max rows to return (optional)
    "offset": int,                 // Skip N rows (optional)
    "sort_column": "string",       // Column to sort by (optional)
    "sort_order": "string",        // "asc" or "desc" (optional)
    "search_value": "string",      // Global search term (optional, deprecated)
    "query_filters": {             // Column-specific filters (optional)
        "column_name": "value",
        ...
    }
}
```

**Output:**
```javascript
{
    "headers": ["col1", "col2", ...],     // Column names
    "data": [[...], [...], ...],          // 2D array of row data
    "row_count": int,                     // Rows in this response
    "total_count": int,                   // Total rows in table
    "filtered_count": int,                // Rows matching filters
    "table_name": "string",               // Table name echoed back
    "response_time_ms": float,            // Total server time
    "db_query_ms": float,                 // SQLite query time
    "conversion_ms": float,               // Data conversion time
    "source": "REDIS" | "SQLite"          // Data source (V2.6+)
}
```

### `list_tables(params)`

**Input:**
```javascript
{
    "berdl_table_id": "string"  // BERDLTable reference
}
```

**Output:**
```javascript
{
    "tables": ["Genes", "Reactions", ...]  // List of table names
}
```

## Performance Metrics

| Scenario | Response Time | Notes |
|----------|---------------|-------|
| Redis cache hit | <5ms | Fastest path |
| SQLite (indexed) | 20-50ms | Column filters |
| SQLite (no index) | 200+ms | Avoid full scans |

**Throughput:** ~121,000 rows/sec (measured with 3,356-row Genes table)

## Caching Behavior

### Cache Key Generation
```
user_id:berdl_table_id:table_name:SHA256(query_params)
```

- **Same query, same user** → Redis hit
- **Different query** → Redis miss, SQLite query
- **Different user** → Isolated cache entry

### Cache Invalidation
- **Automatic**: TTL expires after 3600 seconds
- **Manual**: Redis flush (if needed)
- **On miss**: Re-query SQLite and update cache

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |

## Demo Viewer

For a comprehensive demonstration of all features, open `ui/demo_viewer.html` in your browser. It includes:

- **Live Demo**: Real-time metrics and interactive table browser
- **Architecture**: Visual diagrams of the caching layers
- **Performance**: Benchmark comparisons and KPIs
- **FAQ**: Design decisions and technical explanations

See [`docs/DEMO_GUIDE.md`](DEMO_GUIDE.md) for presentation tips and usage scenarios.

## Testing

**Run unit tests:**
```bash
python -m pytest test/BERDLTable_conversion_service_server_test.py -v
```

**Expected:** 11/11 tests pass

**Test Redis caching:**
```bash
python test_local/test_redis.py
```

## Troubleshooting

**Problem:** Service returns "Table not found"  
**Solution:** Check that the table name exists via `list_tables()`

**Problem:** Redis connection errors in logs  
**Solution:** Expected if Redis is not running. Service falls back to SQLite automatically.

**Problem:** Slow query performance  
**Solution:** Ensure column filters are used instead of global search. Check that indices exist (automatic in V3.0).

## Next Steps

- **V1.5 (Planned)**: Integration with BERDLTables workspace objects
- **Future**: Advanced aggregations, export formats, cross-table joins

## Support

For issues or questions, contact the BERDLTable development team or refer to:
- [`ROADMAP.md`](ROADMAP.md) - Feature timeline and future plans
- [`DEMO_GUIDE.md`](DEMO_GUIDE.md) - Demo viewer instructions
- `test/` - Unit test examples


## Overview

The BERDLTable Conversion Service provides fast, efficient access to tabular data stored in BERDLTable objects. It supports pagination, searching, sorting, and filtering for interactive data exploration.

## Quick Start

### Python Usage

```python
from installed_clients.BERDLTable_conversion_serviceClient import BERDLTable_conversion_service

# Initialize client
service_url = "https://kbase.us/services/berdl_table_service" # Subject to change on actual service url
client = BERDLTable_conversion_service(service_url)

# Get table data
result = client.get_table_data({
    "berdl_table_id": "12345/67/8",
    "table_name": "Genes",
    "limit": 25,
    "offset": 0
})

print(f"Loaded {result['row_count']} of {result['total_count']} rows")
```

### JavaScript Usage

```javascript
const response = await fetch(serviceUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        method: 'BERDLTable_conversion_service.get_table_data',
        params: [{
            berdl_table_id: '12345/67/8',
            table_name: 'Genes',
            limit: 25
        }],
        version: '1.1',
        id: '1'
    })
});
```

## Features

### 1. Pagination

```python
# Get first page
page1 = client.get_table_data({
    "table_name": "Genes",
    "limit": 25,
    "offset": 0
})

# Get second page
page2 = client.get_table_data({
    "table_name": "Genes",
    "limit": 25,
    "offset": 25
})
```

### 2. Global Search

```python
result = client.get_table_data({
    "table_name": "Genes",
    "search_value": "DNA repair"
})
```

### 3. Sorting

```python
result = client.get_table_data({
    "table_name": "Genes",
    "sort_column": "ID",
    "sort_order": "asc"
})
```

### 4. Column Filtering

```python
result = client.get_table_data({
    "table_name": "Genes",
    "query_filters": {
        "Function": "DNA",
        "ID": "ACIAD"
    }
})
```

## API Reference

### get_table_data

**Parameters:**
- `berdl_table_id` (string, required): Object reference
- `table_name` (string, required): Table name
- `offset` (int): Rows to skip
- `limit` (int): Max rows to return
- `sort_column` (string): Column to sort by
- `sort_order` (string): "asc" or "desc"
- `search_value` (string): Global search term
- `query_filters` (mapping): Column-specific filters

**Returns:**
- `headers`: Column names
- `data`: 2D array of rows
- `row_count`: Rows in response
- `total_count`: Total rows in table
- `filtered_count`: Rows matching filters
- `response_time_ms`: Server processing time

### list_tables

**Parameters:**
- `berdl_table_id` (string, required): Object reference

**Returns:**
- `tables`: List of table names

## Performance Tips

1. **Use pagination**: Always set `limit` for large tables
2. **Filter before sorting**: Reduce dataset size first
3. **Use column filters**: More efficient than global search

## HTML Viewer

Copy `ui/test_viewer.html` to your report and configure:

```javascript
const CONFIG = {
    serviceUrl: 'https://kbase.us/services/berdl_table_service',
    berdlTableId: '12345/67/8'
};
```

## Support

- GitHub Issues: Report bugs or request features
- KBase Help: help@kbase.us
- Roadmap: See `docs/ROADMAP.md`
