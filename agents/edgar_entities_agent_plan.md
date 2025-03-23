# EDGAR Entities Database API Agent Plan

## API Overview
The EDGAR Entities Database API provides access to information on over 800,000 EDGAR filing entities that have filed with the SEC since 1994. This agent serves as an interface to query and retrieve detailed entity information including CIK numbers, IRS numbers, state of incorporation, fiscal year end dates, SIC codes, auditor information, and more.

## Available Methods

### get_entity_data(search_request)
Primary method for querying the EDGAR entities database with the following parameters:

#### Parameters
- query (str): Query string in the format "field:value" (e.g., "cik:1318605")
- from (str, optional): Starting index for pagination (default: "0")
- size (str, optional): Number of results to return (default: "50")
- sort (list, optional): Sorting criteria in the format [{"field": {"order": "asc/desc"}}]

#### Supported Query Fields
- cik: Central Index Key
- irsNumber: IRS Number
- stateOfIncorporation: State code
- fiscalYearEnd: Fiscal year end date (MMDD format)
- sicCode: Standard Industrial Classification code
- currentAuditor: Current auditing firm
- latestICFRAuditDate: Latest ICFR audit date
- filerCategory: SEC filer category

## Response Format
```json
{
    "query": {
        "query": string,
        "from": string,
        "size": string,
        "sort": array
    },
    "total": number,
    "data": [
        {
            "cik": string,
            "irsNumber": string,
            "stateOfIncorporation": string,
            "fiscalYearEnd": string,
            "sicCode": string,
            "currentAuditor": string,
            "latestICFRAuditDate": string,
            "filerCategory": string,
            "cikUpdatedAt": string
        }
    ]
}
```

## Implementation Notes

1. Input Validation
   - Validate query string format
   - Ensure pagination parameters are valid numbers
   - Verify sort criteria format

2. Error Handling
   - Handle API authentication errors (401)
   - Handle rate limiting (429)
   - Handle malformed queries (400)
   - Handle not found errors (404)
   - Handle server errors (500)

3. Response Processing
   - Parse and validate response JSON
   - Convert date strings to appropriate format
   - Handle empty result sets

4. Best Practices
   - Implement rate limiting (max 10 requests per second)
   - Cache frequently accessed results
   - Support proxy configuration for corporate environments

## Usage Examples

1. Query by CIK:
```python
search_request = {
    "query": "cik:1318605",
    "from": "0",
    "size": "50",
    "sort": [{"cikUpdatedAt": {"order": "desc"}}]
}
```

2. Query by State of Incorporation:
```python
search_request = {
    "query": "stateOfIncorporation:DE",
    "from": "0",
    "size": "50"
}
```

3. Query by SIC Code with sorting:
```python
search_request = {
    "query": "sicCode:7370",
    "from": "0",
    "size": "50",
    "sort": [{"fiscalYearEnd": {"order": "asc"}}]
}
``` 