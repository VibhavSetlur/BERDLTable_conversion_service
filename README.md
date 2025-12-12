# BERDLTable Conversion Service

A high-performance KBase Dynamic Service for serving tabular data from BERDLTable objects with automated local disk caching.

## 🚀 Features

- **Local Disk Caching** (V4.0): Efficient filesystem usage with automated cleanup (1-day retention)
- **Advanced Querying** (V2.0-V2.1): Pagination, sorting, column-specific filters
- **Query Optimization** (V3.0): Automatic indexing for <50ms response times
- **Robust Error Handling**: Simulated error states and clean failure modes for mock pangenomes
- **Production Ready**: 16/16 tests passing, ~100K+ rows/sec throughput

## 📊 Demo Viewer (UI)

**Interactive demonstration with real-time metrics:**

1.  **Start Local Server**:
    ```bash
    python3 test/scripts/start_server.py
    ```
2.  **Open in Browser**:
    *   Open `ui/demo_viewer.html` in your browser.
    *   **Note**: Because of CORS restrictions with `file://` protocol, direct fetch requests may be blocked by modern browsers.
    *   **Chrome Workaround**: Launch Chrome with `--allow-file-access-from-files` (dev only).
    *   **Best Practice**: Use a simple HTTP server:
        ```bash
        # From project root
        python3 -m http.server 8000
        # Open http://localhost:8000/ui/demo_viewer.html
        ```

Features:
- **Live Demo**: Real-time performance metrics & table browser
- **Architecture**: Visual diagrams of caching layers
- **Performance**: Benchmark comparisons & KPIs

## ⚡ Performance

| Scenario | Response Time | Throughput |
|----------|---------------|------------|
| SQLite (indexed) | 20-50ms | ~110,000 rows/sec |
| SQLite (no index) | 200+ms | Avoid |
| Pangenome Switch | ~1.6ms | Instant |

## 🏗️ Architecture (V4.0)

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Local Disk Check│
│ /scratch/caches │
└────────┬────────┘
         │
    MISS │ (Check 1-Day Age (temp))
         ▼
┌─────────────────┐
│ SQLite Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return JSON     │
└─────────────────┘
```

**Layers:**
1.  **Filesystem (V2.5/V4.0)**: Persistent SQLite files per pangenome.
2.  **Indexing (V3.0)**: `CREATE INDEX` on all columns.
3.  **Cleanup (V4.0)**: Automated deletion of caches older than 24 hours.

## 🧪 Testing

### 1. Docker Environment (Official)
Run the full KBase SDK test suite (ensures Docker compatibility):
```bash
kb-sdk test
```
*Expected Result: "OK" (16 tests passed)*

### 2. Local Python Environment (Fast)
Run tests directly on your host machine:
```bash
python3 test/BERDLTable_conversion_service_server_test.py
```

## 📦 Installation / Dev Setup

```bash
# Clone repository
git clone <repo-url>
cd BERDLTable_conversion_service

# Install dependencies
pip install pytest coverage
```

## 📖 Documentation

- **[walkthrough.md](.gemini/antigravity/brain/46c97fe7-5685-46ee-a909-2d4405a5a31a/walkthrough.md)**: Implementation walkthrough

## 🎯 Quick API Example

```python
# Python client example
service.get_table_data({
    "berdl_table_id": "workspace/object_id",
    "pangenome_id": "pg_lims",
    "table_name": "Genes",
    "limit": 25,
    "query_filters": {
        "Primary_function": "DNA"
    }
})
```

## 🏆 Version History

| Version | Feature | Status |
|---------|---------|--------|
| V1.0 | Dynamic service, bundled data | ✅ Complete |
| V2.0 | Pagination, sorting, search | ✅ Complete |
| V2.5 | Filesystem caching | ✅ Complete |
| V3.0 | Query optimization & indexing | ✅ Complete |
| V4.0 | Local Disk Management (No Redis) | ✅ Complete |

## 🤝 Contributing

For questions or contributions, contact the BERDLTable development team.
