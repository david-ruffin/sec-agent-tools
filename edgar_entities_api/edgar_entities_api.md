# SEC Edgar Entities API Documentation

## Overview

The SEC Edgar Entities API provides access to information about over 800,000 EDGAR filing entities since 1994. This implementation is specifically designed for use with LangChain agents, providing structured responses and comprehensive error handling.

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```bash
   pip install sec-api python-dotenv
   ```
3. Set up your SEC API key in a `.env` file:
   ```
   SEC_API_KEY=your_api_key_here
   ```

## Available Functions

### 1. get_data(search_request)

Search and retrieve entity information using various criteria.

```python
from sec_api import EdgarEntitiesApi

edgarEntitiesApi = EdgarEntitiesApi("YOUR_API_KEY")

# Example search request
search_request = {
    "query": "cik:1318605",  # Search by CIK
    "from": "0",             # Pagination start
    "size": "50",            # Number of results
    "sort": [{"cikUpdatedAt": {"order": "desc"}}]  # Sort options
}

response = edgarEntitiesApi.get_data(search_request)
print(response["data"])  # Access the data directly
```

#### Parameters
- `search_request` (dict): A dictionary containing search parameters
  - `query` (str): Search query (e.g., "cik:1318605", "ticker:TSLA")
  - `from` (str): Starting index for pagination
  - `size` (str): Number of results to return
  - `sort` (list): Sorting options

#### Response Format
```python
{
    "data": [
        {
            "id": "1318605",
            "cik": "1318605",
            "name": "Tesla, Inc.",
            "sic": "3711",
            "sicLabel": "Motor Vehicles & Passenger Car Bodies",
            "businessAddress": {
                "street1": "3500 DEER CREEK RD",
                "city": "PALO ALTO",
                "state": "CA",
                "zip": "94304",
                "country": ""
            },
            "fiscalYearEnd": "1231",
            "stateOfIncorporation": "DE",
            "phone": "650-681-5000",
            "irsNo": "912197729",
            "formTypes": {
                "10-K": true,
                "10-Q": true,
                "8-K": true,
                # ... other form types
            },
            "filerCategory": "Large Accelerated Filer",
            "auditorName": "PricewaterhouseCoopers LLP",
            "auditorLocation": "San Jose, California",
            # ... additional metadata fields
        }
    ]
}
```

#### Query Examples
1. Search by CIK:
   ```python
   search_request = {"query": "cik:1318605"}
   ```

2. Search by Ticker:
   ```python
   search_request = {"query": "ticker:TSLA"}
   ```

3. Search by Company Name:
   ```python
   search_request = {"query": "name:Tesla"}
   ```

4. Search by SIC Code:
   ```python
   search_request = {"query": "sic:3711"}
   ```

## Implementation Versions

### Version 1 (Current)
- Added `get_data` function with search capabilities
- Implemented exact response format from SEC API
- Added pagination support
- Added sorting options
- Added comprehensive error handling
- Added query examples for common searches

## Next Steps
1. Test the `get_data` function with various search criteria
2. Document additional functions as they are discovered
3. Add helper methods for common searches (by CIK, ticker, etc.)
4. Add response data field descriptions

## Contributing

Feel free to submit issues and enhancement requests! 