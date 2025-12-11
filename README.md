# BERDLTable Conversion Service

A high-performance KBase Dynamic Service for serving tabular data from BERDLTable objects with 2-layer caching architecture.

## 🚀 Features

- **Multi-Layer Caching** (V2.5-V2.6): Redis + Filesystem for optimal performance
- **Advanced Querying** (V2.0-V2.1): Pagination, sorting, column-specific filters
- **Query Optimization** (V3.0): Automatic indexing, 20-50ms response times
- **Multi-User Support**: Isolated caches per user with graceful degradation
- **Production Ready**: 11/11 tests passing, ~121K rows/sec throughput

## 📊 Demo Viewer

**Interactive demonstration with real-time metrics:**

```bash
# Start local server
python3 scripts/start_server.py

# Open in browser
file:///path/to/ui/demo_viewer.html
```

Features 4 tabs:
- **Live Demo**: Real-time performance metrics & table browser
- **Architecture**: Visual diagrams of caching layers
- **Performance**: Benchmark comparisons & KPIs
- **FAQ**: Design decisions & technical details

See [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md) for presentation tips.

## ⚡ Performance

| Scenario | Response Time | Speedup |
|----------|---------------|---------|
| Redis cache hit | <5ms | 10x faster |
| SQLite (indexed) | 20-50ms | Baseline |
| SQLite (no index) | 200+ms | Avoid |

**Throughput**: ~121,000 rows/sec (Genes table, 3,356 rows)

## 🏗️ Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐  HIT   ┌──────────┐
│ Redis Cache     ├───────►│ Return   │
│ (V2.6)          │  <5ms  │ JSON     │
└────────┬────────┘        └──────────┘
         │ MISS
         ▼
┌─────────────────┐
│ SQLite Query    │
│ (V2.5 + V3.0)   │
│ 20-50ms         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cache Result    │
│ TTL=3600s       │
└─────────────────┘
```

**Layers:**
1. **Redis (V2.6)**: In-memory result cache, O(1) lookup
2. **Filesystem (V2.5)**: Persistent SQLite files per user/table
3. **Indexing (V3.0)**: `CREATE INDEX` on all columns

## 📦 Installation

```bash
# Clone repository
git clone <repo-url>
cd BERDLTable_conversion_service

# Install dependencies
pip install redis  # For V2.6 caching

# Set environment (optional)
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest test/BERDLTable_conversion_service_server_test.py -v

# Expected: 11/11 PASSED

# Test Redis caching
python test_local/test_redis.py
```

## 📖 Documentation

- **[USER_GUIDE.md](docs/USER_GUIDE.md)**: API reference, features, troubleshooting
- **[DEMO_GUIDE.md](docs/DEMO_GUIDE.md)**: Demo viewer usage & presentation tips
- **[ROADMAP.md](docs/ROADMAP.md)**: Feature timeline & future plans
- **[walkthrough.md](.gemini/antigravity/brain/.../walkthrough.md)**: Implementation walkthrough

## 🎯 Quick API Example

```python
# Python client example
service.get_table_data({
    "berdl_table_id": "workspace/object_id",
    "table_name": "Genes",
    "limit": 25,
    "offset": 0,
    "query_filters": {
        "Function": "DNA repair",
        "Start": ">1000"
    }
})

# Response includes:
# - headers, data (2D array)
# - total_count, filtered_count
# - response_time_ms, db_query_ms
# - source: "REDIS" or "SQLite"
```

## 🛠️ Technology Stack

- **Backend**: Python, SQLite, Redis
- **Frontend**: HTML/JS, DataTables, Chart.js
- **Infrastructure**: KBase Dynamic Service framework
- **Testing**: pytest, unittest

## 🏆 Version History

| Version | Feature | Status |
|---------|---------|--------|
| V1.0 | Dynamic service, bundled data | ✅ Complete |
| V2.0 | Pagination, sorting, search | ✅ Complete |
| V2.1 | Column filtering | ✅ Complete |
| V2.5 | Filesystem caching | ✅ Complete |
| V2.6 | Redis result caching | ✅ Complete |
| V3.0 | Query optimization & indexing | ✅ Complete |
| V1.5 | Workspace integration | 📋 Planned |

## 🤝 Contributing

This service is part of the BERDataLakehouse ecosystem and follows the same Redis caching patterns.

For questions or contributions, contact the BERDLTable development team.

## 📄 License

Part of the KBase project, see KBase licensing terms.

---

**Key differentiators:**
- ⚡ **10x faster** with Redis cache hits
- 🔒 **Multi-user safe** with isolated caches
- 🛡️ **Production ready** with graceful Redis fallback
- 📊 **Comprehensive demo** viewer for presentations
