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

### API Endpoints

#### 1. Fetch Listings
**Endpoint:** `GET /inserate`

**Description:** Retrieves a list of listings based on search criteria.

##### Query Parameters:
- **`query`** *(string, optional)*: The search term (e.g., "fahrrad" to search for bicycles).
- **`location`** *(string, optional)*: The location or postal code to narrow the search (e.g., `10178` for Berlin).
- **`radius`** *(integer, optional)*: The search radius in kilometers from the specified location (e.g., `5` for a 5 km radius).
- **`min_price`** *(integer, optional)*: The minimum price in Euros for the listings (e.g., `200` for at least 200 Euros).
- **`max_price`** *(integer, optional)*: The maximum price in Euros for the listings (e.g., `500` for at most 500 Euros).
- **`page_count`** *(integer, optional)*: The number of pages to search or return (e.g., `5` for the first 5 pages, default is 1, max: 20 pages).

##### Example Request:
```http
GET /inserate?query=fahrrad&location=10178&radius=5&min_price=200&page_count=5
```

#### 2. Fetch Listing Details
**Endpoint:** `GET /inserat/{id}`

**Description:** Retrieves detailed information about a specific listing.

##### Path Parameters:
- **`id`** *(string)*: The unique identifier of the listing to fetch details for.

##### Example Request:
```http
GET /inserat/12345
```


### Documentation

#### API Response Format
All API endpoints return responses in the following JSON format:
```json
{
  "success": true,
  "data": [
    ...
  ]
}
```

API documentation is available at `http://localhost:8000/docs` when running locally.

### Model Context Protocol

The MCP server mirrors the REST API as tools that can be invoked by MCP-compatible clients. Configure your client to connect to `http://localhost:8001/mcp` (or the container port you expose) and authenticate if required by your setup. The following environment variables are available:

- `MCP_HOST` (default `0.0.0.0`)
- `MCP_PORT` (default `8001`)
- `API_HOST` (default `0.0.0.0`)
- `API_PORT` (default `8000`)

When running via Docker, both services are started automatically.

## License
Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
