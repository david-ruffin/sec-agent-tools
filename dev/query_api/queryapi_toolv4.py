################################
## Imports ##
## Required libraries for the tool ##
################################
import os
from dotenv import load_dotenv
from sec_api import QueryApi
from langchain.tools import StructuredTool
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

################################
## Environment Setup ##
## Load API keys and configs ##
################################
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

# Initialize SEC API client
queryApi = QueryApi(api_key=SEC_API_KEY)

################################
## Constants ##
## Configuration values ##
################################
VALID_SORT_FIELDS = ["filedAt", "ticker", "companyName", "formType"]
VALID_SORT_ORDERS = ["asc", "desc"]
MAX_SIZE = "100"
DEFAULT_SIZE = "10"

################################
## Helper Functions ##
## Utility functions ##
################################
def validate_date_format(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_parameters(params: Dict[str, Any]) -> List[str]:
    """Validate query parameters and return list of errors"""
    errors = []
    
    # Validate sort field
    if "sort" in params and params["sort"]:
        sort_field = list(params["sort"][0].keys())[0]
        if sort_field not in VALID_SORT_FIELDS:
            errors.append(f"Invalid sort field. Must be one of: {', '.join(VALID_SORT_FIELDS)}")
        
        sort_order = params["sort"][0][sort_field]["order"]
        if sort_order not in VALID_SORT_ORDERS:
            errors.append(f"Invalid sort order. Must be one of: {', '.join(VALID_SORT_ORDERS)}")
    
    # Validate size
    if "size" in params:
        try:
            size_int = int(params["size"])
            if size_int < 1 or size_int > int(MAX_SIZE):
                errors.append(f"Size must be between 1 and {MAX_SIZE}")
        except ValueError:
            errors.append("Size must be a valid number")
    
    # Validate from parameter
    if "from" in params:
        try:
            from_int = int(params["from"])
            if from_int < 0:
                errors.append("From parameter must be non-negative")
        except ValueError:
            errors.append("From parameter must be a valid number")
    
    return errors

################################
## Tool Function ##
## Main query functionality ##
################################
def search_sec_filings(
    query: str,
    from_param: str = "0",
    size: str = DEFAULT_SIZE,
    sort_field: str = "filedAt",
    sort_order: str = "desc"
) -> str:
    """
    Search SEC filings using the QueryApi with parameter validation and error handling.
    
    Args:
        query: Search query following SEC-API query syntax
        from_param: Starting point for pagination
        size: Number of results to return (max 100)
        sort_field: Field to sort by (filedAt, ticker, companyName, formType)
        sort_order: Sort order (asc/desc)
    """
    try:
        # Build query parameters
        search_params = {
            "query": query,
            "from": from_param,
            "size": size,
            "sort": [{ sort_field: { "order": sort_order } }]
        }
        
        # Validate parameters
        errors = validate_parameters(search_params)
        if errors:
            return "Parameter validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        
        print(f"Executing SEC API query: {json.dumps(search_params, indent=2)}")
        
        # Call the API
        filings = queryApi.get_filings(search_params)
        
        if not filings:
            return "No results found matching your criteria."
        
        # Format results
        total_filings = filings.get("total", {}).get("value", 0)
        formatted_results = [f"Found {total_filings} results. Showing first 3:"]
        
        for i, filing in enumerate(filings.get("filings", [])[:3], 1):
            formatted_results.append(f"\nResult {i}:")
            formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
            formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
            formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
            # Add items for 8-K filings
            if filing.get('formType') == '8-K' and filing.get('items'):
                formatted_results.append(f"Items: {filing.get('items', 'N/A')}")
            # Add description if available
            if filing.get('description'):
                formatted_results.append(f"Description: {filing.get('description')}")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"An error occurred while searching SEC filings: {str(e)}"

################################
## LangChain Integration ##
## Tool and agent setup ##
################################
# Create the tool
sec_tool = StructuredTool.from_function(
    func=search_sec_filings,
    name="sec_filing_search",
    description="""Search SEC filings using the Query API. 
    Supports searching by:
    - ticker (e.g., 'ticker:TSLA')
    - form type (e.g., 'formType:"10-Q"')
    - date range (e.g., 'filedAt:[2020-01-01 TO 2020-12-31]')
    - 8-K items (e.g., 'items:"9.01"')
    
    Additional parameters:
    - from_param: Starting point for pagination (default: "0")
    - size: Number of results (1-100, default: 10)
    - sort_field: Field to sort by (filedAt, ticker, companyName, formType)
    - sort_order: Sort order (asc/desc)
    """
)

# Create LLM and agent
llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
agent = initialize_agent(
    [sec_tool],
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

################################
## Testing ##
## Using documented examples ##
################################
if __name__ == "__main__":
    # Test 1: TSLA example from documentation
    print("\n=== Testing TSLA Example ===")
    test_query_1 = 'ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:"10-Q"'
    result_1 = search_sec_filings(test_query_1)
    print(result_1)

    # Test 2: 8-K Items example from documentation
    print("\n=== Testing 8-K Items Example ===")
    test_query_2 = 'formType:"8-K" AND items:"9.01"'
    result_2 = search_sec_filings(test_query_2)
    print(result_2)

    # Test 3: Invalid parameters
    print("\n=== Testing Invalid Parameters ===")
    result_3 = search_sec_filings(
        query='formType:"8-K"',
        size="invalid",
        sort_field="invalid_field",
        sort_order="invalid_order"
    )
    print(result_3)

    # Test 4: Agent with error handling
    print("\n=== Testing Agent with Error Handling ===")
    response = agent.invoke({
        "input": "Find TSLA filings from 2020, sort by invalid_field"
    })
    print(f"\nAgent response:\n{response['output']}") 