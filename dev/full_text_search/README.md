# SEC-API LangChain Integration

This project implements a LangChain tool that integrates with the SEC-API service to search for SEC filings. The tool provides a user-friendly interface for accessing the SEC's EDGAR database through natural language queries.

## Implementation Plan

### Iteration 1: Basic Functionality with Pagination ✅ COMPLETE
**Goal**: Implement basic search functionality with pagination support.
- Add parameters: `from_param` and `size` for pagination control
- Ensure the tool returns total count of matching filings
- Document the behavior of these parameters
- FINDINGS: The API's behavior regarding the `size` parameter is not always consistent. Sometimes it returns more results than requested.

### Iteration 2: Enhanced Result Display ✅ COMPLETE
**Goal**: Improve the display and organization of search results.
- Add `max_results` parameter to control how many results to display (default: 3)
- Add optional parameters for including additional metadata fields
- Add `include_snippets` parameter to show text snippets when available
- Improve formatting of the output for better readability
- FINDINGS: 
  - All metadata fields were successfully implemented
  - `max_results` parameter works as expected, limiting the display but not the API call
  - Text snippets are included when requested, but may not always be available in API response for all filing types

### Iteration 3: Advanced Query Support ✅ COMPLETE
**Goal**: Add support for advanced query syntax and improve overall functionality.
- Add `use_exact_match` parameter to control matching behavior
- Support for Boolean operators (AND, OR, NOT)
- Support for wildcards and exclusions
- Add `count_only` parameter for retrieving just the count of matching results
- Improve error handling for invalid queries
- FINDINGS:
  - Advanced query functionality works well with proper syntax
  - Boolean operators (AND, OR, NOT) and wildcards (*) function as expected
  - Error handling successfully catches and reports invalid query syntax
  - Count-only mode provides an efficient way to check result counts without retrieving details

### Iteration 4: Sorting Capabilities ✅ COMPLETE
**Goal**: Add sorting options for search results.
- Add `sort_by` parameter to specify field for sorting results
- Add `sort_order` parameter for ascending/descending sort
- Enhance result display to include sorting information
- FINDINGS:
  - Sorting by common fields like "filedAt", "formType", "cik", and "companyName" works correctly
  - The tool properly validates sort order values and defaults to "desc" for invalid inputs
  - Result headers now include clear information about the applied sorting
  - The agent can effectively process natural language sort requests

### Iteration 5: Final Polish and Documentation ✅ COMPLETE
**Goal**: Finalize code organization, improve documentation, and add comprehensive examples.
- Reorganize code with clear separation of concerns
- Add constants for default values
- Extract helper functions for better maintainability
- Provide comprehensive docstrings with examples
- Add detailed tool description for agent understanding
- FINDINGS:
  - The refactored code is more maintainable with clear section organization
  - Helper functions improve code readability and reduce duplication
  - Comprehensive documentation makes the tool more accessible to users
  - The tool now supports the full range of SEC-API FullTextSearchApi functionality

## Key Features

1. **Flexible Search Options**:
   - Basic search with exact phrase matching
   - Advanced query syntax with Boolean operators (AND, OR, NOT)
   - Support for wildcards and exclusions
   - Filtering by form types and date ranges

2. **Pagination and Result Control**:
   - Control starting position with `from_param`
   - Set results per page with `size`
   - Limit displayed results with `max_results`
   - Get just the count with `count_only`

3. **Result Customization**:
   - Include detailed metadata with `include_all_metadata`
   - Show text snippets with `include_snippets`
   - Sort results by any field with `sort_by` and `sort_order`

4. **Error Handling**:
   - Graceful handling of invalid queries
   - Clear error messages for troubleshooting
   - Fallback defaults for invalid parameter values

## Usage Examples

```python
# Basic search with default parameters
search_sec_filings("LPCN 1154")

# Advanced search with Boolean operators
search_sec_filings(
    "LPCN 1154 OR LPCN 1107",
    use_exact_match=False
)

# Get only the count of matching filings
search_sec_filings("LPCN 1154", count_only=True)

# Search with pagination, sorting, and detailed results
search_sec_filings(
    "LPCN 1154",
    form_types=["10-K", "10-Q"],
    start_date="2020-01-01",
    end_date="2022-12-31",
    from_param=5,
    size=10,
    max_results=5,
    include_all_metadata=True,
    include_snippets=True,
    sort_by="filedAt",
    sort_order="desc"
)
```

## Agent Integration Examples

The tool can be used with LangChain agents to provide natural language access to SEC filings:

```
"Find SEC filings mentioning LPCN 1154 filed in 2022"
"How many 10-K forms mention climate change between 2020 and 2022?"
"Show me the 5 most recent 8-K filings that mention revenue growth"
"Find SEC filings with either 'artificial intelligence' or 'machine learning', show all metadata"
```

## API Key Setup

To use this tool, you need:
1. An SEC-API key (obtain from sec-api.io)
2. An OpenAI API key (for the LangChain agent)

Store these in a `.env` file:
```
SEC_API_KEY=your_sec_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
``` 