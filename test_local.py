#!/usr/bin/env python3
"""
Local testing script for SEC MCP Server
Tests tool invocations with Bearer token authentication
"""
import requests
import json

# Configuration
MCP_SERVER_URL = "http://localhost:8080/mcp"
TEST_ACCOUNT_ID = "test_account_123"


def test_tool_call(tool_name: str, arguments: dict = None):
    """Test a specific MCP tool"""
    
    headers = {
        "Authorization": f"Bearer {TEST_ACCOUNT_ID}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    
    response = requests.post(MCP_SERVER_URL, json=payload, headers=headers)
    print(f"\n{'='*60}")
    print(f"Tool: {tool_name}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("Testing SEC MCP Server...")
    
    # Test SEC API tools
    test_tool_call("get_company_submissions", {"cik": "0000320193"})  # Apple
    test_tool_call("get_company_facts", {"cik": "0000320193"})
    test_tool_call("get_company_concept", {
        "cik": "0000320193",
        "taxonomy": "us-gaap",
        "tag": "AccountsPayableCurrent"
    })
    test_tool_call("get_xbrl_frames", {
        "taxonomy": "us-gaap",
        "tag": "AccountsPayableCurrent",
        "unit": "USD",
        "period": "CY2019Q1I"
    })

