#!/usr/bin/env python3
"""
SEC EDGAR MCP Server - Unified Financial Filings Tool
======================================================

Single MCP tool that converts a ticker + date range + form type into
structured financial data (JSON or Markdown).

Workflow:
1. Ticker → CIK lookup
2. Fetch SEC filing index for date range
3. Download XBRL XML files
4. Parse and convert to requested format
"""

import os
import json
import logging
import time
import xml.etree.ElementTree as ET
from collections import defaultdict

import requests
from fastmcp import FastMCP
from starlette.responses import FileResponse

# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("sec-mcp")

# ============================================================================
# Configuration
# ============================================================================

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SEC_HEADERS = {
    "User-Agent": "sec-mcp-server/1.0 (contact@example.com)",
    "Accept-Encoding": "gzip, deflate",
}

# ============================================================================
# Load Ticker → CIK Mapping
# ============================================================================

def load_ticker_map() -> dict:
    """Load company-tickers.json into a ticker → CIK dict."""
    path = os.path.join(SCRIPT_DIR, "company-tickers.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return {
            entry["ticker"].upper(): str(entry["cik_str"])
            for entry in data.values()
            if entry.get("ticker") and entry.get("cik_str") is not None
        }
    except Exception as e:
        logger.error(f"Failed to load tickers: {e}")
        return {}

TICKER_TO_CIK = load_ticker_map()
logger.info(f"Loaded {len(TICKER_TO_CIK)} ticker mappings")

# ============================================================================
# SEC API Helpers
# ============================================================================

def get_filings(cik: str, form_type: str, start: str, end: str) -> list[dict]:
    """Fetch filing metadata from SEC for a CIK within date range."""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=SEC_HEADERS)
    resp.raise_for_status()
    recent = resp.json()["filings"]["recent"]
    
    # Map form_type input to SEC form names
    form_map = {"10-Q": "10-Q", "10Q": "10-Q", "10-K": "10-K", "10K": "10-K"}
    target_form = form_map.get(form_type.upper())
    if not target_form:
        return []
    
    filings = []
    for form, acc, date in zip(recent["form"], recent["accessionNumber"], recent["filingDate"]):
        if form == target_form and start <= date <= end:
            filings.append({
                "form": form,
                "accession": acc.replace("-", ""),
                "date": date
            })
    return filings


def get_xml_url(cik: str, accession: str) -> str | None:
    """Find the _htm.xml file URL for a filing."""
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/index.json"
    resp = requests.get(url, headers=SEC_HEADERS)
    resp.raise_for_status()
    
    for item in resp.json()["directory"]["item"]:
        if item["name"].lower().endswith("_htm.xml"):
            return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{item['name']}"
    return None


def download_xml(url: str) -> str:
    """Download XML content from URL."""
    resp = requests.get(url, headers=SEC_HEADERS)
    resp.raise_for_status()
    time.sleep(0.1)  # Rate limiting
    return resp.text

# ============================================================================
# XBRL Parser (from xbrl_parser/parser.py)
# ============================================================================

def parse_xbrl(xml_content: str) -> dict:
    """Parse XBRL XML string and extract contexts, units, and facts."""
    root = ET.fromstring(xml_content)
    
    contexts, units, facts = {}, {}, []
    
    for child in root:
        tag = child.tag
        local = tag.split("}")[-1] if "}" in tag else tag
        
        if local == "context":
            ctx_id = child.get("id")
            ctx_data = {}
            dims = {}
            for node in child.iter():
                node_local = node.tag.split("}")[-1]
                if node_local in ["startDate", "endDate", "instant"]:
                    ctx_data[node_local] = node.text
                elif node_local == "explicitMember":
                    dim = node.get("dimension")
                    if dim:
                        dims[dim] = node.text
            if dims:
                ctx_data["dimensions"] = dims
            contexts[ctx_id] = ctx_data
            
        elif local == "unit":
            unit_id = child.get("id")
            for node in child.iter():
                if node.tag.split("}")[-1] == "measure":
                    units[unit_id] = node.text
                    break
                    
        elif local not in ["schemaRef", "linkbaseRef", "roleRef", "arcroleRef"]:
            ctx_ref = child.get("contextRef")
            if not ctx_ref:
                continue
            
            ns_uri = tag.split("}")[0][1:] if "}" in tag else ""
            prefix = "unknown"
            if "us-gaap" in ns_uri: prefix = "us-gaap"
            elif "dei" in ns_uri: prefix = "dei"
            elif "sec.gov" in ns_uri: prefix = "sec"
            
            raw_text = "".join(child.itertext())
            facts.append({
                "tag": f"{prefix}:{local}",
                "value": " ".join(raw_text.split()),
                "contextRef": ctx_ref,
                "unitRef": child.get("unitRef"),
                "decimals": child.get("decimals")
            })
    
    # Enrich facts with period/unit info
    enriched = []
    for f in facts:
        item = f.copy()
        if f["contextRef"] in contexts:
            item["period"] = contexts[f["contextRef"]]
        if f["unitRef"] in units:
            item["unit"] = units[f["unitRef"]]
        enriched.append(item)
    
    return {"document_type": "XBRL", "contexts": contexts, "units": units, "facts": enriched}

# ============================================================================
# Markdown Converter (from xbrl_parser/converter.py)
# ============================================================================

def format_currency(value: str, unit: str | None) -> str:
    """Format numeric value with unit."""
    try:
        val = float(value)
        formatted = f"{val:,.2f}"
        if unit == "iso4217:USD":
            return f"$ {formatted}"
        return f"{formatted} {unit}" if unit else formatted
    except:
        return f"{value} {unit}" if unit else value


def to_markdown(data: dict, ticker: str, filing_date: str) -> str:
    """Convert parsed XBRL data to markdown report."""
    lines = [
        f"# {ticker.upper()} Financial Report",
        f"**Filing Date:** {filing_date}",
        f"**Document Type:** {data.get('document_type', 'XBRL')}",
        ""
    ]
    
    # Group facts by tag
    by_tag = defaultdict(list)
    for fact in data.get("facts", []):
        by_tag[fact["tag"]].append(fact)
    
    # Key metrics
    key_tags = [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:NetIncomeLoss",
        "us-gaap:EarningsPerShareBasic",
        "us-gaap:Assets",
        "us-gaap:AssetsCurrent",
        "us-gaap:Liabilities",
        "us-gaap:StockholdersEquity",
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "us-gaap:OperatingIncomeLoss"
    ]
    
    lines.append("## Key Financial Metrics")
    found = False
    for tag in key_tags:
        if tag not in by_tag:
            continue
        found = True
        metrics = sorted(
            by_tag[tag],
            key=lambda x: x.get("period", {}).get("endDate", x.get("period", {}).get("instant", "")),
            reverse=True
        )[:3]
        for m in metrics:
            val = format_currency(m["value"], m.get("unit"))
            p = m.get("period", {})
            period = f"{p.get('startDate', '')} to {p.get('endDate', '')}" if "endDate" in p else f"As of {p.get('instant', 'N/A')}"
            lines.append(f"- **{tag.split(':')[-1]}**: {val} ({period})")
    
    if not found:
        lines.append("- No key metrics found")
    
    lines.append("")
    lines.append(f"## All Facts ({len(data.get('facts', []))} total)")
    
    for tag in sorted(by_tag.keys())[:50]:  # Limit output
        lines.append(f"\n### {tag}")
        for f in sorted(by_tag[tag], key=lambda x: x.get("period", {}).get("endDate", ""), reverse=True)[:5]:
            val = format_currency(f["value"], f.get("unit"))
            p = f.get("period", {})
            period = f"{p.get('startDate', '')} to {p.get('endDate', '')}" if "endDate" in p else f"As of {p.get('instant', 'N/A')}"
            lines.append(f"- {val} ({period})")
    
    return "\n".join(lines)

# ============================================================================
# FastMCP Server
# ============================================================================

mcp = FastMCP("sec-filings")

# Favicon
FAVICON_PATH = os.path.join(SCRIPT_DIR, "favicon.ico")

@mcp.custom_route("/favicon.ico", methods=["GET"])
async def favicon(request):
    return FileResponse(FAVICON_PATH, media_type="image/x-icon")


@mcp.tool()
def get_sec_filing(
    ticker: str,
    start_date: str,
    end_date: str,
    form_type: str = "10-Q",
    output_format: str = "markdown"
) -> str:
    """
    Retrieve SEC financial filings for a company and return parsed data.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "NVDA", "MSFT")
        start_date: Start of date range in YYYY-MM-DD format (e.g., "2024-01-01")
        end_date: End of date range in YYYY-MM-DD format (e.g., "2025-12-31")
        form_type: Filing type - "10-Q" (quarterly) or "10-K" (annual)
        output_format: Output format - "markdown" or "json"
    
    Returns:
        Financial data from SEC filings in the requested format.
        For markdown: A formatted report with key metrics and all financial facts.
        For JSON: Structured data with contexts, units, and enriched facts.
    
    Example:
        get_sec_filing("AAPL", "2024-01-01", "2025-12-31", "10-Q", "markdown")
    """
    ticker = ticker.strip().upper()
    logger.info(f"get_sec_filing | {ticker} | {form_type} | {start_date} to {end_date}")
    
    # Validate ticker
    if ticker not in TICKER_TO_CIK:
        return f"Error: Ticker '{ticker}' not found in SEC database"
    
    cik = TICKER_TO_CIK[ticker]
    
    # Fetch filings
    try:
        filings = get_filings(cik, form_type, start_date, end_date)
    except Exception as e:
        return f"Error fetching filings: {e}"
    
    if not filings:
        return f"No {form_type} filings found for {ticker} between {start_date} and {end_date}"
    
    # Process each filing
    results = []
    for filing in filings:
        try:
            xml_url = get_xml_url(cik, filing["accession"])
            if not xml_url:
                continue
            
            xml_content = download_xml(xml_url)
            parsed = parse_xbrl(xml_content)
            
            if output_format.lower() == "json":
                results.append({
                    "ticker": ticker,
                    "form": filing["form"],
                    "filing_date": filing["date"],
                    "data": parsed
                })
            else:
                results.append(to_markdown(parsed, ticker, filing["date"]))
                
        except Exception as e:
            logger.error(f"Error processing {filing['accession']}: {e}")
            continue
    
    if not results:
        return f"No processable filings found for {ticker}"
    
    # Return results
    if output_format.lower() == "json":
        return json.dumps(results, indent=2)
    else:
        return "\n\n---\n\n".join(results)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SEC EDGAR MCP Server")
    print("=" * 60)
    print(f"Host: {HOST}:{PORT}")
    print(f"Endpoint: http://{HOST}:{PORT}/mcp")
    print(f"Tickers: {len(TICKER_TO_CIK)}")
    print("=" * 60)
    print("\nTool: get_sec_filing(ticker, start_date, end_date, form_type, output_format)")
    print("=" * 60)
    
    mcp.run(transport="streamable-http", host=HOST, port=PORT)

