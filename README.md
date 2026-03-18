# Warranty Check API

A REST API that looks up device warranty status for **Lenovo** and **HP** laptops and desktops by serial number. Deployed at [warranty-check.sigatics.com](https://warranty-check.sigatics.com).

## Features

- Warranty lookup for **Lenovo** devices via Lenovo's `pcsupport` API (no browser required)
- Warranty lookup for **HP** devices via Selenium-powered headless Chrome scraping
- Automatic brand detection from serial number patterns
- Unified JSON response format for both brands
- Persistent browser pool for faster repeated HP lookups
- Docker-ready for easy deployment

## Architecture

```
main.py                     ← FastAPI entry point, routing, brand detection
warrantylenovoo.py          ← Lenovo warranty lookup (HTTP requests only)
ultra_fast_warranty.py      ← HP warranty lookup (Selenium + headless Chrome)
index.html                  ← Static frontend that calls the API
requirements.txt            ← Python dependencies
Dockerfile                  ← Container image definition
docker-compose.yml          ← Docker Compose service definition
```

## API Endpoints

### `GET /warranty/{serial_number}`

Returns warranty information for the given serial number.

**Supported brands:** Lenovo, HP

**Example request:**
```
GET /warranty/MJ0JCZZ8
```

**Example response:**
```json
{
  "Brand": "Lenovo",
  "Product Name": "ThinkCentre M70s Gen 3",
  "Serial Number": "MJ0JCZZ8",
  "Warranty Start": "15/01/2023",
  "Warranty End": "14/01/2026"
}
```

**Error responses:**

| Status | Description |
|--------|-------------|
| `400`  | Serial number belongs to an unsupported or unrecognized brand |
| `404`  | Warranty information not found for the given serial number |
| `500`  | Internal error retrieving warranty data |

### `GET /`

Health check endpoint. Returns a welcome message.

## Requirements

- Python 3.11+
- Google Chrome (for HP lookups)
- See [`requirements.txt`](requirements.txt) for Python packages:
  - `fastapi`
  - `uvicorn`
  - `requests`
  - `selenium`
  - `webdriver-manager`

## Installation & Running

### Local (without Docker)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# source .venv/Scripts/activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the development server (auto-reload)
python main.py
# or
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Docker

```bash
# Build and start the container
docker compose up --build

# Run in the background
docker compose up --build -d
```

The API will be available at `http://localhost:8000`.

> **Note:** The Docker image bundles Google Chrome and pre-downloads ChromeDriver so HP lookups work out of the box.

## Brand Detection

The `determinar_marca_por_serial` function in `main.py` identifies the brand from the serial number using length and prefix heuristics:

| Brand  | Example patterns |
|--------|-----------------|
| Lenovo | `MJ…` (8 chars), `PF…` (8/10 chars), `1S…` (20/22/24 chars), `CN…` (10 chars, non-`CND`) |
| HP     | `CND…`, `MXL…`, `5CD…`, `4CE…` (10 chars); `APBH…` (13 chars) |
| Dell   | 7-char alphanumeric, `ZZQYH…` (15 chars) |

> Serial numbers that cannot be matched to a supported brand return a `400` error.

## Notes

- **CORS** is fully open (`allow_origins=["*"]`), suitable for the single-page frontend but consider restricting in hardened deployments.
- The Lenovo lookup uses a dynamic CSRF token (`x-csrf-token`) that may need refreshing if Lenovo's API invalidates old tokens.
- HP warranty data is scraped from the live HP support website; the scraper may break if HP changes their page layout.
- Production URL: `https://warranty-check.sigatics.com`
