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
import json

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
    
    # Check for potential form type conflicts
    if "formType:" in query.upper() and form_types:
        print(f"WARNING: Query contains 'formType:' and form_types parameter is also specified.")
        print(f"This may cause conflicts. Consider removing one or ensuring they don't contradict.")
    
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
    sort_order: Optional[str] = "desc",
    save_to_file: Optional[bool] = False,
    output_file: Optional[str] = None
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
               - Proximity searches: '"climate change"~10' finds terms within 10 words of each other
               - Field-specific searches: 'formType:10-K AND revenue'
               - Grouping: '(AI OR "artificial intelligence") AND risk'
               
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
        save_to_file: Whether to save the raw API response to a JSON file.
                     Defaults to False.
        output_file: The filename to save the API response to if save_to_file is True.
                    If None, a default filename based on the query will be used.
    
    Returns:
        A formatted string with the search results or count.
        
    Example:
        >>> search_sec_filings("artificial intelligence", form_types=["10-K"], size=5)
    """
    try:
        # Set default values if not provided
        form_types = form_types or DEFAULT_FORM_TYPES
        start_date = start_date or DEFAULT_START_DATE
        end_date = end_date or DEFAULT_END_DATE
        
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
        
        # Print the query being executed (for debugging)
        print(f"Executing SEC API query: {search_params}")
        
        # Execute the search
        response = fullTextSearchApi.get_filings(search_params)
        
        # Save raw response if requested
        if save_to_file:
            filename = output_file or f"sec_search_{query.replace(' ', '_').lower()[:20]}.json"
            with open(filename, 'w') as f:
                json.dump(response, f, indent=2)
            print(f"Raw response saved to {filename}")
        
        # Handle count-only request
        if count_only:
            total_count = response.get('total', {}).get('value', 0)
            return f"Total filings matching '{query}': {total_count}"
        
        # Format results
        filings = response.get('filings', [])
        if not filings:
            return "No results found matching your criteria."
        
        total_count = response.get('total', {}).get('value', 0)
        actual_count = min(len(filings), max_results) if max_results else len(filings)
        
        result_lines = [f"Found {total_count} results. Showing first {actual_count}:"]
        
        # Display up to max_results (default 3)
        for idx, filing in enumerate(filings[:max_results]):
            result_lines.extend(format_filing_result(
                filing=filing,
                index=idx + 1,  # 1-based indexing for display
                from_param=from_param,
                include_all_metadata=include_all_metadata,
                include_snippets=include_snippets
            ))
        
        return "\n".join(result_lines)
    
    except Exception as e:
        return f"Error searching SEC filings: {str(e)}"

##################################
## EXAMPLES ##
## Examples of using the search function ##
##################################
def run_advanced_query_examples():
    """Run examples of advanced queries to demonstrate functionality."""
    
    print("\n=== Example 1: Basic Query ===")
    print(search_sec_filings(
        query="artificial intelligence",
        form_types=["10-K"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        max_results=2
    ))
    
    print("\n=== Example 2: Boolean Query ===")
    print(search_sec_filings(
        query="AI AND (risk OR threat)",
        form_types=["10-K", "10-Q"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        use_exact_match=False,
        max_results=2
    ))
    
    print("\n=== Example 3: Field-Specific Query ===")
    print(search_sec_filings(
        query="formType:10-K AND ticker:MSFT AND cybersecurity",
        use_exact_match=False,
        form_types=[],  # Empty because we're using formType in the query
        max_results=2
    ))
    
    print("\n=== Example 4: Count Only ===")
    print(search_sec_filings(
        query="pandemic impact",
        form_types=["8-K"],
        start_date="2020-03-01",
        end_date="2020-12-31",
        count_only=True
    ))
    
    print("\n=== Example 5: With Snippets ===")
    print(search_sec_filings(
        query="climate change mitigation",
        form_types=["10-K"],
        start_date="2022-01-01",
        end_date="2023-12-31",
        include_snippets=True,
        max_results=1
    ))
    
    print("\n=== Example 6: Sorted Results ===")
    print(search_sec_filings(
        query="supply chain disruption",
        form_types=["10-Q"],
        start_date="2022-01-01",
        end_date="2023-12-31",
        sort_by="filedAt",
        sort_order="asc",  # Oldest first
        max_results=2
    ))

##################################
## LANGCHAIN INTEGRATION ##
## Tool and agent setup ##
##################################
# Create the LangChain tool
sec_filing_search_tool = StructuredTool.from_function(
    func=search_sec_filings,
    name="sec_full_text_search",
    description="""
    Search the full text of SEC filings to find mentions of specific terms or concepts.
    Useful for finding discussions of topics in financial disclosures across many companies.
    
    Key parameters:
    - query: The search term or phrase to look for
    - form_types: List of form types (e.g., ["10-K", "10-Q", "8-K"])
    - start_date: Starting date in YYYY-MM-DD format
    - end_date: Ending date in YYYY-MM-DD format
    
    The tool returns formatted results with company name, ticker, form type, and filing date.
    """
)

# Agent example setup
def run_agent_examples():
    """Set up and run an example LangChain agent."""
    
    # Create LLM
    llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    
    # Create agent
    agent = initialize_agent(
        [sec_filing_search_tool],
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True
    )
    
    # Run the agent with example queries
    print("\n=== Agent Example 1: Climate Change Disclosures ===")
    result1 = agent.invoke({"input": "What are large tech companies saying about climate change in their recent annual reports?"})
    print(f"\nAgent response:\n{result1['output']}")
    
    print("\n=== Agent Example 2: Inflation Impact ===")
    result2 = agent.invoke({"input": "How did companies in the retail sector discuss inflation impacts in 2022?"})
    print(f"\nAgent response:\n{result2['output']}")

# Run examples if the file is executed directly
if __name__ == "__main__":
    print("=== SEC API Full Text Search Examples ===")
    
    # Example of running the search function directly
    print("\n=== Direct Function Call Example ===")
    result = search_sec_filings(
        query="metaverse",
        form_types=["10-K"],
        start_date="2022-01-01",
        end_date="2023-12-31",
        max_results=2
    )
    print(result)
    
    # Uncomment to run more examples
    # run_advanced_query_examples()
    # run_agent_examples() 