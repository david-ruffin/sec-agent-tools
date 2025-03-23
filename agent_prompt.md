Simplified SEC Agent Generation Prompt

# SEC-API Agent Generation Template

Generate a standardized agent for the {API_NAME} endpoint from SEC-API.

## Input Documentation
{PASTE THE RELEVANT SECTION FROM SEC-API-PYTHON DOCUMENTATION HERE}

## File Structure
Create a file named `{api_name_snake_case}_agent.py` with the following structure:

```python
"""
Agent for accessing the SEC-API {API_NAME} endpoint.

This module provides a standardized interface to the {API_NAME} endpoint
from the SEC-API Python package.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def {api_name_snake_case}_agent(
    # REQUIRED PARAMETERS GO HERE
    # OPTIONAL PARAMETERS GO HERE
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API {API_NAME} endpoint.
    
    This agent {ONE LINE DESCRIPTION OF WHAT THIS AGENT DOES}.
    
    Args:
        # DOCUMENT PARAMETERS HERE
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (the primary payload when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "{EXACT_API_ENDPOINT_NAME}",
        "params": {
            # PARAMETER LOGGING GOES HERE
        }
    }
    
    # Validate required parameters
    # VALIDATION CODE GOES HERE
    
    try:
        # Initialize the SEC-API client
        from sec_api import {ORIGINAL_API_CLASS}
        client = {ORIGINAL_API_CLASS}(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
        # Call the SEC-API endpoint with appropriate parameters
        result = client.{METHOD_NAME}({PARAMETERS})
        
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
            
        logger.error(f"Error calling {API_NAME}: {str(e)}")
        
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
```

## Common Elements for All Agents

1. **Filename Pattern**: `{api_name_snake_case}_agent.py`
   - Example: `company_resolution_agent.py` for the Mapping API
   - Example: `filing_search_agent.py` for the Query API

2. **Function Name Pattern**: `{api_name_snake_case}_agent`
   - Example: `company_resolution_agent` for the Mapping API
   - Example: `filing_search_agent` for the Query API

3. **Import Pattern**: Always use `from sec_api import {OriginalApiClass}`

4. **Parameter Pattern**:
   - Required parameters first (no default values)
   - Optional parameters next (with default values)
   - Standard parameters (api_key, proxies) last

5. **Status Codes**:
   - 200: Success 
   - 400: Bad request/invalid parameters
   - 404: Resource not found
   - 429: Rate limit exceeded
   - 500: Internal error/unexpected exception

6. **Return Format**: Always return a dictionary with the exact keys:
   - `status`: Integer status code
   - `data`: API response when successful, None when error
   - `error`: Error message when error, None when successful
   - `metadata`: Dictionary with timestamp and API endpoint info

7. **API Key Handling**: 
   - Load from .env file using python-dotenv 
   - Allow override via parameter
   - Use pattern: `api_key=api_key or SEC_API_KEY`

## Example Usage for Query API

Given this documentation from SEC-API Python:
from sec_api import QueryApi
queryApi = QueryApi(api_key="YOUR_API_KEY")
query = {
"query": "ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:\"10-Q\"",
"from": "0",
"size": "10",
"sort": [{ "filedAt": { "order": "desc" } }]
}
filings = queryApi.get_filings(query)

Create a file named `filing_search_agent.py` containing:

```python
"""
Agent for accessing the SEC-API Query API endpoint.

This module provides a standardized interface to the SEC Filing Search endpoint
from the SEC-API Python package.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

def filing_search_agent(
    query: Dict[str, Any],
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API Query API endpoint.
    
    This agent searches SEC filings based on provided query parameters.
    
    Args:
        query: Dictionary containing search parameters (query string, from, size, sort)
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
            "query_provided": "yes" if query is not None else "no"
        }
    }
    
    # Validate required parameters
    if query is None:
        return {
            "status": 400,
            "data": None,
            "error": "query is required",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        from sec_api import QueryApi
        client = QueryApi(api_key=api_key or SEC_API_KEY, proxies=proxies)
        
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
            
        logger.error(f"Error calling Query API: {str(e)}")
        
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
```
```

## How to Use This Prompt

1. Identify which SEC-API endpoint you want to create an agent for
2. Find the relevant documentation section from the SEC-API Python package
3. Copy and paste that section into the prompt where indicated
4. Send the prompt to the LLM (you can use one prompt per endpoint)
5. The LLM will generate a complete agent file that follows the standard pattern

The LLM should be able to:
1. Derive the correct parameters from the example code
2. Structure the function appropriately
3. Create proper validation
4. Maintain consistent error handling
5. Follow the naming conventions

All agent implementations should be around 100-200 lines, with most of that being standard boilerplate. This approach avoids over-engineering while ensuring all agents follow a consistent pattern.

## Environment Setup

Ensure your project has a `.env` file with the SEC API key:

```
SEC_API_KEY=your_api_key_here
```

And install the required dependencies:

```bash
pip install python-dotenv sec-api
```