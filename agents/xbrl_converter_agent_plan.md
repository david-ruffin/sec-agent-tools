# XBRL-To-JSON Converter API Agent Plan

## API Overview
Parse and standardize any XBRL and convert it to JSON or pandas dataframes. Extract financial statements and metadata from 10-K, 10-Q and any other SEC filing supporting XBRL.

The entire US GAAP taxonomy is fully supported. All XBRL items are fully converted into JSON, including `us-gaap`, `dei` and custom items. XBRL facts are automatically mapped to their respective context including period instants and date ranges.

## Available Methods

The SEC-API Python XbrlApi class exposes the following methods:

1. **`xbrl_to_json(htm_url=None, xbrl_url=None, accession_no=None)`**
   - Converts XBRL data to structured JSON
   - Supports three methods of conversion:
     - Using HTML filing URL (htm_url) ending with .htm
     - Using XBRL file URL (xbrl_url) ending with .xml
     - Using accession number (accession_no)
   - At least one parameter must be provided

## Supported Financial Statements

All financial statements are accessible and standardized:

* StatementsOfIncome
* StatementsOfIncomeParenthetical
* StatementsOfComprehensiveIncome
* StatementsOfComprehensiveIncomeParenthetical
* BalanceSheets
* BalanceSheetsParenthetical
* StatementsOfCashFlows
* StatementsOfCashFlowsParenthetical
* StatementsOfShareholdersEquity
* StatementsOfShareholdersEquityParenthetical

Variants such as `ConsolidatedStatementsofOperations` or `ConsolidatedStatementsOfLossIncome` are automatically standardized to their root name, e.g. `StatementsOfIncome`.

## Response Format
Each statement item in the response includes:

- `decimals` - Decimal precision
- `unitRef` - Unit of measurement (usually "usd")
- `period` - Time period
  - `startDate` - Period start date (for ranges)
  - `endDate` - Period end date (for ranges)
  - `instant` - Point in time (for balances)
- `value` - The numerical value

Example income statement item:
```json
{
  "StatementsOfIncome": {
    "RevenueFromContractWithCustomerExcludingAssessedTax": [
      {
        "decimals": "-6",
        "unitRef": "usd",
        "period": {
          "startDate": "2019-09-29",
          "endDate": "2020-09-26"
        },
        "value": "274515000000"
      }
    ]
  }
}
```

## Implementation Notes

The XBRL converter agent should:

1. Support all three conversion methods:
   - HTML filing URL (ending with .htm)
   - XBRL file URL (ending with .xml)
   - Accession number

2. Return all standardized financial statements:
   - Income Statements
   - Balance Sheets
   - Cash Flow Statements
   - Comprehensive Income
   - Shareholders' Equity
   - Including all parenthetical versions

3. Validate inputs:
   - At least one parameter must be provided
   - URLs must be valid SEC.gov URLs
   - Accession numbers must be properly formatted

4. Handle all error cases:
   - Invalid/missing parameters
   - Network/API errors
   - Rate limiting
   - Invalid XBRL data

5. Return standardized response format:
   - Status code
   - Error message (if applicable)
   - Structured financial data
   - Metadata about the request

The agent should be a "dumb" tool that exposes the full functionality of the XBRL-to-JSON Converter API while maintaining consistent error handling and response structure. 