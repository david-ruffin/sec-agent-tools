# SEC Filing Analyzer

A specialized tool for analyzing SEC filings using the SEC-API.io service with a focus on delivering concise, accurate answers.

## Overview

The SEC Filing Analyzer is a Python-based tool designed to provide clear, accurate insights from SEC filings. It leverages the official SEC-API.io service to access filing data, with a focus on:

1. **Concise Answers**: Delivering precise information without unnecessary verbosity
2. **Data Accuracy**: Ensuring all information comes directly from official SEC filings
3. **User-Friendly Format**: Presenting complex financial information in an easily digestible format

The system operates on the principle that users need direct answers to their questions about SEC filings without having to navigate complex financial documents or understand the underlying API structure.

### Core Functionality

This system focuses on providing accurate answers to queries about SEC filings by:

1. **Natural Language Understanding**: Converting user questions into specific SEC data requests
2. **Direct Data Retrieval**: Accessing the exact sections and data points needed
3. **Focused Summarization**: Presenting only the most relevant information in a clear format

## Current Implementation Status

The current working implementation (`sec_analyzer_langgraph_v2.py`) provides the following functionality:

1. **Four-Step Process**:
   - **Planning**: Analyzes natural language queries to extract company, form type, section, and date requirements
   - **Company Resolution**: Resolves company names/tickers to their SEC CIK numbers
   - **Filing Search**: Locates the specific filing (e.g., most recent 10-K)
   - **Section Extraction**: Extracts the complete text of the requested section

2. **File Output**:
   - Saves the complete, unmodified section text to a file named `output_TICKER_FORM_SECTION.txt`
   - For example: `output_AAPL_10-K_1A.txt` for Apple's Risk Factors

3. **Console Display**:
   - Shows a preview (first 500 characters) of the extracted section in the console
   - Indicates where the full content is saved

4. **Technical Details**:
   - Uses SEC-API.io's Extractor API with the "text" format for section extraction
   - Handles command line arguments for direct queries
   - Currently contains HTML entities (e.g., `&#8217;`) in the extracted text that need proper decoding

5. **Current Limitations**:
   - No summarization or analysis of extracted content (raw extraction only)
   - HTML entity decoding needs improvement for better readability
   - No web interface (console application only)

Future versions will build on this foundation to add the analytical capabilities described in the Features section below, including summarization, comparative analysis, and a proper web interface with formatted output.

### Architecture

The system follows a modular design with three main components:

1. **API Modules**: Specialized modules for each SEC-API endpoint:
   - `query_api/`: For searching and retrieving SEC filings metadata
   - `extractor_api/`: For extracting specific sections from filings
   - `edgar_entities_api/`: For accessing entity information
   - `mapping_api/`: For company name resolution
   - `full_text_search/`: For searching within filing content

2. **Knowledge Module** (`sec_api_knowledge.py`): Contains mappings for SEC filing analysis, including section IDs and XBRL field names.

3. **Core Analyzer** (`sec_analyzer.py`): The main implementation that processes user queries and generates concise responses.

4. **Enhanced Implementations**:
   - `sec_analyzer_with_chunking.py`: Adds text chunking for analyzing large documents
   - `sec_analyzer_langgraph.py`: Implements sophisticated state management using LangGraph

## Features

### Response Structure

The system provides responses in a consistent, user-friendly format:

1. **Direct Answer**: A clear, concise answer to the query
2. **Source Reference**: The specific filing and section where the data was extracted
3. **Key Data Points**: Important metrics or statements relevant to the query

Example response:
```
Microsoft's Management Discussion and Analysis highlights strong cloud growth and continued investment in AI initiatives during FY2023.

Source: Microsoft 10-K (2023), Section 7 (MD&A)
```

### Query Capabilities

The system handles various types of SEC filing queries, including:

1. **Financial Data Extraction**:
   ```
   What was Immix Biopharma's revenue for Q3 2023?
   How many shares outstanding did Apple have in their latest 10-K?
   ```

2. **Textual Section Analysis**:
   ```
   Summarize Microsoft's Management Discussion and Analysis from 2023
   What are Tesla's main risk factors in their latest 10-Q?
   ```

3. **Comparative Analysis**:
   ```
   Compare risk factors between Apple's most recent quarterly filings
   Compare revenue recognition between Microsoft and Amazon for 2023
   ```

4. **Change Detection**:
   ```
   Identify new accounting policies in Amazon's latest quarterly report
   Detect cybersecurity disclosure changes in Tesla's recent 10-Q
   ```

## Implementation Details

### Knowledge Base Integration

The `sec_api_knowledge.py` module contains essential mappings for:

1. **Section ID Mappings**: Complete mappings for all sections in 10-K, 10-Q, and 8-K filings
2. **XBRL Field Mappings**: Standardized XBRL tags for common financial metrics

### Processing Flow

1. **Query Processing**: Understand user's question and identify key elements (company, filing type, section)
2. **Company Resolution**: Accurately identify the requested company through ticker/name resolution
3. **Filing Retrieval**: Locate and access the specific filing documents 
4. **Section Extraction**: Pull the exact section or data point needed
5. **Answer Generation**: Format a clear, concise response with the essential information

### Response Focus

The system's responses prioritize:

1. **Accuracy**: Ensuring information comes directly from SEC sources
2. **Brevity**: Providing clear answers without lengthy explanations
3. **Relevance**: Including only information that directly answers the query
4. **Attribution**: Clearly stating the source for verification

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
python sec_analyzer.py "What did Microsoft report as revenue for Q1 2023?"
```

For enhanced analysis with chunking:

```bash
python sec_analyzer_with_chunking.py "Summarize Apple's latest Risk Factors"
```

For the LangGraph implementation:

```bash
python sec_analyzer_langgraph.py "Identify accounting policy changes in Amazon's recent 10-Q"
```

For the current LangGraph v2 implementation:

```bash
python sec_analyzer_langgraph_v2.py "What were Apple's risk factors in their 2023 10-K?"
```

Example output:
```
Step 1: Planning Phase - Complete
Query Analysis:
- Company: Apple
- Form Type: 10-K
- Section: 1A (Risk Factors)
- Date Range: 2023
- Tool Recommendation: SECQueryAPI and SECExtractSection

Step 2: Company Resolution - Complete
Resolved: Apple Inc. (AAPL) - CIK: 0000320193

Step 3: Filing Search - Complete
Found: 10-K filed on 2023-11-03

Step 4: Section Extraction - Complete
Extracted: Section 1A from 10-K

Preview (first 500 chars):
 Item 1A. Risk Factors 

The Company&#8217;s business, reputation, results of operations, financial condition and stock price can be affected by a number of factors, whether currently known or unknown, including those described below. When any one or more of these risks materialize from time to time, the Company&#8217;s business, reputation, results of operations, financial condition and stock price can be materially and adversely affected. 

Because of the following factors, as well as other fa...

Full content written to output_AAPL_10-K_1A.txt
```

For backward compatibility, older implementations are still available:

```bash
python sec_analyzer.py "What did Microsoft report as revenue for Q1 2023?"
python sec_analyzer_with_chunking.py "Summarize Apple's latest Risk Factors"
python sec_analyzer_langgraph.py "Identify accounting policy changes in Amazon's recent 10-Q"
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
├── extractor_api/            # SEC Extractor API implementation
├── edgar_entities_api/       # SEC EDGAR Entities API implementation
├── mapping_api/              # SEC Mapping API implementation
└── full_text_search/         # SEC Full Text Search implementation
```

## License

[MIT License](LICENSE)

## Acknowledgements

- [SEC-API.io](https://sec-api.io) for providing the API services
- [LangChain](https://langchain.com) for the toolkit
- [LangGraph](https://github.com/langchain-ai/langgraph) for state management 

## Planned Improvements

### HTML Entity Handling
The current version outputs raw text from the SEC-API which contains HTML entities (e.g., `&#8217;` for apostrophes). Future updates will:
- Implement proper HTML entity decoding using Python's `html.unescape()`
- Format output for better readability

### Web Interface
A web interface is planned with the following features:
- Option to view the entire section without downloading files
- Properly formatted HTML display with preserved document structure
- Different output formats (text/HTML) depending on user preference
- Search and navigation capabilities within sections

### Analysis Features
Building on the current extraction capabilities:
- Summarization of key points in sections
- Comparative analysis between filings
- Highlighting changes between sequential filings
- Extraction of specific data points (financials, metrics, etc.) 