# Full Text Search API Agent Plan

## API Overview
Full-text search allows you to search the full text of all EDGAR filings submitted since 2001. The full text of a filing includes all data in the filing itself as well as all attachments (such as exhibits) to the filing.

## Available Methods

The SEC-API Python FullTextSearchApi class exposes the following methods:

1. **`get_filings(query)`**
   - Searches the full text of all filings and their attachments
   - Takes a query object with search parameters
   - Returns matching filings with metadata

## Query Parameters

The query object can include:

1. **`query`**:
   - The search text, can include phrases in quotes
   - Required parameter
   - Example: `"climate change"` (searches for the exact phrase)

2. **`formTypes`**:
   - Array of form types to search within
   - Optional parameter
   - Example: `['10-K', '10-Q', '8-K']`

3. **`startDate`**:
   - Start date for the search range (YYYY-MM-DD)
   - Optional parameter
   - Example: `'2021-01-01'`

4. **`endDate`**:
   - End date for the search range (YYYY-MM-DD)
   - Optional parameter
   - Example: `'2021-12-31'`

## Query Syntax

The query syntax supports:

1. **Exact phrases**:
   - Enclosed in double quotes
   - Example: `"climate risk"` (exact phrase)

2. **Boolean operators**:
   - Use `AND`, `OR`, and `NOT`
   - Example: `"climate risk" AND disclosure`

3. **Wildcards**:
   - Use `*` for wildcard matches
   - Example: `sustainab*` (matches sustainable, sustainability, etc.)

4. **Proximity search**:
   - Use `~` with a number to find terms within a certain distance
   - Example: `"climate change"~10` (finds where terms are within 10 words)

## Response Format
The response includes:

- `id` - Unique identifier for the filing
- `cik` - Company CIK
- `ticker` - Company ticker
- `companyName` - Name of the company
- `formType` - SEC form type
- `filedAt` - Filing date
- `fileUrl` - URL to the full filing
- `excerpts` - Snippets of text showing the search term in context

## Implementation Notes

The full text search agent should:

1. Support all search features:
   - Exact phrase matching
   - Boolean operators
   - Wildcards
   - Proximity search
   - Date range filtering
   - Form type filtering

2. Validate inputs:
   - Query syntax
   - Date formats
   - Form types

3. Handle all error cases:
   - Invalid query syntax
   - Invalid dates
   - Network/API errors
   - Rate limiting
   - No results found

4. Return standardized response format:
   - Status code
   - Error message (if applicable)
   - Results array
   - Query metadata
   - Context-aware excerpts

The agent should be a "dumb" tool that exposes the full text search capabilities of the API while maintaining consistent error handling and response structure. 