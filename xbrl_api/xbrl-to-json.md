# SEC XBRL-to-JSON Converter API Documentation

## Overview

Parse and standardize any XBRL and convert it to JSON or pandas DataFrames. Extract financial statements and metadata from 10-K, 10-Q and any other SEC filing supporting XBRL. Designed for easy integration with LangChain agents.

The entire US GAAP taxonomy is fully supported. All XBRL items are fully converted into JSON, including `us-gaap`, `dei` and custom items. XBRL facts are automatically mapped to their respective context including period instants and date ranges.

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

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```bash
   pip install sec-api python-dotenv pandas
   ```
3. Set up your SEC API key in a `.env` file:
   ```
   SEC_API_KEY=your_api_key_here
   ```

## Usage

### Basic JSON Conversion
There are three ways to convert XBRL to JSON:

1. **Using HTM URL**
```python
from sec_api import XbrlApi

xbrl_api = XbrlApi("YOUR_API_KEY")

# Using HTM URL
filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm"
xbrl_json = xbrl_api.xbrl_to_json(htm_url=filing_url)

# access income statement, balance sheet and cash flow statement
print(xbrl_json["StatementsOfIncome"])
print(xbrl_json["BalanceSheets"])
print(xbrl_json["StatementsOfCashFlows"])
```

2. **Using XBRL URL**
```python
# Using XBRL URL
xbrl_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231_htm.xml"
xbrl_json = xbrl_api.xbrl_to_json(xbrl_url=xbrl_url)
```

3. **Using Accession Number**
```python
# Using Accession Number
xbrl_json = xbrl_api.xbrl_to_json(accession_no="0001564590-21-004599")
```

### DataFrame Conversion for LangChain
```python
import pandas as pd

def convert_to_dataframe(xbrl_json, statement_type="StatementsOfIncome"):
    """Convert XBRL JSON to pandas DataFrame for LangChain consumption."""
    if statement_type not in xbrl_json:
        return pd.DataFrame()
        
    data = []
    for metric, values in xbrl_json[statement_type].items():
        for entry in values:
            row = {
                'metric': metric,
                'value': float(entry['value']),
                'unit': entry['unitRef'],
                'decimals': entry['decimals'],
                'tag_type': metric.split(':')[0] if ':' in metric else 'us-gaap'  # Extract tag type (us-gaap, dei, custom)
            }
            # Add period information
            if 'period' in entry:
                if 'instant' in entry['period']:
                    row['date'] = entry['period']['instant']
                else:
                    row['start_date'] = entry['period']['startDate']
                    row['end_date'] = entry['period']['endDate']
            data.append(row)
            
    return pd.DataFrame(data)

def discover_available_tags(xbrl_json, statement_type=None):
    """
    Discover available XBRL tags in the filing.
    
    Args:
        xbrl_json: The JSON response from xbrl_to_json
        statement_type: Optional specific statement to look in (e.g., "StatementsOfIncome")
        
    Returns:
        DataFrame with columns: tag, statement_type, tag_type (us-gaap/dei/custom)
    """
    tags = []
    
    statements = [statement_type] if statement_type else xbrl_json.keys()
    
    for stmt in statements:
        if stmt in xbrl_json:
            for tag in xbrl_json[stmt].keys():
                tag_type = tag.split(':')[0] if ':' in tag else 'us-gaap'
                tags.append({
                    'tag': tag,
                    'statement_type': stmt,
                    'tag_type': tag_type
                })
    
    return pd.DataFrame(tags).drop_duplicates()

# Example usage with LangChain
xbrl_json = xbrl_api.xbrl_to_json(htm_url=filing_url)

# Get all available tags
all_tags_df = discover_available_tags(xbrl_json)
print("Available tags:")
print(all_tags_df)

# Get tags for specific statement
income_tags_df = discover_available_tags(xbrl_json, "StatementsOfIncome")
print("\nIncome Statement tags:")
print(income_tags_df)

# Convert statements to DataFrames
income_df = convert_to_dataframe(xbrl_json, "StatementsOfIncome")
balance_df = convert_to_dataframe(xbrl_json, "BalanceSheets")
cashflow_df = convert_to_dataframe(xbrl_json, "StatementsOfCashFlows")
```

### XBRL Tag Types

The API supports three types of XBRL tags:

1. **us-gaap**: Standard US GAAP taxonomy tags (e.g., "RevenueFromContractWithCustomerExcludingAssessedTax")
2. **dei**: Document and Entity Information tags (e.g., "EntityRegistrantName")
3. **custom**: Company-specific custom tags (usually prefixed with company identifier)

You can use the `discover_available_tags()` function to explore available tags in a filing. This is particularly useful for:
- Understanding what financial metrics are available
- Finding statement-specific tags
- Identifying custom tags used by a company
- Building dynamic queries based on available data

## Response Format

The API returns a structured JSON object containing financial statements. Example response structure:

```python
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
      },
      {
        "decimals": "-6",
        "unitRef": "usd",
        "period": {
          "startDate": "2018-09-30",
          "endDate": "2019-09-28"
        },
        "value": "260174000000"
      }
    ]
  }
}
```

## Example URLs for Testing

```python
# Tesla 10-K (2020)
htm_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
xbrl_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231_htm.xml"
accession_no = "0001564590-21-004599"

# Apple 10-K (2020)
htm_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm"
xbrl_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926_htm.xml"
accession_no = "0000320193-20-000096"
```
