"""
# CUSIP/CIK/Ticker Mapping API Agent Plan

## API Overview
The Mapping API provides tools to:
1. Resolve company identifiers (name, ticker, CIK, CUSIP)
2. List companies by exchange, sector, or industry

## Available Methods

The SEC-API Python MappingApi class exposes the following methods:

1. **`resolve(identifier_type, identifier_value)`**
   - Resolves a company identifier or lists companies by a category
   - `identifier_type` can be:
     - `name` - Company name
     - `ticker` - Stock ticker symbol
     - `cik` - CIK number
     - `cusip` - CUSIP identifier
     - `exchange` - Stock exchange name
     - `sector` - Industry sector
     - `industry` - Specific industry
   - `identifier_value` is the value to resolve or filter by

## Identifier Types and Values

### Company Resolution

1. **By Name**:
   - `identifier_type`: `name`
   - `identifier_value`: Company name or part of name
   - Example: `resolve("name", "Apple")`

2. **By Ticker**:
   - `identifier_type`: `ticker`
   - `identifier_value`: Stock ticker symbol
   - Example: `resolve("ticker", "AAPL")`

3. **By CIK**:
   - `identifier_type`: `cik`
   - `identifier_value`: CIK number (with or without leading zeros)
   - Example: `resolve("cik", "320193")`

4. **By CUSIP**:
   - `identifier_type`: `cusip`
   - `identifier_value`: CUSIP identifier
   - Example: `resolve("cusip", "037833100")`

### Company Listing

1. **By Exchange**:
   - `identifier_type`: `exchange`
   - `identifier_value`: Exchange name (e.g., "NYSE", "NASDAQ")
   - Example: `resolve("exchange", "NYSE")`

2. **By Sector**:
   - `identifier_type`: `sector`
   - `identifier_value`: Sector name (e.g., "Technology", "Healthcare")
   - Example: `resolve("sector", "Technology")`

3. **By Industry**:
   - `identifier_type`: `industry`
   - `identifier_value`: Industry name (e.g., "Software", "Biotechnology")
   - Example: `resolve("industry", "Software")`

## Response Format

### Company Resolution Response
When resolving a company identifier, the response includes:

For name searches:
- Array of matching companies with:
  - `cik` - Company CIK number
  - `ticker` - Stock ticker symbol
  - `name` - Company name
  - `exchange` - Stock exchange
  - `isDelisted` - Whether the company is delisted
  - `category` - Company category

For ticker, CIK, or CUSIP searches:
- Single company object with:
  - `cik` - Company CIK number
  - `ticker` - Stock ticker symbol
  - `name` - Company name
  - `exchange` - Stock exchange
  - `isDelisted` - Whether the company is delisted
  - `category` - Company category

### Company Listing Response
When listing companies by exchange, sector, or industry:
- Array of company names

## Implementation Notes

The mapping agent should:

1. Support all identifier types:
   - `name` - Company name search
   - `ticker` - Ticker symbol resolution
   - `cik` - CIK number resolution
   - `cusip` - CUSIP identifier resolution
   - `exchange` - Exchange listing
   - `sector` - Sector listing
   - `industry` - Industry listing

2. Handle all value formats:
   - Partial name matching
   - Case-insensitive searches
   - CIK numbers with or without leading zeros
   - Standard CUSIP format

3. Validate inputs:
   - Identifier type must be valid
   - Identifier value must be provided
   - Value format must be appropriate for type

4. Handle all error cases:
   - Invalid identifier type
   - Invalid identifier value
   - No matches found
   - Network/API errors
   - Rate limiting

5. Return standardized response format:
   - Status code
   - Error message (if applicable)
   - Result data (company info or company list)
   - Metadata about the request

The agent should be a "dumb" tool that exposes the full functionality of the Mapping API while maintaining consistent error handling and response structure.
""" 