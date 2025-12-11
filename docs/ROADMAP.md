# BERDLTable Conversion Service - Roadmap

## Current Version: V2.1

### ✅ Completed Features

#### V1.0 - Core Service (Completed)
- ✅ KBase Dynamic Service configuration
- ✅ Bundled SQLite database support
- ✅ `get_table_data` and `list_tables` methods
- ✅ 2D string array output format
- ✅ Performance metrics (db_query_ms, conversion_ms, response_time_ms)
- ✅ Comprehensive test suite
- ✅ HTML DataTables viewer

#### V2.0 - Query & Pagination (Completed)
- ✅ Pagination support (`offset`, `limit`)
- ✅ Sorting (`sort_column`, `sort_order`)
- ✅ Global search (`search_value`)
- ✅ Server-side processing for DataTables
- ✅ Row count metrics (`total_count`, `filtered_count`)

#### V2.1 - Advanced Query (Completed)
- ✅ Column-specific filtering (`query_filters`)
- ✅ Per-column search inputs in UI
- ✅ AND logic for multiple filters
- ✅ Unit tests for all query features

#### V2.5 - Multi-User Persistence (Completed)
- ✅ Namespaced scratch directory design
- ✅ Local verification of file persistence
- ✅ Logic for reuse of downloaded databases

---

## Planned Features

### V2.6 - Redis Result Caching (High Priority)
**Goal:** Cache query results to minimize SQLite file I/O and computing overhead.
**Features:**
- [ ] Connect to Redis (local/Rancher)
- [ ] Cache JSON results for `get_table_data` keys
- [ ] Implement TTL (e.g., 1 hour)
- [ ] Fallback to SQLite if Redis miss

### V1.5 - BERDLTables Integration (High Priority)
**Goal:** Connect to actual BERDLTable workspace objects.
**Features:**
- [ ] Download BERDLTable objects from workspace
- [ ] Extract data handle references
- [ ] Download SQLite files (if not effectively cached via Redis/Disk strategy)
- [ ] Local filesystem caching (V2.5 logic) as fallback for Redis misses

**Benefits:**
- Users can browse their own data
- No need to bundle databases in Docker image
- Dynamic data access from workspace

**Estimated Effort:** 2-3 weeks

---

### V2.2 - Advanced Filtering (Medium Priority)

**Goal:** Support more sophisticated query operations.

**Features:**
- [ ] Numeric range filters (e.g., `Start > 100 AND Start < 500`)
- [ ] Regular expression search
- [ ] Case-sensitive vs case-insensitive options
- [ ] NULL/empty value filtering
- [ ] Multiple sort columns

**Example:**
```python
result = client.get_table_data({
    "table_name": "Genes",
    "query_filters": {
        "Start": {"operator": "range", "min": 100, "max": 500},
        "Function": {"operator": "regex", "pattern": "DNA.*repair"}
    }
})
```

**Estimated Effort:** 1-2 weeks

---

### V3.0 - Data Aggregation (Medium Priority)

**Goal:** Provide summary statistics and aggregations.

**Features:**
- [ ] COUNT, SUM, AVG, MIN, MAX operations
- [ ] GROUP BY support
- [ ] Histogram/binning for numeric columns
- [ ] Value frequency counts

**Example:**
```python
result = client.aggregate_table({
    "table_name": "Genes",
    "group_by": "Function",
    "aggregations": {
        "count": "ID",
        "avg_length": "Length"
    }
})
```

**Estimated Effort:** 2-3 weeks

---

### V3.1 - Export Formats (Low Priority)

**Goal:** Support multiple export formats beyond CSV.

**Features:**
- [ ] JSON export
- [ ] Excel (.xlsx) export
- [ ] Parquet export for large datasets
- [ ] Compressed downloads (gzip)

**Estimated Effort:** 1 week

---

### V4.0 - Performance Optimizations (Low Priority)

**Goal:** Improve performance for very large tables (>1M rows).

**Features:**
- [ ] Database indexing recommendations
- [ ] Query result caching
- [ ] Streaming responses for large datasets
- [ ] Parallel query execution
- [ ] Connection pooling

**Estimated Effort:** 2-3 weeks

---

## Future Considerations

### Integration Features
- **Cross-table joins**: Query across multiple tables
- **Saved queries**: Store and reuse common queries
- **Query history**: Track recent queries per user

### UI Enhancements
- **Column visibility toggle**: Show/hide columns
- **Column reordering**: Drag-and-drop columns
- **Custom themes**: Light/dark mode
- **Mobile responsive design**: Better mobile experience

### Data Visualization
- **Built-in charts**: Histograms, scatter plots
- **Heatmaps**: For numeric data
- **Interactive plots**: Plotly integration

### Security & Access Control
- **Row-level permissions**: Filter data by user
- **Audit logging**: Track data access
- **Rate limiting**: Prevent abuse

---

## Version Timeline

| Version | Status | Target Date |
|---------|--------|-------------|
| V1.0 | ✅ Complete | Dec 2024 |
| V2.0 | ✅ Complete | Dec 2024 |
| V2.1 | ✅ Complete | Dec 2024 |
| V1.5 | 🔜 Planned | Q1 2025 |
| V2.2 | 📋 Backlog | Q2 2025 |
| V3.0 | 📋 Backlog | Q3 2025 |

---

## Contributing

We welcome feature requests and contributions!

**How to suggest a feature:**
1. Open a GitHub issue with the `enhancement` label
2. Describe the use case and expected behavior
3. Provide example code if possible

**Priority criteria:**
- User demand
- Implementation complexity
- Performance impact
- Compatibility with existing features

---

## Changelog

### V2.1 (Dec 2024)
- Added column-specific filtering with `query_filters`
- Added per-column search inputs in HTML viewer
- Improved test coverage for filtering scenarios

### V2.0 (Dec 2024)
- Added pagination with `offset` and `limit`
- Added sorting with `sort_column` and `sort_order`
- Added global search with `search_value`
- Implemented DataTables server-side processing
- Added `total_count` and `filtered_count` to responses

### V1.0 (Dec 2024)
- Initial release as KBase Dynamic Service
- Basic `get_table_data` and `list_tables` methods
- Bundled SQLite database support
- HTML DataTables viewer
- Performance metrics tracking
