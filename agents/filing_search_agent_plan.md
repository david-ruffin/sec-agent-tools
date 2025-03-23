# EDGAR Filing Search & Download APIs Plan

## API Overview

The SEC-API provides several APIs for searching and downloading SEC filings:

* SEC Filing Search API - Search all SEC EDGAR filings using a powerful query language
* Real-Time Filing Stream API - Receive new filings as soon as they are published
* Download API - Download any SEC filing, exhibit and attached file
* PDF Generator API - Download SEC filings and exhibits as PDF

## Available Methods

The SEC-API Python package exposes the following classes and methods:

### QueryApi

1. **`get_filings(query, start=0, size=100)`**
   - Searches for filings matching the query
   - Supports pagination with start and size parameters
   - Returns an array of matching filings with metadata

### RealTimeApi

1. **`get_filings()`**
   - Streams new filings in real-time from SEC EDGAR

### RenderApi

1. **`get_filing(url)`**
   - Downloads any SEC EDGAR filing, exhibit or attached file in its original format
   - Supports all file types (HTML, XML, JPEG, Excel, text, PDF, etc.)

Note: The RenderApi does not provide separate methods for HTML or PDF formats, contrary to what was initially documented. Only the original format download is available through the `get_filing` method.

## Query Language
The query language supports:

1. **Field queries**:
   - `ticker`: Company ticker symbol
   - `cik`: Company CIK number
   - `companyName`: Company name
   - `formType`: SEC form type
   - `filedAt`: Filing date
   - And many more fields

2. **Boolean operators**:
   - `AND`: Both conditions must be true
   - `OR`: Either condition must be true
   - `NOT`: Condition must be false

3. **Special operators**:
   - `>`, `>=`, `<`, `<=`: Numeric comparisons
   - `:`: Exact match
   - `*`: Wildcard

## Data Coverage

* Access to over 18 million SEC EDGAR filings from 1993 to the present
* Supports all 150+ filing types, including 10-Q, 10-K, Form 4, 8-K, 13-F, S-1, 424B4, and many others
* Real-time access to newly published filings
* Every filing is linked to its corresponding CIK and ticker

## Response Format
Each filing in the query response includes:

- `id` - Unique identifier
- `accessionNo` - SEC accession number
- `cik` - Company CIK
- `ticker` - Company ticker symbol
- `companyName` - Company name
- `formType` - SEC form type
- `description` - Filing description
- `filedAt` - Filing date
- `linkToFilingDetails` - URL to filing details
- `linkToHtmlAnnouncement` - URL to HTML filing
- `linkToXbrl` - URL to XBRL data (if available)
- `xbrlFiles` - Array of XBRL files associated with the filing
- `totalFiling` - Total number of filings found

## Implementation Notes

The filing search agent should:

1. Support the full query language:
   - Field-specific searches
   - Boolean operators
   - Special operators
   - Date ranges
   - Form types

2. Handle pagination properly:
   - Default to reasonable page size
   - Support start/offset parameter
   - Include total count in response

3. ~~Enable real-time filing streaming (optional)~~ **NOTE: Real-time streaming implementation limitation**:
   - The SEC-API Python package does not provide a class-based API for real-time streaming
   - Real-time streaming is only available through WebSockets (requires `websockets` package)
   - Current implementation does not include WebSocket-based real-time streaming
   - Users requiring real-time notifications will need to implement a separate WebSocket client
   - For most use cases, regular polling using the QueryApi with recent date filters is sufficient

4. Support downloading filings in different formats:
   - Original format (the only format directly supported by the RenderApi)
   - ~~HTML~~ (not directly supported by the RenderApi)
   - ~~PDF~~ (not directly supported by the RenderApi)

5. Validate inputs:
   - Query syntax
   - Pagination parameters
   - Field names and operators
   - URL formats

6. Handle all error cases:
   - Invalid query syntax
   - Network/API errors
   - Rate limiting
   - No results found

7. Return standardized response format:
   - Status code
   - Error message (if applicable)
   - Results array
   - Pagination metadata
   - Query metadata

The agent should be a "dumb" tool that exposes the full query capabilities of the Filing Search API while maintaining consistent error handling and response structure. 