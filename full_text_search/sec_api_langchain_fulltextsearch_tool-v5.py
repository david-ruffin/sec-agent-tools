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
from typing import List, Optional, Dict, Any

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
    size: Optional[int] = 10,
    max_results: Optional[int] = 3,
    include_snippets: Optional[bool] = False,
    include_all_metadata: Optional[bool] = False,
    count_only: Optional[bool] = False,
    use_exact_match: Optional[bool] = True
) -> str:
    """
    Search SEC filings with advanced query support.
    
    Args:
        query: Search term to look for in SEC filings. Supports advanced syntax:
               - Single terms: "apple" finds filings mentioning "apple"
               - Exact phrases: Use quotes within quotes like '\\"Fiduciary Product\\"' for exact phrase matching
               - Boolean operators: "software OR hardware" finds filings with either term
               - Exclusions: "software -hardware" or "software NOT hardware" finds filings with "software" but not "hardware"
               - Wildcards: "gas*" finds variations like "gas" or "gasoline"
               
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
        max_results: Maximum number of results to display in the response.
                    Defaults to 3 results.
        include_snippets: Whether to include text snippets from the filings.
                         Defaults to False.
        include_all_metadata: Whether to include all available metadata fields.
                             Defaults to False.
        count_only: If True, returns only the count of matching filings without the actual filings.
                   Defaults to False.
        use_exact_match: If True, wraps the query in quotes for exact phrase matching.
                        If False, uses the query as-is for advanced query syntax.
                        Defaults to True for backward compatibility.
    """
    # Set defaults if not provided
    if form_types is None:
        form_types = ['8-K', '10-Q']
    if start_date is None:
        start_date = '2021-01-01'
    if end_date is None:
        end_date = '2021-06-14'
    
    # Process query - either use exact phrase match or advanced syntax
    processed_query = f'"{query}"' if use_exact_match else query
    
    search_params = {
        "query": processed_query,
        "formTypes": form_types,
        "startDate": start_date,
        "endDate": end_date,
        "from": str(from_param),
        "size": str(size)
    }
    
    print(f"Executing SEC API query: {search_params}")
    
    try:
        # Call the API
        filings = fullTextSearchApi.get_filings(search_params)
    except Exception as e:
        return f"Error executing SEC API query: {str(e)}. Please verify your query syntax."
    
    if not filings or "filings" not in filings:
        return "Error: Unexpected API response format. Please try a different query."
    
    if not filings["filings"]:
        return "No results found matching your criteria."
    
    # Format results
    total = filings.get("total", {}).get("value", 0)
    results_count = len(filings["filings"])
    
    # Return count only if requested
    if count_only:
        return f"Found {total} filings matching your criteria."
    
    # Otherwise, display results with metadata
    display_count = min(max_results, results_count)
    
    formatted_results = [f"Found {total} results. Showing {display_count} of {results_count} results starting from position {from_param}:"]
    
    for i, filing in enumerate(filings["filings"][:display_count], 1):
        formatted_results.append(f"Result {from_param + i}:")
        
        # Basic fields always included
        formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
        formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
        formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
        
        # Add additional metadata if requested
        if include_all_metadata:
            formatted_results.append(f"Accession Number: {filing.get('accessionNo', 'N/A')}")
            formatted_results.append(f"CIK: {filing.get('cik', 'N/A')}")
            formatted_results.append(f"Description: {filing.get('description', 'N/A')}")
            formatted_results.append(f"Document Type: {filing.get('type', 'N/A')}")
            formatted_results.append(f"Filing URL: {filing.get('filingUrl', 'N/A')}")
        
        # Add text snippets if requested
        if include_snippets and "text" in filing:
            snippet = filing.get("text", "")
            if len(snippet) > 300:
                snippet = snippet[:297] + "..."
            formatted_results.append(f"Snippet: {snippet}")
            
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
    description="""
    Search SEC filings with advanced query capabilities. Options include:
    - query: Supports Boolean operators (OR, NOT), exclusions (-term), wildcards (term*), and exact phrases
    - form_types: Specify SEC form types like '10-K', '10-Q', '8-K', etc. 
    - start_date/end_date: Filter by date range in 'YYYY-MM-DD' format
    - from_param/size: Control pagination (starting position and results per page)
    - max_results: Control how many results to display (default: 3)
    - include_snippets: Include text extracts from filings (default: False)
    - include_all_metadata: Show all available metadata fields (default: False)
    - count_only: Return just the count of matching filings without details (default: False)
    - use_exact_match: If True, treats query as exact phrase; if False, enables advanced syntax (default: True)
    """
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
# Test with Boolean OR operator
print("\n=== Testing with Boolean OR Operator ===")
result = search_sec_filings(
    "LPCN 1154 OR LPCN 1107", 
    use_exact_match=False
)
print(result)

# Test with Boolean NOT operator
print("\n=== Testing with Boolean NOT Operator ===")
result = search_sec_filings(
    "LPCN -1107", 
    use_exact_match=False
)
print(result)

# Test with wildcard
print("\n=== Testing with Wildcard ===")
result = search_sec_filings(
    "LPC*", 
    use_exact_match=False
)
print(result)

# Test count-only mode
print("\n=== Testing Count-Only Mode ===")
result = search_sec_filings(
    "LPCN 1154", 
    count_only=True
)
print(result)

# Test error handling with invalid syntax
print("\n=== Testing Error Handling with Invalid Syntax ===")
result = search_sec_filings(
    "LPCN 1154 AND AND",  # Intentionally invalid syntax
    use_exact_match=False
)
print(result)

# Test agent with advanced query
print("\n=== Testing Agent with Advanced Query ===")
response = agent.invoke({"input": "Find SEC filings that mention either LPCN 1154 or LPCN 1107, using advanced search syntax"})
print(f"\nAgent response:\n{response['output']}")

# Test agent with count-only query
print("\n=== Testing Agent with Count-Only Query ===")
response = agent.invoke({"input": "How many SEC filings mention LPCN 1154? Just give me the count."})
print(f"\nAgent response:\n{response['output']}") 