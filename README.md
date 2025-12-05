# SEC EDGAR MCP Server

**Live:** https://mcp-sec-edgar-336274559375.us-central1.run.app/mcp

A single MCP tool that retrieves and parses SEC financial filings (10-Q and 10-K).

---

## MCP Tool: `get_sec_filing`

Converts a ticker + date range into structured financial data.

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ticker` | string | Stock ticker symbol | `"AAPL"` |
| `start_date` | string | Start date (YYYY-MM-DD) | `"2024-01-01"` |
| `end_date` | string | End date (YYYY-MM-DD) | `"2025-12-31"` |
| `form_type` | string | `"10-Q"` (quarterly) or `"10-K"` (annual) | `"10-Q"` |
| `output_format` | string | `"markdown"` or `"json"` | `"markdown"` |

### Example Usage

```
get_sec_filing("AAPL", "2024-01-01", "2024-12-31", "10-Q", "markdown")
```

Returns a formatted financial report with:
- Key metrics (Revenue, Net Income, Assets, etc.)
- All XBRL facts from the filing

---

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

Server runs at: `http://localhost:8080/mcp`

---

## Architecture

```
Ticker → CIK Lookup → SEC API → XBRL XML → Parse → JSON/Markdown
```

1. **Ticker → CIK**: Uses `company-tickers.json` (10,000+ companies)
2. **SEC API**: Fetches filing index, finds `_htm.xml` files
3. **XBRL Parser**: Extracts contexts, units, and facts
4. **Converter**: Outputs markdown report or structured JSON

---

## Files

| File | Description |
|------|-------------|
| `server.py` | Unified MCP server |
| `company-tickers.json` | Ticker → CIK mapping |
| `Dockerfile` | Cloud Run deployment |

---

## Done

- [x] Ticker to CIK conversion
- [x] SEC filing XML download (10-Q, 10-K)
- [x] XBRL parsing to JSON
- [x] Markdown report generation
- [x] Unified MCP tool
