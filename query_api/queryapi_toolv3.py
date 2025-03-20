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
## Tool Function ##
## Main query functionality ##
################################
def search_sec_filings(
    query: str,
    from_param: str = "0",
    size: str = "10",
    sort_field: str = "filedAt",
    sort_order: str = "desc"
) -> str:
    """
    Search SEC filings using the QueryApi with configurable parameters.
    
    Args:
        query: Search query following SEC-API query syntax
        from_param: Starting point for pagination
        size: Number of results to return
        sort_field: Field to sort by
        sort_order: Sort order (asc/desc)
    """
    # Build query parameters exactly as shown in documentation
    search_params = {
        "query": query,
        "from": from_param,
        "size": size,
        "sort": [{ sort_field: { "order": sort_order } }]
    }
    
    print(f"Executing SEC API query: {search_params}")
    
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

    # Test 3: Agent with 8-K query and pagination
    print("\n=== Testing Agent with 8-K Query and Pagination ===")
    response = agent.invoke({
        "input": "Find the next 10 8-K filings with Item 9.01 after the first 10 results"
    })
    print(f"\nAgent response:\n{response['output']}")

    # Test 4: Agent with sorting
    print("\n=== Testing Agent with Custom Sorting ===")
    response = agent.invoke({
        "input": "Find TSLA 10-Q filings from 2020, sorted by filing date in ascending order"
    })
    print(f"\nAgent response:\n{response['output']}") 