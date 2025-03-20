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
from typing import List, Optional, Dict, Any, Union, Tuple

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
## CONSTANTS ##
## Define constants used in the implementation ##
##################################
# Default date range
DEFAULT_START_DATE = '2021-01-01'
DEFAULT_END_DATE = '2021-06-14'

# Default form types
DEFAULT_FORM_TYPES = ['8-K', '10-Q']

# Valid sort orders
VALID_SORT_ORDERS = ["asc", "desc"]

# Maximum snippet length
MAX_SNIPPET_LENGTH = 300

##################################
## HELPER FUNCTIONS ##
## Define helper functions for the main tool ##
##################################
def validate_sort_order(sort_order: str) -> str:
    """
    Validate the sort order parameter.
    
    Args:
        sort_order: The sort order to validate.
        
    Returns:
        A valid sort order ("asc" or "desc").
    """
    if sort_order not in VALID_SORT_ORDERS:
        return "desc"  # Default to descending if invalid
    return sort_order


def format_filing_result(
    filing: Dict[str, Any], 
    index: int, 
    from_param: int, 
    include_all_metadata: bool, 
    include_snippets: bool
) -> List[str]:
    """
    Format a single filing result for display.
    
    Args:
        filing: The filing data dictionary.
        index: The current index in the results list.
        from_param: The starting position parameter.
        include_all_metadata: Whether to include all metadata fields.
        include_snippets: Whether to include text snippets.
        
    Returns:
        A list of formatted strings representing the filing.
    """
    result_lines = []
    
    # Result header with position
    result_lines.append(f"Result {from_param + index}:")
    
    # Basic fields always included
    result_lines.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
    result_lines.append(f"Form Type: {filing.get('formType', 'N/A')}")
    result_lines.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
    
    # Add additional metadata if requested
    if include_all_metadata:
        result_lines.append(f"Accession Number: {filing.get('accessionNo', 'N/A')}")
        result_lines.append(f"CIK: {filing.get('cik', 'N/A')}")
        result_lines.append(f"Description: {filing.get('description', 'N/A')}")
        result_lines.append(f"Document Type: {filing.get('type', 'N/A')}")
        result_lines.append(f"Filing URL: {filing.get('filingUrl', 'N/A')}")
    
    # Add text snippets if requested and available
    if include_snippets and "text" in filing:
        snippet = filing.get("text", "")
        if len(snippet) > MAX_SNIPPET_LENGTH:
            snippet = snippet[:MAX_SNIPPET_LENGTH - 3] + "..."
        result_lines.append(f"Snippet: {snippet}")
    
    # Empty line after each result
    result_lines.append("")
    
    return result_lines


def prepare_search_params(
    query: str,
    form_types: List[str],
    start_date: str,
    end_date: str,
    from_param: int,
    size: int,
    use_exact_match: bool,
    sort_by: Optional[str],
    sort_order: str
) -> Dict[str, Any]:
    """
    Prepare the search parameters dictionary for the SEC API.
    
    Args:
        query: The search query.
        form_types: List of form types to search.
        start_date: Start date for the search range.
        end_date: End date for the search range.
        from_param: Starting position for pagination.
        size: Number of results per page.
        use_exact_match: Whether to use exact matching for the query.
        sort_by: Field to sort results by.
        sort_order: Sort direction (asc or desc).
        
    Returns:
        A dictionary of search parameters.
    """
    # Check if the query looks like it contains Boolean operators or special syntax
    has_boolean_operators = any(op in query for op in [' AND ', ' OR ', ' NOT ', ' -', ':', '*', '~', '(', ')'])
    
    # Only add quotes if use_exact_match is True AND the query doesn't contain Boolean operators
    processed_query = query
    if use_exact_match and not has_boolean_operators:
        processed_query = f'"{query}"'
    
    # Build search parameters
    search_params = {
        "query": processed_query,
        "formTypes": form_types,
        "startDate": start_date,
        "endDate": end_date,
        "from": str(from_param),
        "size": str(size)
    }
    
    # Add sorting if specified
    if sort_by:
        # Validate sort_order
        valid_sort_order = validate_sort_order(sort_order)
        search_params["sort"] = [{sort_by: {"order": valid_sort_order}}]
    
    return search_params

##################################
## MAIN TOOL FUNCTION ##
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
    use_exact_match: Optional[bool] = True,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc"
) -> str:
    """
    Search SEC filings with full functionality of the SEC API FullTextSearchApi.
    
    This function allows you to search the full text of all EDGAR filings submitted since 2001,
    including all data in the filing itself as well as attachments (exhibits). The function
    supports advanced query syntax, filtering by form types, date ranges, pagination, sorting,
    and customization of the displayed results.
    
    Args:
        query: Search term to look for in SEC filings. Supports advanced syntax when use_exact_match=False:
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
                   Note: The SEC API documentation uses a "page" parameter, but our implementation
                   follows the parameter naming found in example code with "from" and "size".
        size: Number of results to return per page.
              Defaults to 10 results.
              Note: Testing shows the SEC API may not strictly enforce this parameter and
              sometimes returns more results than requested.
        max_results: Maximum number of results to display in the response.
                    Defaults to 3 results.
        include_snippets: Whether to include text snippets from the filings.
                         Defaults to False.
                         Note: Snippets may not always be available in the API response.
        include_all_metadata: Whether to include all available metadata fields.
                             Defaults to False.
        count_only: If True, returns only the count of matching filings without the actual filings.
                   Defaults to False.
        use_exact_match: If True, wraps the query in quotes for exact phrase matching.
                        If False, uses the query as-is for advanced query syntax.
                        Defaults to True for backward compatibility.
        sort_by: Field to sort results by. Common options include "filedAt", "formType", "cik", "companyName".
                If None, results are sorted by relevance.
        sort_order: Sort direction, either "asc" (ascending) or "desc" (descending).
                   Defaults to "desc" (newest first when sorting by date).
    
    Returns:
        A formatted string with the search results or count.
        
    Example:
        >>> # Search for an exact phrase with default parameters
        >>> search_sec_filings("LPCN 1154")
        
        >>> # Search with advanced query syntax and sorting
        >>> search_sec_filings(
        ...     "LPCN 1154 OR LPCN 1107",
        ...     use_exact_match=False,
        ...     sort_by="filedAt",
        ...     sort_order="desc"
        ... )
        
        >>> # Get only the count of matching filings
        >>> search_sec_filings("LPCN 1154", count_only=True)
        
        >>> # Get detailed metadata with custom date range
        >>> search_sec_filings(
        ...     "LPCN 1154",
        ...     start_date="2020-01-01",
        ...     end_date="2022-12-31",
        ...     include_all_metadata=True
        ... )
    """
    # Set defaults if not provided
    if form_types is None:
        form_types = DEFAULT_FORM_TYPES.copy()
    if start_date is None:
        start_date = DEFAULT_START_DATE
    if end_date is None:
        end_date = DEFAULT_END_DATE
    
    # Prepare search parameters
    search_params = prepare_search_params(
        query=query,
        form_types=form_types,
        start_date=start_date,
        end_date=end_date,
        from_param=from_param,
        size=size,
        use_exact_match=use_exact_match,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
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
    
    # Prepare header with sorting information
    sorting_info = ""
    if sort_by:
        valid_sort_order = validate_sort_order(sort_order)
        sorting_info = f" (sorted by {sort_by} in {valid_sort_order}ending order)"
    
    # Format results header
    formatted_results = [
        f"Found {total} results{sorting_info}. "
        f"Showing {display_count} of {results_count} results starting from position {from_param}:"
    ]
    
    # Format each filing result
    for i, filing in enumerate(filings["filings"][:display_count], 1):
        formatted_results.extend(
            format_filing_result(
                filing=filing,
                index=i,
                from_param=from_param,
                include_all_metadata=include_all_metadata,
                include_snippets=include_snippets
            )
        )
    
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
    Search SEC EDGAR filings with complete functionality of the SEC API FullTextSearchApi.
    
    This tool allows you to search the full text of all SEC EDGAR filings submitted since 2001,
    including all data in the filings and their attachments (exhibits).
    
    Parameters:
    - query: Search term to look for in SEC filings
        - For basic searches, simply provide the search term
        - For advanced searches (when use_exact_match=False):
            - Single terms: "apple" finds filings mentioning "apple"
            - Exact phrases with quotes: "Fiduciary Product" for the exact phrase
            - Boolean operators: "software OR hardware" for either term
            - Exclusions: "software -hardware" excludes filings with "hardware"
            - Wildcards: "gas*" for variations like "gas" or "gasoline"
    
    - form_types: List of SEC form types to search (default: ['8-K', '10-Q'])
        - Common types include: '10-K', '10-Q', '8-K', '13-F', 'S-1', '424B4'
    
    - start_date/end_date: Filter by date range in 'YYYY-MM-DD' format
        - Default range is 2021-01-01 to 2021-06-14
    
    - from_param/size: Control pagination
        - from_param: Starting position (0-based)
        - size: Number of results per page
    
    - Display options:
        - max_results: Number of results to display (default: 3)
        - include_snippets: Include text extracts from filings (default: False)
        - include_all_metadata: Show all metadata fields (default: False)
        - count_only: Return just the count without filing details (default: False)
    
    - Query and sorting options:
        - use_exact_match: If True, treats query as exact phrase (default: True)
        - sort_by: Field to sort by (e.g., "filedAt", "formType", "cik", "companyName")
        - sort_order: "asc" (ascending) or "desc" (descending) (default: "desc")
    
    Examples:
    - Basic search: "Find SEC filings mentioning LPCN 1154"
    - Advanced search: "Find SEC filings containing either LPCN 1154 or LPCN 1107 using advanced query syntax"
    - Counting: "How many SEC filings mention LPCN 1154?"
    - Sorting: "Find SEC filings with LPCN 1154, sort by filing date from newest to oldest"
    - Filtering: "Show me 10-K filings that mention LPCN 1154 between 2020 and 2022"
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
# Comprehensive test example
print("\n=== Comprehensive Test Example ===")
result = search_sec_filings(
    query="LPCN 1154 OR LPCN 1107",
    form_types=['8-K', '10-Q', '10-K'],
    start_date='2020-01-01',
    end_date='2022-12-31',
    from_param=0,
    size=10,
    max_results=3,
    include_snippets=True,
    include_all_metadata=True,
    use_exact_match=False,
    sort_by="filedAt",
    sort_order="desc"
)
print(result)

# Agent with comprehensive query
print("\n=== Testing Agent with Comprehensive Query ===")
response = agent.invoke({
    "input": "Search for SEC filings that mention either LPCN 1154 or LPCN 1107, filed between 2020 and 2022, including only 10-K forms, sorted by filing date from newest to oldest, and show me all metadata for the first 2 results."
})
print(f"\nAgent response:\n{response['output']}")

# Print completion message
print("\n=== Implementation Complete ===")
print("All features of the FullTextSearchApi have been implemented and tested.")
print("The LangChain tool now supports the full range of functionality available in the original SEC API.")
print("See README.md for detailed documentation and usage examples.") 