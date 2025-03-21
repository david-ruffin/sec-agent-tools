# SEC Filing Analyzer

A specialized tool for analyzing SEC filings using the SEC-API.io service with Contextual Retrieval enhancement.

## Overview

The SEC Filing Analyzer is a Python-based tool designed to extract, analyze, and provide insights from SEC filings. It leverages the official SEC-API.io service to access filing data, enhanced with Contextual Retrieval techniques for more accurate and relevant responses.

### Core Principle: Data Availability

This system operates based on the principle that data can only be queried if it's available through the official SEC-API Python library. The system is designed to work with the following data sources:

- **SEC Query API**: For finding and filtering SEC filings
- **SEC Extractor API**: For retrieving specific sections from filings
- **SEC XBRL API**: For extracting standardized financial data
- **SEC Mapping API**: For company information resolution
- **SEC Edgar Entities API**: For retrieving entity-specific information
- **SEC Full Text Search API**: For searching within filing content

### Architecture

The system follows a modular design with three main components:

1. **API Modules**: Specialized modules for each SEC-API endpoint:
   - `query_api/`: For searching and retrieving SEC filings metadata
   - `extractor_api/`: For extracting specific sections from filings
   - `edgar_entities_api/`: For accessing entity information
   - `mapping_api/`: For company name resolution
   - `full_text_search/`: For searching within filing content

2. **Knowledge Module** (`sec_api_knowledge.py`): Contains mappings and helper functions for SEC filing analysis, including section IDs, XBRL field names, and query intent detection.

3. **Core Analyzer** (`sec_analyzer.py`): The main implementation that processes user queries, selects appropriate SEC-API tools, and generates responses with proper context.

4. **Enhanced Implementations**:
   - `sec_analyzer_with_chunking.py`: Adds text chunking for analyzing large documents
   - `sec_analyzer_langgraph.py`: Implements a more sophisticated state management using LangGraph

## Features

### Contextual Retrieval for SEC Filings

The system implements a lightweight version of Contextual Retrieval specifically designed for SEC filings:

1. **Context Preservation**: Maintains critical context between retrieval steps, including:
   - Company identification (name, ticker, CIK)
   - Filing type and date
   - Section hierarchy and relationships
   - Financial period information

2. **Specialized Retrieval**: Uses different retrieval strategies based on query type:
   - Direct XBRL lookup for financial metrics (revenue, assets, etc.)
   - Section extraction with metadata for textual analysis
   - Multi-filing retrieval for comparative questions

3. **Query Understanding**: Analyzes user queries to determine:
   - The company or companies being referenced
   - The time period or filing dates of interest
   - The type of information being requested (financial vs. textual)
   - The specific SEC form types to search

### Query Capabilities

The system can handle various types of SEC filing queries, including:

1. **Financial Data Extraction**:
   ```
   What did Immix Biopharma report as revenue for the quarter ended September 30, 2024?
   How many shares outstanding did Apple have as of their latest 10-K?
   ```

2. **Textual Section Analysis**:
   ```
   Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K
   What are the main risk factors mentioned in Tesla's latest 10-Q?
   ```

3. **Comparative Analysis**:
   ```
   Identify and list risk factors that are similar across Apple's four most recent quarterly filings.
   Compare revenue recognition policies between Microsoft and Amazon in their 2023 10-K filings.
   ```

4. **Change Detection**:
   ```
   Identify new significant accounting policies introduced in Amazon's latest quarterly report.
   Detect and analyze new footnote disclosures related to cybersecurity in Tesla's most recent 10-Q.
   ```

## Implementation Details

### Contextual Knowledge Base

The `sec_api_knowledge.py` module serves as a comprehensive knowledge base containing:

1. **Section ID Mappings**: Complete mappings for all sections in 10-K, 10-Q, and 8-K filings
2. **XBRL Field Mappings**: Standardized XBRL tags for common financial metrics
3. **Query Intent Detection**: Functions to determine what type of information is being requested
4. **Tool Selection Logic**: Logic to determine which SEC-API tool is appropriate for each query

### API Modules

The project contains specialized modules for each SEC-API endpoint:

1. **Query API** (`query_api/`): 
   - Implementation for searching SEC filings
   - Includes query building and result parsing
   - Supports filtering by company, form type, date, etc.

2. **Extractor API** (`extractor_api/`):
   - Implementation for extracting specific sections from filings
   - Handles section ID mapping and content formatting
   - Supports both text and HTML output formats

3. **Edgar Entities API** (`edgar_entities_api/`):
   - Access to entity-specific information from EDGAR
   - Entity metadata retrieval and processing
   - Support for entity relationships

4. **Mapping API** (`mapping_api/`): 
   - Company name resolution functionality
   - Maps between various identifiers (name, ticker, CIK)
   - Standardizes company information format

5. **Full Text Search API** (`full_text_search/`):
   - Searching within filing content
   - Advanced query processing for content searches
   - Result ranking and formatting

### Context Management

The system manages context through a simple but effective approach:

1. **Step-by-Step Context Tracking**: Each retrieval step stores and passes relevant context to subsequent steps
2. **Context Enrichment**: Retrieved data is enriched with metadata about its source and meaning
3. **Context-Aware Response Generation**: Final responses include relevant contextual information for clarity

## Installation and Setup

### Prerequisites

- Python 3.8+
- SEC-API.io API key
- OpenAI API key (for LLM integration)

### Dependencies

```
sec-api>=1.0.0
langchain>=0.1.0
langchain_openai>=0.0.1
python-dotenv>=1.0.0
openai>=1.0.0
langgraph>=0.0.23  # Only needed for LangGraph implementation
```

### Environment Setup

Create a `.env` file in the project root with your API keys:

```
SEC_API_KEY=your_sec_api_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4  # or another supported model
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`

## Usage

### Command Line Interface

Run the basic analyzer:

```bash
python sec_analyzer.py "What did Microsoft report as revenue for the quarter ended March 31, 2023?"
```

For enhanced analysis with chunking:

```bash
python sec_analyzer_with_chunking.py "Summarize the Risk Factors section of Apple's latest 10-K"
```

For the LangGraph implementation:

```bash
python sec_analyzer_langgraph.py "Identify changes in accounting policies between Amazon's Q1 and Q2 reports in 2023"
```

### Interactive Mode

All implementations support an interactive mode:

```bash
python sec_analyzer.py
```

## File Structure

```
sec/
├── .env                      # Environment variables
├── requirements.txt          # Project dependencies
├── README.md                 # Project documentation
├── roadmap.txt               # Development roadmap
├── history.txt               # Development history
├── suggestions.txt           # Future improvement ideas
│
├── sec_api_knowledge.py      # SEC API knowledge mappings
├── sec_analyzer.py           # Basic implementation
├── sec_analyzer_with_chunking.py  # Implementation with text chunking
├── sec_analyzer_langgraph.py # Implementation with LangGraph
│
├── query_api/                # SEC Query API implementation
│   ├── query_api.md          # Documentation
│   └── queryapi_toolv5.py    # Current implementation
│
├── extractor_api/            # SEC Extractor API implementation
│   ├── Extractor_API.md      # Documentation
│   └── extractor_apiv9.py    # Current implementation
│
├── edgar_entities_api/       # SEC EDGAR Entities API implementation
│   ├── edgar_entities_api.md # Documentation
│   └── edgar_entities_apiv2.py # Current implementation
│
├── mapping_api/              # SEC Mapping API implementation
│   └── mapping_apiv1.py      # Current implementation
│
└── full_text_search/         # SEC Full Text Search implementation
    ├── sec_api_advanced_queries.md # Documentation
    └── sec_api_langchain_fulltextsearch_tool_v8.py # Current implementation
```

## License

[MIT License](LICENSE)

## Acknowledgements

- [SEC-API.io](https://sec-api.io) for providing the API services
- [LangChain](https://langchain.com) for the toolkit
- [LangGraph](https://github.com/langchain-ai/langgraph) for state management 