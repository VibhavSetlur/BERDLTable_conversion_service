# BERDLTable Conversion Service - User Guide

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
