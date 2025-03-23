import os
import re
import time
from typing import Dict, Any
from sec_api import EdgarEntitiesApi

class RateLimiter:
    def __init__(self, max_requests_per_second: int = 10):
        self.last_request_time = 0
        self.min_interval = 1.0 / max_requests_per_second

    def wait(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_interval:
            time.sleep(self.min_interval - time_since_last_request)
        self.last_request_time = time.time()

def validate_query(search_request: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the search request parameters."""
    if "query" not in search_request:
        return {
            "status": 400,
            "error": "Missing required parameter: query"
        }
    
    # Validate query format (field:value)
    if not re.match(r'^[a-zA-Z]+:[^:]+$', search_request["query"]):
        return {
            "status": 400,
            "error": "Invalid query format. Expected format: field:value"
        }
    
    # Validate pagination parameters
    if "from" in search_request and not search_request["from"].isdigit():
        return {
            "status": 400,
            "error": "Parameter 'from' must be a non-negative integer"
        }
    
    if "size" in search_request and not search_request["size"].isdigit():
        return {
            "status": 400,
            "error": "Parameter 'size' must be a non-negative integer"
        }
    
    # Validate sort criteria
    if "sort" in search_request:
        if not isinstance(search_request["sort"], list):
            return {
                "status": 400,
                "error": "Sort criteria must be a list"
            }
        for sort_item in search_request["sort"]:
            if not isinstance(sort_item, dict) or len(sort_item) != 1:
                return {
                    "status": 400,
                    "error": "Invalid sort criteria format"
                }
            for field, order in sort_item.items():
                if not isinstance(order, dict) or "order" not in order:
                    return {
                        "status": 400,
                        "error": "Invalid sort order format"
                    }
                if order["order"] not in ["asc", "desc"]:
                    return {
                        "status": 400,
                        "error": "Sort order must be 'asc' or 'desc'"
                    }
    
    return {"status": 200}

def edgar_entities_agent(search_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query the EDGAR Entities Database API.
    
    Args:
        search_request (dict): The search parameters including query, pagination, and sorting
        
    Returns:
        dict: Response containing status code and either data or error message
    """
    # Validate input
    validation_result = validate_query(search_request)
    if validation_result["status"] != 200:
        return validation_result
    
    try:
        # Initialize API client with rate limiting
        api_key = os.getenv("SEC_API_KEY")
        if not api_key:
            return {
                "status": 401,
                "error": "API key not found in environment variables"
            }
        
        entities_api = EdgarEntitiesApi(api_key)
        rate_limiter = RateLimiter()
        
        # Apply rate limiting
        rate_limiter.wait()
        
        # Make API request
        response = entities_api.get_data(search_request)
        
        # Process and validate response
        if not response or "data" not in response:
            return {
                "status": 404,
                "error": "No data found for the given query"
            }
        
        # Format dates in response
        for item in response["data"]:
            if "latestICFRAuditDate" in item and item["latestICFRAuditDate"]:
                item["latestICFRAuditDate"] = item["latestICFRAuditDate"].split("T")[0]
            if "cikUpdatedAt" in item and item["cikUpdatedAt"]:
                item["cikUpdatedAt"] = item["cikUpdatedAt"].split("T")[0]
        
        return {
            "status": 200,
            "query": search_request,
            "total": response.get("total", 0),
            "data": response["data"]
        }
        
    except Exception as e:
        error_message = str(e).lower()
        
        if "rate limit" in error_message:
            return {
                "status": 429,
                "error": "Rate limit exceeded. Please try again later."
            }
        elif "api key" in error_message or "unauthorized" in error_message:
            return {
                "status": 401,
                "error": "Invalid API key or unauthorized access"
            }
        elif "not found" in error_message:
            return {
                "status": 404,
                "error": "Requested resource not found"
            }
        else:
            return {
                "status": 500,
                "error": f"An unexpected error occurred: {str(e)}"
            } 