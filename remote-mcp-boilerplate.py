#!/usr/bin/env python3
"""
SEC EDGAR MCP Server - Stock Ticker to CIK Lookup
==================================================

This MCP server provides a tool to convert US equity stock tickers
to their corresponding SEC CIK (Central Index Key) identifiers.

The CIK is a unique identifier assigned by the SEC to companies
and is required for accessing SEC EDGAR filings.

Deployment URL: https://mcp-sec-edgar-xxxxxxxx-uc.a.run.app/mcp
"""

import os
import json
import logging
from fastmcp import FastMCP, settings  # type: ignore

# ============================================================================
# Configure Logging for Google Cloud Run
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger("sec-edgar-mcp")

# ============================================================================
# Configure FastMCP Global Settings
# ============================================================================

settings.streamable_http_path = "/mcp"

# ============================================================================
# Environment Variables & Configuration
# ============================================================================

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# ============================================================================
# Load Company Tickers Data
# ============================================================================

def load_ticker_to_cik_mapping() -> dict:
    """
    Load the company-tickers.json file and create a ticker -> CIK mapping.
    
    Returns:
        dict: Mapping of ticker symbols (uppercase) to formatted CIK strings
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "company-tickers.json")
    
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        
        # Build ticker -> CIK mapping
        ticker_to_cik = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            cik_num = entry.get("cik_str")
            if ticker and cik_num is not None:
                # Format CIK as 10-digit zero-padded string with "CIK" prefix
                formatted_cik = f"CIK{str(cik_num).zfill(10)}"
                ticker_to_cik[ticker] = {
                    "cik": formatted_cik,
                    "title": entry.get("title", "")
                }
        
        logger.info(f"Loaded {len(ticker_to_cik)} ticker-to-CIK mappings")
        return ticker_to_cik
        
    except FileNotFoundError:
        logger.error(f"company-tickers.json not found at {json_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing company-tickers.json: {e}")
        return {}

# Load the mapping at startup
TICKER_TO_CIK = load_ticker_to_cik_mapping()

# ============================================================================
# Create FastMCP Instance
# ============================================================================

mcp = FastMCP("sec-edgar")

# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def get_cik_from_ticker(ticker: str) -> str:
    """
    Convert a US equity stock ticker symbol to its SEC CIK identifier.
    
    The CIK (Central Index Key) is a unique 10-digit identifier assigned by the
    SEC to companies and individuals who file disclosures. This tool looks up
    the ticker symbol and returns the properly formatted CIK.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., "AAPL", "NVDA", "GOOGL").
                      Case-insensitive.
    
    Returns:
        str: The CIK identifier formatted as "CIKxxxxxxxxxx" where x is a digit.
             The CIK is always 10 digits, zero-padded on the left.
             Example: "AAPL" returns "CIK0000320193"
                      "NVDA" returns "CIK0001045810"
    
    Examples:
        get_cik_from_ticker("AAPL") -> "CIK0000320193"
        get_cik_from_ticker("nvda") -> "CIK0001045810"
        get_cik_from_ticker("GOOGL") -> "CIK0001652044"
    """
    # Normalize ticker to uppercase
    ticker_upper = ticker.strip().upper()
    
    logger.info(f"get_cik_from_ticker | ticker={ticker_upper}")
    
    if not ticker_upper:
        error_msg = "Error: Ticker symbol cannot be empty"
        logger.warning(f"get_cik_from_ticker | VALIDATION_ERROR | empty ticker")
        return error_msg
    
    # Look up the ticker
    if ticker_upper in TICKER_TO_CIK:
        result = TICKER_TO_CIK[ticker_upper]
        cik = result["cik"]
        title = result["title"]
        logger.info(f"get_cik_from_ticker | SUCCESS | {ticker_upper} -> {cik} ({title})")
        return cik
    else:
        error_msg = f"Error: Ticker '{ticker_upper}' not found in SEC database"
        logger.warning(f"get_cik_from_ticker | NOT_FOUND | {ticker_upper}")
        return error_msg


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SEC EDGAR MCP Server - Stock Ticker to CIK Lookup")
    print("=" * 70)
    print("Transport: Streamable HTTP (MCP 2025-06-18)")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Endpoint: http://{HOST}:{PORT}/mcp")
    print(f"Tickers loaded: {len(TICKER_TO_CIK)}")
    print("=" * 70)
    print("\nServer starting...\n")
    print("✓ Tool available: get_cik_from_ticker")
    print("✓ Cloud Run ready with structured logging")
    print("=" * 70)
    print()
    
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
