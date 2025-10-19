# Ebay Kleinanzeigen API

<div align="center">
  <h3 align="center">Ebay Kleinanzeigen API</h3>

  <p align="center">
    A powerful API interface for Ebay-Kleinanzeigen.de that enables you to fetch listings and specific data.
  </p>

  <p align="center">
    <b>🚀 Looking for a ready-to-use solution?</b>
    <br />
    Try it at <a href="https://kleinanzeigen-agent.de/features/developer-api"><strong>kleinanzeigen-agent.de »</strong></a>
    <br />
    ✓ Automated Search Agents
    <br />
    ✓ Search & Detail API
    <br />
    <a href="https://github.com/DanielWTE/ebay-kleinanzeigen-api/issues">Report Bug</a>
    ·
    <a href="https://github.com/DanielWTE/ebay-kleinanzeigen-api/issues">Request Feature</a>
  </p>
</div>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Want to skip the setup?

Visit [kleinanzeigen-agent.de](https://kleinanzeigen-agent.de/features/developer-api) for our hosted solution with additional features and zero configuration required.

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Playwright

### Installation

1. Clone the repository

```sh
git clone https://github.com/DanielWTE/ebay-kleinanzeigen-api.git
cd ebay-kleinanzeigen-api
```

2. Install dependencies

```sh
pip install -r requirements.txt
playwright install chromium
```

3. Start the services

```sh
python serve.py
```

This command starts both servers:
- REST API on `http://localhost:8000`
- MCP server on `http://localhost:8001/mcp`

### Installation using UV

#### Prerequisites

- uv package manager

#### Installation of dependencies

```sh
uv sync
```

#### Start the API

```sh
uv run uvicorn main:app --reload
```

### Installation using Docker

1. Build the Docker image

```sh
docker build -t ebay-kleinanzeigen-api .
```

2. Run the Docker container

```sh
docker run -p 8000:8000 ebay-kleinanzeigen-api
```

The API will be available at `http://localhost:8000`

### Deployment with Docker Compose (API + Frontend + Postgres)

For a full stack deployment including the Next.js frontend and the PostgreSQL database, use the provided `docker-compose.yml`:

```sh
docker compose up -d --build
```

The stack exposes:

- API: `http://localhost:8000`
- Frontend: `http://localhost:3001`
- **Database data**: Persisted locally in `~/kleinanzeigen-database/` directory (persistent across container restarts)

#### Database Persistence

The PostgreSQL database data is stored in a dedicated directory (`~/kleinanzeigen-database/`) which ensures:
- ✅ **Data survives container restarts and rebuilds**
- ✅ **Data persists across system reboots**
- ✅ **Easy backup** (just copy the `~/kleinanzeigen-database/` directory)
- ✅ **No data loss** when running `docker compose down`

The `kleinanzeigen-database/` directory is automatically created and stored in the user's home directory.

Environment variables relevant to the compose setup:

- `DATABASE_URL` – connection string used by the backend (defaults to the bundled Postgres service)
- `SCRAPER_INTERVAL_SECONDS` – default interval for scheduled scrape jobs (seconds)
- `SCRAPER_JOBS` – JSON array describing automated searches, e.g. `[{"name":"woom-3","query":"Woom 3","page_count":1}]`

### Image Similarity Detection & Monitoring

The backend now analyses all stored listing images automatically and flags entries where photos are re-used across multiple listings.

- A lightweight in-process event bus fans out `ListingImagesUpdated` events once new data is persisted by the scheduler.
- The dedicated `ImageAnalysisService` downloads the images, computes perceptual hashes via [`imagehash`](https://pypi.org/project/ImageHash/) and stores fingerprints in the new `image_fingerprints` table.
- Listings with hashes that are within the configurable Hamming distance threshold (default: `<= 5`) receive the label `Verdächtig` together with metadata about the matches.
- Results are surfaced in the backend API (see `ListingResponse.is_suspicious`) and in the Next.js frontend.
- Prometheus metrics for background processing are exposed at `GET /metrics` (`image_analysis_events_total`, `image_analysis_duration_seconds`).

#### Database Migration (existing installations)

When upgrading an existing database you need to add the new columns/table manually before starting the API:

```sql
-- PostgreSQL
ALTER TABLE listings
    ADD COLUMN IF NOT EXISTS is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS suspicion_reason VARCHAR(128),
    ADD COLUMN IF NOT EXISTS suspicion_confidence DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS suspicion_meta JSONB,
    ADD COLUMN IF NOT EXISTS last_analyzed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS posted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS posted_at_text VARCHAR(128);

CREATE TABLE IF NOT EXISTS image_fingerprints (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    image_url VARCHAR(2048) NOT NULL,
    hash_method VARCHAR(32) NOT NULL DEFAULT 'phash',
    hash_hex VARCHAR(32) NOT NULL,
    hash_bits BIGINT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_image_fingerprints_listing_id ON image_fingerprints(listing_id);
CREATE INDEX IF NOT EXISTS ix_image_fingerprints_hash_hex ON image_fingerprints(hash_hex);
```

```sql
-- SQLite (run via sqlite3 CLI)
ALTER TABLE listings ADD COLUMN is_suspicious INTEGER NOT NULL DEFAULT 0;
ALTER TABLE listings ADD COLUMN suspicion_reason TEXT;
ALTER TABLE listings ADD COLUMN suspicion_confidence REAL;
ALTER TABLE listings ADD COLUMN suspicion_meta JSON;
ALTER TABLE listings ADD COLUMN last_analyzed_at TEXT;
ALTER TABLE listings ADD COLUMN posted_at TEXT;
ALTER TABLE listings ADD COLUMN posted_at_text TEXT;

CREATE TABLE IF NOT EXISTS image_fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    hash_method TEXT NOT NULL DEFAULT 'phash',
    hash_hex TEXT NOT NULL,
    hash_bits INTEGER,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_image_fingerprints_listing_id ON image_fingerprints(listing_id);
CREATE INDEX IF NOT EXISTS ix_image_fingerprints_hash_hex ON image_fingerprints(hash_hex);
```

After applying the migration restart the API. The scheduler will enqueue analysis jobs automatically for listings whose image set changed.

### API Endpoints

#### 1. Fetch Listings (Standard)

**Endpoint:** `GET /inserate`

**Description:** Retrieves a list of listings based on search criteria.

##### Query Parameters

- **`query`** *(string, optional)*: The search term (e.g., "fahrrad" to search for bicycles).
- **`location`** *(string, optional)*: The location or postal code to narrow the search (e.g., `10178` for Berlin).
- **`radius`** *(integer, optional)*: The search radius in kilometers from the specified location (e.g., `5` for a 5 km radius).
- **`min_price`** *(integer, optional)*: The minimum price in Euros for the listings (e.g., `200` for at least 200 Euros).
- **`max_price`** *(integer, optional)*: The maximum price in Euros for the listings (e.g., `500` for at most 500 Euros).
- **`page_count`** *(integer, optional)*: The number of pages to search or return (e.g., `5` for the first 5 pages, default is 1, max: 20 pages).

##### Example Request

```http
GET /inserate?query=fahrrad&location=10178&radius=5&min_price=200&page_count=5
```

#### 2. Fetch Listing Details

**Endpoint:** `GET /inserat/{id}`

**Description:** Retrieves detailed information about a specific listing.

##### Path Parameters

- **`id`** *(string)*: The unique identifier of the listing to fetch details for.

##### Example Request

```http
GET /inserat/12345
```

#### 3. Fetch Listings with Details (Combined)

**Endpoint:** `GET /inserate-detailed`

**Description:** Retrieves listings and their detailed information in a single request.

##### Query Parameters

Same as `/inserate` endpoint, plus:

- **`max_concurrent_details`** *(integer, optional)*: Maximum concurrent detail fetches (default: 5, max: 10).

##### Example Request

```http
GET /inserate-detailed?query=laptop&page_count=2&max_concurrent_details=5
```

#### 4. Persisted Listings

**Endpoint:**

- `GET /stored-listings` – returns paginated results of all stored listings
- `GET /stored-listings/{external_id}` – returns a single stored listing with full metadata

**Query Parameters for `/stored-listings`:**

- `limit` *(integer, optional, default 25)* – number of entries per page (max. 100)
- `offset` *(integer, optional, default 0)* – pagination offset
- `query_name` *(string, optional)* – filter by the configured job name
- `status` *(string, optional)* – filter by listing status (e.g. `active`, `sold`)
- `search` *(string, optional)* – full-text search in title and description

**Example Request**

```http
GET /stored-listings?query_name=woom-3&limit=50
```

### Documentation

#### API Response Format

All API endpoints return responses in the following JSON format:

##### API Response Format

```json
{
  "success": true,
  "time_taken": 1.23,
  "unique_results": 100,
  "data": [...],
  "performance_metrics": {
    "pages_requested": 5,
    "pages_successful": 5,
    "success_rate": 100.0,
    "average_page_time": 2.45
  }
}
```

##### Combined Endpoint Response Format

```json
{
  "success": true,
  "time_taken": 3.45,
  "unique_results": 25,
  "data": [
    {
      "adid": "123456",
      "title": "Example Item",
      "price": "100",
      "details": {
        "id": "123456",
        "description": "Full description...",
        "seller": {...},
        "location": {...}
      }
    }
  ],
  "performance_metrics": {
    "listings_found": 25,
    "details_fetched": 25,
    "success_rate": 100.0
  }
}
```

## Performance Features

## 📊 Performance Benchmarks

Performance tests conducted on **Arch Linux** with **Intel i7-1260P** processor:

| Endpoint | Operation | Avg Time | Min Time | Max Time | Success Rate | Results |
|----------|-----------|----------|----------|----------|--------------|---------|
| Root | API status check | 0.004s | 0.001s | 0.009s | 100% | - |
| Listings | 1 page search | 1.209s | 1.081s | 1.596s | 100% | 25 |
| Listings | 5 pages search | 2.436s | 2.328s | 2.532s | 100% | 125 |
| Listings | 10 pages search | 4.989s | 4.790s | 5.229s | 100% | 250 |
| Details | Single listing details | 1.072s | 0.928s | 1.276s | 100% | 1 |
| Combined | 1 page + details | 9.058s | 8.804s | 9.319s | 100% | 25 |
| Combined | 2 pages + details | 17.512s | 17.063s | 18.038s | 100% | 50 |

### Performance Highlights

- **Single page search**: ~1.2s average response time
- **10-page search**: ~5.0s average response time  
- **Individual listing details**: ~1.1s average response time
- **Combined search + details**: ~9.1s average for 1 page with full details

*All tests performed with uvloop optimization and browser context pooling enabled.*

### 🚀 Technical Features

- **uvloop Integration**: High-performance asyncio event loop
- **Context Pooling**: Efficient browser resource reuse
- **Memory Optimization**: Automatic garbage collection and efficient processing
- **Intelligent Concurrency**: Optimal concurrent processing with resource control

### 🔧 Production Ready

- **Clean API Responses**: Minimal overhead with essential data only
- **Resource Management**: Automatic cleanup and efficient resource usage
- **Scalable Architecture**: Handles concurrent requests efficiently
- **Docker Optimized**: Fast container builds with uv package manager

API documentation is available at `http://localhost:8000/docs` when running locally.

### Model Context Protocol (MCP)

The MCP server runs alongside the REST API and exposes the same functionality as tools for MCP-compatible clients. 

- **MCP Endpoint**: `http://localhost:8001/mcp`
- **Available Tools**: 
  - `search_listings` - Search Kleinanzeigen with all filters
  - `get_listing_details` - Fetch detailed information for a listing

Configure your MCP client to connect to `http://localhost:8001/mcp`. Environment variables:

- `MCP_HOST` (default `0.0.0.0`)
- `MCP_PORT` (default `8001`)
- `API_HOST` (default `0.0.0.0`)
- `API_PORT` (default `8000`)

When running via Docker, both services start automatically. Map both ports:
```sh
docker run -p 8000:8000 -p 8001:8001 ebay-kleinanzeigen-api
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
