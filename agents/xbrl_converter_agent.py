"""
Agent for accessing the SEC-API XBRL-to-JSON Converter API endpoint.

This module provides a standardized interface to convert XBRL financial statements
to JSON format using the SEC-API Python package.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from sec_api import XbrlApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def xbrl_converter_agent(
    htm_url: Optional[str] = None,
    xbrl_url: Optional[str] = None,
    accession_no: Optional[str] = None,
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API XBRL-to-JSON Converter API endpoint.
    
    This agent converts XBRL financial statements to structured JSON format.
    Supports three methods of conversion:
    1. Using HTML filing URL (htm_url)
    2. Using XBRL file URL (xbrl_url)
    3. Using accession number (accession_no)
    
    Args:
        htm_url: URL of the filing ending with .htm
        xbrl_url: URL of the XBRL file ending with .xml
        accession_no: Accession number of the filing (e.g., 0001564590-21-004599)
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (JSON financial data when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "XbrlApi.xbrl_to_json",
        "params": {
            "htm_url": "provided" if htm_url else "not provided",
            "xbrl_url": "provided" if xbrl_url else "not provided",
            "accession_no": "provided" if accession_no else "not provided"
        }
    }
    
    # Validate that at least one parameter is provided
    if not any([htm_url, xbrl_url, accession_no]):
        return {
            "status": 400,
            "data": None,
            "error": "At least one of htm_url, xbrl_url, or accession_no must be provided",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        client = XbrlApi(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
        # Call the SEC-API endpoint with appropriate parameters
        if htm_url:
            result = client.xbrl_to_json(htm_url=htm_url)
        elif xbrl_url:
            result = client.xbrl_to_json(xbrl_url=xbrl_url)
        else:
            result = client.xbrl_to_json(accession_no=accession_no)
        
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
            
        logger.error(f"Error calling XBRL-to-JSON Converter API: {str(e)}")
        
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