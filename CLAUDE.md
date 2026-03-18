# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Warranty check API that looks up device warranty status for **Lenovo** and **HP** laptops/desktops by serial number. Deployed at `warranty-check.sigatics.com`.

## Architecture

- **`main.py`** — FastAPI application entry point. Defines the `/warranty/{serial_number}` endpoint. Routes requests by brand using serial number pattern matching (`determinar_marca_por_serial`). Lenovo serials go to `warrantylenovoo.py`, HP serials go to `ultra_fast_warranty.py`.
- **`warrantylenovoo.py`** — Lenovo warranty lookup via Lenovo's pcsupport API (`getproducts` + `getIbaseInfo`). Pure HTTP requests, no browser automation.
- **`ultra_fast_warranty.py`** — HP warranty lookup via Selenium (headless Chrome). Scrapes HP's support warranty page because HP has no public API. Chrome options are tuned for Ubuntu server deployment.
- **`index.html`** — Static frontend served separately. Calls the API and renders warranty results. Uses Microsoft Clarity for analytics.
- **`requests_you.py`** — Standalone test/exploration script for the Lenovo iBase API (not imported by the app).
- **`warrantylenovo.py`** — Earlier iteration of Lenovo warranty code (not imported by the app).
- **`ultra.py` / `ultra_fast_warranty_prod.py`** — Variant/staging copies of the HP warranty scraper.

## Running

```bash
# Activate venv
source .venv/Scripts/activate   # Windows/Laragon
source .venv/bin/activate       # Linux

# Run dev server (auto-reload)
python main.py
# or directly:
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API runs on `http://127.0.0.1:8000`. Test with: `GET /warranty/{serial_number}`.

## Key Dependencies

- FastAPI + uvicorn (web framework)
- Selenium + webdriver-manager (HP warranty scraping)
- requests (Lenovo API calls)

## Important Details

- The serial number brand detection logic in `main.py:determinar_marca_por_serial` uses length + prefix heuristics and has many edge cases with overlapping patterns between Dell/HP/Lenovo. Changes here require careful testing.
- HP warranty extraction depends on the live HP support website DOM structure — it can break if HP changes their page layout.
- The API response format differs slightly between brands: Lenovo returns `Brand`/`Product Name`/`Serial Number`/`Warranty Start`/`Warranty End`; HP returns `brand`/`product_name`/`serial_number`/`warranty_start`/`warranty_end` (snake_case).
- CORS is fully open (`allow_origins=["*"]`).
- Production URL: `https://warranty-check.sigatics.com`
