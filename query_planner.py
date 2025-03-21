"""
SEC Filing Query Planner

This module analyzes user queries and determines appropriate SEC-API query parameters.
It helps the planning agent make intelligent decisions about how to structure API calls.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

# Constants
MAX_SIZE = 100
DEFAULT_SIZE = 10
SINGLE_FILING_SIZE = 1

class QueryIntent:
    """Represents the intent of a user's query"""
    SINGLE_FILING = "single_filing"  # e.g., "latest 10-K"
    MULTIPLE_FILINGS = "multiple_filings"  # e.g., "compare quarterly reports"
    HISTORICAL_ANALYSIS = "historical_analysis"  # e.g., "all 2023 filings"
    GENERAL_SEARCH = "general_search"  # e.g., "filings mentioning AI"

def determine_query_intent(query: str) -> str:
    """
    Analyze the query to determine its intent.
    
    Args:
        query: The user's query string
        
    Returns:
        QueryIntent value indicating the type of query
    """
    query = query.lower()
    
    # Check for single filing patterns
    if any(pattern in query for pattern in [
        "latest", "most recent", "current", "last"
    ]) and any(form in query for form in ["10-k", "10-q", "8-k"]):
        return QueryIntent.SINGLE_FILING
    
    # Check for multiple filing patterns
    if any(pattern in query for pattern in [
        "compare", "all", "every", "each", "multiple"
    ]):
        return QueryIntent.MULTIPLE_FILINGS
    
    # Check for historical analysis patterns
    if any(pattern in query for pattern in [
        "history", "historical", "over time", "trend", "throughout"
    ]) or re.search(r'\b\d{4}\b', query):  # Contains a year
        return QueryIntent.HISTORICAL_ANALYSIS
    
    # Default to general search
    return QueryIntent.GENERAL_SEARCH

def determine_size_parameter(query: str) -> int:
    """
    Determine the appropriate size parameter based on query intent.
    
    Args:
        query: The user's query string
        
    Returns:
        int: The size parameter to use
    """
    intent = determine_query_intent(query)
    
    if intent == QueryIntent.SINGLE_FILING:
        return SINGLE_FILING_SIZE
    elif intent == QueryIntent.HISTORICAL_ANALYSIS:
        return MAX_SIZE
    elif intent == QueryIntent.MULTIPLE_FILINGS:
        # For multiple filings, try to determine count from query
        # Default to 10 if not specified
        count_match = re.search(r'(\d+)\s*(filing|report)', query.lower())
        return int(count_match.group(1)) if count_match else DEFAULT_SIZE
    else:
        return DEFAULT_SIZE

def determine_date_range(query: str) -> Dict[str, str]:
    """
    Determine the appropriate date range based on query context.
    
    Args:
        query: The user's query string
        
    Returns:
        Dict with start_date and end_date in YYYY-MM-DD format
    """
    query = query.lower()
    today = datetime.now()
    
    # Check for explicit year
    year_match = re.search(r'\b(19|20)\d{2}\b', query)
    if year_match:
        year = year_match.group(0)
        return {
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31"
        }
    
    # Check for relative time periods
    if "recent" in query or "latest" in query:
        three_months_ago = today - timedelta(days=90)
        return {
            "start_date": three_months_ago.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d")
        }
    
    # Default to last year if no time period specified
    one_year_ago = today - timedelta(days=365)
    return {
        "start_date": one_year_ago.strftime("%Y-%m-%d"),
        "end_date": today.strftime("%Y-%m-%d")
    }

def determine_form_types(query: str) -> List[str]:
    """
    Determine which SEC form types to search for based on query context.
    
    Args:
        query: The user's query string
        
    Returns:
        List of form type strings
    """
    query = query.lower()
    
    # Direct form type mentions
    form_types = []
    if "10-k" in query or "annual" in query:
        form_types.append("10-K")
    if "10-q" in query or "quarter" in query:
        form_types.append("10-Q")
    if "8-k" in query or "current" in query:
        form_types.append("8-K")
    if "13f" in query or "holdings" in query:
        form_types.append("13F")
    
    # Return all found types or default to most common
    return form_types if form_types else ["10-K", "10-Q", "8-K"]

def determine_sort_parameters(query: str) -> Dict[str, str]:
    """
    Determine how results should be sorted based on query context.
    
    Args:
        query: The user's query string
        
    Returns:
        Dict with sort_field and sort_order
    """
    query = query.lower()
    
    # Default sorting
    sort_params = {
        "sort_field": "filedAt",
        "sort_order": "desc"
    }
    
    # Check for chronological analysis
    if any(term in query for term in [
        "oldest", "first", "early", "chronological", "ascending"
    ]):
        sort_params["sort_order"] = "asc"
    
    # Check for company name sorting
    if "by company" in query or "alphabetical" in query:
        sort_params["sort_field"] = "companyName"
        sort_params["sort_order"] = "asc"
    
    return sort_params

def plan_query_parameters(query: str) -> Dict[str, Any]:
    """
    Plan all query parameters based on the user's request.
    
    Args:
        query: The user's query string
        
    Returns:
        Dict containing all necessary query parameters
    """
    # Get individual parameter determinations
    size = determine_size_parameter(query)
    date_range = determine_date_range(query)
    form_types = determine_form_types(query)
    sort_params = determine_sort_parameters(query)
    
    # Combine into final parameters
    return {
        "size": str(size),
        "from": "0",  # Start from beginning
        "start_date": date_range["start_date"],
        "end_date": date_range["end_date"],
        "form_types": form_types,
        "sort_field": sort_params["sort_field"],
        "sort_order": sort_params["sort_order"]
    } 