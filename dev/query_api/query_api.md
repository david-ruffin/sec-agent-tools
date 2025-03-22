# SEC EDGAR Query API Tool

The SEC EDGAR Query API Tool provides a powerful interface to search and filter through the entire SEC EDGAR filings database. This tool is designed to be used with LangChain agents and provides structured access to over 18 million filings dating back to 1993.

## Features

- Search across all SEC EDGAR filings using complex query parameters
- Filter by form type, date range, company identifiers (CIK, ticker)
- Support for advanced query syntax with boolean operators
- Pagination and sorting capabilities
- Structured response format optimized for AI agent consumption
- Built-in validation and error handling
- Comprehensive metadata for each filing

## Installation

```bash
pip install sec-api
```

## Authentication

The tool requires an SEC-API key. Set it in your environment variables:

```bash
export SEC_API_KEY=your_api_key
```

Or use a .env file:

```
SEC_API_KEY=your_api_key
```

## Basic Usage

```python
from query_api.queryapi_toolv5 import SECQueryTool

# Initialize the tool
query_tool = SECQueryTool()

# Simple search for Tesla's 10-K filings
query = {
    "query": "ticker:TSLA AND formType:\"10-K\"",
    "from": "0",
    "size": "10",
    "sort": [{ "filedAt": { "order": "desc" } }]
}

results = query_tool.search_filings(query)
```

## Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| query | Main search query with support for boolean operators | "ticker:AAPL AND formType:\"10-Q\"" |
| from | Starting position for pagination | "0" |
| size | Number of results to return | "10" |
| sort | Sorting criteria | [{ "filedAt": { "order": "desc" } }] |

## Advanced Query Examples

### Search by Date Range
```python
query = {
    "query": "filedAt:[2020-01-01 TO 2020-12-31] AND formType:\"10-K\"",
    "from": "0",
    "size": "10"
}
```

### Multiple Form Types
```python
query = {
    "query": "ticker:MSFT AND (formType:\"10-K\" OR formType:\"10-Q\")",
    "from": "0",
    "size": "10"
}
```

### Full Text Search with Specific Terms
```python
query = {
    "query": "formType:\"8-K\" AND content:\"acquisition\"",
    "from": "0",
    "size": "10"
}
```

## Response Format

The tool returns structured responses containing:

```python
{
    "total": {
        "value": 100,
        "relation": "eq"
    },
    "filings": [
        {
            "id": "...",
            "accessionNo": "0001640147-21-000066",
            "cik": "1640147",
            "ticker": "COIN",
            "companyName": "Coinbase Global, Inc.",
            "companyNameLong": "Coinbase Global, Inc. (Exact name of registrant...)",
            "formType": "10-Q",
            "description": "Quarterly report [Sections 13 or 15(d)]",
            "filedAt": "2021-05-17T20:06:33-04:00",
            "linkToFilingDetails": "https://www.sec.gov/Archives/edgar/data/1640147/000164014721000066/0001640147-21-000066-index.htm",
            "linkToHtmlAnnouncement": "https://www.sec.gov/Archives/edgar/data/1640147/000164014721000066/coin-20210331.htm",
            # ... additional metadata
        }
    ],
    "query_info": {
        "total_results": 100,
        "showing_results": 10,
        "query": "original_query",
        "time_taken": "0.123s"
    }
}
```

## Error Handling

The tool includes comprehensive error handling for:
- Invalid queries
- API rate limits
- Network issues
- Authentication errors
- Malformed responses

## Tool Versions

The tool has multiple versions with progressive improvements:

- v1: Basic query functionality
- v2: Added error handling and validation
- v3: Enhanced metadata processing
- v4: Improved response formatting
- v5: Advanced query capabilities and comprehensive documentation

## Integration with LangChain

The tool is designed to work seamlessly with LangChain agents:

```python
from langchain.agents import Tool
from query_api.queryapi_toolv5 import SECQueryTool

query_tool = SECQueryTool()

tools = [
    Tool(
        name="SEC_Filing_Search",
        func=query_tool.search_filings,
        description="Search SEC EDGAR filings with complex queries"
    )
]
```

## Best Practices

1. Use specific queries to limit result size
2. Implement pagination for large result sets
3. Cache frequently accessed results
4. Handle rate limits appropriately
5. Validate query parameters before sending

## References

- [SEC-API Documentation](https://sec-api.io/docs)
- [SEC EDGAR Website](https://www.sec.gov/edgar.shtml)
- [API Rate Limits](https://sec-api.io/docs/rate-limit) 