#!/usr/bin/env python3
"""
Remote MCP Server Boilerplate - Google Cloud Run Deployment
============================================================

This template provides a complete structure for building a remote MCP server
that can be deployed to Google Cloud Run and accessed via HTTP.

Key Features:
- Streamable HTTP transport (MCP 2025-06-18 protocol)
- Custom endpoint configuration (/mcp)
- Bearer token authentication for account routing
- Structured logging for Cloud Run
- Error handling patterns

To use this template:
1. Replace "your-service-name" with your actual service name
2. Add your environment variables and API clients
3. Implement your MCP tools using @mcp.tool() decorator
4. Deploy to Google Cloud Run

Deployment URL: https://your-service.silk.fund/mcp
"""

import os
import logging
from dotenv import load_dotenv  # type: ignore
from fastmcp import FastMCP, settings  # type: ignore

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# Configure Logging for Google Cloud Run
# ============================================================================
# Cloud Run expects structured logs with severity levels (INFO, WARNING, ERROR)
# This format works well with Cloud Logging's automatic parsing

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger("your-service-mcp")

# ============================================================================
# Configure FastMCP Global Settings
# ============================================================================
# IMPORTANT: This MUST be done BEFORE creating the FastMCP instance
# Sets the MCP endpoint to /mcp instead of default /sse

settings.streamable_http_path = "/mcp"

# ============================================================================
# Environment Variables & Configuration
# ============================================================================
# Load your service-specific configuration here
# Example: API keys, service endpoints, feature flags

# Required configuration
YOUR_API_KEY = os.getenv("YOUR_API_KEY")
YOUR_API_SECRET = os.getenv("YOUR_API_SECRET")

# Optional configuration with defaults
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# Validate required credentials
if not YOUR_API_KEY or not YOUR_API_SECRET:
    raise ValueError(
        "Missing required environment variables: YOUR_API_KEY and YOUR_API_SECRET"
    )

# ============================================================================
# Initialize External API Clients
# ============================================================================
# Initialize any third-party API clients here
# Example: your_client = YourAPIClient(api_key=YOUR_API_KEY, secret=YOUR_API_SECRET)

# your_client = YourAPIClient(
#     api_key=YOUR_API_KEY,
#     secret_key=YOUR_API_SECRET,
#     environment=ENVIRONMENT
# )

# ============================================================================
# Create FastMCP Instance
# ============================================================================
# The name here appears in MCP protocol messages and helps identify your server

mcp = FastMCP("your-service-name")

# ============================================================================
# Authentication Helper Function
# ============================================================================
def get_account_id_from_header() -> str:
    """
    Extract account_id from Authorization Bearer token.
    
    This pattern allows the orchestrator to route requests to the correct account
    without the LLM needing to know or pass account_id in every tool call.
    
    The Authorization header format: "Bearer <account_id>"
    
    Returns:
        str: Account ID extracted from Bearer token
        
    Raises:
        ValueError: If Authorization header is missing or invalid
        
    Usage in tools:
        account_id = get_account_id_from_header()
    """
    from fastmcp.server.dependencies import get_http_request  # type: ignore
    
    # Get the current HTTP request context
    request = get_http_request()
    if not request:
        raise ValueError("No HTTP request context found.")
    
    # Extract Authorization header (case-insensitive)
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise ValueError("No Authorization header found. Please provide account_id as Bearer token.")
    
    # Validate Bearer scheme format
    if not auth_header.startswith("Bearer "):
        raise ValueError("Authorization header must use Bearer scheme.")
    
    # Extract token (account_id) from "Bearer <token>"
    account_id = auth_header[7:]  # Remove "Bearer " prefix (7 characters)
    if not account_id:
        raise ValueError("Bearer token is empty. Please provide account_id as Bearer token.")
    
    return account_id


# ============================================================================
# MCP Tools - Define Your Service Tools Here
# ============================================================================
# Each tool is a function decorated with @mcp.tool()
# The function's docstring becomes the tool's description for the LLM
# Type hints are used for parameter validation

@mcp.tool()
def example_tool(
    required_param: str,
    optional_param: str = "default_value",
    numeric_param: float = 1.0
) -> str:
    """
    Brief one-line description of what this tool does.
    
    More detailed explanation of the tool's purpose and behavior.
    This docstring is sent to the LLM to help it understand when and how
    to use this tool.
    
    Args:
        required_param (str): Description of this required parameter
        optional_param (str, optional): Description of this optional parameter.
            Defaults to "default_value"
        numeric_param (float, optional): Description of numeric parameter.
            Defaults to 1.0
    
    Returns:
        str: Description of what this tool returns. Always return strings
            for MCP tools - they're designed for LLM consumption.
    
    Examples:
        Simple usage: required_param="test"
        With options: required_param="test", optional_param="custom", numeric_param=2.5
    """
    # Extract account_id from authentication header
    account_id = get_account_id_from_header()
    
    # Log the tool invocation with key parameters
    logger.info(f"example_tool | account={account_id} | param={required_param}")
    
    try:
        # Your tool logic here
        # Example: result = your_client.do_something(account_id, required_param)
        
        result = f"Processed {required_param} for account {account_id}"
        
        # Log successful completion
        logger.info(f"example_tool | SUCCESS | result_length={len(result)}")
        return result
        
    except ValueError as e:
        # Handle validation errors - these are expected user errors
        error_msg = f"Error: {str(e)}"
        logger.warning(f"example_tool | VALIDATION_ERROR | {str(e)}")
        return error_msg
        
    except Exception as e:
        # Handle unexpected errors - these need investigation
        error_msg = f"Error: {type(e).__name__} - {str(e)}"
        logger.error(f"example_tool | ERROR | {type(e).__name__}: {str(e)}")
        return error_msg


@mcp.tool()
def get_account_info() -> str:
    """
    Get information about the authenticated account.
    
    This is a common pattern for account-based services where tools
    need to operate on the authenticated user's account.
    
    Returns:
        str: Formatted account information
    """
    account_id = get_account_id_from_header()
    logger.info(f"get_account_info | account={account_id}")
    
    try:
        # Example: account_data = your_client.get_account(account_id)
        
        result = f"""Account Information
Account ID: {account_id}
Status: Active
Environment: {ENVIRONMENT}"""
        
        logger.info(f"get_account_info | SUCCESS")
        return result
        
    except Exception as e:
        logger.error(f"get_account_info | ERROR | {type(e).__name__}: {str(e)}")
        return f"Error: {type(e).__name__} - {str(e)}"


@mcp.tool()
def example_list_tool(limit: int = 10) -> str:
    """
    Example tool that returns a list of items.
    
    Demonstrates pagination and formatting lists for LLM consumption.
    
    Args:
        limit (int, optional): Maximum number of items to return. Defaults to 10.
    
    Returns:
        str: Formatted list of items
    """
    account_id = get_account_id_from_header()
    logger.info(f"example_list_tool | account={account_id} | limit={limit}")
    
    try:
        # Example: items = your_client.list_items(account_id, limit=limit)
        
        # Simulate empty result
        items = []
        
        if not items:
            logger.info("example_list_tool | NO_ITEMS")
            return "No items found"
        
        # Format list with header
        result = f"Items ({len(items)})\n"
        for item in items:
            result += f"- {item}\n"
        
        logger.info(f"example_list_tool | SUCCESS | count={len(items)}")
        return result.rstrip()  # Remove trailing newline
        
    except Exception as e:
        logger.error(f"example_list_tool | ERROR | {type(e).__name__}: {str(e)}")
        return f"Error: {type(e).__name__} - {str(e)}"


# ============================================================================
# Helper Functions (Optional)
# ============================================================================
# For complex tools, create helper functions to keep tool code clean
# These don't need the @mcp.tool() decorator

def _validate_parameter(value: str) -> bool:
    """
    Example validation helper function.
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If validation fails
    """
    if not value or len(value) < 3:
        raise ValueError("Parameter must be at least 3 characters long")
    return True


def _format_result(data: dict) -> str:
    """
    Example formatting helper function.
    
    Args:
        data: Data to format
        
    Returns:
        str: Formatted string suitable for LLM consumption
    """
    lines = []
    for key, value in data.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Display server configuration on startup
    # This helps with debugging and verification during deployment
    
    print("=" * 80)
    print("Your Service MCP Server")
    print("=" * 80)
    print(f"Environment: {ENVIRONMENT}")
    print("Transport: Streamable HTTP (MCP 2025-06-18)")
    print("Authentication: Bearer Token (account_id)")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Endpoint: http://{HOST}:{PORT}/mcp")
    print("=" * 80)
    print("\nServer starting...\n")
    print("✓ Tools available: example_tool, get_account_info, example_list_tool")
    print("✓ Account routing via Bearer token")
    print("✓ Cloud Run ready with structured logging")
    print("=" * 80)
    print()
    
    # Start the FastMCP server
    # - transport="streamable-http": Uses modern MCP HTTP protocol
    # - host: Bind to all interfaces (required for Cloud Run)
    # - port: Use PORT from environment (Cloud Run provides this)
    
    mcp.run(transport="streamable-http", host=HOST, port=PORT)

