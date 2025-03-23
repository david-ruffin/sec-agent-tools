"""
Agent for accessing the SEC-API Mapping API endpoint.

This module provides a standardized interface to the company resolution endpoint
and company listing endpoints from the SEC-API Python package.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from sec_api import MappingApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def company_resolution_agent(
    identifier_type: str,  # 'name', 'ticker', 'cik', or 'cusip'
    identifier_value: str,
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API Mapping API endpoint.
    
    This agent resolves company identifiers (name, ticker, CIK, CUSIP) to full company details.
    
    Args:
        identifier_type: Type of identifier ('name', 'ticker', 'cik', or 'cusip')
        identifier_value: Value of the identifier to resolve
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (company information when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "MappingApi.resolve",
        "params": {
            "identifier_type": identifier_type,
            "identifier_value": identifier_value
        }
    }
    
    # Validate required parameters
    if identifier_type is None:
        return {
            "status": 400,
            "data": None,
            "error": "identifier_type is required",
            "metadata": metadata
        }
    
    if identifier_value is None:
        return {
            "status": 400,
            "data": None,
            "error": "identifier_value is required",
            "metadata": metadata
        }
    
    if identifier_type not in ["name", "ticker", "cik", "cusip"]:
        return {
            "status": 400,
            "data": None,
            "error": "identifier_type must be one of: name, ticker, cik, cusip",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        client = MappingApi(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
        # Use resolve() for all identifier types
        result = client.resolve(identifier_type, identifier_value)
        
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
            
        logger.error(f"Error calling Mapping API: {str(e)}")
        
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

def list_companies_agent(
    list_type: str,  # 'exchange', 'sector', or 'industry'
    list_value: str,
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API Mapping API listing endpoints.
    
    This agent lists companies by exchange, sector, or industry.
    
    Args:
        list_type: Type of listing ('exchange', 'sector', or 'industry')
        list_value: Value to filter by (exchange name, sector name, or industry name)
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (list of companies when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": f"MappingApi.resolve({list_type})",
        "params": {
            "list_type": list_type,
            "list_value": list_value
        }
    }
    
    # Validate required parameters
    if list_type is None:
        return {
            "status": 400,
            "data": None,
            "error": "list_type is required",
            "metadata": metadata
        }
    
    if list_value is None:
        return {
            "status": 400,
            "data": None,
            "error": "list_value is required",
            "metadata": metadata
        }
    
    if list_type not in ["exchange", "sector", "industry"]:
        return {
            "status": 400,
            "data": None,
            "error": "list_type must be one of: exchange, sector, industry",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        client = MappingApi(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
        # Use resolve() method with appropriate list_type
        result = client.resolve(list_type, list_value)
        
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
            
        logger.error(f"Error calling Mapping API for {list_type} listing: {str(e)}")
        
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