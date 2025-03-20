# SEC-API LangChain Tools

A collection of LangChain-compatible tools and functions that enable AI agents to interact with the SEC-API.io services for retrieving and analyzing SEC filing data.

## Overview

This repository contains a set of tools designed to be used with LangChain agents, enabling them to access, query, and analyze SEC filing data through the SEC-API.io service. These tools allow AI agents to perform advanced searches of SEC filings, extract specific sections from documents, access entity information, and parse XBRL financial data.

## Features

The repository provides tools for interacting with various SEC-API.io endpoints:

### Full Text Search API

- Semantic search across SEC filings
- Filter by form type, date range, company, and more
- Format results for AI consumption
- Support for advanced queries with customizable parameters

### Extractor API

- Extract specific sections from SEC filings (10-K, 10-Q, 8-K)
- Clean and format extracted content
- Retrieve metadata about sections and filings
- Process HTML content into clean text

### EDGAR Entities API

- Retrieve company information from the SEC EDGAR database
- Search for entities by CIK, ticker, or other parameters
- Format entity data into structured responses
- Convert results to pandas DataFrames for analysis

### XBRL-to-JSON API

- Convert XBRL financial statements to JSON format
- Access standardized financial data from SEC filings
- Support for accessing data via HTML URL, XBRL URL, or accession number

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/sec-api-langchain-tools.git
   cd sec-api-langchain-tools
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by creating a `.env` file:
   ```
   SEC_API_KEY=your_sec_api_key
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-3.5-turbo  # or your preferred model
   ```

## Usage

### Full Text Search

```python
from full_text_search.sec_api_langchain_fulltextsearch_tool import search_sec_filings

# Search for filings mentioning "climate change"
results = search_sec_filings(
    query="climate change", 
    form_types=["10-K"], 
    start_date="2022-01-01", 
    end_date="2023-01-01",
    size=5
)

print(results)
```

### Extract Filing Sections

```python
from extractor_api.extractor_apiv9 import SECExtractorTool

extractor = SECExtractorTool()

# Get risk factors section from a 10-K filing
filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
risk_factors = extractor.get_section(filing_url, "1A")

print(risk_factors["content"])
```

### Retrieve Entity Information

```python
from edgar_entities_api.edgar_entities_apiv2 import SECEdgarEntitiesAPI

entities_api = SECEdgarEntitiesAPI()

# Get information about Tesla
tesla_info = entities_api.get_entity_data("ticker:TSLA")

print(tesla_info)
```

### Convert XBRL to JSON

```python
from xbrl_api.xbrl_apiv1 import SECXbrlTool

xbrl_tool = SECXbrlTool()

# Convert Tesla's 10-K XBRL data to JSON
htm_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
xbrl_data = xbrl_tool.xbrl_to_json(htm_url=htm_url)

print(xbrl_data)
```

## Integration with LangChain Agents

These tools are designed to be easily integrated with LangChain agents. Example:

```python
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from full_text_search.sec_api_langchain_fulltextsearch_tool import search_sec_filings
from extractor_api.extractor_apiv9 import SECExtractorTool
from langchain.tools import StructuredTool

# Initialize the language model
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# Create tools
search_tool = StructuredTool.from_function(
    func=search_sec_filings,
    name="SECFullTextSearch",
    description="Search SEC filings for specific terms or criteria"
)

extractor = SECExtractorTool()
extract_tool = StructuredTool.from_function(
    func=extractor.get_section,
    name="SECExtractSection",
    description="Extract a specific section from an SEC filing"
)

# Create agent
agent = initialize_agent(
    tools=[search_tool, extract_tool],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Run the agent
agent.run("Find recent 10-K filings from Tesla and extract the risk factors section")
```

## API Key

You need an API key from SEC-API.io to use these tools. Sign up at [SEC-API.io](https://sec-api.io) to obtain your key.

## Available Tools

The repository includes multiple versions of each tool with different capabilities:

- `full_text_search/`: Tools for searching SEC filings
- `extractor_api/`: Tools for extracting sections from filings
- `edgar_entities_api/`: Tools for accessing entity information
- `xbrl_api/`: Tools for converting XBRL to JSON
- `query_api/`: Tools for advanced querying of SEC data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [SEC-API.io](https://sec-api.io) for providing the API service
- [LangChain](https://github.com/langchain-ai/langchain) for the agent framework 