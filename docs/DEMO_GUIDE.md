# BERDLTable Conversion Service - Demo Viewer Guide

## Quick Start

1. **Start the local server:**
   ```bash
   python3 scripts/start_server.py
   ```

2. **Open the live demo viewer:**
   ```bash
   # Open in your browser:
   file:///path/to/ui/demo_viewer.html
   ```

## Features Demonstrated

The viewer provides a single, focused dashboard for demonstrating the service capabilities:

### 1. 🏗️ Visualization
- **Architecture Flow**: A dynamic diagram showing the request path:
  - **Redis Cache** (Layer 1): &lt;5ms response (Green highlight)
  - **SQLite DB** (Layer 2): 20-50ms response (Purple highlight)
  - **Graceful Fallback**: Visual indication of cache misses

### 2. 📊 Metrics Dashboard
- **Total Queries**: Counter of all requests made
- **Cache Hits**: Number of requests served from Redis
- **Last Response**: Server service time for the most recent query
- **Last Source**: Explicit indicator (⚡ REDIS vs 💾 SQLite)

### 3. ⚙️ Interactive Controls
- **Table Selector**: Dynamically populates with all tables from `lims_mirror.db` (e.g., Genes, Reactions)
- **User ID**: Input field to demonstrate cache isolation between users
- **Controls**: Load button and page size selector

### 4. 📋 Data Browser
- **Live Data**: Full tabular display of the selected BERDL table
- **Column Filtering**: Input fields in the table footer to filter by specific columns (e.g., filter "Function" by "DNA")
- **Sorting**: Click column headers to sort ascending/descending
- **Pagination**: Navigate through large datasets (server-side processed)

## Presentation Scenarios

### Scenario 1: Cache Performance & Flow
1. Select "Genes" table.
2. Click **Load Table**.
   - Note the **SQLite** flow box highlights.
   - Response time: ~30-40ms.
3. Click **Load Table** again (same parameters).
   - Note the **Redis** flow box highlights.
   - Response time: <5ms.
   - "Cache Hits" counter increments.

### Scenario 2: Multi-User Isolation
1. Load "Genes" as `demo_user` (Result: Redis HIT if previously loaded).
2. Change User ID to `user_2`.
3. Click **Load Table**.
   - Result: **SQLite** (Miss).
   - Explain: "Cache keys are namespaced by User ID, ensuring private data isolation."

### Scenario 3: Query Capability
1. Load "Genes" table.
2. Scroll to the footer (bottom of table).
3. Type "DNA" in the **Primary_function** filter input.
4. Watch table update to show only DNA-related genes.
   - Explain: "This uses V3.0 indexed columns for fast, specific filtering."

## Key Talking Points

- **Redis-First Architecture**: We always check Redis first for sub-millisecond responses.
- **Graceful Degradation**: If Redis is offline (as in local dev without docker), the service transparently falls back to SQLite.
- **Full Dynamic Service**: Pagination, sorting, and filtering are handled on the server, not the client.

## Troubleshooting

**Problem:** "Service Offline" indicator usually red.
**Solution:** Ensure `python3 scripts/start_server.py` is running.

**Problem:** Dropdown says "Connection Failed".
**Solution:** Check if port 5000 is blocked or in use.

**Files Reference:**
- `ui/demo_viewer.html`: The interactive viewer.
- `docs/USER_GUIDE.md`: Detailed documentation and FAQ.
