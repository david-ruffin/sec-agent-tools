"""
Agent for accessing the SEC-API Section Extraction API endpoint.

This module provides a standardized interface to extract sections from SEC filings
using the SEC-API Python package.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from sec_api import ExtractorApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def section_extraction_agent(
    filing_url: str,
    section: str,
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API Section Extraction API endpoint.
    
    This agent extracts specific sections from SEC filings using their URLs.
    
    Args:
        filing_url: URL of the SEC filing to extract from
        section: Section to extract (e.g., "1A", "7", "7A" for Risk Factors, MD&A, etc.)
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (extracted section content when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "ExtractorApi.get_section",
        "params": {
            "filing_url": "provided" if filing_url else "not provided",
            "section": section
        }
    }
    
    # Validate required parameters
    if not filing_url:
        return {
            "status": 400,
            "data": None,
            "error": "filing_url is required",
            "metadata": metadata
        }
    
    if not section:
        return {
            "status": 400,
            "data": None,
            "error": "section is required",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        client = ExtractorApi(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
        # Call the SEC-API endpoint with appropriate parameters
        result = client.get_section(filing_url, section)
        
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
            
        logger.error(f"Error calling Section Extraction API: {str(e)}")
        
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