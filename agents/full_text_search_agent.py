"""
Agent for accessing the SEC-API Full-Text Search API endpoint.

This module provides a standardized interface to search the full text of SEC filings
using the SEC-API Python package.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from sec_api import FullTextSearchApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def full_text_search_agent(
    query: Dict[str, Any],
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API Full-Text Search API endpoint.
    
    This agent searches the full text of SEC filings and their attachments.
    
    Args:
        query: Dictionary containing search parameters:
              - query: Search phrase (required)
              - formTypes: List of form types to search
              - startDate: Start date in YYYY-MM-DD format
              - endDate: End date in YYYY-MM-DD format
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (search results when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "FullTextSearchApi.get_filings",
        "params": {
            "query": "provided" if query and "query" in query else "not provided",
            "form_types": query.get("formTypes", []) if query else [],
            "date_range": f"{query.get('startDate', 'none')} to {query.get('endDate', 'none')}" if query else "none"
        }
    }
    
    # Validate required parameters
    if not query:
        return {
            "status": 400,
            "data": None,
            "error": "query dictionary is required",
            "metadata": metadata
        }
    
    if "query" not in query:
        return {
            "status": 400,
            "data": None,
            "error": "query.query (search phrase) is required",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        client = FullTextSearchApi(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
        # Call the SEC-API endpoint with appropriate parameters
        result = client.get_filings(query)
        
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
            
        logger.error(f"Error calling Full-Text Search API: {str(e)}")
        
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