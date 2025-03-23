# SEC Filing Analyzer

A specialized tool for analyzing SEC filings using the SEC-API.io service with a focus on delivering concise, accurate answers.

## Overview

The SEC Filing Analyzer is a Python-based system designed to provide clear, accurate insights from SEC filings. It leverages the official SEC-API.io service to access filing data through a collection of specialized agents, each focused on a specific API endpoint.

The system operates on an agent-based architecture with:

1. **Specialized Agents**: Each SEC-API endpoint has its own dedicated agent
2. **Consistent Interfaces**: All agents follow a standardized pattern for error handling and response formatting
3. **Comprehensive Coverage**: Provides access to a wide range of SEC filing data, from basic searches to specialized databases

This approach ensures modularity, maintainability, and consistent behavior across all SEC-API interactions, making the system reliable and extensible.

### Core Principles

This system focuses on providing accurate answers to queries about SEC filings by:

1. **Clean API Abstractions**: Each agent provides a simplified, standardized interface to its corresponding SEC-API endpoint
2. **Complete Functionality Coverage**: All agents expose the full capabilities of their respective SEC-API endpoints
3. **Consistent Error Handling**: Uniform approach to parameter validation, rate limits, and API errors
4. **Clear Documentation**: Each agent has its own plan file detailing its methods, parameters, and response formats

## Current Implementation Status

The project currently has 8 fully implemented and tested agents:

1. **Filing Search Agent**: Searches for SEC filings with full query language support
   - Exposes the `QueryApi.get_filings()` endpoint
   - Supports complex query language for finding specific filings
   - Handles pagination and sorting

2. **Full Text Search Agent**: Performs content-based searches within filings
   - Exposes the `FullTextSearchApi.get_filings()` endpoint
   - Supports phrase searches and form type filtering
   - Includes relevance-based sorting

3. **Section Extraction Agent**: Extracts specific sections from filings
   - Exposes the `ExtractorApi.get_section()` endpoint
   - Supports all sections in 10-K, 10-Q, and 8-K filings
   - Provides both HTML and text output formats

4. **XBRL Converter Agent**: Converts XBRL data to structured JSON
   - Exposes the `XbrlApi.xbrl_to_json()` endpoint
   - Supports multiple input methods (HTM URL, XBRL URL, accession number)
   - Returns structured financial statements

5. **Mapping Agent**: Resolves company identifiers and lists companies
   - Exposes the `MappingApi.resolve()` endpoint
   - Supports resolution by name, ticker, CIK, and CUSIP
   - Includes listing companies by exchange, sector, or industry

6. **EDGAR Entities Agent**: Retrieves company information
   - Exposes the `EdgarEntitiesApi.get_data()` endpoint
   - Supports querying by CIK, state, SIC code, and more
   - Returns detailed entity information

7. **Download Agent**: Downloads SEC filings in HTML format
   - Uses the `RenderApi.get_file()` endpoint
   - Downloads complete filings, primary documents, or exhibits
   - Manages file organization on disk

8. **PDF Generator Agent**: Generates PDF versions of SEC filings
   - Uses the `PdfGeneratorApi.get_pdf()` endpoint
   - Supports complete filings, primary documents, and exhibits
   - Includes quality options for PDF generation

Each agent follows a standardized interface with:
- Uniform input validation
- Consistent error handling with HTTP-style status codes
- Rate limiting management
- Comprehensive test suite

### Architecture

The system uses a modular architecture with each component having a single responsibility:

1. **Agent Modules**: Each SEC-API endpoint has three dedicated files:
   - `{agent_name}_agent_plan.md`: Documents the API's capabilities, methods, parameters, and response formats
   - `{agent_name}_agent.py`: Implements the agent as a pure Python function
   - `test_{agent_name}_agent.py`: Tests all functionality and error handling

2. **Common Components**:
   - Standard response format across all agents
   - Consistent error handling patterns
   - Uniform API key management

3. **Planned Orchestration Layer**: 
   - LangGraph-based workflow management (in development)
   - Smart planner node for determining which agents to use
   - Context preservation between agent calls

This architecture allows each agent to focus solely on its specific SEC-API endpoint, making the code easier to maintain, test, and extend.

## Features

### Agent Capabilities

Each agent provides a standardized interface to its SEC-API endpoint, enabling:

1. **Data Retrieval**: Direct access to all data available through the SEC-API
2. **Query Construction**: Support for complex query parameters and filters
3. **Error Handling**: Consistent management of API errors, rate limits, and invalid parameters
4. **Response Formatting**: Uniform response structure across all agents

### Agent Usage Pattern

All agents follow the same pattern:

```python
from {agent_name}_agent import {agent_name}_agent

# Call the agent with the required parameters
result = {agent_name}_agent(
    param1="value1",
    param2="value2",
    # ...
)

# Check the response status
if result["status"] == 200:
    # Handle successful response
    data = result["data"]
    print(f"Retrieved data: {data}")
else:
    # Handle error
    print(f"Error {result['status']}: {result['error']}")
```

### Query Capabilities

The system will handle various types of SEC filing queries, including:

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

### Agent Implementation Pattern

Each agent follows this exact structure:

```python
def agent_name(
    # Required parameters
    required_param1: Type,
    required_param2: Type,
    # Optional parameters
    optional_param1: Type = default_value,
    optional_param2: Type = default_value,
    # Standard parameters
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Agent for the SEC-API [Endpoint Name].
    
    This agent [description of what this agent does].
    
    Args:
        required_param1: Description of parameter
        required_param2: Description of parameter
        optional_param1: Description of parameter
        optional_param2: Description of parameter
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (the primary payload when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Function implementation follows a standard pattern...
```

This consistent pattern makes the codebase easy to maintain and extend.

### Response Format

All agents return responses in this standard format:

```python
{
    "status": 200,  # HTTP-style status code
    "data": {...},  # The primary payload (None if error)
    "error": None,  # Error message (None if success)
    "metadata": {   # Contextual information
        "timestamp": "2023-06-01T12:34:56",
        "api_endpoint": "QueryApi.get_filings",
        "params": {
            # Parameter values used in the call
        }
    }
}
```

## Installation and Setup

### Prerequisites

- Python 3.8+
- SEC-API.io API key

### Dependencies

```
sec-api>=1.0.0      # Official SEC-API Python client
python-dotenv>=1.0.0  # For environment variables
```

Additional dependencies for future development:
```
langgraph>=0.0.23   # For agent orchestration (when implemented)
langchain>=0.1.0    # For LLM integration (when implemented)
openai>=1.0.0       # For OpenAI API access (when implemented)
```

### Environment Setup

Create a `.env` file in the project root with your API key:

```
SEC_API_KEY=your_sec_api_key
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`

## Usage

### Agent Usage Examples

Example usage of the Filing Search Agent:

```python
from filing_search_agent import filing_search_agent

# Search for Apple's 10-K filings from 2023
result = filing_search_agent({
    "query": "cik:320193 AND formType:\"10-K\" AND filedAt:[2023-01-01 TO 2023-12-31]",
    "from": "0",
    "size": "10",
    "sort": [{"filedAt": {"order": "desc"}}]
})

# Check the response
if result["status"] == 200:
    filings = result["data"]["filings"]
    print(f"Found {len(filings)} filings")
    for filing in filings:
        print(f"{filing['formType']} filed on {filing['filedAt']}")
else:
    print(f"Error {result['status']}: {result['error']}")
```

Example usage of the Section Extraction Agent:

```python
from section_extraction_agent import section_extraction_agent

# Extract the Risk Factors section from a filing
result = section_extraction_agent(
    filing_url="https://www.sec.gov/Archives/edgar/data/...",
    section_id="1A",  # Risk Factors
    output_format="text"
)

# Check the response
if result["status"] == 200:
    content = result["data"]
    print(f"Section content (first 100 chars): {content[:100]}...")
else:
    print(f"Error {result['status']}: {result['error']}")
```

## File Structure

```
sec/
├── .env                              # Environment variables
├── requirements.txt                  # Project dependencies
├── README.md                         # Project documentation
├── roadmap.txt                       # Development roadmap
├── history.txt                       # Development history
├── suggestions.txt                   # Future improvement ideas
│
├── agents/                           # Agent implementations
│   ├── filing_search_agent_plan.md   # Filing Search Agent plan
│   ├── filing_search_agent.py        # Filing Search Agent implementation
│   ├── test_filing_search_agent.py   # Filing Search Agent tests
│   ├── full_text_search_agent_plan.md # Full Text Search Agent plan
│   ├── full_text_search_agent.py     # Full Text Search Agent implementation
│   ├── test_full_text_search_agent.py # Full Text Search Agent tests
│   └── ...                           # Other agent files
│
├── sec_api_knowledge.py              # SEC API knowledge mappings
├── sec_analyzer.py                   # Basic implementation (legacy)
└── sec_analyzer_langgraph.py         # LangGraph implementation (in development)
```

## License

[MIT License](LICENSE)

## Acknowledgements

- [SEC-API.io](https://sec-api.io) for providing the API services
- [LangChain](https://langchain.com) for the toolkit
- [LangGraph](https://github.com/langchain-ai/langgraph) for state management 

## Development Roadmap

The project will continue development in these phases:

1. **Agent Implementation**: Complete the remaining agents (25 more planned)
2. **Agent Orchestration**: Implement LangGraph-based workflow management
3. **Context Preservation**: Add context tracking between agent calls
4. **Advanced Query Processing**: Build multi-filing comparison capabilities

See `roadmap.txt` for detailed development plans. 