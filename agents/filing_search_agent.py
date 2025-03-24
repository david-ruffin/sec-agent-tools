"""
Agent for accessing the SEC-API Filing Search & Download APIs.

This module provides a standardized interface to the SEC Filing Search endpoints
from the SEC-API Python package, including search and downloading.
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv
from sec_api import QueryApi, RenderApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def validate_query(query: Dict[str, Any]) -> Optional[str]:
    """Validate query parameters and syntax."""
    if not isinstance(query, dict):
        return "query must be a dictionary"
        
    # Check that query contains the "query" field which is the actual query string
    if "query" not in query:
        return "query.query is required"
        
    # Validate query syntax
    query_str = query["query"]
    if "AND AND" in query_str or "OR OR" in query_str:
        return "invalid boolean operator usage"
        
    # Validate pagination parameters
    if "from" in query and not str(query["from"]).isdigit():
        return "from must be a non-negative integer"
        
    if "size" in query and not str(query["size"]).isdigit():
        return "size must be a non-negative integer"
        
    # Validate sort parameters
    if "sort" in query and not isinstance(query["sort"], list):
        return "sort must be a list"
        
    return None

def filing_search_agent(
    query: Union[Dict[str, Any], str],
    download_format: Optional[str] = None,
    stream_mode: bool = False,
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API Filing Search & Download APIs.
    
    This agent provides access to filing search and file downloading.
    
    Args:
        query: Dictionary containing search parameters (query string, from, size, sort)
               or a string that will be properly formatted into the query dictionary
        download_format: Optional format for downloading ('original', 'html', 'pdf')
        stream_mode: Whether to use real-time streaming mode (currently not implemented)
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (filing data when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "QueryApi.get_filings",
        "params": {
            "query": "provided" if query is not None else "not provided",
            "download_format": download_format,
            "stream_mode": stream_mode
        }
    }
    
    # Check for stream_mode - note this is not implemented
    if stream_mode:
        return {
            "status": 501,  # Not Implemented
            "data": None,
            "error": "Real-time streaming is not implemented in this agent. Streaming requires WebSockets implementation. Use standard search with recent date filters instead.",
            "metadata": metadata
        }
    
    # Validate required parameters
    if query is None:
        return {
            "status": 400,
            "data": None,
            "error": "query is required",
            "metadata": metadata
        }
    
    # Process query parameter based on its type
    if isinstance(query, str):
        # If query is a string, format it into the expected dictionary structure
        formatted_query = {
            "query": query,
            "from": "0",
            "size": "10",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        logger.info(f"Converted string query to formatted query: {formatted_query}")
        query = formatted_query
    
    # Validate query structure and syntax
    validation_error = validate_query(query)
    if validation_error:
        return {
            "status": 400,
            "data": None,
            "error": validation_error,
            "metadata": metadata
        }
    
    # Log the final query being sent to SEC-API
    logger.info(f"Sending SEC-API query: {query}")
    
    try:
        api_key = api_key or SEC_API_KEY
        
        # Standard search mode
        client = QueryApi(api_key=api_key, proxies=proxies)
        result = client.get_filings(query)
        
        # Handle file downloading if requested
        if download_format and result.get("filings"):
            render_client = RenderApi(api_key=api_key, proxies=proxies)
            first_filing = result["filings"][0]
            url = first_filing.get("linkToFilingDetails")
            
            if url:
                if download_format == "original":
                    file_content = render_client.get_filing(url)
                    result["downloadedContent"] = file_content
                else:
                    return {
                        "status": 400,
                        "data": None,
                        "error": f"Invalid or unsupported download format: {download_format}. Only 'original' format is supported by RenderApi.",
                        "metadata": metadata
                    }
        
        # Return standardized success response
        return {
            "status": 200,
            "data": result,
            "error": None,
            "metadata": metadata
        }
    except Exception as e:
        # Determine appropriate error code
        error_code = 500
        if "rate limit" in str(e).lower():
            error_code = 429
        elif "not found" in str(e).lower():
            error_code = 404
        elif "invalid" in str(e).lower() or "bad request" in str(e).lower():
            error_code = 400
            
        logger.error(f"Error calling Filing Search API: {str(e)}")
        
        # Return standardized error response
        return {
            "status": error_code,
            "data": None,
            "error": str(e),
            "metadata": {
                **metadata,
                "exception_type": type(e).__name__
            }
        } 