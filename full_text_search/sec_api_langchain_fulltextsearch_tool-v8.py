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
    # Check for formType in the query and warn if it conflicts with form_types parameter
    if form_types and "formType:" in query.lower():
        print(f"Warning: Your query includes 'formType:' parameter but you've also specified form_types={form_types}.")
        print("The SEC API will use both constraints, which might yield fewer results than expected.")
        print("Consider removing one of these constraints if you're not getting expected results.")

    # Set defaults if not specified
    form_types = form_types or ["8-K", "10-Q"]
    start_date = start_date or "2021-01-01"
    end_date = end_date or "2021-06-14"
    
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
        
        # Save raw API response to file if requested
        if save_to_file:
            filename = output_file or f"sec_api_results_{query.replace(' ', '_')[:20]}.json"
            with open(filename, 'w') as f:
                json.dump(filings, f, indent=2)
            print(f"Raw API response saved to {filename}")
            
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
    for i, filing in enumerate(filings["filings"][:display_count], from_param + 1):
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
            - Proximity searches: '"climate change"~10' finds terms within 10 words of each other
            - Field-specific searches: 'formType:10-K AND revenue'
            - Grouping: '(AI OR "artificial intelligence") AND risk'
    
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
        
    - Output options:
        - save_to_file: Save the raw API response to a JSON file (default: False)
        - output_file: Filename to save the API response (default: auto-generated)
    
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
## ADVANCED QUERY EXAMPLES ##
## Examples demonstrating complex query patterns ##
##################################
def run_advanced_query_examples():
    """Run examples showcasing advanced query capabilities of the SEC API."""
    
    print("\n" + "=" * 80)
    print("ADVANCED SEC API QUERY EXAMPLES")
    print("=" * 80)
    
    # Example 1: Boolean Operators with Grouping
    print("\n--- Example 1: Boolean Operators with Grouping ---")
    print("Query: (AI OR \"artificial intelligence\") AND \"risk factors\"")
    print("Description: Find filings that mention either 'AI' or 'artificial intelligence' in")
    print("             conjunction with the phrase 'risk factors'")
    boolean_grouping_result = search_sec_filings(
        query='(AI OR "artificial intelligence") AND "risk factors"',
        form_types=["10-K"],
        start_date="2022-01-01",
        end_date="2023-12-31", 
        max_results=2,
        include_snippets=True,
        use_exact_match=False
    )
    print(boolean_grouping_result)
    
    # Example 2: Wildcards and Exclusions
    print("\n--- Example 2: Wildcards and Exclusions ---")
    print("Query: cyber* -insurance")
    print("Description: Find filings containing terms starting with 'cyber' (like cybersecurity,")
    print("             cyberattack, etc.) but excluding filings that mention 'insurance'")
    wildcard_exclusion_result = search_sec_filings(
        query="cyber* -insurance",
        form_types=["10-K", "8-K"],
        start_date="2022-01-01",
        end_date="2023-12-31",
        max_results=2,
        include_snippets=True,
        use_exact_match=False
    )
    print(wildcard_exclusion_result)
    
    # Example 3: Proximity Search
    print("\n--- Example 3: Proximity Search ---")
    print("Query: \"climate change\"~10")
    print("Description: Find filings where 'climate' and 'change' appear within 10 words of each other")
    proximity_result = search_sec_filings(
        query='"climate change"~10',
        form_types=["10-K"],
        start_date="2022-01-01",
        end_date="2023-12-31",
        max_results=2,
        include_snippets=True,
        use_exact_match=False
    )
    print(proximity_result)
    
    # Example 4: Field-Specific Search
    print("\n--- Example 4: Field-Specific Search ---")
    print("Query: formType:10-K AND ticker:AAPL AND \"supply chain\"")
    print("Description: Find 10-K filings from Apple Inc. that mention 'supply chain'")
    field_specific_result = search_sec_filings(
        query='formType:10-K AND ticker:AAPL AND "supply chain"',
        start_date="2018-01-01",
        end_date="2023-12-31",
        max_results=2,
        include_snippets=True,
        use_exact_match=False
    )
    print(field_specific_result)
    
    # Example 5: Complex Multi-Criteria Search
    print("\n--- Example 5: Complex Multi-Criteria Search ---")
    print("Query: (\"revenue decline\" OR \"decreased revenue\") AND (covid* OR pandemic) -guidance")
    print("Description: Find filings mentioning revenue declines in relation to COVID/pandemic,")
    print("             but exclude those just mentioning 'guidance'")
    complex_result = search_sec_filings(
        query='("revenue decline" OR "decreased revenue") AND (covid* OR pandemic) -guidance',
        form_types=["10-Q", "10-K"],
        start_date="2020-01-01",
        end_date="2022-12-31",
        max_results=2,
        include_snippets=True,
        use_exact_match=False
    )
    print(complex_result)
    
    # Example 6: Date Range Comparison
    print("\n--- Example 6: Date Range Comparison (ESG Reporting Evolution) ---")
    print("Description: Compare how ESG reporting has evolved over time by running the same")
    print("             query for different time periods and comparing the counts")
    
    # Early period (2018-2019)
    early_period_result = search_sec_filings(
        query='"ESG" OR "Environmental Social Governance"',
        form_types=["10-K"],
        start_date="2018-01-01",
        end_date="2019-12-31",
        count_only=True,
        use_exact_match=False
    )
    print("2018-2019 Period:")
    print(early_period_result)
    
    # Middle period (2020-2021)
    middle_period_result = search_sec_filings(
        query='"ESG" OR "Environmental Social Governance"',
        form_types=["10-K"],
        start_date="2020-01-01",
        end_date="2021-12-31",
        count_only=True,
        use_exact_match=False
    )
    print("2020-2021 Period:")
    print(middle_period_result)
    
    # Recent period (2022-2023)
    recent_period_result = search_sec_filings(
        query='"ESG" OR "Environmental Social Governance"',
        form_types=["10-K"],
        start_date="2022-01-01",
        end_date="2023-12-31",
        count_only=True,
        use_exact_match=False
    )
    print("2022-2023 Period:")
    print(recent_period_result)
    
    # Example 7: Industry-Specific Search
    print("\n--- Example 7: Industry-Specific Search (Semiconductor Supply Chain) ---")
    print("Query: semiconductor AND (\"supply chain\" OR shortage OR constraint) AND formType:10-K")
    print("Description: Find 10-K filings discussing semiconductor supply chain issues")
    industry_specific_result = search_sec_filings(
        query='semiconductor AND ("supply chain" OR shortage OR constraint) AND formType:10-K',
        start_date="2020-01-01",
        end_date="2023-12-31",
        max_results=2,
        include_snippets=True,
        use_exact_match=False
    )
    print(industry_specific_result)
    
    # Example 8: Competitive Analysis
    print("\n--- Example 8: Competitive Analysis (AI Adoption in Big Tech) ---")
    print("Description: Compare how frequently major tech companies mention AI technologies")
    
    companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    for ticker in companies:
        company_result = search_sec_filings(
            query=f'ticker:{ticker} AND ("artificial intelligence" OR "machine learning" OR "neural network" OR "generative AI" OR "LLM" OR "large language model")',
            form_types=["10-K", "10-Q"],
            start_date="2021-01-01",
            end_date="2023-12-31",
            count_only=True,
            use_exact_match=False
        )
        print(f"{ticker}: {company_result}")
    
    print("\n" + "=" * 80)
    print("Advanced Query Examples Complete")
    print("=" * 80)

##################################
## AGENT EXAMPLES WITH ADVANCED QUERIES ##
## Examples of LangChain agent using advanced queries ##
##################################
def run_agent_examples():
    """Run examples of the LangChain agent using advanced SEC API queries."""
    
    print("\n" + "=" * 80)
    print("LANGCHAIN AGENT WITH ADVANCED SEC API QUERIES")
    print("=" * 80)
    
    # Example 1: Boolean operators in natural language
    print("\n--- Agent Example 1: Boolean Operators in Natural Language ---")
    result1 = agent.invoke({
        "input": "Find SEC filings that mention either 'climate change' or 'global warming' in 10-K forms from 2022, and show me snippets from the text"
    })
    print(f"\nAgent response:\n{result1['output']}")
    
    # Example 2: Exclusions in natural language
    print("\n--- Agent Example 2: Exclusions in Natural Language ---")
    result2 = agent.invoke({
        "input": "Find 10-K filings from 2022 that discuss cybersecurity but don't mention insurance"
    })
    print(f"\nAgent response:\n{result2['output']}")
    
    # Example 3: Complex multi-criteria search
    print("\n--- Agent Example 3: Complex Multi-Criteria Search ---")
    result3 = agent.invoke({
        "input": "Find recent SEC filings from Apple that discuss supply chain challenges related to either COVID or semiconductor shortages"
    })
    print(f"\nAgent response:\n{result3['output']}")
    
    print("\n" + "=" * 80)
    print("Agent Examples Complete")
    print("=" * 80)

##################################
## MAIN FUNCTION ##
## Run examples if executed directly ##
##################################
if __name__ == "__main__":
    # Run the advanced query examples
    run_advanced_query_examples()
    
    # Run the agent examples
    run_agent_examples()
    
    # Print completion message
    print("\n=== SEC API LangChain Tool v8 Complete ===")
    print("Advanced query capabilities have been demonstrated")
    print("The tool now supports the full range of SEC API query syntax")
    print("See README.md for detailed documentation and usage examples.") 