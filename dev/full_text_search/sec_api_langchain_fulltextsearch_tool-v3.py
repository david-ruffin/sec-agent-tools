##################################
## IMPORTS ##
## Import required libraries ##
##################################
import os
from dotenv import load_dotenv
from sec_api import FullTextSearchApi
from langchain.tools import StructuredTool
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from typing import List, Optional

##################################
## ENVIRONMENT SETUP ##
## Initialize API keys and clients ##
##################################
# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

# Initialize SEC API client
fullTextSearchApi = FullTextSearchApi(api_key=SEC_API_KEY)

##################################
## TOOL FUNCTION ##
## Define the SEC filing search function ##
##################################
def search_sec_filings(
    query: str, 
    form_types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    from_param: Optional[int] = 0,
    size: Optional[int] = 10
) -> str:
    """
    Search SEC filings for specific terms with pagination support.
    
    Args:
        query: Search term to look for in SEC filings
        form_types: List of SEC form types to search (e.g., ['10-K', '10-Q', '8-K']).
                   Defaults to ['8-K', '10-Q'] if not specified.
        start_date: Start date for filing search in format 'YYYY-MM-DD'.
                   Defaults to '2021-01-01' if not specified.
        end_date: End date for filing search in format 'YYYY-MM-DD'.
                 Defaults to '2021-06-14' if not specified.
        from_param: Starting position for pagination (0-based).
                   Defaults to 0 (first page).
        size: Number of results to return per page.
              Defaults to 10 results.
    """
    # Set defaults if not provided
    if form_types is None:
        form_types = ['8-K', '10-Q']
    if start_date is None:
        start_date = '2021-01-01'
    if end_date is None:
        end_date = '2021-06-14'
    
    search_params = {
        "query": f'"{query}"',
        "formTypes": form_types,
        "startDate": start_date,
        "endDate": end_date,
        "from": str(from_param),
        "size": str(size)
    }
    
    print(f"Executing SEC API query: {search_params}")
    
    # Call the API
    filings = fullTextSearchApi.get_filings(search_params)
    
    if not filings or "filings" not in filings or not filings["filings"]:
        return "No results found matching your criteria."
    
    # Format results
    total = filings.get("total", {}).get("value", 0)
    results_count = len(filings["filings"])
    
    formatted_results = [f"Found {total} results. Showing {results_count} results starting from position {from_param}:"]
    
    for i, filing in enumerate(filings["filings"], 1):
        formatted_results.append(f"Result {from_param + i}:")
        formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
        formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
        formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
        formatted_results.append("")
    
    return "\n".join(formatted_results)

##################################
## LANGCHAIN TOOL CREATION ##
## Create the structured tool for agent use ##
##################################
# Create the tool
sec_tool = StructuredTool.from_function(
    func=search_sec_filings,
    name="sec_filing_search",
    description="Search SEC filings for specific terms. You can specify form types like '10-K', '10-Q', '8-K', etc., date ranges with start_date and end_date in 'YYYY-MM-DD' format, and pagination with from_param and size parameters."
)

##################################
## AGENT SETUP ##
## Configure the LangChain agent ##
##################################
# Create LLM and agent
llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
agent = initialize_agent(
    [sec_tool],
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

##################################
## TESTING ##
## Test the implementation ##
##################################
# Test the direct example with default parameters (first page)
print("\n=== Testing Direct Example with Default Parameters ===")
result = search_sec_filings("LPCN 1154")
print(result)

# Test the direct example with custom page size
print("\n=== Testing Direct Example with Custom Page Size ===")
result = search_sec_filings("LPCN 1154", size=5)
print(result)

# Test the direct example with pagination (second page)
print("\n=== Testing Direct Example with Pagination (Second Page) ===")
result = search_sec_filings("LPCN 1154", from_param=5, size=5)
print(result)

# Test with date range and pagination
print("\n=== Testing with Date Range and Pagination ===")
result = search_sec_filings("LPCN 1154", start_date='2020-01-01', end_date='2022-12-31', from_param=10, size=5)
print(result)

# Test agent with pagination specified
print("\n=== Testing Agent with Pagination Specified ===")
response = agent.invoke({"input": "Find SEC filings that mention LPCN 1154, show me results 6-10"})
print(f"\nAgent response:\n{response['output']}") 